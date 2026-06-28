#!/usr/bin/env python3
"""Stop-hook self-verification for GEOS XML authoring tasks.

Fires when the Claude Code agent ends its turn. Checks that
``/workspace/inputs/`` contains at least one ``.xml`` file and that every XML
file parses. Optionally also schema-validates against the GEOS XSD via
``xmllint``. If any check fails, emits ``decision: "block"`` on stdout so
Claude Code re-enters the agent with the reason as feedback; otherwise allows
the stop.

Environment knobs:
    GEOS_HOOK_INPUTS_DIR   Override the workspace inputs directory.
                           Defaults to ``$CLAUDE_PROJECT_DIR/inputs`` if that
                           env var is set, else ``/workspace/inputs``.
    GEOS_HOOK_MAX_RETRIES  Max times this hook will block before giving up.
                           Default 2. Counter lives in
                           ``<inputs-parent>/.verify_retry_count``.
    GEOS_HOOK_DISABLE      If ``1``/``true``/``yes``, hook no-ops.
    GEOS_HOOK_SELF_REFLECT If ``1``/``true``/``yes``, after the XML passes the
                           static checks, also block once with a self-review
                           prompt (off by default — see XN-010 section 6.3).
    GEOS_HOOK_XMLLINT      If ``1``/``true``/``yes``, run ``xmllint --schema``
                           against each XML after the parse check; block with
                           the schema errors as feedback if validation fails.
                           Off by default; counts toward the same retry
                           budget as the parse-error block.
    GEOS_HOOK_SCHEMA_PATH  Path to schema.xsd inside the container. Defaults to
                           ``/geos_lib/src/coreComponents/schema/schema.xsd``.

Input JSON is read from stdin; see Claude Code Stop-hook schema. We only read
``stop_hook_active`` to short-circuit nested stops; the rest we do not need.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SCHEMA_PATH = Path("/geos_lib/src/coreComponents/schema/schema.xsd")
MAX_ERRORS_PER_FILE = 8
MAX_FILES_REPORTED = 4


def _envflag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _event_log_path(inputs_dir: Path) -> Path:
    """Location of the hook event log — one JSONL line per hook invocation."""
    override = os.environ.get("GEOS_HOOK_EVENTS_PATH")
    if override:
        return Path(override)
    parent = inputs_dir.parent if inputs_dir.parent.exists() else Path("/tmp")
    return parent / ".verify_hook_events.jsonl"


def _log_event(
    inputs_dir: Path,
    decision: str,
    reason_category: str,
    retries_so_far: int,
    detail: str = "",
) -> None:
    path = _event_log_path(inputs_dir)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "reason_category": reason_category,
        "retries_so_far": retries_so_far,
        "detail": detail,
    }
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _allow_stop(
    inputs_dir: Path | None = None,
    reason_category: str = "allow",
    retries_so_far: int = 0,
    extra: dict | None = None,
) -> None:
    """Emit a non-blocking result and exit 0."""
    if inputs_dir is not None:
        _log_event(inputs_dir, "allow", reason_category, retries_so_far)
    payload: dict = {"continue": True, "suppressOutput": True}
    if extra:
        payload.update(extra)
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def _block(
    reason: str,
    inputs_dir: Path,
    reason_category: str,
    retries_so_far: int,
    detail: str = "",
) -> None:
    _log_event(inputs_dir, "block", reason_category, retries_so_far, detail)
    # Stop hook schema: {decision: "block", reason: "..."}.
    # Earlier versions of this file included a hookSpecificOutput block which
    # triggered Claude Code "stop-hook-error" notifications — that field is
    # for UserPromptSubmit-style hooks, not Stop hooks. Keep this minimal.
    payload = {"decision": "block", "reason": reason}
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def _inputs_dir() -> Path:
    override = os.environ.get("GEOS_HOOK_INPUTS_DIR")
    if override:
        return Path(override)
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if project:
        return Path(project) / "inputs"
    return Path("/workspace/inputs")


def _retry_counter(inputs_dir: Path) -> Path:
    parent = inputs_dir.parent if inputs_dir.parent.exists() else Path("/tmp")
    return parent / ".verify_retry_count"


def _bump_counter(counter: Path) -> int:
    try:
        current = int(counter.read_text().strip() or "0")
    except (FileNotFoundError, ValueError):
        current = 0
    current += 1
    try:
        counter.write_text(str(current))
    except OSError:
        pass
    return current


def _list_xml(inputs_dir: Path) -> list[Path]:
    if not inputs_dir.exists():
        return []
    return sorted(p for p in inputs_dir.rglob("*.xml") if p.is_file())


def _first_parse_error(paths: list[Path]) -> tuple[Path, str] | None:
    for p in paths:
        try:
            ET.parse(p)
        except ET.ParseError as exc:
            return p, str(exc)
        except (OSError, UnicodeDecodeError) as exc:
            return p, f"read error: {exc}"
    return None


def _xmllint_validate(
    paths: list[Path],
    schema_path: Path,
    inputs_dir: Path,
) -> str | None:
    """Schema-validate every XML; return formatted error feedback or None.

    Runs ``xmllint --schema <schema> --noout <file>`` per file; xmllint
    exits 0 when the file validates and non-zero with one error per line
    on failure. We collect errors, summarise, and return a feedback
    string suitable for the agent. Returns None when every file validates
    or when xmllint is unavailable (we don't penalise the agent for our
    own infra gap).
    """
    if not schema_path.exists():
        return None
    if shutil.which("xmllint") is None:
        return None
    files_with_errors: list[tuple[Path, list[str]]] = []
    for p in paths:
        try:
            res = subprocess.run(
                ["xmllint", "--schema", str(schema_path), "--noout", str(p)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        if res.returncode == 0:
            continue
        # xmllint prints errors to stderr, one per line. The summary line
        # ``<file> fails to validate`` follows; drop it.
        err_lines = []
        for line in res.stderr.splitlines():
            line = line.strip()
            if not line: continue
            if line.endswith("fails to validate"): continue
            if line.endswith("validates"): continue
            # Strip the absolute file prefix the agent already knows
            try:
                rel = p.relative_to(inputs_dir)
                line = line.replace(f"{p}:", f"{rel}:")
            except (ValueError, AttributeError):
                pass
            err_lines.append(line)
        if err_lines:
            files_with_errors.append((p, err_lines[:MAX_ERRORS_PER_FILE]))
    if not files_with_errors:
        return None

    # Build feedback. Report up to MAX_FILES_REPORTED files; reference
    # the rest by count if there are more.
    parts = []
    for p, errs in files_with_errors[:MAX_FILES_REPORTED]:
        try:
            rel = p.relative_to(inputs_dir)
        except (ValueError, AttributeError):
            rel = p
        joined = "\n  ".join(errs)
        parts.append(f"- {rel}:\n  {joined}")
    extra = len(files_with_errors) - MAX_FILES_REPORTED
    summary = "\n".join(parts)
    if extra > 0:
        summary += f"\n- ...plus {extra} more file(s) with schema errors."
    return summary
    return None


def main() -> None:
    inputs_dir = _inputs_dir()

    if _envflag("GEOS_HOOK_DISABLE"):
        _allow_stop(inputs_dir, reason_category="disabled")

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        _allow_stop(inputs_dir, reason_category="bad_hook_input")

    # Note: we do NOT early-return on payload["stop_hook_active"]. The
    # max_retries counter is the loop-protection mechanism. Early-return
    # would prevent us from catching malformed XML written by the model
    # after a no_xml block — the model can produce a parseable end_turn
    # with broken XML, and we want the hook to catch that too.
    stop_active = bool(payload.get("stop_hook_active"))

    counter = _retry_counter(inputs_dir)
    max_retries = int(os.environ.get("GEOS_HOOK_MAX_RETRIES", "2") or 2)

    xml_files = _list_xml(inputs_dir)

    if not xml_files:
        retries = _bump_counter(counter)
        if retries > max_retries:
            _allow_stop(
                inputs_dir,
                reason_category="no_xml_max_retries",
                retries_so_far=retries,
            )
        _block(
            "Stop blocked by verify_outputs hook: no .xml files found under "
            f"{inputs_dir}. This is a required output of the task. Produce the "
            "requested GEOS XML files now using the Write tool (write under "
            f"{inputs_dir}/) and then end your turn.",
            inputs_dir=inputs_dir,
            reason_category="no_xml",
            retries_so_far=retries,
        )

    parse_err = _first_parse_error(xml_files)
    if parse_err is not None:
        path, detail = parse_err
        retries = _bump_counter(counter)
        if retries > max_retries:
            _allow_stop(
                inputs_dir,
                reason_category="parse_error_max_retries",
                retries_so_far=retries,
            )
        rel = path.relative_to(inputs_dir) if path.is_relative_to(inputs_dir) else path
        _block(
            f"Stop blocked by verify_outputs hook: XML parse error in {rel}: "
            f"{detail}. Open the file, fix the syntax, then end your turn.",
            inputs_dir=inputs_dir,
            reason_category="parse_error",
            retries_so_far=retries,
            detail=f"{rel}: {detail}",
        )

    if _envflag("GEOS_HOOK_XMLLINT"):
        schema_override = os.environ.get("GEOS_HOOK_SCHEMA_PATH")
        schema_path = Path(schema_override) if schema_override else DEFAULT_SCHEMA_PATH
        feedback = _xmllint_validate(xml_files, schema_path, inputs_dir)
        if feedback is not None:
            retries = _bump_counter(counter)
            if retries > max_retries:
                _allow_stop(
                    inputs_dir,
                    reason_category="schema_error_max_retries",
                    retries_so_far=retries,
                )
            _block(
                "Stop blocked by verify_outputs hook: one or more XML files "
                f"under {inputs_dir} fail GEOS schema validation. "
                f"Schema: {schema_path}. Errors:\n\n"
                f"{feedback}\n\n"
                "Fix the offending element/attribute names against the schema "
                "(do NOT guess again — `xmllint` lists expected alternatives "
                "for unexpected-element errors and required attribute names "
                "for missing-attribute errors). Re-validate locally with\n"
                f"  xmllint --schema {schema_path} --noout <file>.xml\n"
                "before ending your turn.",
                inputs_dir=inputs_dir,
                reason_category="schema_error",
                retries_so_far=retries,
                detail=feedback[:500],
            )

    if _envflag("GEOS_HOOK_SELF_REFLECT"):
        flag = counter.parent / ".verify_reflected"
        if not flag.exists():
            try:
                flag.write_text("1")
            except OSError:
                pass
            files = ", ".join(
                str(p.relative_to(inputs_dir)) if p.is_relative_to(inputs_dir) else str(p)
                for p in xml_files
            )
            _block(
                "Stop blocked by verify_outputs hook (self-reflection pass): "
                f"you produced {files}. Before ending the turn, re-read each "
                "file once and verify: (a) the solver block matches the "
                "physics the task describes; (b) all referenced materials, "
                "regions, and BC set-names actually exist elsewhere in the "
                "same file; (c) benchmark/smoke variants import the base via "
                "<Included>. Fix any issues you find, then end your turn. "
                "If everything already looks correct, just end your turn — "
                "this reflection will not repeat.",
                inputs_dir=inputs_dir,
                reason_category="self_reflect",
                retries_so_far=0,
            )

    _allow_stop(inputs_dir, reason_category="xml_clean")


if __name__ == "__main__":
    main()

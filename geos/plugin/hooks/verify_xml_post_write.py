#!/usr/bin/env python3
"""PostToolUse hook: parse XML right after Write|Edit|MultiEdit.

Catches XML malformations (notably the `<<TagTag>` doubled-bracket pattern
emitted by gemma/qwen/minimax via OpenRouter) within seconds of the bad
write, instead of waiting until end-of-turn for the Stop hook. Without
this, the agent can spend 10-25 minutes thinking before discovering its
own bug — and then has to rewrite the whole file via Write under deadline
pressure. With per-write feedback the agent can apply a small Edit fix.

Behavior:
  - Only fires for Write/Edit/MultiEdit on files inside ``$GEOS_HOOK_INPUTS_DIR``
    (default ``$CLAUDE_PROJECT_DIR/inputs`` or ``/workspace/inputs``).
  - Only checks files with ``.xml`` suffix.
  - Allows (no output) on success.
  - Returns ``decision: "block"`` with a one-line fix hint on parse failure;
    Claude Code feeds this back to the model as system feedback before its
    next turn.
  - No retry budget — every problematic write fires until the file parses,
    but the agent feedback loop is short so it self-resolves quickly.
  - Honors ``GEOS_HOOK_DISABLE`` so the existing kill switch covers both hooks.

Logs each invocation to ``<inputs-parent>/.verify_post_hook_events.jsonl``
to make hook activity auditable post-hoc, mirroring the Stop hook.
"""
from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

DOUBLE_BRACKET_OPEN_RE = re.compile(r"<<([A-Za-z][A-Za-z0-9_]*)\1\b")
DOUBLE_BRACKET_CLOSE_RE = re.compile(r"<</([A-Za-z][A-Za-z0-9_]*)\1>")


def _envflag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _inputs_dir() -> Path:
    override = os.environ.get("GEOS_HOOK_INPUTS_DIR")
    if override:
        return Path(override)
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if project:
        return Path(project) / "inputs"
    return Path("/workspace/inputs")


def _event_log_path(inputs_dir: Path) -> Path:
    override = os.environ.get("GEOS_POST_HOOK_EVENTS_PATH")
    if override:
        return Path(override)
    parent = inputs_dir.parent if inputs_dir.parent.exists() else Path("/tmp")
    return parent / ".verify_post_hook_events.jsonl"


def _log_event(inputs_dir: Path, decision: str, detail: str) -> None:
    path = _event_log_path(inputs_dir)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "detail": detail,
    }
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _allow(inputs_dir: Path, detail: str = "") -> None:
    _log_event(inputs_dir, "allow", detail)
    json.dump({"continue": True, "suppressOutput": True}, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def _block(reason: str, inputs_dir: Path, detail: str) -> None:
    _log_event(inputs_dir, "block", detail)
    json.dump({"decision": "block", "reason": reason}, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def _doubled_bracket_hint(content: str) -> str:
    if not (DOUBLE_BRACKET_OPEN_RE.search(content) or DOUBLE_BRACKET_CLOSE_RE.search(content)):
        return ""
    return (
        " Detected the `<<TagTag>` doubled-bracket-and-name pattern. "
        "Fix in place with Edit (do NOT rewrite the whole file via Write): "
        r"replace `<<\1\1` with `<\1` and `<</\1\1>` with `</\1>` for each "
        "affected tag name. Example: `<<ProblemProblem>` -> `<Problem>`, "
        "`<</ProblemProblem>` -> `</Problem>`."
    )


def _collect_paths(payload: dict) -> list[Path]:
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    out: list[Path] = []
    if tool in {"Write", "Edit", "MultiEdit"}:
        p = tool_input.get("file_path")
        if isinstance(p, str) and p:
            out.append(Path(p))
    return out


def main() -> None:
    inputs_dir = _inputs_dir()

    if _envflag("GEOS_HOOK_DISABLE"):
        _allow(inputs_dir, "disabled")

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        _allow(inputs_dir, "bad_hook_input")

    paths = _collect_paths(payload)
    if not paths:
        _allow(inputs_dir, "non_write_tool")

    try:
        inputs_resolved = inputs_dir.resolve()
    except OSError:
        inputs_resolved = inputs_dir

    for raw in paths:
        try:
            p = raw.resolve()
        except OSError:
            continue
        if p.suffix.lower() != ".xml":
            continue
        try:
            inside = p.is_relative_to(inputs_resolved)
        except (AttributeError, ValueError):
            inside = str(p).startswith(str(inputs_resolved))
        if not inside or not p.exists():
            continue
        try:
            ET.parse(p)
        except ET.ParseError as exc:
            try:
                rel = p.relative_to(inputs_resolved)
            except (ValueError, AttributeError):
                rel = p
            try:
                content = p.read_text(errors="ignore")
            except OSError:
                content = ""
            hint = _doubled_bracket_hint(content)
            _block(
                f"PostToolUse verify_xml_post_write: {rel} failed to parse: "
                f"{exc}.{hint} Fix this file before continuing.",
                inputs_dir=inputs_dir,
                detail=f"{rel}: {exc}",
            )
        except OSError:
            continue

    _allow(inputs_dir, "xml_clean")


if __name__ == "__main__":
    main()

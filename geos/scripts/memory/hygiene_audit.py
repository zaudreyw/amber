#!/usr/bin/env python3
"""Hygiene audit for memory artifacts.

Blocks memory content that could leak test-task GT XML basenames or RST
paths into an agent's prompt. Enforced gate before any memory artifact is
used in an eval run.

Two checks:

1. **Generic XML filename regex.** Anything matching ``\\b[a-z0-9_]+\\.xml\\b``
   (case-insensitive) in artifact content is flagged — memory should not
   reference filenames at all.
2. **Test-blocklist substring match.** Every test task's blocked GT XML
   basename (and RST relpath) is loaded from
   ``misc/memory_artifacts/test_blocklist.json`` and searched as a lowercase
   substring in every artifact field. Any match fails the audit.

Usage:

    python scripts/memory/hygiene_audit.py \\
        --artifact plugin/memory_index.json \\
        --out misc/memory_artifacts/M0/hygiene_audit.json

Exit status:
    0  - audit passed (no leaks)
    1  - audit failed (leaks found; artifact unsafe)
    2  - usage error

The audit result is also written as JSON to ``--out`` for durable record.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


BASENAME_RE = re.compile(r"\b([a-z0-9_][a-z0-9_\-]*\.xml)\b", flags=re.IGNORECASE)


def _gather_strings(obj: Any, path: str = "$") -> list[tuple[str, str]]:
    """Walk any JSON-like object, yielding (json_path, string_value) pairs.

    Markdown/plain-text artifacts arrive as a single string at path "$".
    """
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(_gather_strings(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_gather_strings(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        out.append((path, obj))
    return out


def _load_artifact(path: Path) -> Any:
    """Load artifact as JSON if possible, else as raw string."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return text


def audit_artifact(
    artifact_path: Path,
    blocklist: dict,
) -> dict:
    """Audit one artifact file. Returns structured audit result."""
    test_xml_union: set[str] = {x.lower() for x in blocklist.get("union_xml", [])}
    test_rst: set[str] = {r.lower() for r in blocklist.get("union_rst_relpaths", [])}

    artifact = _load_artifact(artifact_path)
    strings = _gather_strings(artifact)

    regex_hits: list[dict] = []
    blocklist_hits: list[dict] = []
    rst_hits: list[dict] = []

    for json_path, s in strings:
        s_lower = s.lower()
        # Generic filename regex
        for m in BASENAME_RE.finditer(s):
            regex_hits.append({
                "path": json_path,
                "matched": m.group(1),
                "context": s[max(0, m.start()-30):m.end()+30],
            })
        # Exact test-blocked basenames
        for blocked in test_xml_union:
            if blocked in s_lower:
                idx = s_lower.find(blocked)
                blocklist_hits.append({
                    "path": json_path,
                    "blocked_basename": blocked,
                    "context": s[max(0, idx-30):idx+len(blocked)+30],
                })
        # Exact RST relpaths (or their leaf basenames)
        for rst in test_rst:
            if rst in s_lower or Path(rst).name.lower() in s_lower:
                blocklist_hits.append({
                    "path": json_path,
                    "blocked_rst": rst,
                    "context": s[:200],
                })

    passed = (len(regex_hits) == 0 and len(blocklist_hits) == 0)
    return {
        "artifact": str(artifact_path),
        "artifact_size_chars": sum(len(s) for _, s in strings),
        "n_strings_checked": len(strings),
        "regex_hits": regex_hits,
        "blocklist_hits": blocklist_hits,
        "passed": passed,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", required=True, type=Path,
                   help="Artifact file (JSON or text/markdown) to audit")
    p.add_argument("--blocklist", default=Path("/home/matt/sci/repo3/misc/memory_artifacts/test_blocklist.json"),
                   type=Path,
                   help="Pre-computed test-blocklist JSON from get_blocked_files_for_task")
    p.add_argument("--out", required=True, type=Path,
                   help="Where to write the audit result JSON")
    p.add_argument("--strict", action="store_true", default=True,
                   help="Fail on any regex or blocklist hit (default: True)")
    args = p.parse_args(argv)

    if not args.artifact.exists():
        print(f"ERROR: artifact not found: {args.artifact}", file=sys.stderr)
        return 2
    if not args.blocklist.exists():
        print(f"ERROR: blocklist not found: {args.blocklist}", file=sys.stderr)
        return 2

    blocklist = json.loads(args.blocklist.read_text())
    result = audit_artifact(args.artifact, blocklist)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))

    status = "PASS" if result["passed"] else "FAIL"
    print(f"Audit {status}: {args.artifact}")
    print(f"  regex_hits={len(result['regex_hits'])}")
    print(f"  blocklist_hits={len(result['blocklist_hits'])}")
    if not result["passed"]:
        print(f"  sample regex hit: {result['regex_hits'][:2]}")
        print(f"  sample blocklist hit: {result['blocklist_hits'][:2]}")
    print(f"  written: {args.out}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

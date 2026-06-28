#!/usr/bin/env python3
"""Extract file-access events (Read / Edit / Write) from an agent trace.

Input can be JSON (array) or JSONL. Output defaults to JSON on stdout:
  [{"path": "...", "reads": N, "edits": N, "writes": N, "first_line": L}, ...]

Flags:
  --list          Print unique paths only, one per line (reads + edits + writes).
  --reads-only    Only Read calls.
  --edits-only    Only Edit / MultiEdit calls.
  --writes-only   Only Write / NotebookEdit calls.
  --sort PATH|COUNT  Sort order (default: COUNT).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

READ_TOOLS = {"Read"}
EDIT_TOOLS = {"Edit", "MultiEdit"}
WRITE_TOOLS = {"Write", "NotebookEdit"}
FILE_TOOLS = READ_TOOLS | EDIT_TOOLS | WRITE_TOOLS


def iter_records(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()

    # Try JSON first (array or single object) if it looks that way.
    if stripped.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("Top-level JSON must be an array for this path.")
        for i, rec in enumerate(data, start=1):
            if isinstance(rec, dict):
                yield i, rec
        return

    if stripped.startswith("{"):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict):
            for key in ("events", "records", "messages", "transcript", "conversation", "items"):
                nested = obj.get(key)
                if isinstance(nested, list):
                    for i, rec in enumerate(nested, start=1):
                        if isinstance(rec, dict):
                            yield i, rec
                    return
            yield 1, obj
            return

    # Fallback: JSONL
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if isinstance(rec, dict):
            yield lineno, rec


def extract_file_events(records: Iterable[tuple[int, dict[str, Any]]]):
    events: list[tuple[int, str, str]] = []  # (line, tool_name, file_path)

    for lineno, record in records:
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if not isinstance(name, str) or name not in FILE_TOOLS:
                continue
            inp = block.get("input")
            if not isinstance(inp, dict):
                continue
            file_path = inp.get("file_path") or inp.get("notebook_path")
            if not isinstance(file_path, str):
                continue
            events.append((lineno, name, file_path))

    return events


def aggregate(events, *, reads_only=False, edits_only=False, writes_only=False):
    aggregated: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    for lineno, name, path in events:
        is_read = name in READ_TOOLS
        is_edit = name in EDIT_TOOLS
        is_write = name in WRITE_TOOLS
        if reads_only and not is_read:
            continue
        if edits_only and not is_edit:
            continue
        if writes_only and not is_write:
            continue

        entry = aggregated.get(path)
        if entry is None:
            entry = {
                "path": path,
                "reads": 0,
                "edits": 0,
                "writes": 0,
                "first_line": lineno,
            }
            aggregated[path] = entry
        if is_read:
            entry["reads"] += 1
        elif is_edit:
            entry["edits"] += 1
        elif is_write:
            entry["writes"] += 1

    return list(aggregated.values())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", type=Path, help="Path to a .json or .jsonl agent transcript.")
    ap.add_argument("--list", action="store_true", help="Emit only unique file paths, one per line.")
    ap.add_argument("--reads-only", action="store_true")
    ap.add_argument("--edits-only", action="store_true")
    ap.add_argument("--writes-only", action="store_true")
    ap.add_argument("--sort", choices=("count", "path"), default="count")
    args = ap.parse_args()

    if sum([args.reads_only, args.edits_only, args.writes_only]) > 1:
        ap.error("Pick at most one of --reads-only / --edits-only / --writes-only.")

    if not args.path.exists():
        ap.error(f"File not found: {args.path}")

    records = list(iter_records(args.path))
    events = extract_file_events(records)
    agg = aggregate(
        events,
        reads_only=args.reads_only,
        edits_only=args.edits_only,
        writes_only=args.writes_only,
    )

    if args.sort == "count":
        agg.sort(key=lambda e: (-(e["reads"] + e["edits"] + e["writes"]), e["path"]))
    else:
        agg.sort(key=lambda e: e["path"])

    if args.list:
        for entry in agg:
            print(entry["path"])
    else:
        json.dump(agg, sys.stdout, indent=2)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

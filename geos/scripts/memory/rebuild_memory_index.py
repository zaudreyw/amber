#!/usr/bin/env python3
"""Rebuild memory_index.json with basenames stripped.

The legacy ``plugin/memory_index.json`` leaks test-task GT XML basenames
through `reference_xmls` and `productive_rag_queries` (see RN-003).
This script produces a hygiene-safe replacement:

- **Strips** `reference_xmls` (replaced with `n_reference_xmls` count and
  `reference_xml_solver_families` summary — no raw paths).
- **Sanitizes** `productive_rag_queries` (any query containing a
  `*.xml` substring is replaced with the token ``"<xml_filename_stripped>"``;
  others pass through).
- **Strips** `written_xmls` entirely.
- **Sanitizes** `instructions_excerpt` (any `*.xml` substrings replaced).
- Keeps: `task_id`, `final_treesim`, `topic_keywords`, `section_strengths`,
  `solver_family`.
- Adds: `abstract_summary` field (empty; filled by distiller later).

Archives old index as ``plugin/memory_index_v1_LEAKY.json.bak`` with a
README-style header line.

After running, invoke ``scripts/memory/hygiene_audit.py`` on the new
index to confirm it passes.

Usage:
    python scripts/memory/rebuild_memory_index.py \\
        --src plugin/memory_index.json \\
        --dst plugin/memory_index.json  # overwrites in place, backup first
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


XML_FILENAME_RE = re.compile(r"\b([a-z0-9_][a-z0-9_\-]*\.xml)\b", flags=re.IGNORECASE)


def sanitize_string(s: str) -> str:
    """Replace any *.xml substring with a placeholder."""
    return XML_FILENAME_RE.sub("<xml_filename_stripped>", s)


def solver_family_for_xml_path(xml_path: str) -> str:
    """Extract a coarse solver family label from a reference XML path.

    Uses the immediate parent directory under inputFiles/ as the family tag.
    """
    try:
        parts = Path(xml_path).parts
        if "inputFiles" in parts:
            idx = parts.index("inputFiles")
            if idx + 1 < len(parts):
                return parts[idx + 1]
    except Exception:
        pass
    return "unknown"


def rebuild_entry(entry: dict) -> dict:
    ref_xmls = entry.get("reference_xmls", []) or []
    families = [solver_family_for_xml_path(x) for x in ref_xmls]
    # Count each family
    fam_counts: dict[str, int] = {}
    for f in families:
        fam_counts[f] = fam_counts.get(f, 0) + 1

    productive_queries = entry.get("productive_rag_queries", []) or []
    sanitized_queries = [sanitize_string(q) for q in productive_queries]

    instructions = entry.get("instructions_excerpt", "") or ""
    sanitized_instructions = sanitize_string(instructions)

    return {
        "task_id": entry.get("task_id"),
        "final_treesim": entry.get("final_treesim"),
        "topic_keywords": entry.get("topic_keywords", []),
        "section_strengths": entry.get("section_strengths", {}),
        "solver_family": entry.get("solver_family", "unknown"),
        # Replace raw paths with a coarse family summary
        "n_reference_xmls": len(ref_xmls),
        "reference_xml_solver_families": fam_counts,
        # Sanitized fields (filenames stripped)
        "productive_rag_queries": sanitized_queries,
        "instructions_excerpt": sanitized_instructions,
        # Placeholder for distiller output
        "abstract_summary": "",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", default=Path("/home/matt/sci/repo3/plugin/memory_index.json"), type=Path)
    p.add_argument("--dst", default=Path("/home/matt/sci/repo3/plugin/memory_index.json"), type=Path)
    p.add_argument("--backup", default=Path("/home/matt/sci/repo3/plugin/memory_index_v1_LEAKY.json.bak"), type=Path)
    args = p.parse_args(argv)

    src = args.src
    if not src.exists():
        print(f"ERROR: source not found: {src}", file=sys.stderr)
        return 2

    original = json.loads(src.read_text())
    entries = original.get("tasks", original) if isinstance(original, dict) else original
    if not isinstance(entries, list):
        print(f"ERROR: unexpected index shape: {type(entries)}", file=sys.stderr)
        return 2

    # Archive original
    if src == args.dst:
        # In-place replacement; create backup before overwriting
        if not args.backup.exists():
            # Header note tells future readers why this file is retained
            note = f"// WARNING: Leaky memory index. See RN-003 for details. Archived 2026-04-22.\n"
            args.backup.write_text(note + src.read_text())
            print(f"archived leaky index: {args.backup}")
        else:
            print(f"backup already exists: {args.backup} (not overwriting)")

    rebuilt_entries = [rebuild_entry(e) for e in entries]
    rebuilt = {
        "schema_version": "v2_hygiene_fixed",
        "generated_from": original.get("generated_from") if isinstance(original, dict) else None,
        "n_tasks": len(rebuilt_entries),
        "hygiene_note": "Basenames and raw XML paths stripped. See RN-003.",
        "tasks": rebuilt_entries,
    }
    args.dst.parent.mkdir(parents=True, exist_ok=True)
    args.dst.write_text(json.dumps(rebuilt, indent=2))
    print(f"wrote sanitized index: {args.dst}")
    print(f"  entries: {len(rebuilt_entries)}")
    print(f"  sample solver_family counts: {rebuilt_entries[0].get('reference_xml_solver_families')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

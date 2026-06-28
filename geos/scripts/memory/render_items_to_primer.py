#!/usr/bin/env python3
"""Render RB-style memory items JSON as a markdown primer.

For M4-u / M4-g variants, external primer injection needs a human-readable
markdown view of the items. This script converts items.json → artifact.md
preserving the structured fields.

Usage:
  python scripts/memory/render_items_to_primer.py \\
      --items misc/memory_artifacts/M4-g/items.json \\
      --out misc/memory_artifacts/M4-g/artifact.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def render(items: list[dict]) -> str:
    parts = ["# Reasoning-Memory Items (distilled from past trajectories)\n",
             "*Each item is a cross-task rule or anti-pattern. Use these to guide "
             "solver selection, schema choices, and attribute usage.*\n\n"]
    for i, it in enumerate(items, 1):
        title = it.get("title", f"Item {i}")
        fam = it.get("solver_family", "—")
        kind = it.get("kind", "—")
        level = it.get("abstraction_level", "—")
        desc = it.get("description", "")
        applies = it.get("applies_when", "")
        content = it.get("content", "")
        parts.append(f"## {i}. {title}\n")
        parts.append(f"- **Solver family:** {fam}")
        parts.append(f"- **Kind:** {kind} ({level} abstraction)")
        if desc:
            parts.append(f"- **Description:** {desc}")
        if applies:
            parts.append(f"- **Applies when:** {applies}")
        if content:
            parts.append(f"\n{content}")
        parts.append("")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args(argv)
    items = json.loads(args.items.read_text())
    if not isinstance(items, list):
        print("ERROR: items not a list", file=sys.stderr)
        return 2
    args.out.write_text(render(items))
    print(f"rendered {len(items)} items → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

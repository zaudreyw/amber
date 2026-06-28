#!/usr/bin/env python3
"""Re-run hygiene check on existing relaxed specs without re-rewriting."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from relax_specs import hygiene_check, ADDENDUM_MEDIUM, ADDENDUM_HARD  # noqa


SRC_DIR = Path("/data/shared/geophysics_agent_data/data/eval/experiments_test36_template")

for level in ("medium", "hard"):
    addendum = ADDENDUM_MEDIUM if level == "medium" else ADDENDUM_HARD
    root = Path(f"data/eval/experiments_relaxed_{level}")
    if not root.exists():
        continue
    for task_dir in sorted(root.iterdir()):
        if not task_dir.is_dir():
            continue
        rewrite_path = task_dir / "instructions.txt"
        omitted_path = task_dir / "_omitted.json"
        orig_path = SRC_DIR / task_dir.name / "instructions.txt"
        if not (rewrite_path.exists() and omitted_path.exists() and orig_path.exists()):
            continue
        rewrite = rewrite_path.read_text()
        original = orig_path.read_text()
        d = json.loads(omitted_path.read_text())
        kept = list(d.get("kept_t4_values", [])) + list(d.get("kept_t3_values", []))
        check = hygiene_check(
            original_spec=original,
            rewrite=rewrite,
            dropped_values=d.get("dropped_values", []),
            level=level,
            kept_values=kept,
        )
        d["hygiene"] = check
        omitted_path.write_text(json.dumps(d, indent=2))
        print(f"{task_dir.name}/{level} drop={check['drop_ratio']:.3f} "
              f"leaks={len(check['leaks'])} shared={len(check['shared_values'])}")

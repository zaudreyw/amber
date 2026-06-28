#!/usr/bin/env python3
"""Judge a single task's generated XML against ground truth.

Usage:
    uv run python scripts/eval/judge_one.py \\
        --gt data/eval/experiments_gt/ExampleEDPWellbore/inputs \\
        --gen data/eval/claude_code/run1/ExampleEDPWellbore/inputs
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.eval import judge_geos, lxml_xml_eval


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gt", type=Path, required=True, help="ground-truth dir or file")
    p.add_argument("--gen", type=Path, required=True, help="generated dir or file")
    p.add_argument("--legacy", action="store_true",
                   help="Use lxml_xml_eval weighted-dimension scorer")
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    mod = lxml_xml_eval if args.legacy else judge_geos
    if args.gt.is_dir():
        result = mod.evaluate_directories(args.gt, args.gen)
    else:
        result = mod.evaluate_files(args.gt, args.gen)

    pretty = json.dumps(result, indent=2, default=str)
    print(pretty)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(pretty)
    return 0


if __name__ == "__main__":
    sys.exit(main())

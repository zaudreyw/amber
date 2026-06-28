#!/usr/bin/env python3
"""Cross-harness comparison: OpenHands runs vs vanilla CC no-plugin runs.

Builds the per-task TreeSim table and aggregate stats used in
docs/XN-016_openhands-baseline.md §Results.

Usage:
    python scripts/openhands_compare.py \\
        --oh oh_test17_s1 oh_test17_s2 oh_test17_s3 \\
        --cc noplug_mm_v2 noplug_mm_v2_s2 \\
        --output docs/XN-016_results_table.md

Or just print to stdout:
    python scripts/openhands_compare.py --oh oh_test17_s1 --cc noplug_mm_v2
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from math import comb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.harnessless_eval import TEST_TASKS_17  # canonical 17

OH_RESULTS_ROOT = REPO_ROOT / "data" / "eval" / "results"
CC_RESULTS_ROOT = REPO_ROOT / "data" / "eval" / "results"


def read_treesim(results_dir: Path, task: str) -> float | None:
    f = results_dir / f"{task}_eval.json"
    if not f.exists():
        return None
    return json.loads(f.read_text()).get("treesim")


def sign_test(deltas: list[float]) -> float:
    pos = sum(1 for d in deltas if d > 0)
    neg = sum(1 for d in deltas if d < 0)
    n = pos + neg
    if n == 0:
        return 1.0
    return sum(comb(n, k) * 0.5**n for k in range(n+1) if k <= min(pos, neg) or k >= max(pos, neg))


def collect_seed(seeds: list[str], harness_subdir: str) -> dict[str, list[float]]:
    """For each task, list of TreeSim across the seeds where it scored."""
    out: dict[str, list[float]] = {t: [] for t in TEST_TASKS_17}
    for seed in seeds:
        d = OH_RESULTS_ROOT / seed / harness_subdir
        if not d.exists():
            print(f"WARN: results dir missing: {d}", file=sys.stderr)
            continue
        for t in TEST_TASKS_17:
            v = read_treesim(d, t)
            if v is not None:
                out[t].append(v)
    return out


def fmt(x: float | None, w: int = 6) -> str:
    if x is None:
        return f'{"--":>{w}}'
    return f'{x:>{w}.3f}'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oh", nargs="+", required=True,
                    help="OpenHands run names (under data/eval/results/<name>/openhands_no_plugin/)")
    ap.add_argument("--cc", nargs="+", required=True,
                    help="CC no-plugin run names (under data/eval/results/<name>/claude_code_no_plugin/)")
    ap.add_argument("--output", type=Path, default=None,
                    help="Optional markdown output path")
    args = ap.parse_args()

    oh = collect_seed(args.oh, "openhands_no_plugin")
    cc = collect_seed(args.cc, "claude_code_no_plugin")

    lines: list[str] = []
    p = lines.append

    p(f"# Cross-harness comparison: OpenHands vs vanilla CC (no plugin)")
    p("")
    p(f"- OH seeds: {', '.join(args.oh)}")
    p(f"- CC seeds: {', '.join(args.cc)}")
    p("")

    # Per-task table
    header_oh = " ".join(f"OH_s{i+1}" for i in range(len(args.oh)))
    header_cc = " ".join(f"CC_s{i+1}" for i in range(len(args.cc)))
    p(f"| Task | {header_oh.replace(' ', ' | ')} | OH mean | {header_cc.replace(' ', ' | ')} | CC mean | Δ (OH−CC mean) |")
    p("|---|" + "|".join(["---:"] * (len(args.oh) + 1)) + "|" + "|".join(["---:"] * (len(args.cc) + 1)) + "|---:|")

    deltas: list[float] = []
    oh_means: list[float] = []
    cc_means: list[float] = []
    paired_oh_means: list[float] = []
    paired_cc_means: list[float] = []
    for t in TEST_TASKS_17:
        oh_vals = oh[t]
        cc_vals = cc[t]
        oh_m = statistics.mean(oh_vals) if oh_vals else None
        cc_m = statistics.mean(cc_vals) if cc_vals else None

        if oh_m is not None:
            oh_means.append(oh_m)
        if cc_m is not None:
            cc_means.append(cc_m)
        delta = None
        if oh_m is not None and cc_m is not None:
            delta = oh_m - cc_m
            deltas.append(delta)
            paired_oh_means.append(oh_m)
            paired_cc_means.append(cc_m)

        oh_cells = " | ".join(fmt(v) for v in (oh_vals + [None]*(len(args.oh)-len(oh_vals))))
        cc_cells = " | ".join(fmt(v) for v in (cc_vals + [None]*(len(args.cc)-len(cc_vals))))
        p(f"| {t} | {oh_cells} | {fmt(oh_m)} | {cc_cells} | {fmt(cc_m)} | "
          + (f"{delta:+.3f}" if delta is not None else "--") + " |")

    p("")
    p("## Aggregates")
    p("")
    if oh_means:
        p(f"- OH per-task mean across seeds, then averaged ({len(oh_means)} tasks): "
          f"**{statistics.mean(oh_means):.3f}**"
          + (f" ± {statistics.stdev(oh_means):.3f}" if len(oh_means) > 1 else ""))
    if cc_means:
        p(f"- CC per-task mean across seeds, then averaged ({len(cc_means)} tasks): "
          f"**{statistics.mean(cc_means):.3f}**"
          + (f" ± {statistics.stdev(cc_means):.3f}" if len(cc_means) > 1 else ""))
    if deltas:
        p(f"- Paired delta (n={len(deltas)} tasks scored on both sides): "
          f"**{statistics.mean(deltas):+.3f}**"
          + (f" ± {statistics.stdev(deltas):.3f}" if len(deltas) > 1 else ""))
        wins = sum(1 for d in deltas if d > 0)
        losses = sum(1 for d in deltas if d < 0)
        p(f"- OH wins / losses: **{wins} / {losses}**")
        p(f"- Sign-test p (2-sided): **{sign_test(deltas):.3f}**")

    # OH variance per task (for seed-stability claim)
    if len(args.oh) >= 2:
        per_task_std = []
        for t in TEST_TASKS_17:
            if len(oh[t]) >= 2:
                per_task_std.append((t, statistics.stdev(oh[t])))
        if per_task_std:
            per_task_std.sort(key=lambda x: -x[1])
            p("")
            p(f"## OpenHands seed-variance (per-task std across {len(args.oh)} seeds, top 5)")
            p("")
            for t, s in per_task_std[:5]:
                p(f"- {t}: σ = {s:.3f}  (values: {oh[t]})")

    text = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

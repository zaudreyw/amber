#!/usr/bin/env python3
"""Paired-by-task comparison of orchestrator run vs an existing baseline run.

Reads two batch_evaluate `_summary.json` files and produces:
- Per-task delta table (orchestrator - baseline)
- Win/loss/tie counts
- Mean / median scores
- Wilcoxon signed-rank statistic (if scipy available)

Usage:
    python -m scripts.orchestrator.compare_with_baseline \\
        --orchestrator data/eval/results/orch_dsv4_s1/orchestrator_dsv4flash/_summary.json \\
        --baseline    data/eval/results/<E03_run>/claude_code_repo3_plugin/_summary.json \\
        --out         data/eval/results/orch_dsv4_s1/comparison.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def load_summary(p: Path) -> dict[str, float]:
    """Return {task_name -> score}. Score key tries overall_score then mean_score."""
    data = json.loads(p.read_text())
    out: dict[str, float] = {}
    for r in data.get("results", []):
        if r.get("status") != "success":
            continue
        name = r.get("experiment") or r.get("task")
        score = r.get("overall_score") or r.get("mean_score")
        if score is None:
            tree = r.get("xml_tree_similarity") or {}
            score = tree.get("mean_score") or tree.get("score")
        if name and score is not None:
            out[name] = float(score)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--orchestrator", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--out", type=Path, required=False)
    p.add_argument("--baseline-label", default="baseline")
    p.add_argument("--orch-label", default="orchestrator")
    args = p.parse_args()

    orch = load_summary(args.orchestrator)
    base = load_summary(args.baseline)

    common = sorted(set(orch.keys()) & set(base.keys()))
    if not common:
        print("ERROR: no common tasks between the two runs.")
        return 1

    print(f"\n# Orchestrator vs {args.baseline_label} — paired comparison ({len(common)} common tasks)\n")
    print(f"{'task':<55} {args.orch_label:>8} {args.baseline_label:>10} {'delta':>8} {'win?':>4}")
    print("-" * 95)
    deltas: list[float] = []
    wins = losses = ties = 0
    for name in common:
        o = orch[name]
        b = base[name]
        d = o - b
        deltas.append(d)
        if d > 0.01:
            tag = "+"
            wins += 1
        elif d < -0.01:
            tag = "-"
            losses += 1
        else:
            tag = "="
            ties += 1
        print(f"{name[:55]:<55} {o:>8.3f} {b:>10.3f} {d:>+8.3f} {tag:>4}")

    omean = statistics.fmean(orch[n] for n in common)
    bmean = statistics.fmean(base[n] for n in common)
    dmean = statistics.fmean(deltas)
    dmedian = statistics.median(deltas)
    print("-" * 95)
    print(f"{'mean':<55} {omean:>8.3f} {bmean:>10.3f} {dmean:>+8.3f}")
    print(f"{'median delta':<55} {' ':>8} {' ':>10} {dmedian:>+8.3f}")
    print(f"\nwins/losses/ties (delta > ±0.01): {wins}/{losses}/{ties}")

    try:
        from scipy.stats import wilcoxon
        if any(abs(d) > 0 for d in deltas):
            w = wilcoxon([orch[n] for n in common], [base[n] for n in common])
            print(f"\nWilcoxon signed-rank: stat={w.statistic:.3f} p={w.pvalue:.4f}")
    except ImportError:
        print("\n(scipy not installed; skipping Wilcoxon)")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w") as f:
            f.write(f"# Orchestrator vs {args.baseline_label} comparison\n\n")
            f.write(f"Common tasks: {len(common)}\n")
            f.write(f"Mean: {args.orch_label}={omean:.3f}, {args.baseline_label}={bmean:.3f}, "
                    f"delta={dmean:+.3f} (median {dmedian:+.3f})\n")
            f.write(f"Win/loss/tie: {wins}/{losses}/{ties}\n\n")
            f.write("| task | orch | baseline | delta |\n|---|---:|---:|---:|\n")
            for name in common:
                f.write(f"| {name} | {orch[name]:.3f} | {base[name]:.3f} | {orch[name]-base[name]:+.3f} |\n")
        print(f"\nWritten: {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

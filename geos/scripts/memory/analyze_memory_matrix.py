#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["scipy>=1.11", "numpy>=1.26"]
# ///
"""Aggregate memory-ablation scores and run paired-per-task Wilcoxon against A3.

Expects summary JSONs at:
  misc/memory_artifacts/scores/mem_<cond>_s<N>_summary.json   (for memory conds)
  misc/pac1/scores/e23_summary.json, e23s2_summary.json,
    a3_s3_summary.json  (for A3 baseline)

Emits:
- `misc/memory_artifacts/scores/matrix_aggregate.json` — full per-condition
  per-seed per-task table + paired deltas vs A3 + Wilcoxon p-values.
- `misc/memory_artifacts/scores/matrix_summary.md` — human-readable table.

Usage:
  python scripts/memory/analyze_memory_matrix.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean, stdev

REPO = Path("/home/matt/sci/repo3")
SCORES = REPO / "misc" / "memory_artifacts" / "scores"
PAC1_SCORES = REPO / "misc" / "pac1" / "scores"

CONDITIONS = [
    ("A3_RAG_SR", [
        PAC1_SCORES / "e23_summary.json",
        PAC1_SCORES / "e23s2_summary.json",
        PAC1_SCORES / "a3_s3_summary.json",
    ]),
    ("A4p_RAG_Mem_noSR", [
        PAC1_SCORES / "a4prime_s1_summary.json",
        PAC1_SCORES / "a4prime_s2_summary.json",
    ]),
    ("A5_RAG_Mem_SR", [
        PAC1_SCORES / "e24_summary.json",
        PAC1_SCORES / "e24s2_summary.json",
        PAC1_SCORES / "e24s3_summary.json",
    ]),
    ("placebo", [
        SCORES / "mem_placebo_s1_summary.json",
        SCORES / "mem_placebo_s2_summary.json",
        SCORES / "mem_placebo_s3_summary.json",
    ]),
    ("M1-u", [
        SCORES / "mem_m1u_s1_summary.json",
        SCORES / "mem_m1u_s2_summary.json",
        SCORES / "mem_m1u_s3_summary.json",
    ]),
    ("M1-g", [
        SCORES / "mem_m1g_s1_summary.json",
        SCORES / "mem_m1g_s2_summary.json",
        SCORES / "mem_m1g_s3_summary.json",
    ]),
    ("M3-g", [
        SCORES / "mem_m3g_s1_summary.json",
        SCORES / "mem_m3g_s2_summary.json",
        SCORES / "mem_m3g_s3_summary.json",
    ]),
    ("M4-u", [
        SCORES / "mem_m4u_s1_summary.json",
        SCORES / "mem_m4u_s2_summary.json",
        SCORES / "mem_m4u_s3_summary.json",
    ]),
    ("M4-g", [
        SCORES / "mem_m4g_s1_summary.json",
        SCORES / "mem_m4g_s2_summary.json",
        SCORES / "mem_m4g_s3_summary.json",
    ]),
]


def load_summary(path: Path) -> dict[str, float] | None:
    """Return {task: treesim} mapping from a batch_evaluate summary JSON."""
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    results = d.get("results", [])
    out: dict[str, float] = {}
    for r in results:
        task = r.get("experiment")
        ts = r.get("treesim")
        if task is None:
            continue
        out[task] = float(ts) if isinstance(ts, (int, float)) else 0.0
    return out


def fa0_mean(scores: dict[str, float], tasks: list[str] | None = None) -> float:
    if tasks is None:
        tasks = list(scores.keys())
    return mean(scores.get(t, 0.0) for t in tasks)


def wilcoxon_signed_rank(deltas: list[float]) -> dict:
    """Simple Wilcoxon signed-rank test (two-sided). Returns {W, n_nonzero, p_approx}.

    Uses normal approximation for n >= 6 (our case is 17 tasks). For exact p
    at this small n, prefer scipy.stats.wilcoxon if available.
    """
    try:
        from scipy import stats  # type: ignore
        if not deltas:
            return {"W": 0, "n": 0, "p_value": 1.0, "method": "no-data"}
        # scipy's wilcoxon with zero_method='wilcox' drops zeros by default
        res = stats.wilcoxon([d for d in deltas if d != 0], alternative="two-sided")
        return {"W": float(res.statistic), "n": len([d for d in deltas if d != 0]),
                "p_value": float(res.pvalue), "method": "scipy.wilcoxon"}
    except ImportError:
        # Manual normal approximation
        nonzero = [d for d in deltas if d != 0]
        n = len(nonzero)
        if n == 0:
            return {"W": 0, "n": 0, "p_value": 1.0, "method": "manual-nozero"}
        abs_ranks = sorted(range(n), key=lambda i: abs(nonzero[i]))
        ranks = [0] * n
        for rank, i in enumerate(abs_ranks, 1):
            ranks[i] = rank
        W_pos = sum(r for r, d in zip(ranks, nonzero) if d > 0)
        W_neg = sum(r for r, d in zip(ranks, nonzero) if d < 0)
        W = min(W_pos, W_neg)
        mu = n * (n + 1) / 4
        sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        z = (W - mu) / sigma if sigma > 0 else 0
        import math as _math
        p = 2 * (0.5 - 0.5 * _math.erf(abs(z) / _math.sqrt(2)))
        return {"W": W, "n": n, "p_value": p, "method": "manual-normal-approx"}


def main() -> int:
    # Load everything
    condition_data: dict[str, list[dict]] = {}
    for cond_name, paths in CONDITIONS:
        seeds = []
        for p in paths:
            s = load_summary(p)
            if s is None:
                continue
            seeds.append({"seed_path": str(p), "scores": s})
        condition_data[cond_name] = seeds
        n = len(seeds)
        if n == 0:
            print(f"[{cond_name}] no seeds found")
            continue
        # mean fa0 per seed
        per_seed_means = [fa0_mean(sd["scores"]) for sd in seeds]
        mean_across_seeds = mean(per_seed_means) if per_seed_means else 0.0
        std_across_seeds = stdev(per_seed_means) if len(per_seed_means) >= 2 else 0.0
        print(f"[{cond_name}] n={n} seed_means={[f'{m:.3f}' for m in per_seed_means]} mean={mean_across_seeds:.3f} std={std_across_seeds:.3f}")

    # Baseline: A3 per-task mean across seeds
    a3_seeds = condition_data.get("A3_RAG_SR", [])
    if not a3_seeds:
        print("ERROR: no A3 baseline loaded")
        return 1

    # Per-task A3 mean (across its seeds)
    tasks_in_a3 = set.intersection(*(set(sd["scores"].keys()) for sd in a3_seeds)) if a3_seeds else set()
    a3_per_task_mean = {t: mean(sd["scores"].get(t, 0.0) for sd in a3_seeds) for t in tasks_in_a3}

    # Per condition vs A3 paired
    rows = []
    for cond_name, seeds in condition_data.items():
        if not seeds or cond_name == "A3_RAG_SR":
            continue
        # Take per-task mean within this condition
        tasks_common = tasks_in_a3 & set.intersection(*(set(sd["scores"].keys()) for sd in seeds))
        if not tasks_common:
            continue
        cond_per_task_mean = {t: mean(sd["scores"].get(t, 0.0) for sd in seeds) for t in tasks_common}
        deltas = [cond_per_task_mean[t] - a3_per_task_mean[t] for t in tasks_common]
        wilcoxon = wilcoxon_signed_rank(deltas)
        per_seed_means = [fa0_mean(sd["scores"]) for sd in seeds]
        rows.append({
            "condition": cond_name,
            "n_seeds": len(seeds),
            "mean_fa0": mean(per_seed_means) if per_seed_means else 0.0,
            "std_fa0": stdev(per_seed_means) if len(per_seed_means) >= 2 else 0.0,
            "paired_n_tasks": len(tasks_common),
            "mean_delta_vs_a3": mean(deltas),
            "median_delta_vs_a3": sorted(deltas)[len(deltas)//2],
            "wins_over_a3": sum(1 for d in deltas if d > 0),
            "losses_vs_a3": sum(1 for d in deltas if d < 0),
            "ties_vs_a3": sum(1 for d in deltas if d == 0),
            "wilcoxon": wilcoxon,
        })

    aggregate = {
        "conditions": {c: {"n_seeds": len(s), "seed_paths": [sd["seed_path"] for sd in s]}
                       for c, s in condition_data.items()},
        "a3_baseline_per_task": a3_per_task_mean,
        "comparisons": rows,
    }
    out_json = SCORES / "matrix_aggregate.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(aggregate, indent=2))

    # Markdown summary
    md = ["# Memory Ablation Matrix — Results", ""]
    md.append(f"_Generated: 2026-04-22_")
    md.append("")
    md.append("## Per-condition mean fa0 TreeSim (17 v2 tasks, minimax-m2.7)")
    md.append("")
    md.append("| Condition | n seeds | mean fa0 | std | Δ vs A3 mean | Wilcoxon p | wins/ties/losses |")
    md.append("|---|:-:|---:|---:|---:|---:|---|")
    a3_mean = mean([fa0_mean(sd["scores"]) for sd in a3_seeds])
    a3_std = stdev([fa0_mean(sd["scores"]) for sd in a3_seeds]) if len(a3_seeds) >= 2 else 0
    md.append(f"| A3 (RAG+SR) baseline | {len(a3_seeds)} | {a3_mean:.3f} | {a3_std:.3f} | — | — | — |")
    for r in rows:
        wp = r["wilcoxon"]["p_value"]
        md.append(
            f"| {r['condition']} | {r['n_seeds']} | {r['mean_fa0']:.3f} | {r['std_fa0']:.3f} "
            f"| {r['mean_delta_vs_a3']:+.3f} | {wp:.3f} | "
            f"{r['wins_over_a3']}/{r['ties_vs_a3']}/{r['losses_vs_a3']} |"
        )
    md.append("")
    md.append("## Decision-gate status")
    md.append("")

    def _find(name: str) -> dict | None:
        for r in rows:
            if r["condition"] == name:
                return r
        return None

    claim_a_candidates = [
        r for r in rows
        if r["condition"].startswith("M") or r["condition"].startswith("placebo")
    ]
    claim_a_passers = [
        r for r in claim_a_candidates
        if r["mean_delta_vs_a3"] >= 0.05
        and r["wilcoxon"]["p_value"] <= 0.10
        and r["std_fa0"] <= max(a3_std, 0.08)
    ]
    md.append(f"**Claim A (outcome):** Memory variant beats A3 by ≥ +0.05 mean AND Wilcoxon p ≤ 0.10 AND std ≤ max(A3 std, 0.08).")
    if claim_a_passers:
        md.append(f"  - PASS: {', '.join(r['condition'] for r in claim_a_passers)}")
    else:
        md.append(f"  - FAIL or N/A (no variant meets all criteria yet).")
    md.append("")

    md.append("**Claim B (attribution — grounded distillation is a method contribution):**")
    for u, g in [("M1-u", "M1-g"), ("M4-u", "M4-g")]:
        ru = _find(u); rg = _find(g)
        if ru is not None and rg is not None:
            delta = rg["mean_fa0"] - ru["mean_fa0"]
            md.append(f"  - {g} − {u}: mean fa0 delta = {delta:+.3f} "
                      f"({'PASS' if delta >= 0.04 else 'FAIL'} at +0.04 threshold)")
        else:
            md.append(f"  - {g} − {u}: awaiting data.")
    md.append("")

    md.append("**Claim C (locus — external injection beats tool-locus):**")
    m3g = _find("M3-g"); m4g = _find("M4-g")
    if m3g is not None and m4g is not None:
        delta = m4g["mean_fa0"] - m3g["mean_fa0"]
        md.append(f"  - M4-g − M3-g: mean fa0 delta = {delta:+.3f} (weakened — tool-list-shape confound, RN-003 P2 #5)")
    else:
        md.append(f"  - M4-g − M3-g: awaiting data.")
    md.append("")

    md.append("**Placebo sanity:** If placebo is near zero vs A3, primer-injection is null-effect and memory content lift is real.")
    pl = _find("placebo")
    if pl is not None:
        md.append(f"  - placebo − A3: mean fa0 delta = {pl['mean_delta_vs_a3']:+.3f}, wins {pl['wins_over_a3']}/{pl['losses_vs_a3']}")
    md.append("")

    (SCORES / "matrix_summary.md").write_text("\n".join(md))
    print(f"\nwrote {out_json}")
    print(f"wrote {SCORES / 'matrix_summary.md'}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

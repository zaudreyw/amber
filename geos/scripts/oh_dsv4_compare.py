#!/usr/bin/env python3
"""Per-task table + paired stats for OH-DSv4 vanilla vs adapt (XN-019)."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.harnessless_eval import TEST_TASKS_17  # noqa: E402

RESULTS_ROOT = REPO_ROOT / "data" / "eval" / "results"
RUNS_ROOT = REPO_ROOT / "data" / "eval" / "openhands_no_plugin"

VANILLA_RUNS = ["oh_dsv4_vanilla_s1", "oh_dsv4_vanilla_s2"]
ADAPT_RUNS = ["oh_dsv4_adapt_s1", "oh_dsv4_adapt_s2"]


def read_treesim(run: str, task: str) -> float | None:
    f = RESULTS_ROOT / run / "openhands_no_plugin" / f"{task}_eval.json"
    if not f.exists():
        return None
    return json.loads(f.read_text()).get("treesim")


def read_status(run: str, task: str) -> dict:
    s = RUNS_ROOT / run / task / "status.json"
    return json.loads(s.read_text()) if s.exists() else {}


def per_task_means(runs):
    out = {}
    for t in TEST_TASKS_17:
        vals = []
        for r in runs:
            v = read_treesim(r, t)
            if v is not None:
                vals.append(v)
            else:
                # failed_no_outputs etc. → score 0 (failures-as-zero convention)
                vals.append(0.0)
        out[t] = vals
    return out


def aggregate(runs, label):
    pt = per_task_means(runs)
    all_means = [statistics.mean(v) for v in pt.values()]
    mean = statistics.mean(all_means)
    sd = statistics.stdev(all_means) if len(all_means) > 1 else 0.0
    n_pass = sum(1 for v in all_means if v >= 0.7)
    print(f"\n{label}: failures-as-zero per-task mean = {mean:.3f}  σ={sd:.3f}  pass≥0.7={n_pass}/17")
    # cost per seed (best-effort using DeepSeek pricing)
    INP_C, INP_H, OUT = 0.14e-6, 0.0028e-6, 0.28e-6  # USD/token
    for r in runs:
        s_in = s_h = s_out = 0
        n_attempts_total = sr_used = 0
        for t in TEST_TASKS_17:
            st = read_status(r, t)
            s_in += st.get("prompt_tokens") or 0
            s_h += st.get("cache_read_tokens") or 0
            s_out += st.get("completion_tokens") or 0
            n_attempts_total += st.get("n_attempts") or 0
            if (st.get("n_attempts") or 0) > 1:
                sr_used += 1
        cost = ((s_in - s_h) * INP_C) + (s_h * INP_H) + (s_out * OUT)
        print(f"    {r}: prompt={s_in/1e6:.2f}M cache_read={s_h/1e6:.2f}M completion={s_out/1e3:.1f}K  $={cost:.3f}  attempts_sum={n_attempts_total}  tasks_with_retry={sr_used}")
    return pt


def paired_delta(vanilla_pt, adapt_pt):
    print("\nPaired (per-task seed-mean) vanilla vs adapt:")
    print(f"  {'task':<45} {'van_mean':>9} {'adp_mean':>9} {'delta':>8}")
    deltas = []
    wins = losses = ties = 0
    for t in TEST_TASKS_17:
        v = statistics.mean(vanilla_pt[t])
        a = statistics.mean(adapt_pt[t])
        d = a - v
        deltas.append(d)
        if d > 0.01:
            wins += 1
        elif d < -0.01:
            losses += 1
        else:
            ties += 1
        print(f"  {t:<45} {v:>9.3f} {a:>9.3f} {d:>+8.3f}")
    print(f"  --- Wins/Losses/Ties (|delta|>0.01): {wins}/{losses}/{ties} ---")
    print(f"  Mean delta (adapt - vanilla): {statistics.mean(deltas):+.3f}  σ={statistics.stdev(deltas):.3f}")


if __name__ == "__main__":
    print("=" * 78)
    print("OH-DSv4 vanilla vs adapt (XN-019)")
    print("=" * 78)
    v_pt = aggregate(VANILLA_RUNS, "Vanilla (n=2)")
    a_pt = aggregate(ADAPT_RUNS, "Adapt (RAG+M1u+self-refine, n=2)")
    paired_delta(v_pt, a_pt)

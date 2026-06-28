#!/usr/bin/env python3
"""Per-task treesim matrix across canonical conditions.

Builds wide table: task × (vanilla_dsv4_min, vanilla_dsv4_full, best_dsv4,
best_m1u_dsv4, m1u_minimax, a3_minimax, vanilla_minimax) showing mean across
seeds and per-seed list. Used to settle the "plugin-helps-vs-hurts"
question by paired comparison.
"""
from __future__ import annotations
import json, statistics
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/matt/sci/repo3")

# Each entry: (label, [list of summary.json paths or per-task dirs])
# We accept either a `_summary.json`-with-`results` (old format) or a
# directory of `<task>_eval.json` files (new format).
CONDITIONS = {
    # --- DSv4-flash (new) ---
    "vanilla_dsv4_min":   [("dir", ROOT / f"data/eval/results/dsv4_min_primer_s{i}/claude_code_no_plugin_minprimer") for i in (1,2,3)],
    "vanilla_dsv4_full":  [("dir", ROOT / f"data/eval/results/dsv4_full_primer_s{i}/claude_code_no_plugin") for i in (2,3)] + [("dir", ROOT / "data/eval/results/dsv4flash_direct_s1/claude_code_no_plugin")],
    "best_dsv4":          [("dir", ROOT / f"data/eval/results/best_setup_dsv4_s{i}/claude_code_repo3_plugin_xmllint_all") for i in (1,2,3)],
    "best_m1u_dsv4":      [("dir", ROOT / f"data/eval/results/best_setup_m1u_dsv4_s{i}/claude_code_repo3_plugin_xmllint_all_m1u") for i in (1,2,3)],
    # --- minimax m2.7 (old) ---
    "m1u_minimax":        [("summary", ROOT / f"misc/memory_artifacts/scores/mem_m1u_s{i}_summary.json") for i in (1,2,3)],
    "a3_minimax":         [("summary", ROOT / f"misc/pac1/scores/e23_summary.json"),
                           ("summary", ROOT / f"misc/pac1/scores/e23s2_summary.json"),
                           ("summary", ROOT / f"misc/pac1/scores/a3_s3_summary.json")],
    "a5_minimax":         [("summary", ROOT / f"misc/pac1/scores/e24_summary.json"),
                           ("summary", ROOT / f"misc/pac1/scores/e24s2_summary.json"),
                           ("summary", ROOT / f"misc/pac1/scores/e24s3_summary.json")],
    "vanilla_minimax":    [("summary", ROOT / "misc/memory_artifacts/scores/noplug_mm_v2_s2_summary.json")],
    "best_mm":            [("dir", ROOT / "data/eval/results/best_setup_mm_s1/claude_code_repo3_plugin_xmllint_all")],
    "best_m1u_mm":        [("dir", ROOT / "data/eval/results/best_setup_m1u_mm_s1/claude_code_repo3_plugin_xmllint_all_m1u")],
    "minprimer_mm":       [("dir", ROOT / "data/eval/results/minprimer_mm_s1/claude_code_no_plugin_minprimer")],
}

def read_one(kind: str, path: Path) -> dict[str, float]:
    """Returns {task_name: treesim} for one seed."""
    out = {}
    if kind == "summary":
        if not path.exists():
            return out
        d = json.loads(path.read_text())
        for r in d.get("results", []):
            t = r.get("treesim")
            if t is not None:
                out[r["experiment"]] = float(t)
    elif kind == "dir":
        if not path.exists():
            return out
        for f in path.glob("*_eval.json"):
            try:
                d = json.loads(f.read_text())
            except Exception:
                continue
            t = d.get("treesim")
            if t is not None:
                out[d.get("experiment", f.stem.replace("_eval",""))] = float(t)
    return out

def load_condition(specs):
    """Returns {task: [scores across seeds]}"""
    out = defaultdict(list)
    for kind, p in specs:
        d = read_one(kind, p)
        for task, score in d.items():
            out[task].append(score)
    return dict(out)

def main():
    data = {name: load_condition(specs) for name, specs in CONDITIONS.items()}

    all_tasks = sorted({t for d in data.values() for t in d.keys()})

    # Print main table
    cols = ["vanilla_minimax","a3_minimax","m1u_minimax","a5_minimax",
            "vanilla_dsv4_full","vanilla_dsv4_min","best_dsv4","best_m1u_dsv4"]
    print(f"{'task':40s} " + " ".join(f"{c:>16s}" for c in cols))
    for t in all_tasks:
        row = [t[:40]]
        for c in cols:
            scores = data[c].get(t, [])
            if scores:
                m = statistics.mean(scores)
                if len(scores) > 1:
                    sd = statistics.stdev(scores)
                    row.append(f"{m:6.3f}±{sd:5.3f}")
                else:
                    row.append(f"{m:6.3f}      ")
            else:
                row.append(" "*15 + "—")
        print(f"{row[0]:40s} " + " ".join(f"{r:>16s}" for r in row[1:]))

    print()
    print("=== aggregate means (treesim) ===")
    for c in cols:
        scores_per_seed = []  # mean per seed
        # collect seeds: max seed count we have for any task
        seed_counts = [len(data[c].get(t, [])) for t in all_tasks if data[c].get(t)]
        nseeds = max(seed_counts) if seed_counts else 0
        for s in range(nseeds):
            seed_scores = [data[c][t][s] for t in all_tasks if t in data[c] and len(data[c][t]) > s]
            if seed_scores:
                scores_per_seed.append(statistics.mean(seed_scores))
        if scores_per_seed:
            m = statistics.mean(scores_per_seed)
            sd = statistics.stdev(scores_per_seed) if len(scores_per_seed)>1 else 0.0
            print(f"  {c:25s}  n_seeds={len(scores_per_seed):d}  mean={m:.4f}  σ={sd:.4f}  per_seed={['%.3f'%x for x in scores_per_seed]}")
        else:
            print(f"  {c:25s}  no data")

    print()
    print("=== paired diffs vs vanilla_dsv4_min (mean-of-seed-means) ===")
    base = data["vanilla_dsv4_min"]
    for c in ["best_dsv4","best_m1u_dsv4","vanilla_dsv4_full"]:
        diffs = []
        for t in all_tasks:
            if t in base and t in data[c]:
                bm = statistics.mean(base[t])
                cm = statistics.mean(data[c][t])
                diffs.append((t, cm - bm))
        if diffs:
            tot = statistics.mean(d for _,d in diffs)
            wins = sum(1 for _,d in diffs if d > 0.02)
            losses = sum(1 for _,d in diffs if d < -0.02)
            ties = len(diffs) - wins - losses
            print(f"\n{c}  vs  vanilla_dsv4_min   mean Δ={tot:+.4f}  W/L/T={wins}/{losses}/{ties}")
            for t, d in sorted(diffs, key=lambda x: x[1]):
                marker = "*" if abs(d) > 0.10 else " "
                print(f"  {marker} {t[:55]:55s} {d:+.3f}")

    print()
    print("=== paired diffs: m1u_minimax vs a3_minimax (the OLD plugin lift) ===")
    a3 = data["a3_minimax"]; m1 = data["m1u_minimax"]
    diffs = []
    for t in all_tasks:
        if t in a3 and t in m1:
            diffs.append((t, statistics.mean(m1[t]) - statistics.mean(a3[t])))
    if diffs:
        tot = statistics.mean(d for _,d in diffs)
        wins = sum(1 for _,d in diffs if d > 0.02); losses = sum(1 for _,d in diffs if d < -0.02)
        print(f"  m1u - a3 (n={len(diffs)})  mean Δ={tot:+.4f}  W/L/T={wins}/{losses}/{len(diffs)-wins-losses}")
        for t, d in sorted(diffs, key=lambda x: x[1]):
            marker = "*" if abs(d) > 0.10 else " "
            print(f"  {marker} {t[:55]:55s} {d:+.3f}")

    print()
    print("=== paired diffs: vanilla_dsv4_min vs m1u_minimax (the NEW vs OLD-best) ===")
    new = data["vanilla_dsv4_min"]; old = data["m1u_minimax"]
    diffs = []
    for t in all_tasks:
        if t in new and t in old:
            diffs.append((t, statistics.mean(new[t]) - statistics.mean(old[t])))
    if diffs:
        tot = statistics.mean(d for _,d in diffs)
        wins = sum(1 for _,d in diffs if d > 0.02); losses = sum(1 for _,d in diffs if d < -0.02)
        print(f"  vanilla_dsv4_min - m1u_minimax (n={len(diffs)})  mean Δ={tot:+.4f}  W/L/T={wins}/{losses}/{len(diffs)-wins-losses}")
        for t, d in sorted(diffs, key=lambda x: x[1]):
            marker = "*" if abs(d) > 0.10 else " "
            print(f"  {marker} {t[:55]:55s} {d:+.3f}")

if __name__ == "__main__":
    main()

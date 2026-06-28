#!/usr/bin/env python3
"""Compare two scored runs task-by-task. Output: aggregate stats + per-task deltas."""
from __future__ import annotations
import json
import statistics
import sys
from pathlib import Path

def load_run(results_dir: Path) -> dict[str, dict]:
    out = {}
    for f in sorted(results_dir.glob("*_eval.json")):
        if f.name.startswith("_"):
            continue
        r = json.loads(f.read_text())
        name = r.get("experiment") or f.name.removesuffix("_eval.json")
        out[name] = r
    return out

def score(r: dict) -> float | None:
    if r.get("status") != "success":
        return None
    return r.get("treesim", r.get("overall_01"))

def summarize(label: str, run: dict[str, dict]) -> dict:
    scores = [(n, score(r)) for n, r in run.items()]
    ok = [(n, s) for n, s in scores if s is not None]
    failed = [n for n, s in scores if s is None]
    vals = [s for _, s in ok]
    return {
        "label": label,
        "n_total": len(scores),
        "n_scored": len(ok),
        "n_failed": len(failed),
        "failed": failed,
        "mean": statistics.mean(vals) if vals else 0.0,
        "median": statistics.median(vals) if vals else 0.0,
        "min": min(vals) if vals else 0.0,
        "max": max(vals) if vals else 0.0,
        "pass_ge07": sum(1 for v in vals if v >= 0.7),
    }

def main(a_dir: str, a_label: str, b_dir: str, b_label: str):
    a = load_run(Path(a_dir))
    b = load_run(Path(b_dir))

    common = sorted(set(a) & set(b))
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))

    print(f"\n{'='*78}")
    print(f"  {a_label} vs {b_label}")
    print(f"{'='*78}")
    print(f"  tasks in both: {len(common)}")
    if only_a: print(f"  only in {a_label}: {only_a}")
    if only_b: print(f"  only in {b_label}: {only_b}")

    sa = summarize(a_label, a)
    sb = summarize(b_label, b)
    for s in (sa, sb):
        print(f"\n  {s['label']}")
        print(f"    scored: {s['n_scored']}/{s['n_total']}    failed: {s['failed']}")
        print(f"    mean: {s['mean']:.3f}    median: {s['median']:.3f}    range: [{s['min']:.3f}, {s['max']:.3f}]")
        print(f"    pass >=0.7: {s['pass_ge07']}/{s['n_scored']}")

    # Paired comparison on common tasks both scored ok
    pairs = []
    for n in common:
        sa_v = score(a[n]); sb_v = score(b[n])
        if sa_v is not None and sb_v is not None:
            pairs.append((n, sa_v, sb_v, sa_v - sb_v))
    if pairs:
        deltas = [d for _,_,_,d in pairs]
        print(f"\n  Paired on {len(pairs)} tasks scored in both runs:")
        print(f"    mean delta ({a_label} - {b_label}): {statistics.mean(deltas):+.3f}")
        print(f"    median delta: {statistics.median(deltas):+.3f}")
        print(f"    wins {a_label}: {sum(1 for d in deltas if d > 0)}")
        print(f"    wins {b_label}: {sum(1 for d in deltas if d < 0)}")
        print(f"    ties: {sum(1 for d in deltas if d == 0)}")

        print(f"\n  Biggest wins for {a_label}:")
        for n, sa_v, sb_v, d in sorted(pairs, key=lambda x: -x[3])[:8]:
            print(f"    {d:+.3f}   {a_label}={sa_v:.3f}  {b_label}={sb_v:.3f}   {n}")
        print(f"\n  Biggest wins for {b_label}:")
        for n, sa_v, sb_v, d in sorted(pairs, key=lambda x: x[3])[:8]:
            print(f"    {d:+.3f}   {a_label}={sa_v:.3f}  {b_label}={sb_v:.3f}   {n}")

    # Tasks where one run has no input/failed
    only_a_scored = [n for n in common if score(a[n]) is not None and score(b[n]) is None]
    only_b_scored = [n for n in common if score(b[n]) is not None and score(a[n]) is None]
    if only_a_scored:
        print(f"\n  Scored only in {a_label}: {only_a_scored}")
    if only_b_scored:
        print(f"\n  Scored only in {b_label}: {only_b_scored}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

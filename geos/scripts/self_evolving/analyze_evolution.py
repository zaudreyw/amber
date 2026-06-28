#!/usr/bin/env python3
"""Analyze self-evolving agent runs: compare versions across rounds.

Reads `data/.../self_evolving_2026-04-30/abl_se_round/se_roundN_s1/` for
N in 0..3, scores them, and produces comparison tables:

1. Per-round score table (v0/v1/v2/v3)
2. v3 vs v0 head-to-head on same tasks (round 0 task list, run with v3 in round 3)
3. v3 vs C6 (best human-designed cell)
4. Per-version edit summary (what files did the agent author at each step?)

Usage:
    python3 scripts/self_evolving/analyze_evolution.py
"""
from __future__ import annotations
import json
import statistics
from pathlib import Path

ROOT = Path('/data/shared/geophysics_agent_data/data/eval/self_evolving_2026-04-30')
RES_ROOT = ROOT / '_results'
PLUGIN_BASE = Path('/home/matt/sci/repo3/plugin_evolving')


def gather_round(round_n: int) -> dict[str, float]:
    rd = ROOT / 'abl_se_round' / f'se_round{round_n}_s1'
    eval_dir = RES_ROOT / f'se_round{round_n}_s1' / 'abl_se_round'
    out = {}
    if not eval_dir.exists():
        return out
    for ej in sorted(eval_dir.glob('*_eval.json')):
        task = ej.stem.replace('_eval', '')
        try:
            out[task] = json.loads(ej.read_text())['treesim']
        except Exception:
            pass
    return out


def gather_C6() -> dict[str, list[float]]:
    """Per-task scores for C6 (winning cell from Task 0), 3 seeds."""
    base = Path('/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results')
    out = {}
    for s in (1, 2, 3):
        ed = base / f'c6_dsv4_s{s}' / 'abl_c6_xmllint_hook'
        if not ed.exists(): continue
        for ej in ed.glob('*_eval.json'):
            task = ej.stem.replace('_eval', '')
            try:
                t = json.loads(ej.read_text())['treesim']
                out.setdefault(task, []).append(t)
            except Exception:
                pass
    return out


def render_evolution_log() -> str:
    log = ROOT / 'version_log.jsonl'
    if not log.exists():
        return "(no version log yet)"
    parts = []
    for line in log.read_text().splitlines():
        try:
            d = json.loads(line.strip())
            parts.append(
                f"v{d['version']} (parent v{d['parent']}) @ {d['timestamp']}: "
                f"round_mean_treesim={d.get('round_mean_treesim','?'):.4f if isinstance(d.get('round_mean_treesim'), float) else d.get('round_mean_treesim','?')} "
                f"files_written={d.get('files_written',[])}"
            )
        except Exception:
            pass
    return "\n".join(parts)


def render_plugin_evolution() -> str:
    """For each version, list the editable files that exist."""
    parts = []
    for v_dir in sorted(PLUGIN_BASE.glob('v*'), key=lambda p: int(p.name[1:])):
        n = int(v_dir.name[1:])
        files = []
        primer = v_dir / 'PRIMER.md'
        if primer.exists():
            files.append(('PRIMER.md', primer.stat().st_size))
        for sub in ('memory', 'skills', 'agents'):
            d = v_dir / sub
            if d.exists():
                for f in sorted(d.glob('*.md')):
                    files.append((f'{sub}/{f.name}', f.stat().st_size))
        parts.append(f"v{n}: {len(files)} files")
        for name, sz in files:
            parts.append(f"  - {name} ({sz}B)")
    return "\n".join(parts)


def main():
    rounds = {n: gather_round(n) for n in range(4)}
    print("=== Per-round mean treesim ===")
    for n in range(4):
        scores = list(rounds[n].values())
        if scores:
            print(f"  v{n} on round {n}: mean={statistics.mean(scores):.4f}  n={len(scores)}")
        else:
            print(f"  v{n} on round {n}: NO DATA")

    print()
    print("=== v3 vs v0 (round 3 = v3 re-running round 0's tasks) ===")
    v0_scores = rounds[0]  # tasks 1-6 with v0
    v3_scores = rounds[3]  # tasks 1-6 with v3 (if run was done)
    common = set(v0_scores.keys()) & set(v3_scores.keys())
    if common:
        diffs = [(t, v3_scores[t] - v0_scores[t]) for t in sorted(common)]
        for t, d in diffs:
            print(f"  {t[:50]:50s}  v0={v0_scores[t]:.3f}  v3={v3_scores[t]:.3f}  Δ={d:+.3f}")
        mean_d = statistics.mean(d for _, d in diffs)
        wins = sum(1 for _, d in diffs if d > 0.02)
        losses = sum(1 for _, d in diffs if d < -0.02)
        print(f"  mean Δ = {mean_d:+.4f}, W/L = {wins}/{losses}")
    else:
        print("  (no common tasks yet — round 3 not done)")

    print()
    print("=== v3 vs C6 (across all 17 tasks) ===")
    # v3 covers round 0 tasks (6); also round 1+2+3 are different versions on different tasks
    # For comprehensive comparison: run v3 on all 17 tasks (not done yet).
    # For now: compare v3's scores on round 0 tasks vs C6's.
    c6 = gather_C6()
    c6_means = {t: statistics.mean(scores) for t, scores in c6.items() if scores}
    if v3_scores:
        common = set(v3_scores.keys()) & set(c6_means.keys())
        if common:
            for t in sorted(common):
                d = v3_scores[t] - c6_means[t]
                print(f"  {t[:50]:50s}  C6={c6_means[t]:.3f}  v3={v3_scores[t]:.3f}  Δ={d:+.3f}")
        else:
            print("  (no v3 data yet)")

    print()
    print("=== Plugin evolution ===")
    print(render_plugin_evolution())

    print()
    print("=== Version log ===")
    print(render_evolution_log())


if __name__ == "__main__":
    main()

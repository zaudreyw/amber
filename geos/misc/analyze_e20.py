#!/usr/bin/env python3
"""Analysis for E20 hook-ablation (D-004 pre-registered decision rule).

Reads per-run per-task status.json + hook-event logs from the 4 E20 cells
× 3 independent runs (e20_run1/run2/run3), joins with TreeSim scores if
available, and emits a pre-registered comparison table.

Usage:
    cd /home/matt/sci/repo3
    uv run python misc/analyze_e20.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

REPO = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO / "data" / "eval"

CELLS = {
    "C0_nohook":        "claude_code_repo3_plugin_nohook",
    "C1_hook":          "claude_code_repo3_plugin",
    "C2_noop_nohook":   "claude_code_repo3_plugin_noop_nohook",
    "C4_hook_noop":     "claude_code_repo3_plugin_noop",
}
RUNS = ["e20_run1", "e20_run2", "e20_run3"]
TASKS = [
    "AdvancedExampleDeviatedElasticWellbore",
    "AdvancedExampleDruckerPrager",
    "ExampleDPWellbore",
    "ExampleThermalLeakyWell",
]


def load_status(cell_dir: Path, run: str, task: str) -> dict | None:
    path = cell_dir / run / task / "status.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def load_hook_events(cell_dir: Path, run: str, task: str) -> list[dict]:
    path = cell_dir / run / task / ".verify_hook_events.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text().splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    return events


_SUMMARY_CACHE: dict[tuple[str, str], dict[str, dict]] = {}


def load_treesim(cell_dir: Path, run: str, task: str) -> float | None:
    """Look up task's treesim from the batch_evaluate --output summary JSON.

    score_e20.sh writes per-(cell,run) summaries to
    data/eval/results/e20/<cell_subdir>__<run>_summary.json with
    {results: [{experiment, treesim, overall_score, status, ...}]}.
    """
    key = (cell_dir.name, run)
    if key not in _SUMMARY_CACHE:
        summary_path = EVAL_DIR / "results" / "e20" / f"{cell_dir.name}__{run}_summary.json"
        if not summary_path.exists():
            _SUMMARY_CACHE[key] = {}
        else:
            try:
                payload = json.loads(summary_path.read_text())
                by_task: dict[str, dict] = {}
                for r in payload.get("results", []):
                    exp = r.get("experiment") or r.get("task") or r.get("name")
                    if isinstance(exp, str):
                        by_task[exp] = r
                _SUMMARY_CACHE[key] = by_task
            except Exception:
                _SUMMARY_CACHE[key] = {}
    entry = _SUMMARY_CACHE[key].get(task)
    if entry is None:
        return None
    if entry.get("status") != "success":
        return None  # scorer failure → treat as fa0 later
    ts = entry.get("treesim")
    return float(ts) if ts is not None else None


def summarize_cell(cell_key: str, cell_subdir: str) -> dict:
    cell_dir = EVAL_DIR / cell_subdir
    per_run = []
    statuses = Counter()            # final status (post runner retry)
    attempt_statuses = Counter()    # first-attempt status (pre retry)
    hook_event_counts = Counter()
    hook_rescues_attempted = 0
    hook_rescues_succeeded = 0
    stop_hook_errors = 0

    per_task_treesim: dict[str, list[tuple[str, float]]] = defaultdict(list)

    for run in RUNS:
        for task in TASKS:
            task_dir = cell_dir / run / task
            st = load_status(cell_dir, run, task)
            if st is None:
                per_run.append({"run": run, "task": task, "status": "MISSING"})
                statuses["MISSING"] += 1
                continue
            s = st.get("status", "unknown")
            statuses[s] += 1
            # First-attempt status: look for attempt_1/ (runner archives the
            # failed first attempt when --pseudo-tool-retries fires).
            a1 = task_dir / "attempt_1" / "status.json"
            if a1.exists():
                try:
                    ast = json.loads(a1.read_text()).get("status", "unknown")
                    attempt_statuses[ast] += 1
                except Exception:
                    attempt_statuses["unknown"] += 1
            else:
                attempt_statuses[s] += 1  # no retry fired; final == first attempt
            # Count stop-hook-error system events across this task + attempt_1
            for evpath in [task_dir / "events.jsonl", a1.parent / "events.jsonl" if a1.exists() else None]:
                if evpath is None or not evpath.exists():
                    continue
                try:
                    for line in evpath.read_text().splitlines():
                        if '"stop-hook-error"' in line:
                            stop_hook_errors += 1
                except Exception:
                    pass
            events = load_hook_events(cell_dir, run, task)
            blocks = [e for e in events if e.get("decision") == "block"]
            if blocks:
                hook_rescues_attempted += 1
                if s not in ("failed_no_outputs",):
                    hook_rescues_succeeded += 1
            for e in events:
                hook_event_counts[e.get("reason_category", "unknown")] += 1
            ts = load_treesim(cell_dir, run, task)
            per_task_treesim[task].append((run, ts if ts is not None else 0.0))
            per_run.append({"run": run, "task": task, "status": s, "treesim": ts})

    # Failures-as-zero mean per task across 3 runs, then mean across 4 tasks.
    per_task_means = {
        t: mean(v for _, v in vals) if vals else 0.0
        for t, vals in per_task_treesim.items()
    }
    overall_faz_mean = mean(per_task_means.values()) if per_task_means else 0.0
    n_failed = statuses.get("failed_no_outputs", 0)
    n_success = statuses.get("success", 0)
    n_total = sum(statuses.values())
    attempt_failed = attempt_statuses.get("failed_no_outputs", 0)
    attempt_total = sum(attempt_statuses.values())
    return {
        "cell": cell_key,
        "agent": cell_subdir,
        "statuses": dict(statuses),
        "attempt_statuses": dict(attempt_statuses),
        "n_total": n_total,
        "n_success": n_success,
        "n_failed_no_outputs": n_failed,
        "failure_rate": n_failed / n_total if n_total else 0,
        "first_attempt_failure_rate": (
            attempt_failed / attempt_total if attempt_total else 0
        ),
        "stop_hook_errors": stop_hook_errors,
        "hook_event_counts": dict(hook_event_counts),
        "hook_rescues_attempted": hook_rescues_attempted,
        "hook_rescues_succeeded": hook_rescues_succeeded,
        "per_task_faz_mean": per_task_means,
        "overall_faz_mean": overall_faz_mean,
        "per_run": per_run,
    }


def paired_treesim_map(cell_subdir: str) -> dict[tuple[str, str], float]:
    """Return {(run, task): treesim (or 0.0 for failures-as-zero)} for cell."""
    out: dict[tuple[str, str], float] = {}
    cell_dir = EVAL_DIR / cell_subdir
    for run in RUNS:
        summary_path = EVAL_DIR / "results" / "e20" / f"{cell_subdir}__{run}_summary.json"
        if not summary_path.exists():
            continue
        try:
            payload = json.loads(summary_path.read_text())
        except Exception:
            continue
        for r in payload.get("results", []):
            task = r.get("experiment")
            if task not in TASKS:
                continue
            if r.get("status") == "success":
                out[(run, task)] = float(r.get("treesim") or 0.0)
            else:
                out[(run, task)] = 0.0  # failures-as-zero
    return out


def wilcoxon_like(a: list[float], b: list[float]) -> dict:
    """Minimal Wilcoxon signed-rank on paired (a_i - b_i).

    Implemented without scipy to stay dep-free. Zero differences are
    dropped (a common convention). Returns rank-sum statistic, direction,
    and a two-sided p-value (normal approximation) for n >= 6.
    """
    diffs = [ai - bi for ai, bi in zip(a, b) if ai != bi]
    n = len(diffs)
    if n == 0:
        return {"n": 0, "W": None, "p_approx": None, "direction": "tie"}
    absd = sorted((abs(d), 1 if d > 0 else -1) for d in diffs)
    # rank (handle ties with average rank)
    ranks: list[float] = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and absd[j + 1][0] == absd[i][0]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2
        for _ in range(i, j + 1):
            ranks.append(avg_rank)
        i = j + 1
    w_plus = sum(r for r, (_, s) in zip(ranks, absd) if s > 0)
    w_minus = sum(r for r, (_, s) in zip(ranks, absd) if s < 0)
    W = min(w_plus, w_minus)
    # Normal approx (ties ignored)
    if n >= 6:
        mu = n * (n + 1) / 4
        sigma = (n * (n + 1) * (2 * n + 1) / 24) ** 0.5
        z = (W - mu) / sigma if sigma > 0 else 0.0
        # Two-sided p via erfc
        from math import erfc, sqrt
        p_approx = erfc(abs(z) / sqrt(2))
    else:
        p_approx = None
    direction = "a>b" if w_plus > w_minus else ("a<b" if w_minus > w_plus else "tie")
    return {
        "n": n,
        "W_plus": w_plus,
        "W_minus": w_minus,
        "W": W,
        "p_approx": p_approx,
        "direction": direction,
    }


def main() -> int:
    rows = [summarize_cell(k, v) for k, v in CELLS.items()]
    print("=" * 72)
    print("E20 hook-ablation summary (D-004)")
    print("=" * 72)
    header = f"{'cell':20s} {'n':>3s} {'succ':>4s} {'fail_no_out':>12s} {'fr':>5s} {'faz_mean':>8s} {'hook_blocks':>11s} {'rescue_succ':>11s}"
    print(header)
    print("-" * len(header))
    for r in rows:
        fr = r["failure_rate"]
        blocks = sum(v for k, v in r["hook_event_counts"].items() if k.startswith("no_xml") or k.startswith("parse_error"))
        print(
            f"{r['cell']:20s} {r['n_total']:>3d} {r['n_success']:>4d} "
            f"{r['n_failed_no_outputs']:>12d} {fr:>5.2f} "
            f"{r['overall_faz_mean']:>8.3f} {blocks:>11d} {r['hook_rescues_succeeded']:>11d}"
        )
    print("-" * len(header))
    print()
    print("Hook event categories (across cells):")
    for r in rows:
        if r["hook_event_counts"]:
            print(f"  {r['cell']}: {r['hook_event_counts']}")
    print()
    print("Decision rule (per D-004):")
    c0 = next(r for r in rows if r["cell"] == "C0_nohook")
    c1 = next(r for r in rows if r["cell"] == "C1_hook")
    c2 = next(r for r in rows if r["cell"] == "C2_noop_nohook")
    c4 = next(r for r in rows if r["cell"] == "C4_hook_noop")
    print(f"  C0 failure rate: {c0['failure_rate']:.2%}")
    print(f"  C1 failure rate: {c1['failure_rate']:.2%}  (hook)")
    print(f"  C2 failure rate: {c2['failure_rate']:.2%}  (noop)")
    print(f"  C4 failure rate: {c4['failure_rate']:.2%}  (hook+noop)")
    print()
    hook_effect = c0["failure_rate"] - c1["failure_rate"]
    noop_effect = c0["failure_rate"] - c2["failure_rate"]
    print(f"  Hook effect  (C0-C1): {hook_effect:+.2%}")
    print(f"  Noop effect  (C0-C2): {noop_effect:+.2%}")
    print(f"  Hook + noop  (C0-C4): {(c0['failure_rate'] - c4['failure_rate']):+.2%}")
    print()
    faz_hook = c1["overall_faz_mean"] - c0["overall_faz_mean"]
    faz_noop = c2["overall_faz_mean"] - c0["overall_faz_mean"]
    print(f"  ΔFailures-as-0 TreeSim (hook): {faz_hook:+.3f}")
    print(f"  ΔFailures-as-0 TreeSim (noop): {faz_noop:+.3f}")

    # Paired Wilcoxon signed-rank on failures-as-zero TreeSim per (run, task)
    c0_map = paired_treesim_map(CELLS["C0_nohook"])
    c1_map = paired_treesim_map(CELLS["C1_hook"])
    c2_map = paired_treesim_map(CELLS["C2_noop_nohook"])
    c4_map = paired_treesim_map(CELLS["C4_hook_noop"])
    print()
    print("Paired TreeSim (failures-as-zero) deltas:")
    for label, a_map, b_map in [
        ("C1 vs C0 (hook effect)", c1_map, c0_map),
        ("C2 vs C0 (noop effect)", c2_map, c0_map),
        ("C4 vs C0 (hook+noop vs bare)", c4_map, c0_map),
        ("C1 vs C2 (hook vs noop)", c1_map, c2_map),
    ]:
        keys = sorted(a_map.keys() & b_map.keys())
        if not keys:
            continue
        a = [a_map[k] for k in keys]
        b = [b_map[k] for k in keys]
        mean_diff = mean(ai - bi for ai, bi in zip(a, b))
        w = wilcoxon_like(a, b)
        print(
            f"  {label:40s} n={w['n']:2d} "
            f"mean_diff={mean_diff:+.3f} dir={w['direction']:>3s} "
            f"p≈{w['p_approx']:.3f}" if w['p_approx'] is not None else
            f"  {label:40s} n={w['n']:2d} mean_diff={mean_diff:+.3f} dir={w['direction']:>3s} p=N/A"
        )

    out = REPO / "misc" / "e20_summary.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

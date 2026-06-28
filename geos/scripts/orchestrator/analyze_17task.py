#!/usr/bin/env python3
"""Cross-implementation analysis on the 17-task v2 set.

Pulls TreeSim, wall-clock, and token usage from each implementation's
artifacts, prints a paired comparison + summary tables, and (optionally)
writes the result to markdown.

Implementations supported:
- orchestrator-DSv4flash (merged from two run dirs: 5task + remaining-12)
- vanilla-DSv4flash (claude_code_no_plugin/dsv4flash_direct_s1)
- openhands-minimax (oh_test17_s1)
- openhands+plugin-minimax (oh_plugin_test17_s1)

Per-task token tally for Claude Code runs reads claude_stdout.json /
acpx_output.json (each line is JSONL with `message.usage`). For OpenHands
status.json carries explicit `prompt_tokens` / `completion_tokens` /
`cache_read_tokens`. The two are reported separately and not summed.
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

V2_TASKS = [
    "AdvancedExampleCasedContactThermoElasticWellbore",
    "AdvancedExampleDeviatedElasticWellbore",
    "AdvancedExampleDruckerPrager",
    "AdvancedExampleExtendedDruckerPrager",
    "AdvancedExampleModifiedCamClay",
    "AdvancedExampleViscoDruckerPrager",
    "ExampleDPWellbore",
    "ExampleEDPWellbore",
    "ExampleIsothermalLeakyWell",
    "ExampleMandel",
    "ExampleThermalLeakyWell",
    "ExampleThermoporoelasticConsolidation",
    "TutorialPoroelasticity",
    "TutorialSneddon",
    "buckleyLeverettProblem",
    "kgdExperimentValidation",
    "pknViscosityDominated",
]


@dataclass
class TaskRecord:
    task: str
    treesim: float | None = None
    elapsed_seconds: float | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_cache_read: int = 0
    tokens_cache_write: int = 0
    cost_usd: float | None = None
    n_llm_calls: int | None = None
    status: str = "unknown"


@dataclass
class Implementation:
    name: str
    workers: int
    records: dict[str, TaskRecord] = field(default_factory=dict)
    # campaign_wall_seconds: max(ended) - min(started) across all task statuses,
    # if those fields are populated. Falls back to None.
    campaign_wall_seconds: float | None = None


# ---------- token loaders ----------

def parse_iso(ts: str | None) -> float | None:
    if not ts:
        return None
    from datetime import datetime
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts).timestamp()
    except Exception:
        return None


def compute_campaign_wall(run_dir: Path) -> float | None:
    """Min(started) → max(ended) across all task status.json files.

    Falls back to filesystem mtimes (earliest task dir ctime → latest
    status.json mtime) if the JSON timestamps are absent — used for the
    orchestrator runner, which doesn't populate started/ended.
    """
    starts: list[float] = []
    ends: list[float] = []
    for p in run_dir.glob("*/status.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        s = parse_iso(d.get("started"))
        e = parse_iso(d.get("ended") or d.get("updated"))
        if s is not None:
            starts.append(s)
        if e is not None:
            ends.append(e)
    if starts and ends:
        return max(ends) - min(starts)
    # Filesystem fallback
    fs_starts: list[float] = []
    fs_ends: list[float] = []
    for sub in run_dir.iterdir():
        if not sub.is_dir():
            continue
        meta = sub / "eval_metadata.json"
        if meta.exists():
            fs_starts.append(meta.stat().st_mtime)
        st = sub / "status.json"
        if st.exists():
            fs_ends.append(st.stat().st_mtime)
    if fs_starts and fs_ends:
        return max(fs_ends) - min(fs_starts)
    return None


def tally_jsonl_usage(path: Path) -> tuple[int, int, int, int]:
    """Sum usage across DISTINCT `message.id` entries in a JSONL file.

    P1C fix (RN-005): the Claude Code stream-json format re-emits the
    same `message.id` multiple times (subagent fan-out, retries). Naive
    summation double-counts by 2-4×. We dedup by `message.id` and use
    the LAST observed usage per id (which has the cumulative count).

    Returns (input, output, cache_read, cache_write).
    """
    if not path.exists():
        return 0, 0, 0, 0
    by_id: dict[str, dict] = {}
    fallback = []  # for lines without message.id
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message")
        if not isinstance(m, dict):
            continue
        u = m.get("usage")
        if not isinstance(u, dict):
            continue
        mid = m.get("id")
        if mid:
            by_id[mid] = u  # last write wins
        else:
            fallback.append(u)
    inp = out = cr = cw = 0
    for u in list(by_id.values()) + fallback:
        inp += int(u.get("input_tokens") or 0)
        out += int(u.get("output_tokens") or 0)
        cr += int(u.get("cache_read_input_tokens") or 0)
        cw += int(u.get("cache_creation_input_tokens") or 0)
    return inp, out, cr, cw


# ---------- TreeSim loader ----------

def load_treesim(eval_dir: Path, task: str) -> float | None:
    p = eval_dir / f"{task}_eval.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
    except Exception:
        return None
    val = d.get("overall_01") or d.get("treesim")
    if val is None:
        return None
    return float(val)


# ---------- Orchestrator (merge two run dirs) ----------

def load_orchestrator(run_dirs: list[Path], result_dirs: list[Path], workers: int) -> Implementation:
    impl = Implementation(name="orchestrator-DSv4flash", workers=workers)
    walls: list[float] = []
    for run_dir, result_dir in zip(run_dirs, result_dirs):
        for task in V2_TASKS:
            task_dir = run_dir / task
            if not task_dir.exists():
                continue
            r = TaskRecord(task=task)
            sp = task_dir / "status.json"
            if sp.exists():
                s = json.loads(sp.read_text())
                r.status = s.get("status", "unknown")
                r.elapsed_seconds = s.get("elapsed_seconds")
            inp, out, cr, cw = tally_jsonl_usage(task_dir / "claude_stdout.json")
            r.tokens_input, r.tokens_output, r.tokens_cache_read, r.tokens_cache_write = inp, out, cr, cw
            r.treesim = load_treesim(result_dir, task)
            impl.records[task] = r
        w = compute_campaign_wall(run_dir)
        if w is not None:
            walls.append(w)
    # If multiple sub-campaigns were merged we report the sum of their walls
    # (these were not run concurrently).
    impl.campaign_wall_seconds = sum(walls) if walls else None
    return impl


# ---------- Vanilla DSv4-flash (claude_code_no_plugin) ----------

def load_vanilla(run_dir: Path, result_dir: Path, workers: int, name: str = "vanilla-DSv4flash") -> Implementation:
    impl = Implementation(name=name, workers=workers)
    impl.campaign_wall_seconds = compute_campaign_wall(run_dir)
    for task in V2_TASKS:
        task_dir = run_dir / task
        if not task_dir.exists():
            continue
        r = TaskRecord(task=task)
        sp = task_dir / "status.json"
        if sp.exists():
            s = json.loads(sp.read_text())
            r.status = "success" if s.get("exit_code") == 0 else f"exit_{s.get('exit_code')}"
            r.elapsed_seconds = s.get("elapsed_seconds")
        inp, out, cr, cw = tally_jsonl_usage(task_dir / "acpx_output.json")
        r.tokens_input, r.tokens_output, r.tokens_cache_read, r.tokens_cache_write = inp, out, cr, cw
        r.treesim = load_treesim(result_dir, task)
        impl.records[task] = r
    return impl


# ---------- OpenHands ----------

def load_openhands(run_dir: Path, result_dir: Path, workers: int, name: str) -> Implementation:
    impl = Implementation(name=name, workers=workers)
    impl.campaign_wall_seconds = compute_campaign_wall(run_dir)
    for task in V2_TASKS:
        task_dir = run_dir / task
        if not task_dir.exists():
            continue
        r = TaskRecord(task=task)
        sp = task_dir / "status.json"
        if sp.exists():
            s = json.loads(sp.read_text())
            r.status = s.get("status", "unknown")
            r.elapsed_seconds = s.get("elapsed_seconds")
            r.tokens_input = int(s.get("prompt_tokens") or 0)
            r.tokens_output = int(s.get("completion_tokens") or 0)
            r.tokens_cache_read = int(s.get("cache_read_tokens") or 0)
            r.tokens_cache_write = int(s.get("cache_write_tokens") or 0)
            r.cost_usd = s.get("accumulated_cost_usd")
            r.n_llm_calls = s.get("n_llm_calls")
        r.treesim = load_treesim(result_dir, task)
        impl.records[task] = r
    return impl


# ---------- summary ----------

def summarize(impl: Implementation, tasks: list[str]) -> dict:
    rec = [impl.records.get(t) for t in tasks]
    rec = [r for r in rec if r is not None]
    ts = [r.treesim for r in rec if r.treesim is not None]
    el = [r.elapsed_seconds for r in rec if r.elapsed_seconds is not None]
    tok_total = sum((r.tokens_input + r.tokens_output) for r in rec)
    cr_total = sum(r.tokens_cache_read for r in rec)
    cost_total = sum((r.cost_usd or 0.0) for r in rec)
    n_succ = sum(1 for r in rec if r.status == "success" or r.status.startswith("exit_0"))
    return {
        "name": impl.name,
        "workers": impl.workers,
        "n_tasks_present": len(rec),
        "n_success": n_succ,
        "treesim_mean": round(statistics.mean(ts), 4) if ts else None,
        "treesim_median": round(statistics.median(ts), 4) if ts else None,
        "treesim_min": round(min(ts), 4) if ts else None,
        "treesim_max": round(max(ts), 4) if ts else None,
        "treesim_n": len(ts),
        "compute_seconds_total": round(sum(el), 1) if el else None,
        "wall_seconds_effective": round(sum(el) / impl.workers, 1) if el else None,
        "campaign_wall_seconds": round(impl.campaign_wall_seconds, 1) if impl.campaign_wall_seconds else None,
        "implied_workers": (round(sum(el) / impl.campaign_wall_seconds, 2)
                            if (el and impl.campaign_wall_seconds) else None),
        "tokens_in_plus_out_total": tok_total,
        "tokens_cache_read_total": cr_total,
        "tokens_in_plus_out_per_task": int(tok_total / len(rec)) if rec else None,
        "cost_usd_total": round(cost_total, 4) if cost_total else None,
    }


def render_md(impls: list[Implementation], tasks: list[str], out: Path | None) -> None:
    lines: list[str] = []
    lines.append("# 17-task v2 — orchestrator vs prior implementations")
    lines.append("")
    lines.append("All metrics computed over the same 17 v2 tasks. TreeSim is the eval harness's tree-similarity score (0–1, higher better). `compute_seconds` sums per-task wall clock; `wall_seconds_effective = compute / workers` is the campaign wall-time at the run's actual concurrency level.")
    lines.append("")

    # per-impl summary
    lines.append("## Summary per implementation")
    lines.append("")
    cols = [
        ("name", "agent"),
        ("workers", "W"),
        ("n_success", "ok"),
        ("treesim_mean", "ts̄"),
        ("treesim_median", "ts̃"),
        ("compute_seconds_total", "compute (s)"),
        ("wall_seconds_effective", "wall@W (s)"),
        ("campaign_wall_seconds", "true wall (s)"),
        ("implied_workers", "impl. W"),
        ("tokens_in_plus_out_total", "tok in+out"),
        ("tokens_cache_read_total", "tok cache-read"),
        ("cost_usd_total", "cost ($)"),
    ]
    header = "| " + " | ".join(label for _, label in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines.append(header)
    lines.append(sep)
    for impl in impls:
        s = summarize(impl, tasks)
        row = []
        for key, _ in cols:
            v = s.get(key)
            if v is None:
                row.append("–")
            elif isinstance(v, float):
                row.append(f"{v:g}")
            else:
                row.append(str(v))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # paired TreeSim table
    lines.append("## Paired TreeSim per task")
    lines.append("")
    h = ["task"] + [i.name for i in impls]
    lines.append("| " + " | ".join(h) + " |")
    lines.append("| " + " | ".join("---" for _ in h) + " |")
    for t in tasks:
        cells = [t]
        for impl in impls:
            r = impl.records.get(t)
            if r is None or r.treesim is None:
                cells.append("–")
            else:
                cells.append(f"{r.treesim:.3f}")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # paired delta orchestrator - vanilla
    if len(impls) >= 2:
        a = impls[0]
        b = impls[1]
        lines.append(f"## Paired delta: {a.name} − {b.name}")
        lines.append("")
        lines.append(f"| task | {a.name} | {b.name} | Δ |")
        lines.append("| --- | --- | --- | --- |")
        deltas = []
        wins = losses = ties = 0
        for t in tasks:
            ra = a.records.get(t)
            rb = b.records.get(t)
            if ra and rb and ra.treesim is not None and rb.treesim is not None:
                d = ra.treesim - rb.treesim
                deltas.append(d)
                tag = "+" if d > 0.01 else ("−" if d < -0.01 else "=")
                if d > 0.01: wins += 1
                elif d < -0.01: losses += 1
                else: ties += 1
                lines.append(f"| {t} | {ra.treesim:.3f} | {rb.treesim:.3f} | {d:+.3f} {tag} |")
            else:
                lines.append(f"| {t} | – | – | – |")
        if deltas:
            lines.append("")
            lines.append(f"**mean Δ = {statistics.mean(deltas):+.3f}** | wins/losses/ties = {wins}/{losses}/{ties} | median Δ = {statistics.median(deltas):+.3f}")
        lines.append("")

    # per-task wall + tokens for each impl
    lines.append("## Per-task wall-clock and tokens")
    lines.append("")
    for impl in impls:
        lines.append(f"### {impl.name} (workers={impl.workers})")
        lines.append("")
        lines.append("| task | elapsed (s) | tok in | tok out | cache-read |")
        lines.append("| --- | --- | --- | --- | --- |")
        for t in tasks:
            r = impl.records.get(t)
            if r is None:
                lines.append(f"| {t} | – | – | – | – |")
                continue
            el = f"{r.elapsed_seconds:.1f}" if r.elapsed_seconds is not None else "–"
            lines.append(f"| {t} | {el} | {r.tokens_input} | {r.tokens_output} | {r.tokens_cache_read} |")
        lines.append("")

    text = "\n".join(lines)
    if out:
        out.write_text(text)
        print(f"\nWrote {out}\n")
    else:
        print(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--orch-runs", nargs="+", required=True,
                    help="Orchestrator run dirs (under data/eval/orchestrator_dsv4flash/)")
    ap.add_argument("--orch-results", nargs="+", required=True,
                    help="Orchestrator result dirs (under data/eval/results/<run>/orchestrator_dsv4flash)")
    ap.add_argument("--orch-workers", type=int, default=2)
    ap.add_argument("--vanilla-run", type=Path,
                    default=REPO / "data/eval/claude_code_no_plugin/dsv4flash_direct_s1")
    ap.add_argument("--vanilla-result", type=Path,
                    default=REPO / "data/eval/results/dsv4flash_direct_s1/claude_code_no_plugin")
    ap.add_argument("--vanilla-workers", type=int, default=6)
    ap.add_argument("--oh-run", type=Path,
                    default=REPO / "data/eval/openhands_no_plugin/oh_test17_s1")
    ap.add_argument("--oh-result", type=Path,
                    default=REPO / "data/eval/results/oh_test17_s1/openhands_no_plugin")
    ap.add_argument("--oh-name", default="openhands-minimax-m2.7")
    ap.add_argument("--oh-workers", type=int, default=4)
    ap.add_argument("--ohp-run", type=Path,
                    default=REPO / "data/eval/openhands_no_plugin/oh_plugin_test17_s1")
    ap.add_argument("--ohp-result", type=Path,
                    default=REPO / "data/eval/results/oh_plugin_test17_s1/openhands_no_plugin")
    ap.add_argument("--ohp-name", default="openhands+plugin-minimax-m2.7")
    ap.add_argument("--ohp-workers", type=int, default=4)
    # Additional DSv4-flash baselines (claude-code-no-plugin variants + plugin)
    ap.add_argument("--minprimer-run", type=Path,
                    default=REPO / "data/eval/claude_code_no_plugin_minprimer/dsv4_min_primer_s2")
    ap.add_argument("--minprimer-result", type=Path,
                    default=REPO / "data/eval/results/dsv4_min_primer_s2/claude_code_no_plugin_minprimer")
    ap.add_argument("--minprimer-workers", type=int, default=6)
    ap.add_argument("--fullprimer-run", type=Path,
                    default=REPO / "data/eval/claude_code_no_plugin/dsv4_full_primer_s2")
    ap.add_argument("--fullprimer-result", type=Path,
                    default=REPO / "data/eval/results/dsv4_full_primer_s2/claude_code_no_plugin")
    ap.add_argument("--fullprimer-workers", type=int, default=6)
    # results-only impls (no timing/tokens available because run dir was cleaned up)
    ap.add_argument("--bestsetup-result", type=Path,
                    default=REPO / "data/eval/results/best_setup_dsv4_s1/claude_code_repo3_plugin_xmllint_all")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if len(args.orch_runs) != len(args.orch_results):
        print("ERROR: --orch-runs and --orch-results must have equal length.")
        return 1

    impls: list[Implementation] = []

    orch = load_orchestrator(
        run_dirs=[Path(p) for p in args.orch_runs],
        result_dirs=[Path(p) for p in args.orch_results],
        workers=args.orch_workers,
    )
    impls.append(orch)

    if args.vanilla_run.exists():
        impls.append(load_vanilla(args.vanilla_run, args.vanilla_result, args.vanilla_workers))

    if args.minprimer_run.exists():
        impls.append(load_vanilla(args.minprimer_run, args.minprimer_result,
                                  args.minprimer_workers, name="DSv4flash+min-primer"))

    if args.fullprimer_run.exists():
        impls.append(load_vanilla(args.fullprimer_run, args.fullprimer_result,
                                  args.fullprimer_workers, name="DSv4flash+full-primer"))

    if args.bestsetup_result.exists():
        # results-only: no run dir, so timing/tokens are absent
        impl = Implementation(name="DSv4flash+plugin+xmllint (best-setup)", workers=6)
        for task in V2_TASKS:
            impl.records[task] = TaskRecord(task=task, treesim=load_treesim(args.bestsetup_result, task))
        impls.append(impl)

    if args.oh_run.exists():
        impls.append(load_openhands(args.oh_run, args.oh_result, args.oh_workers, args.oh_name))

    if args.ohp_run.exists():
        impls.append(load_openhands(args.ohp_run, args.ohp_result, args.ohp_workers, args.ohp_name))

    render_md(impls, V2_TASKS, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

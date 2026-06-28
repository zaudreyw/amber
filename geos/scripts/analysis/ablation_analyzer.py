#!/usr/bin/env python3
"""Ablation analyzer (subagent 1).

Compares two conditions of an ablation, dispatches subagents 0.1 and 0.2
on big-swing tasks, and writes a markdown report.

Phase 1: deterministic only (no Claude trajectory subagent).

Layout assumed:
  <results_root>/<agent_a>/<run_*>/<task>/{events.jsonl, status.json,
                                            inputs/*.xml}
  <results_root>/<agent_b>/<run_*>/<task>/...

Eval JSONs (per task) live in the parallel results-of-results layout
written by `batch_evaluate.py`:
  <eval_root>/<run_name>/<agent>/<task>_eval.json

Usage:
  python3 ablation_analyzer.py \
    --cond-a-name C1_min_primer --cond-a-runs <space-separated run dirs> \
    --cond-b-name C2_sr_no_rag  --cond-b-runs <space-separated run dirs> \
    --eval-root data/eval/results \
    --out docs/ablation_C1_vs_C2.md
"""
from __future__ import annotations
import argparse, json, statistics, sys
from pathlib import Path
from collections import defaultdict
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.analysis.tool_use_differ import diff_tool_use, summarize_one as tool_summarize_one
from scripts.analysis.treesim_xmllint_analyzer import analyze as treesim_analyze, DEFAULT_SCHEMA


def _events_last_assistant_usage(events_path: Path) -> dict:
    """Cumulative cost + final usage from a per-task events.jsonl.

    The `type: result` event (emitted once at the end by Claude Code) carries
    cumulative `total_cost_usd` and a final `usage` block. Fall back to
    summing per-`assistant`-message `message.usage` if no result event present.
    """
    if not events_path.exists():
        return {}
    final_cost = None
    final_usage = None
    sum_in = 0
    sum_out = 0
    sum_cache = 0
    n_assistant_with_usage = 0
    with events_path.open() as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            t = ev.get("type")
            if t == "result":
                if ev.get("total_cost_usd") is not None:
                    final_cost = float(ev["total_cost_usd"])
                u = ev.get("usage")
                if u: final_usage = u
            elif t == "assistant":
                # Per-assistant usage lives under `message.usage`.
                u = (ev.get("message", {}) or {}).get("usage") or {}
                if u:
                    n_assistant_with_usage += 1
                    sum_in    += (u.get("input_tokens", 0) or 0)
                    sum_out   += (u.get("output_tokens", 0) or 0)
                    sum_cache += (u.get("cache_read_input_tokens", 0) or 0)
    if final_usage is not None:
        return {
            "input_tokens": int(final_usage.get("input_tokens", 0) or 0),
            "output_tokens": int(final_usage.get("output_tokens", 0) or 0),
            "cache_read_input_tokens": int(final_usage.get("cache_read_input_tokens", 0) or 0),
            "total_cost_usd": float(final_cost or 0.0),
            "source": "result_event",
        }
    if n_assistant_with_usage > 0:
        return {
            "input_tokens": sum_in,
            "output_tokens": sum_out,
            "cache_read_input_tokens": sum_cache,
            "total_cost_usd": float(final_cost or 0.0),
            "source": "summed_assistant",
        }
    return {}


def _elapsed_seconds(task_dir: Path) -> float | None:
    st = task_dir / "status.json"
    if not st.exists(): return None
    try:
        return float(json.loads(st.read_text()).get("elapsed_seconds") or 0)
    except Exception:
        return None


def _per_task_treesim(run_dirs: list[Path], eval_root: Path, agent_name: str) -> dict[str, list[float]]:
    """{task: [score_per_seed]} aggregating across run_dirs."""
    out = defaultdict(list)
    for rd in run_dirs:
        run_name = rd.name
        eval_dir = eval_root / run_name / agent_name
        if not eval_dir.exists():
            continue
        for ej in eval_dir.glob("*_eval.json"):
            try:
                d = json.loads(ej.read_text())
            except Exception:
                continue
            t = d.get("treesim")
            if t is not None:
                out[d.get("experiment", ej.stem.replace("_eval",""))].append(float(t))
    return dict(out)


def _aggregate_walltime_cost(run_dirs: list[Path]) -> dict[str, dict]:
    """{task: {elapsed_mean, cost_mean, in_tok_mean, out_tok_mean}}"""
    by_task = defaultdict(lambda: {"elapsed": [], "cost": [], "in_tok": [], "out_tok": [], "cache_read": []})
    for rd in run_dirs:
        if not rd.exists(): continue
        for task_dir in rd.iterdir():
            if not task_dir.is_dir(): continue
            t = task_dir.name
            e = _elapsed_seconds(task_dir)
            if e is not None:
                by_task[t]["elapsed"].append(e)
            u = _events_last_assistant_usage(task_dir / "events.jsonl")
            if u:
                by_task[t]["cost"].append(u.get("total_cost_usd", 0))
                by_task[t]["in_tok"].append(u.get("input_tokens", 0))
                by_task[t]["out_tok"].append(u.get("output_tokens", 0))
                by_task[t]["cache_read"].append(u.get("cache_read_input_tokens", 0))
    out = {}
    for t, lists in by_task.items():
        out[t] = {
            "elapsed_mean": statistics.mean(lists["elapsed"]) if lists["elapsed"] else None,
            "cost_mean": statistics.mean(lists["cost"]) if lists["cost"] else None,
            "in_tok_mean": statistics.mean(lists["in_tok"]) if lists["in_tok"] else None,
            "out_tok_mean": statistics.mean(lists["out_tok"]) if lists["out_tok"] else None,
            "cache_read_mean": statistics.mean(lists["cache_read"]) if lists["cache_read"] else None,
        }
    return out


def _representative_seed_dirs(run_dirs: list[Path], task: str) -> Path | None:
    """Pick the first existing seed dir for a task — used for trajectory inspection."""
    for rd in run_dirs:
        d = rd / task
        if d.exists() and d.is_dir():
            return d
    return None


def _render_md(out: Path, ctx: dict):
    a = ctx["a_name"]; b = ctx["b_name"]
    lines = []
    lines.append(f"# Ablation: {a}  vs  {b}")
    lines.append("")
    lines.append(f"*Generated by `ablation_analyzer.py` from "
                 f"{len(ctx['a_runs'])} A-seed(s), {len(ctx['b_runs'])} B-seed(s).*")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **mean treesim**: A = {ctx['mean_a']:.4f}, "
                 f"B = {ctx['mean_b']:.4f}, **Δ = {ctx['mean_b']-ctx['mean_a']:+.4f}**")
    if ctx.get("cost_a") is not None and ctx.get("cost_b") is not None:
        lines.append(f"- **mean cost (CC-reported, anthropic-rate)**: "
                     f"A=${ctx['cost_a']:.3f}/task, B=${ctx['cost_b']:.3f}/task")
    if ctx.get("walltime_a") is not None and ctx.get("walltime_b") is not None:
        lines.append(f"- **mean wall**: A={ctx['walltime_a']:.0f}s/task, B={ctx['walltime_b']:.0f}s/task")
    lines.append(f"- **big-swing tasks** (|Δ| ≥ {ctx['threshold']:.2f}): "
                 f"N={len(ctx['big_swing'])}, of which "
                 f"{sum(1 for t in ctx['big_swing'] if ctx['delta'][t] < 0)} are degradations")
    lines.append("")
    lines.append("## Per-task table")
    lines.append("")
    lines.append("| task | A | B | Δ | walltime_A | walltime_B | cost_A | cost_B |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for t in sorted(ctx["all_tasks"], key=lambda x: -abs(ctx["delta"].get(x, 0))):
        a_v = ctx["per_task_a"].get(t)
        b_v = ctx["per_task_b"].get(t)
        d = ctx["delta"].get(t)
        wa = ctx["walltime_a_per"].get(t)
        wb = ctx["walltime_b_per"].get(t)
        ca = ctx["cost_a_per"].get(t)
        cb = ctx["cost_b_per"].get(t)
        a_str = f"{a_v:.3f}" if a_v is not None else "—"
        b_str = f"{b_v:.3f}" if b_v is not None else "—"
        d_str = f"{d:+.3f}" if d is not None else "—"
        wa_s = f"{wa:.0f}s" if wa is not None else "—"
        wb_s = f"{wb:.0f}s" if wb is not None else "—"
        ca_s = f"${ca:.2f}" if ca is not None else "—"
        cb_s = f"${cb:.2f}" if cb is not None else "—"
        lines.append(f"| {t} | {a_str} | {b_str} | {d_str} | {wa_s} | {wb_s} | {ca_s} | {cb_s} |")
    lines.append("")
    if ctx["big_swing"]:
        lines.append("## Big-swing per-task analyses")
        lines.append("")
        for t in sorted(ctx["big_swing"], key=lambda x: ctx["delta"][x]):
            d = ctx["delta"][t]
            lines.append(f"### {t}: Δ = {d:+.3f}")
            lines.append("")
            tu = ctx["analyses"][t]["tool_use"]
            ts = ctx["analyses"][t]["treesim"]
            lines.append("**Tool-use diff** (subagent 0.1):")
            lines.append("")
            lines.append("| tool | A | B | Δ |")
            lines.append("|---|---:|---:|---:|")
            for k, v in tu["tool_delta"].items():
                a_n = tu["a"]["tools"].get(k, 0)
                b_n = tu["b"]["tools"].get(k, 0)
                lines.append(f"| `{k}` | {a_n} | {b_n} | {v:+d} |")
            lines.append("")
            for blt in tu["summary_bullets"]:
                lines.append(f"- {blt}")
            lines.append("")
            if tu["a"]["bash_subs"] or tu["b"]["bash_subs"]:
                lines.append("Bash sub-commands:")
                allk = set(tu["a"]["bash_subs"]) | set(tu["b"]["bash_subs"])
                for k in sorted(allk, key=lambda kk: -(tu["a"]["bash_subs"].get(kk, 0) + tu["b"]["bash_subs"].get(kk, 0))):
                    lines.append(f"  - `{k}`: A={tu['a']['bash_subs'].get(k,0)}, B={tu['b']['bash_subs'].get(k,0)}")
                lines.append("")
            if tu["b"]["rag_queries"]:
                lines.append("RAG queries (B):")
                for q in tu["b"]["rag_queries"][:6]:
                    lines.append(f"  - {q!r}")
                lines.append("")

            lines.append("**Treesim component-wise + xmllint** (subagent 0.2):")
            lines.append("")
            lines.append("| section | A | B | Δ |")
            lines.append("|---|---:|---:|---:|")
            for sec in sorted(set(ts["section_scores_a"]) | set(ts["section_scores_b"])):
                a_v = ts["section_scores_a"].get(sec, 0)
                b_v = ts["section_scores_b"].get(sec, 0)
                lines.append(f"| {sec} | {a_v:.2f} | {b_v:.2f} | {b_v-a_v:+.2f} |")
            lines.append("")
            for blt in ts["summary_bullets"]:
                lines.append(f"- {blt}")
            lines.append("")
            if ts["node_loss_b"]:
                lines.append("Worst-loss B nodes (top 5):")
                for n in ts["node_loss_b"][:5]:
                    lines.append(f"  - `{n['path']}` score={n['score']:.2f} lost_pts={n['lost_points']:.1f}")
                lines.append("")
            if ts["xmllint_b"] and any(x["errors"] for x in ts["xmllint_b"]):
                lines.append("xmllint errors (B):")
                for x in ts["xmllint_b"]:
                    if x["errors"]:
                        lines.append(f"  - `{x['file']}`:")
                        for e in x["errors"][:3]:
                            lines.append(f"    - {e}")
                lines.append("")
        lines.append("")
    lines.append("## Cross-task patterns")
    lines.append("")
    for p in ctx.get("patterns", []):
        lines.append(f"- {p}")
    lines.append("")
    out.write_text("\n".join(lines))


def _cross_task_patterns(big_swing_analyses: dict) -> list[str]:
    """Detect recurring themes across big-swing tasks."""
    patterns = []
    n = len(big_swing_analyses)
    if n == 0:
        return ["(no big-swing tasks)"]
    rag_replaces_glob = 0
    fewer_reads = 0
    more_xmllint_errors = 0
    section_drops = defaultdict(int)
    for t, a in big_swing_analyses.items():
        tu = a["tool_use"]
        a_search = sum(tu["a"]["tools"].get(k, 0) for k in ("Glob","Grep")) + tu["a"]["bash_subs"].get("find",0) + tu["a"]["bash_subs"].get("grep",0) + tu["a"]["bash_subs"].get("rg",0)
        b_search = sum(tu["b"]["tools"].get(k, 0) for k in ("Glob","Grep")) + tu["b"]["bash_subs"].get("find",0) + tu["b"]["bash_subs"].get("grep",0) + tu["b"]["bash_subs"].get("rg",0)
        b_rag = sum(v for k,v in tu["b"]["tools"].items() if k.startswith("mcp__geos-rag__"))
        if a_search > b_search * 2 and b_rag >= 2:
            rag_replaces_glob += 1
        a_reads = tu["a"]["tools"].get("Read", 0); b_reads = tu["b"]["tools"].get("Read", 0)
        if a_reads > b_reads * 2 and a_reads >= 6:
            fewer_reads += 1
        ts = a["treesim"]
        if ts["xmllint_total_errors_b"] > ts["xmllint_total_errors_a"] + 1:
            more_xmllint_errors += 1
        for sec, d in ts["section_loss"].items():
            if d <= -0.3:
                section_drops[sec] += 1
    if rag_replaces_glob >= max(2, n // 2):
        patterns.append(f"**RAG replaces filesystem search**: in {rag_replaces_glob}/{n} big-swing tasks, "
                        f"B used RAG instead of Glob/Grep (smoking-gun mechanism for plugin underperformance).")
    if fewer_reads >= max(2, n // 2):
        patterns.append(f"**Fewer Reads under B**: in {fewer_reads}/{n} big-swing tasks, "
                        f"B made <½ as many Read calls as A.")
    if more_xmllint_errors >= max(2, n // 2):
        patterns.append(f"**B introduces more schema errors**: {more_xmllint_errors}/{n} big-swing tasks "
                        f"have ≥2 more xmllint errors under B.")
    for sec, count in sorted(section_drops.items(), key=lambda kv: -kv[1]):
        if count >= 2:
            patterns.append(f"**Section '{sec}' drops repeatedly under B**: {count}/{n} big-swing tasks "
                            f"lose ≥0.30 in this section.")
    if not patterns:
        patterns.append("(no strong cross-task pattern detected; per-task analyses likely tell different stories)")
    return patterns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cond-a-name", required=True)
    ap.add_argument("--cond-a-agent", required=True, help="e.g., abl_c1_min_primer")
    ap.add_argument("--cond-a-runs", nargs="+", required=True, help="result run dirs (one per seed)")
    ap.add_argument("--cond-b-name", required=True)
    ap.add_argument("--cond-b-agent", required=True)
    ap.add_argument("--cond-b-runs", nargs="+", required=True)
    ap.add_argument("--eval-root", default="data/eval/results",
                    help="default eval root used for both conditions unless overridden")
    ap.add_argument("--cond-a-eval-root", default=None,
                    help="optional eval root specific to condition A")
    ap.add_argument("--cond-b-eval-root", default=None,
                    help="optional eval root specific to condition B")
    ap.add_argument("--gt-dir", default="/data/shared/geophysics_agent_data/data/eval/experiments_gt")
    ap.add_argument("--threshold", type=float, default=0.10)
    ap.add_argument("--focus", choices=["degradations","improvements","both"], default="both")
    ap.add_argument("--max-trajectory-analyses", type=int, default=8)
    ap.add_argument("--schema-path", default=str(DEFAULT_SCHEMA))
    ap.add_argument("--out", required=True, help="path to .md output")
    args = ap.parse_args()

    a_runs = [Path(p) for p in args.cond_a_runs]
    b_runs = [Path(p) for p in args.cond_b_runs]

    a_eval_root = Path(args.cond_a_eval_root or args.eval_root)
    b_eval_root = Path(args.cond_b_eval_root or args.eval_root)
    a_scores = _per_task_treesim(a_runs, a_eval_root, args.cond_a_agent)
    b_scores = _per_task_treesim(b_runs, b_eval_root, args.cond_b_agent)
    all_tasks = sorted(set(a_scores) | set(b_scores))
    per_task_a = {t: statistics.mean(a_scores[t]) for t in a_scores}
    per_task_b = {t: statistics.mean(b_scores[t]) for t in b_scores}
    delta = {t: (per_task_b.get(t) or 0) - (per_task_a.get(t) or 0)
             for t in all_tasks if t in per_task_a and t in per_task_b}
    mean_a = statistics.mean(per_task_a.values()) if per_task_a else 0
    mean_b = statistics.mean(per_task_b.values()) if per_task_b else 0

    # Walltime + cost
    a_meta = _aggregate_walltime_cost(a_runs)
    b_meta = _aggregate_walltime_cost(b_runs)
    walltime_a_per = {t: a_meta[t]["elapsed_mean"] for t in a_meta if a_meta[t]["elapsed_mean"]}
    walltime_b_per = {t: b_meta[t]["elapsed_mean"] for t in b_meta if b_meta[t]["elapsed_mean"]}
    cost_a_per     = {t: a_meta[t]["cost_mean"] for t in a_meta if a_meta[t]["cost_mean"]}
    cost_b_per     = {t: b_meta[t]["cost_mean"] for t in b_meta if b_meta[t]["cost_mean"]}
    walltime_a = statistics.mean(walltime_a_per.values()) if walltime_a_per else None
    walltime_b = statistics.mean(walltime_b_per.values()) if walltime_b_per else None
    cost_a     = statistics.mean(cost_a_per.values()) if cost_a_per else None
    cost_b     = statistics.mean(cost_b_per.values()) if cost_b_per else None

    # Big-swing
    big_swing = []
    for t, d in delta.items():
        if abs(d) < args.threshold:
            continue
        if args.focus == "degradations" and d > 0: continue
        if args.focus == "improvements" and d < 0: continue
        big_swing.append(t)
    big_swing.sort(key=lambda t: delta[t])  # most negative first
    big_swing = big_swing[: args.max_trajectory_analyses]

    # Run subagents 0.1 + 0.2 on each big-swing task
    analyses = {}
    schema = Path(args.schema_path)
    for t in big_swing:
        a_dir = _representative_seed_dirs(a_runs, t)
        b_dir = _representative_seed_dirs(b_runs, t)
        if a_dir is None or b_dir is None:
            print(f"  [warn] skip {t}: no seed dir found", file=sys.stderr)
            continue
        # eval JSONs
        a_eval = a_eval_root / a_runs[0].name / args.cond_a_agent / f"{t}_eval.json"
        b_eval = b_eval_root / b_runs[0].name / args.cond_b_agent / f"{t}_eval.json"
        analyses[t] = {
            "tool_use": diff_tool_use(a_dir, b_dir),
            "treesim":  treesim_analyze(a_dir, b_dir, a_eval, b_eval, schema_path=schema),
            "a_dir": str(a_dir), "b_dir": str(b_dir),
        }

    patterns = _cross_task_patterns(analyses)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    _render_md(out, {
        "a_name": args.cond_a_name, "b_name": args.cond_b_name,
        "a_runs": a_runs, "b_runs": b_runs,
        "all_tasks": all_tasks,
        "per_task_a": per_task_a, "per_task_b": per_task_b, "delta": delta,
        "mean_a": mean_a, "mean_b": mean_b,
        "walltime_a_per": walltime_a_per, "walltime_b_per": walltime_b_per,
        "cost_a_per": cost_a_per, "cost_b_per": cost_b_per,
        "walltime_a": walltime_a, "walltime_b": walltime_b,
        "cost_a": cost_a, "cost_b": cost_b,
        "threshold": args.threshold,
        "big_swing": big_swing,
        "analyses": analyses,
        "patterns": patterns,
    })
    # Sidecar JSON
    json_out = out.with_suffix(".json")
    json_out.write_text(json.dumps({
        "a_name": args.cond_a_name, "b_name": args.cond_b_name,
        "mean_a": mean_a, "mean_b": mean_b,
        "per_task": {t: {"a": per_task_a.get(t), "b": per_task_b.get(t), "delta": delta.get(t)}
                     for t in all_tasks},
        "big_swing": big_swing,
        "patterns": patterns,
    }, indent=2, default=str))
    print(f"Wrote {out}")
    print(f"Wrote {json_out}")


if __name__ == "__main__":
    main()

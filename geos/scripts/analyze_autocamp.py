#!/usr/bin/env python3
"""Analyze the autocamp 2026-05-01 results.

Outputs a markdown table per phase with:
  - quality (treesim mean, std)
  - reliability (per-task seed std, mean abs deviation across seeds)
  - token efficiency (input + output tokens per task)
  - wall-time efficiency (mean elapsed_seconds per task)
  - tool-call distribution (per-tool counts mean per task)
  - file-extension and subtree distribution (Read calls only)

Usage:
  python3 scripts/analyze_autocamp.py [--root <path>] [--out <md-file>]
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_ROOT = Path("/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01")


def load_summary(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def collect_cell(root: Path, agent: str, run_glob_pattern: str) -> dict:
    """Aggregate over all seed runs for one cell.

    Returns dict with:
      task_scores: {task: [seed_scores]}
      task_elapsed: {task: [elapsed]}
      task_tokens: {task: [(input, cache_create, cache_read, output)]}
      task_tool_counts: {task: [{tool: count}]}
      task_reads: {task: [{path: count}]}
      n_seeds_observed: int
    """
    task_scores: dict[str, list[float]] = defaultdict(list)
    task_elapsed: dict[str, list[float]] = defaultdict(list)
    task_tokens: dict[str, list[tuple]] = defaultdict(list)
    task_tool_counts: dict[str, list[dict]] = defaultdict(list)
    task_reads: dict[str, list[dict]] = defaultdict(list)

    seeds_seen: set[str] = set()

    # Find all summary files matching this agent/run pattern
    for summary_path in sorted((root / "_results").rglob("_summary.json")):
        # path: <root>/_results/<run>/<agent>/_summary.json
        parts = summary_path.parts
        try:
            i = parts.index("_results")
        except ValueError:
            continue
        if i + 2 >= len(parts):
            continue
        run = parts[i + 1]
        a = parts[i + 2]
        if a != agent:
            continue
        # check run matches pattern
        if run_glob_pattern and not _matches_pattern(run, run_glob_pattern):
            continue

        d = load_summary(summary_path)
        if not d:
            continue
        seeds_seen.add(run)

        # results have per-task treesim
        for r in d.get("results", []):
            task = r.get("experiment")
            if not task:
                continue
            ts = r.get("treesim")
            if isinstance(ts, (int, float)):
                task_scores[task].append(float(ts))

        # walk per-task: tool_calls.json, status.json (elapsed), events.jsonl (reads, tokens)
        # The actual run dir is parallel: <root>/<subtree>/<agent>/<run>/<task>/
        # subtree is dsv4 or xmodel - we don't know which but we can check both
        for subtree in ("dsv4", "xmodel"):
            run_dir = root / subtree / agent / run
            if run_dir.is_dir():
                for task_dir in run_dir.iterdir():
                    if not task_dir.is_dir():
                        continue
                    task = task_dir.name
                    _accumulate_per_task(
                        task_dir,
                        task,
                        task_elapsed,
                        task_tokens,
                        task_tool_counts,
                        task_reads,
                    )
                break

    return {
        "task_scores": dict(task_scores),
        "task_elapsed": dict(task_elapsed),
        "task_tokens": dict(task_tokens),
        "task_tool_counts": dict(task_tool_counts),
        "task_reads": dict(task_reads),
        "n_seeds_observed": len(seeds_seen),
        "seeds": sorted(seeds_seen),
    }


def _matches_pattern(run: str, pat: str) -> bool:
    # very simple glob: * and exact prefix
    if pat.endswith("*"):
        return run.startswith(pat[:-1])
    return run == pat


def _accumulate_per_task(
    task_dir: Path,
    task: str,
    task_elapsed: dict,
    task_tokens: dict,
    task_tool_counts: dict,
    task_reads: dict,
):
    # status.json: elapsed_seconds
    status_p = task_dir / "status.json"
    if status_p.exists():
        try:
            s = json.loads(status_p.read_text())
            es = s.get("elapsed_seconds")
            if isinstance(es, (int, float)):
                task_elapsed[task].append(float(es))
        except Exception:
            pass

    # tool_calls.json: per_tool_counts
    tc_p = task_dir / "tool_calls.json"
    if tc_p.exists():
        try:
            tc = json.loads(tc_p.read_text())
            ptc = tc.get("per_tool_counts", {})
            task_tool_counts[task].append(dict(ptc))
        except Exception:
            pass

    # events.jsonl: tokens + read paths
    ev_p = task_dir / "events.jsonl"
    if ev_p.exists():
        input_tokens = 0
        cache_create = 0
        cache_read = 0
        output_tokens = 0
        reads: dict[str, int] = {}
        try:
            for line in ev_p.open():
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("type") != "assistant":
                    continue
                msg = e.get("message", {}) or {}
                u = msg.get("usage", {}) or {}
                input_tokens += int(u.get("input_tokens", 0) or 0)
                cache_create += int(u.get("cache_creation_input_tokens", 0) or 0)
                cache_read += int(u.get("cache_read_input_tokens", 0) or 0)
                output_tokens += int(u.get("output_tokens", 0) or 0)
                content = msg.get("content", [])
                if not isinstance(content, list):
                    continue
                for c in content:
                    if (
                        isinstance(c, dict)
                        and c.get("type") == "tool_use"
                        and c.get("name") == "Read"
                    ):
                        fp = (c.get("input") or {}).get("file_path", "")
                        if fp:
                            reads[fp] = reads.get(fp, 0) + 1
        except Exception:
            pass
        task_tokens[task].append(
            (input_tokens, cache_create, cache_read, output_tokens)
        )
        task_reads[task].append(reads)


def aggregate_cell(cell: dict) -> dict:
    """Compute per-cell aggregate metrics."""
    task_scores = cell["task_scores"]
    task_elapsed = cell["task_elapsed"]
    task_tokens = cell["task_tokens"]
    task_tool_counts = cell["task_tool_counts"]
    task_reads = cell["task_reads"]

    # quality
    seed_means = []
    if task_scores:
        # for each seed (we don't know which seed each entry is, but if all seeds
        # have all tasks the by-seed-mean would be derivable; we use the simple
        # task-mean across all observations)
        # But for a per-seed aggregate, we group by index:
        all_lists = list(task_scores.values())
        n_seeds = max((len(v) for v in all_lists), default=0)
        for s in range(n_seeds):
            seed_vals = [v[s] for v in all_lists if len(v) > s]
            if seed_vals:
                seed_means.append(sum(seed_vals) / len(seed_vals))
    quality_mean = sum(seed_means) / len(seed_means) if seed_means else None
    quality_std = (
        statistics.pstdev(seed_means) if len(seed_means) > 1 else 0.0
    ) if seed_means else None

    # reliability — per-task seed std averaged over tasks
    per_task_stds = []
    for task, vals in task_scores.items():
        if len(vals) >= 2:
            per_task_stds.append(statistics.pstdev(vals))
    reliability = (
        sum(per_task_stds) / len(per_task_stds) if per_task_stds else 0.0
    )

    # token efficiency — total tokens per task (input incl cached + output)
    all_tokens = []
    for vals in task_tokens.values():
        for tup in vals:
            inp, cc, cr, out = tup
            all_tokens.append({"input_total": inp, "cache_create": cc, "cache_read": cr, "output": out})
    total_input = sum(t["input_total"] + t["cache_read"] for t in all_tokens) if all_tokens else 0
    total_output = sum(t["output"] for t in all_tokens) if all_tokens else 0
    n_runs = len(all_tokens)
    avg_in_per_task = total_input / n_runs if n_runs else 0
    avg_out_per_task = total_output / n_runs if n_runs else 0

    # wall time
    all_elapsed = [e for vals in task_elapsed.values() for e in vals]
    avg_elapsed = sum(all_elapsed) / len(all_elapsed) if all_elapsed else 0

    # tool-call distribution
    tool_totals: Counter = Counter()
    n_task_runs = 0
    for vals in task_tool_counts.values():
        for ptc in vals:
            n_task_runs += 1
            for k, v in ptc.items():
                tool_totals[k] += v
    tool_pct = {
        k: 100 * v / sum(tool_totals.values())
        for k, v in tool_totals.items()
    } if tool_totals else {}

    # file extension distribution (over Read calls)
    ext_counts: Counter = Counter()
    subtree_counts: Counter = Counter()
    for vals in task_reads.values():
        for read_dict in vals:
            for fp, n in read_dict.items():
                fn = fp.rsplit("/", 1)[-1] if "/" in fp else fp
                ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else "(no_ext)"
                ext_counts[ext] += n
                # Subtree: top-3 path segments
                parts = fp.lstrip("/").split("/")
                if len(parts) >= 3:
                    subtree_counts["/" + "/".join(parts[:3])] += n
                elif len(parts) >= 2:
                    subtree_counts["/" + "/".join(parts[:2])] += n
                elif parts:
                    subtree_counts["/" + parts[0]] += n

    return {
        "n_seeds": cell["n_seeds_observed"],
        "n_task_runs": n_task_runs,
        "quality_mean": quality_mean,
        "quality_std": quality_std,
        "reliability_avg_pertask_std": reliability,
        "avg_input_tokens_per_task": avg_in_per_task,
        "avg_output_tokens_per_task": avg_out_per_task,
        "avg_elapsed_seconds_per_task": avg_elapsed,
        "tool_call_totals": dict(tool_totals.most_common(20)),
        "tool_call_pct": {k: round(v, 1) for k, v in sorted(tool_pct.items(), key=lambda x: -x[1])[:10]},
        "ext_counts": dict(ext_counts.most_common(15)),
        "subtree_counts": dict(subtree_counts.most_common(15)),
        "seeds_seen": cell["seeds"],
    }


def render_markdown(results: dict, root: Path) -> str:
    lines = []
    lines.append(f"# Autocamp 2026-05-01 — Analysis")
    lines.append("")
    lines.append(f"Source root: `{root}`")
    lines.append("")

    # Main-effects table (Phase 2)
    if any(c.startswith("autocamp_F") for c in results):
        lines.append("## Phase 2 main effects (Resolution-IV factorial)")
        lines.append("")
        effects = compute_main_effects(results)
        lines.append("| factor | mean Δ |")
        lines.append("|---|---:|")
        for name, eff in effects.items():
            if eff is None:
                lines.append(f"| {name} | — |")
            else:
                lines.append(f"| {name} | {eff:+.3f} |")
        lines.append("")
        lines.append("(positive = factor on improves quality)")
        lines.append("")

    # Group cells by phase
    phase1_cells = [c for c in results if c.startswith("autocamp_p_")]
    phase2_cells = [c for c in results if c.startswith("autocamp_F") or c == "autocamp_SE"]
    phase3_cells = [c for c in results if c.startswith("autocamp_xmodel_")]

    for phase_name, cells in (
        ("Phase 1 — primer screen", phase1_cells),
        ("Phase 2 — DSv4 fractional factorial + SE", phase2_cells),
        ("Phase 3 — cross-model", phase3_cells),
    ):
        if not cells:
            continue
        lines.append(f"## {phase_name}")
        lines.append("")
        lines.append("| cell | seeds | quality (mean) | quality σ | reliability (avg per-task σ) | avg input tok | avg output tok | avg wall (s) |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for cell in sorted(cells):
            a = results[cell]
            qm = f"{a['quality_mean']:.3f}" if a['quality_mean'] is not None else "—"
            qs = f"{a['quality_std']:.3f}" if a['quality_std'] is not None else "—"
            lines.append(
                f"| {cell} | {a['n_seeds']} | {qm} | {qs} | {a['reliability_avg_pertask_std']:.3f} | "
                f"{a['avg_input_tokens_per_task']:.0f} | {a['avg_output_tokens_per_task']:.0f} | "
                f"{a['avg_elapsed_seconds_per_task']:.0f} |"
            )
        lines.append("")

        # tool call distribution
        lines.append("### Tool-call distribution (% of tool calls)")
        lines.append("")
        all_tools = set()
        for cell in cells:
            all_tools.update(results[cell]["tool_call_pct"].keys())
        cols = sorted(all_tools)
        lines.append("| cell | " + " | ".join(cols) + " |")
        lines.append("|---" * (len(cols) + 1) + "|")
        for cell in sorted(cells):
            row = [cell]
            for c in cols:
                v = results[cell]["tool_call_pct"].get(c, 0)
                row.append(f"{v:.0f}%" if v else "—")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

        # file extension distribution
        lines.append("### File-extension distribution (Read calls)")
        lines.append("")
        all_exts = set()
        for cell in cells:
            all_exts.update(results[cell]["ext_counts"].keys())
        cols = sorted(all_exts)[:8]
        lines.append("| cell | " + " | ".join(f".{c}" for c in cols) + " |")
        lines.append("|---" * (len(cols) + 1) + "|")
        for cell in sorted(cells):
            row = [cell]
            for ext in cols:
                v = results[cell]["ext_counts"].get(ext, 0)
                row.append(str(v) if v else "—")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

        # subtree distribution
        lines.append("### Subtree distribution (top file-read prefixes)")
        lines.append("")
        for cell in sorted(cells):
            lines.append(f"**{cell}** (n_seeds={results[cell]['n_seeds']}):")
            for tree, n in results[cell]["subtree_counts"].items():
                lines.append(f"  - `{tree}`: {n}")
            lines.append("")

    return "\n".join(lines)


CELLS = [
    "autocamp_p_contract", "autocamp_p_method",
    "autocamp_F0", "autocamp_F1", "autocamp_F2", "autocamp_F3",
    "autocamp_F4", "autocamp_F5", "autocamp_F6", "autocamp_F7",
    "autocamp_SE",
    "autocamp_xmodel_baseline", "autocamp_xmodel_best",
]

# 4-bit factor labels for F-cells (R, S, X, M)
F_FACTORS = {
    "autocamp_F0": (0, 0, 0, 0),
    "autocamp_F1": (1, 0, 0, 1),
    "autocamp_F2": (0, 1, 0, 1),
    "autocamp_F3": (1, 1, 0, 0),
    "autocamp_F4": (0, 0, 1, 1),
    "autocamp_F5": (1, 0, 1, 0),
    "autocamp_F6": (0, 1, 1, 0),
    "autocamp_F7": (1, 1, 1, 1),
}


def compute_main_effects(results: dict) -> dict:
    """Estimate main effects of R, S, X, M from the F0..F7 cells.

    Effect = mean(quality_mean over cells with factor=1)
           - mean(quality_mean over cells with factor=0)
    """
    effects = {}
    for i, name in enumerate(["R (RAG)", "S (SR-hook)", "X (xmllint MCP)", "M (memory)"]):
        plus = []
        minus = []
        for cell, levels in F_FACTORS.items():
            if cell not in results:
                continue
            qm = results[cell]["quality_mean"]
            if qm is None:
                continue
            if levels[i] == 1:
                plus.append(qm)
            else:
                minus.append(qm)
        if plus and minus:
            effects[name] = sum(plus)/len(plus) - sum(minus)/len(minus)
        else:
            effects[name] = None
    return effects


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--out", type=Path, default=Path("/home/matt/sci/repo3/docs/2026-05-02_autocamp_metrics.md"))
    args = p.parse_args()

    root = args.root
    results = {}
    for cell in CELLS:
        cell_data = collect_cell(root, cell, "*")
        if cell_data["n_seeds_observed"] == 0:
            continue
        results[cell] = aggregate_cell(cell_data)
        print(
            f"  {cell}: n_seeds={results[cell]['n_seeds']} "
            f"q={results[cell]['quality_mean']} "
            f"σ={results[cell]['quality_std']}"
        )

    md = render_markdown(results, root)
    args.out.write_text(md)
    print(f"\nWrote: {args.out} ({len(md)} chars)")


if __name__ == "__main__":
    main()

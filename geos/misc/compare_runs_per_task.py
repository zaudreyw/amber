#!/usr/bin/env python3
"""Per-task run-vs-run comparison.

Pulls scored TreeSim AND operational metrics (elapsed, tool counts, tokens,
OpenRouter cost, agent status, XML present) for each task across any number
of runs, and emits a single Markdown table sorted by task name.

Use for: sanity-checking that runs on the "same" tasks score consistently;
finding which tasks explain an aggregate delta between two runs; collaborator
hand-off.

Usage:
  python misc/compare_runs_per_task.py \\
      --label E17_plug_mm_v2 \\
          --results /data/shared/.../results/plug_mm_v2_seed2/claude_code_repo3_plugin \\
          --raw /home/matt/.../data/eval/claude_code_repo3_plugin/plug_mm_v2_seed2 \\
      --label E18_gmem_mm_v2 \\
          --results /data/shared/.../results/gmemsilent_mm_v2/claude_code_repo3_plugin_gmemsilent \\
          --raw /home/matt/.../data/eval/claude_code_repo3_plugin_gmemsilent/gmemsilent_mm_v2 \\
      --out misc/e17_vs_e18_per_task.md

You can pass --label / --results / --raw triples any number of times.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def load_run(label: str, results_dir: Path, raw_dir: Path | None) -> dict[str, dict]:
    """For one run, return {task_name: {treesim, status, elapsed, ...}}."""
    out: dict[str, dict] = {}
    if results_dir and results_dir.exists():
        for f in sorted(results_dir.glob("*_eval.json")):
            if f.name.startswith("_"):
                continue
            try:
                r = json.loads(f.read_text())
            except Exception:
                continue
            name = r.get("experiment") or f.name.removesuffix("_eval.json")
            out.setdefault(name, {})["treesim"] = r.get("treesim")
            out[name]["score_status"] = r.get("status", "?")
    # Enrich with raw task-dir metadata (status.json)
    if raw_dir and raw_dir.exists():
        for td in raw_dir.iterdir():
            if not td.is_dir():
                continue
            sf = td / "status.json"
            if not sf.exists():
                continue
            try:
                s = json.loads(sf.read_text())
            except Exception:
                continue
            e = out.setdefault(td.name, {})
            e["agent_status"] = s.get("status")
            e["elapsed_s"] = s.get("elapsed_seconds")
            e["tool_calls"] = s.get("total_tool_calls")
            rag = s.get("rag_tool_counts") or {}
            e["rag_calls"] = sum(rag.values()) if rag else 0
            mem = {k: v for k, v in (s.get("per_tool_counts") or {}).items() if "memory" in k.lower()}
            e["mem_calls"] = sum(mem.values())
            cost = s.get("openrouter_cost_usd")
            if cost is None:
                cost = s.get("cc_cost_usd")
            e["cost_usd"] = float(cost) if cost is not None else None
            e["xml_written"] = s.get("workspace_inputs_present")
    return out


def fmt_score(s):
    if s is None:
        return " - "
    return f"{s:.3f}"


def fmt_num(n, width=4):
    if n is None:
        return " - "
    if isinstance(n, float):
        return f"{n:.0f}"
    return str(n)


def fmt_money(x):
    if x is None:
        return " - "
    return f"${x:.3f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", action="append", required=True,
                    help="Short label for a run (repeatable). Each --label must be followed by --results and optionally --raw.")
    ap.add_argument("--results", action="append", type=Path, required=True,
                    help="Directory containing <task>_eval.json for this run.")
    ap.add_argument("--raw", action="append", type=Path, default=None,
                    help="Directory containing per-task subdirs with status.json (agent-level metadata).")
    ap.add_argument("--out", type=Path, default=None, help="Write Markdown to this file; otherwise print to stdout.")
    ap.add_argument("--sort-by", choices=("name", "delta", "first_score"), default="name",
                    help="Sort order: task name, abs delta vs first run, or first-run score.")
    ap.add_argument("--compact", action="store_true",
                    help="Show only task + per-run treesim (no elapsed/tools/cost/status columns).")
    args = ap.parse_args()

    if len(args.label) != len(args.results):
        ap.error("--label and --results must be given the same number of times")
    # Fill in missing --raw with Nones aligned to other lists
    raw_list = args.raw or []
    while len(raw_list) < len(args.label):
        raw_list.append(None)

    runs = []
    for lbl, res, raw in zip(args.label, args.results, raw_list):
        runs.append((lbl, load_run(lbl, res, raw)))

    # All tasks seen in any run
    all_tasks = sorted({t for _, d in runs for t in d})

    # Build rows
    def row_sort_key(t):
        if args.sort_by == "name":
            return t
        elif args.sort_by == "first_score":
            s = runs[0][1].get(t, {}).get("treesim")
            return (-1 if s is None else -s, t)
        elif args.sort_by == "delta":
            s0 = runs[0][1].get(t, {}).get("treesim")
            if len(runs) < 2 or s0 is None:
                return (0, t)
            deltas = [abs((r[1].get(t, {}).get("treesim") or s0) - s0) for r in runs[1:]]
            return (-max(deltas) if deltas else 0, t)
        return t
    all_tasks.sort(key=row_sort_key)

    # Markdown table
    lines = []
    lines.append("# Per-task run comparison")
    lines.append("")
    lines.append("Runs compared:")
    for lbl, _ in runs:
        lines.append(f"- **{lbl}**")
    lines.append("")

    if args.compact:
        # Compact: task | treesim per run | delta vs first run
        header = ["Task"] + [lbl for lbl, _ in runs]
        if len(runs) >= 2:
            for lbl, _ in runs[1:]:
                header.append(f"Δ({lbl}-{runs[0][0]})")
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join("---" for _ in header) + "|")
        for t in all_tasks:
            cells = [t]
            scores = [r[1].get(t, {}).get("treesim") for r in runs]
            for s in scores:
                cells.append(fmt_score(s))
            if len(runs) >= 2:
                base = scores[0]
                for s in scores[1:]:
                    if base is None or s is None:
                        cells.append(" - ")
                    else:
                        d = s - base
                        cells.append(f"{d:+.3f}")
            lines.append("| " + " | ".join(cells) + " |")
    else:
        # Full: task + for each run: treesim / status / elapsed / tools / rag / mem / $
        header = ["Task"]
        for lbl, _ in runs:
            header += [f"{lbl}_ts", f"{lbl}_status", f"{lbl}_elapsed", f"{lbl}_tools", f"{lbl}_rag", f"{lbl}_mem", f"{lbl}_$"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join("---" for _ in header) + "|")
        for t in all_tasks:
            cells = [t]
            for _, d in runs:
                e = d.get(t, {})
                cells.extend([
                    fmt_score(e.get("treesim")),
                    e.get("agent_status") or "-",
                    fmt_num(e.get("elapsed_s")),
                    fmt_num(e.get("tool_calls")),
                    fmt_num(e.get("rag_calls")),
                    fmt_num(e.get("mem_calls")),
                    fmt_money(e.get("cost_usd")),
                ])
            lines.append("| " + " | ".join(cells) + " |")

    # Summary rows at the bottom: means, counts, totals
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else None
    def safesum(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) if xs else None

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | {' | '.join(lbl for lbl, _ in runs)} |")
    lines.append(f"|---|{'|'.join('---' for _ in runs)}|")
    row_scored = ["Tasks scored (treesim present)"]
    row_mean = ["Mean TreeSim (scored only)"]
    row_mean_all = ["Mean TreeSim (failures=0, over all tasks below)"]
    row_total_cost = ["Total cost (sum openrouter_cost_usd)"]
    row_total_wall = ["Total per-task elapsed (sum elapsed_s)"]
    n_tasks_seen = len(all_tasks)
    for lbl, d in runs:
        scored = [e.get("treesim") for e in d.values() if e.get("treesim") is not None]
        all_scores = [d.get(t, {}).get("treesim") or 0 for t in all_tasks]
        row_scored.append(f"{len(scored)}/{n_tasks_seen}")
        row_mean.append(f"{mean(scored):.3f}" if scored else "-")
        row_mean_all.append(f"{mean(all_scores):.3f}" if all_scores else "-")
        costs = [e.get("cost_usd") for e in d.values() if e.get("cost_usd") is not None]
        walls = [e.get("elapsed_s") for e in d.values() if e.get("elapsed_s") is not None]
        tot_c = safesum(costs)
        tot_w = safesum(walls)
        row_total_cost.append(fmt_money(tot_c) if tot_c else "-")
        row_total_wall.append(f"{tot_w:.0f}s" if tot_w else "-")
    for r in (row_scored, row_mean, row_mean_all, row_total_cost, row_total_wall):
        lines.append("| " + " | ".join(r) + " |")

    # Paired delta table if exactly 2 runs
    if len(runs) == 2:
        (l0, d0), (l1, d1) = runs
        paired = [(t, d0[t]["treesim"], d1[t]["treesim"])
                  for t in all_tasks
                  if d0.get(t, {}).get("treesim") is not None
                  and d1.get(t, {}).get("treesim") is not None]
        wins_l0 = sum(1 for _, a, b in paired if a > b)
        wins_l1 = sum(1 for _, a, b in paired if b > a)
        ties = sum(1 for _, a, b in paired if a == b)
        deltas = [b - a for _, a, b in paired]
        lines.append("")
        lines.append(f"## Paired ({len(paired)} tasks scored in both)")
        lines.append("")
        lines.append(f"- Mean delta ({l1} - {l0}): **{mean(deltas):+.3f}**")
        lines.append(f"- Wins {l0}: {wins_l0}, Wins {l1}: {wins_l1}, Ties: {ties}")

    text = "\n".join(lines) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"Wrote {args.out}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()

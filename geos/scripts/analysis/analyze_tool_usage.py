#!/usr/bin/env python3
"""
analyze_tool_usage.py
=====================

Aggregate per-tool call counts across all completed agent runs in
``data/eval/<agent_key>/<run_name>/<task_name>/``.

Two important nuances:
  1. ``status.json`` / ``tool_calls.json`` count *attempted* tool uses, including
     calls to MCP tools that did not exist in that runtime (e.g. vanilla Claude
     Code invoking ``mcp__geos-rag__search_navigator`` -> "No such tool
     available"). We re-derive counts directly from ``events.jsonl`` and split
     into ``attempted`` (the assistant emitted the tool_use block) vs
     ``succeeded`` (the matching tool_result block has ``is_error != True``).
  2. We flag any disagreement between the events-derived attempted counts and
     ``per_tool_counts`` from ``status.json``, since the user has seen those
     drift before.

Outputs (default --out-dir scripts/analysis/out/tool_usage/):
  - tool_usage_per_run.csv     : (agent, run, task, tool_name, attempted, succeeded, errored)
  - tool_usage_by_agent.csv    : pivoted, summed across runs of an agent_key, with mean/task
  - tool_usage_summary.md      : narrative

Usage:
  python3 scripts/analysis/analyze_tool_usage.py
  python3 scripts/analysis/analyze_tool_usage.py --agent-keys claude_code_no_plugin
  python3 scripts/analysis/analyze_tool_usage.py --max-tasks-per-run 3
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import pandas as pd

EVAL_ROOT_DEFAULT = Path("/home/matt/sci/repo3/data/eval")
DEFAULT_OUT = Path("/home/matt/sci/repo3/scripts/analysis/out/tool_usage")


def iter_task_dirs(eval_root: Path, agent_keys: list[str] | None) -> Iterator[Path]:
    if agent_keys:
        agent_dirs = [eval_root / k for k in agent_keys]
    else:
        agent_dirs = [p for p in eval_root.iterdir() if p.is_dir()]
    for agent_dir in agent_dirs:
        if not agent_dir.exists():
            print(f"[warn] missing agent_key dir: {agent_dir}", file=sys.stderr)
            continue
        for events in agent_dir.glob("*/*/events.jsonl"):
            yield events.parent


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def extract_tool_counts(events_path: Path) -> dict:
    """Walk events.jsonl, count attempted tool uses + which had errored results.

    Returns:
        {
          'attempted': Counter[name],
          'errored':   Counter[name],
          'tool_use_to_name': dict[id, name]   (debug)
        }
    """
    attempted: Counter = Counter()
    errored: Counter = Counter()
    use_id_to_name: dict[str, str] = {}

    with events_path.open() as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = e.get("type")
            if t == "assistant":
                content = e.get("message", {}).get("content", []) or []
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        name = b.get("name") or "<unknown>"
                        attempted[name] += 1
                        if b.get("id"):
                            use_id_to_name[b["id"]] = name
            elif t == "user":
                content = e.get("message", {}).get("content", []) or []
                if not isinstance(content, list):
                    continue
                for b in content:
                    if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                        continue
                    if not b.get("is_error"):
                        continue
                    name = use_id_to_name.get(b.get("tool_use_id", ""), "<unknown>")
                    errored[name] += 1
    return {
        "attempted": attempted,
        "errored": errored,
        "use_id_to_name": use_id_to_name,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval-root", type=Path, default=EVAL_ROOT_DEFAULT)
    ap.add_argument("--agent-keys", type=str, default=None)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--max-tasks-per-run", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    keys = [k.strip() for k in args.agent_keys.split(",")] if args.agent_keys else None
    args.out_dir.mkdir(parents=True, exist_ok=True)

    per_run_rows: list[dict] = []
    discrepancy_rows: list[dict] = []
    seen_per_run: dict[tuple[str, str], int] = defaultdict(int)
    n_tasks = 0
    n_skipped = 0

    for task_dir in iter_task_dirs(args.eval_root, keys):
        meta = load_json(task_dir / "eval_metadata.json")
        status = load_json(task_dir / "status.json")
        agent = meta.get("agent") or task_dir.parent.parent.name
        run_name = meta.get("run_name") or task_dir.parent.name
        task_name = meta.get("task") or task_dir.name
        model = meta.get("claude_model") or ""
        plugin_enabled = meta.get("plugin_enabled")
        process_status = status.get("process_status") or "unknown"
        elapsed_seconds = status.get("elapsed_seconds")

        if args.max_tasks_per_run:
            key = (agent, run_name)
            if seen_per_run[key] >= args.max_tasks_per_run:
                continue
            seen_per_run[key] += 1

        events_path = task_dir / "events.jsonl"
        if not events_path.exists():
            n_skipped += 1
            continue
        try:
            agg = extract_tool_counts(events_path)
        except Exception as ex:
            print(f"[warn] failed to parse {events_path}: {ex}", file=sys.stderr)
            n_skipped += 1
            continue
        n_tasks += 1

        attempted = agg["attempted"]
        errored = agg["errored"]

        # Per-tool rows
        for name in sorted(set(attempted) | set(errored)):
            att = int(attempted.get(name, 0))
            err = int(errored.get(name, 0))
            per_run_rows.append({
                "agent": agent,
                "run_name": run_name,
                "task": task_name,
                "model": model,
                "plugin_enabled": plugin_enabled,
                "process_status": process_status,
                "elapsed_seconds": elapsed_seconds,
                "tool_name": name,
                "attempted_count": att,
                "errored_count": err,
                "succeeded_count": max(0, att - err),
            })

        # Discrepancy check vs status.json per_tool_counts
        recorded = status.get("per_tool_counts") or {}
        for name in set(attempted) | set(recorded):
            r = int(recorded.get(name, 0))
            a = int(attempted.get(name, 0))
            if r != a:
                discrepancy_rows.append({
                    "agent": agent, "run_name": run_name, "task": task_name,
                    "tool_name": name, "events_attempted": a, "status_recorded": r,
                    "delta": a - r,
                })

        if not args.quiet and n_tasks % 50 == 0:
            print(f"  ... processed {n_tasks} tasks", file=sys.stderr)

    if not per_run_rows:
        print(f"[err] no rows produced (n_tasks={n_tasks}, n_skipped={n_skipped})",
              file=sys.stderr)
        return 2

    df = pd.DataFrame(per_run_rows)

    # ---- by-agent pivot -----------------------------------------------------
    # Sum across all (run, task) for each (agent, tool_name)
    by_agent_long = (df.groupby(["agent", "tool_name"], dropna=False)
                       .agg(attempted=("attempted_count", "sum"),
                            succeeded=("succeeded_count", "sum"),
                            errored=("errored_count", "sum"),
                            n_tasks=("task", "nunique"))
                       .reset_index())
    by_agent_long["attempted_per_task"] = (by_agent_long["attempted"]
                                           / by_agent_long["n_tasks"]).round(2)
    by_agent_long["error_rate"] = (
        by_agent_long["errored"] / by_agent_long["attempted"].clip(lower=1)
    ).round(3)

    # Pivot (attempted) for at-a-glance view
    pivot_attempted = (df.groupby(["agent", "tool_name"])
                         ["attempted_count"].sum().unstack(fill_value=0))
    pivot_succeeded = (df.groupby(["agent", "tool_name"])
                         ["succeeded_count"].sum().unstack(fill_value=0))

    # Save outputs
    per_run_path = args.out_dir / "tool_usage_per_run.csv"
    by_agent_path = args.out_dir / "tool_usage_by_agent.csv"
    pivot_att_path = args.out_dir / "tool_usage_by_agent_pivot_attempted.csv"
    pivot_suc_path = args.out_dir / "tool_usage_by_agent_pivot_succeeded.csv"
    discrepancy_path = args.out_dir / "tool_usage_discrepancies.csv"

    df.to_csv(per_run_path, index=False)
    by_agent_long.to_csv(by_agent_path, index=False)
    pivot_attempted.to_csv(pivot_att_path)
    pivot_succeeded.to_csv(pivot_suc_path)
    pd.DataFrame(discrepancy_rows).to_csv(discrepancy_path, index=False)

    # ---- markdown summary ---------------------------------------------------
    md: list[str] = []
    md.append(f"# Tool-usage summary ({n_tasks} tasks)\n\n")
    md.append(f"- Eval root: `{args.eval_root}`\n")
    md.append(f"- Skipped (no events.jsonl / parse error): {n_skipped}\n")
    md.append(f"- Agent keys: {', '.join(sorted(df['agent'].unique()))}\n\n")

    # Total tool calls per agent
    totals = (df.groupby("agent")
                .agg(n_tasks=("task", "nunique"),
                     total_attempted=("attempted_count", "sum"),
                     total_succeeded=("succeeded_count", "sum"),
                     total_errored=("errored_count", "sum"))
                .reset_index())
    totals["mean_attempted_per_task"] = (totals["total_attempted"]
                                          / totals["n_tasks"]).round(2)
    totals["mean_succeeded_per_task"] = (totals["total_succeeded"]
                                          / totals["n_tasks"]).round(2)
    totals["overall_error_rate"] = (totals["total_errored"]
                                     / totals["total_attempted"].clip(lower=1)).round(3)
    totals = totals.sort_values("total_attempted", ascending=False)

    md.append("## Total tool calls per agent\n\n")
    md.append("| agent | n_tasks | attempted | succeeded | errored | mean_att/task | err_rate |\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|\n")
    for _, r in totals.iterrows():
        md.append(f"| {r['agent']} | {int(r['n_tasks'])} | {int(r['total_attempted'])} | "
                  f"{int(r['total_succeeded'])} | {int(r['total_errored'])} | "
                  f"{r['mean_attempted_per_task']} | {r['overall_error_rate']} |\n")
    md.append("\n")

    # Most-used tools globally
    md.append("## Most-used tools (across all agents)\n\n")
    g = (df.groupby("tool_name")
           .agg(attempted=("attempted_count", "sum"),
                succeeded=("succeeded_count", "sum"),
                errored=("errored_count", "sum"),
                n_tasks=("task", "nunique"))
           .reset_index()
           .sort_values("attempted", ascending=False))
    g["error_rate"] = (g["errored"] / g["attempted"].clip(lower=1)).round(3)
    md.append("| tool_name | attempted | succeeded | errored | n_tasks | error_rate |\n")
    md.append("|---|---:|---:|---:|---:|---:|\n")
    for _, r in g.iterrows():
        md.append(f"| `{r['tool_name']}` | {int(r['attempted'])} | "
                  f"{int(r['succeeded'])} | {int(r['errored'])} | "
                  f"{int(r['n_tasks'])} | {r['error_rate']} |\n")
    md.append("\n")

    # Tools with high error rates (likely "No such tool" or schema issues)
    md.append("## Tools with elevated error rates (>=10% error, >=10 attempts)\n\n")
    flagged = g[(g["error_rate"] >= 0.10) & (g["attempted"] >= 10)]
    if flagged.empty:
        md.append("(none)\n\n")
    else:
        md.append("| tool_name | attempted | errored | error_rate |\n|---|---:|---:|---:|\n")
        for _, r in flagged.iterrows():
            md.append(f"| `{r['tool_name']}` | {int(r['attempted'])} | "
                      f"{int(r['errored'])} | {r['error_rate']} |\n")
        md.append("\n")

    # Plug vs no-plug differences (uses agent name heuristic)
    md.append("## Plug vs no-plug averages\n\n")
    df["plug_bucket"] = df["agent"].apply(
        lambda a: "no_plugin" if "no_plugin" in a or "noplug" in a else
                  ("plugin" if "plugin" in a else "other")
    )
    bucket = (df.groupby(["plug_bucket", "tool_name"])
                .agg(attempted=("attempted_count", "sum"),
                     n_tasks=("task", "nunique"))
                .reset_index())
    bucket["mean_per_task"] = (bucket["attempted"] / bucket["n_tasks"]).round(2)
    md.append("| plug_bucket | tool_name | attempted | n_tasks | mean/task |\n"
              "|---|---|---:|---:|---:|\n")
    top_tools = (bucket.groupby("tool_name")["attempted"].sum()
                 .sort_values(ascending=False).head(12).index)
    for tn in top_tools:
        for _, r in bucket[bucket["tool_name"] == tn].iterrows():
            md.append(f"| {r['plug_bucket']} | `{r['tool_name']}` | "
                      f"{int(r['attempted'])} | {int(r['n_tasks'])} | "
                      f"{r['mean_per_task']} |\n")
    md.append("\n")

    # Discrepancies vs status.json
    md.append("## Discrepancies (events.jsonl attempted vs status.json per_tool_counts)\n\n")
    if discrepancy_rows:
        ddf = pd.DataFrame(discrepancy_rows)
        agg_d = (ddf.groupby(["agent", "tool_name"])
                    .agg(n_disagreements=("delta", "size"),
                         total_delta=("delta", "sum"))
                    .reset_index()
                    .sort_values("n_disagreements", ascending=False)
                    .head(20))
        md.append(f"{len(discrepancy_rows)} (agent,run,task,tool) rows disagree. "
                  "Top mismatches by frequency:\n\n")
        md.append("| agent | tool_name | n_disagreements | total_delta |\n|---|---|---:|---:|\n")
        for _, r in agg_d.iterrows():
            md.append(f"| {r['agent']} | `{r['tool_name']}` | "
                      f"{int(r['n_disagreements'])} | {int(r['total_delta'])} |\n")
        md.append(f"\nFull list: `{discrepancy_path}`\n\n")
    else:
        md.append("None.\n\n")

    md.append("## Output files\n\n")
    md.append(f"- `{per_run_path}`\n")
    md.append(f"- `{by_agent_path}`\n")
    md.append(f"- `{pivot_att_path}`\n")
    md.append(f"- `{pivot_suc_path}`\n")
    md.append(f"- `{discrepancy_path}`\n")

    md_path = args.out_dir / "tool_usage_summary.md"
    md_path.write_text("".join(md))

    print(f"wrote: {per_run_path}")
    print(f"wrote: {by_agent_path}")
    print(f"wrote: {pivot_att_path}")
    print(f"wrote: {pivot_suc_path}")
    print(f"wrote: {discrepancy_path}")
    print(f"wrote: {md_path}")
    print(f"n_tasks_processed={n_tasks}  n_skipped={n_skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

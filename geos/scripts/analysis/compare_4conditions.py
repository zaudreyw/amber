#!/usr/bin/env python3
"""4-condition comparison: CC / +RAG / +RAG+hook / +RAG+hook+memory.

Filters the file_access and tool_usage outputs to canonical minimax m2.7
seeds on the 17-task test set, and prints/writes a clean side-by-side
table for the paper.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

# Canonical multi-seed runs per condition (minimax m2.7, 17-task test set).
CONDITIONS: dict[str, dict] = {
    "CC (vanilla)": {
        "agent": "claude_code_no_plugin",
        "runs": ["mm_noplug_run1", "noplug_mm_v2", "noplug_mm_v2_s2"],
    },
    "CC + RAG": {
        "agent": "claude_code_repo3_plugin_nohook",
        "runs": ["plug_mm_v2_s2"],  # only clean 17-task seed available
    },
    "CC + RAG + hook": {
        "agent": "claude_code_repo3_plugin",
        "runs": ["pac1_plug_hook_s1", "pac1_plug_hook_s2", "pac1_plug_hook_s3", "plug_mm_v2_seed2"],
    },
    "CC + RAG + hook + memory (M1-u)": {
        "agent": "claude_code_repo3_plugin_m1u",
        "runs": ["mem_m1u_s1", "mem_m1u_s2", "mem_m1u_s3"],
    },
}


def select(df: pd.DataFrame, agent: str, runs: list[str]) -> pd.DataFrame:
    return df[(df["agent"] == agent) & (df["run_name"].isin(runs))]


def aggregate_file_access(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"n_seeds": 0, "n_task_runs": 0}
    sums = df[
        [
            "n_tasks",
            "n_unique_files_referenced",
            "n_rst_sphinx_reads",
            "n_rst_nonsphinx_reads",
            "n_xml_input_files_reads",
            "n_xml_workspace_reads",
            "n_xsd_schema_reads",
            "n_python_reads",
            "n_other_reads",
            "n_bash_total",
            "n_bash_xmllint",
            "n_bash_read_rst",
            "n_bash_read_xml",
            "n_glob_calls",
            "n_grep_calls",
        ]
    ].sum()
    n_runs = int(sums["n_tasks"])
    return {
        "n_seeds": int(len(df)),
        "n_task_runs": n_runs,
        "uniq_files": int(sums["n_unique_files_referenced"]),
        "rst_sphinx": int(sums["n_rst_sphinx_reads"]),
        "rst_nonsphinx": int(sums["n_rst_nonsphinx_reads"]),
        "xml_inputfiles": int(sums["n_xml_input_files_reads"]),
        "xml_workspace": int(sums["n_xml_workspace_reads"]),
        "xsd_schema": int(sums["n_xsd_schema_reads"]),
        "bash_total": int(sums["n_bash_total"]),
        "bash_xmllint": int(sums["n_bash_xmllint"]),
        "bash_read_xml": int(sums["n_bash_read_xml"]),
        "glob_calls": int(sums["n_glob_calls"]),
        "grep_calls": int(sums["n_grep_calls"]),
        # Per-task means for fair cross-condition comparison.
        "rst_sphinx_per_task": float(sums["n_rst_sphinx_reads"] / n_runs) if n_runs else 0,
        "rst_nonsphinx_per_task": float(sums["n_rst_nonsphinx_reads"] / n_runs) if n_runs else 0,
        "xml_inputfiles_per_task": float(sums["n_xml_input_files_reads"] / n_runs) if n_runs else 0,
        "xmllint_per_task": float(sums["n_bash_xmllint"] / n_runs) if n_runs else 0,
        "glob_per_task": float(sums["n_glob_calls"] / n_runs) if n_runs else 0,
    }


def aggregate_tool_usage(per_run: pd.DataFrame, agent: str, runs: list[str]) -> dict:
    sub = per_run[(per_run["agent"] == agent) & (per_run["run_name"].isin(runs))]
    if sub.empty:
        return {"n_task_runs": 0}
    n_task_runs = sub[["agent", "run_name", "task"]].drop_duplicates().shape[0]
    by_tool = sub.groupby("tool_name")[["attempted_count", "succeeded_count"]].sum()
    by_tool["error_rate"] = (
        (by_tool["attempted_count"] - by_tool["succeeded_count"]) / by_tool["attempted_count"]
    ).fillna(0).round(3)
    by_tool = by_tool.sort_values("attempted_count", ascending=False)
    total_attempted = int(by_tool["attempted_count"].sum())
    total_succeeded = int(by_tool["succeeded_count"].sum())
    return {
        "n_task_runs": n_task_runs,
        "tool_calls_total_attempted": total_attempted,
        "tool_calls_total_succeeded": total_succeeded,
        "tool_calls_per_task_attempted": round(total_attempted / n_task_runs, 1) if n_task_runs else 0,
        "tool_calls_per_task_succeeded": round(total_succeeded / n_task_runs, 1) if n_task_runs else 0,
        "by_tool": by_tool,
    }


def render_markdown(rows: list[tuple[str, dict, dict]]) -> str:
    cols = [
        ("Seeds", "n_seeds", "{:d}"),
        ("Task-runs", "n_task_runs", "{:d}"),
        ("Tool calls/task (success)", "tool_calls_per_task_succeeded", "{:.1f}"),
        ("Glob/task", "glob_per_task", "{:.1f}"),
        ("RST sphinx/task", "rst_sphinx_per_task", "{:.2f}"),
        ("RST non-sphinx/task", "rst_nonsphinx_per_task", "{:.2f}"),
        ("XML examples/task", "xml_inputfiles_per_task", "{:.1f}"),
        ("xmllint/task", "xmllint_per_task", "{:.2f}"),
    ]
    lines = ["| Condition | " + " | ".join(c[0] for c in cols) + " |"]
    lines.append("|" + "---|" * (len(cols) + 1))
    for label, fa, tu in rows:
        merged = {**fa, **tu}
        cells = [label]
        for _, key, fmt in cols:
            v = merged.get(key, 0)
            cells.append(fmt.format(v) if v is not None else "—")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-base", default="scripts/analysis/out_4cond")
    parser.add_argument("--write-md", default="docs/2026-04-27_4condition-file-tool-comparison.md")
    args = parser.parse_args()

    base = Path(args.out_base)
    fa = pd.read_csv(base / "file_access" / "file_access_summary.csv")
    tu_per_run = pd.read_csv(base / "tool_usage" / "tool_usage_per_run.csv")

    rows: list[tuple[str, dict, dict]] = []
    detailed: dict[str, dict] = {}
    for label, cfg in CONDITIONS.items():
        agent = cfg["agent"]
        runs = cfg["runs"]
        sub_fa = select(fa, agent, runs)
        if sub_fa.empty:
            print(f"[warn] no file_access rows for {label} ({agent} / {runs})")
        f_agg = aggregate_file_access(sub_fa)
        t_agg = aggregate_tool_usage(tu_per_run, agent, runs)
        rows.append((label, f_agg, t_agg))
        detailed[label] = {
            "agent": agent,
            "runs": runs,
            "file_access": f_agg,
            "tool_usage_summary": {k: v for k, v in t_agg.items() if k != "by_tool"},
            "tool_usage_top_tools": (
                t_agg["by_tool"].head(15).reset_index().to_dict(orient="records")
                if "by_tool" in t_agg
                else []
            ),
        }

    md_table = render_markdown(rows)
    print(md_table)
    print()

    # Per-tool top-15 per condition for the markdown
    md = ["# 4-condition file-access + tool-usage comparison",
          "",
          "Generated by `scripts/analysis/compare_4conditions.py` from",
          "`scripts/analysis/out_4cond/{file_access,tool_usage}/*`. Filtered to",
          "**minimax m2.7** runs on the canonical 17-task test set.",
          "",
          "## Condition mapping",
          ""]
    for label, cfg in CONDITIONS.items():
        md.append(f"- **{label}** = `{cfg['agent']}` × runs {cfg['runs']}")
    md.append("")
    md.append("## Headline table (per-task means)")
    md.append("")
    md.append(md_table)
    md.append("")
    md.append("## Top tools per condition (succeeded calls)")
    md.append("")
    for label, fa_agg, tu_agg in rows:
        md.append(f"### {label} (n_task_runs = {tu_agg['n_task_runs']})")
        md.append("")
        if "by_tool" in tu_agg:
            top = tu_agg["by_tool"].head(12).reset_index()
            md.append("| Tool | Attempted | Succeeded | Err rate |")
            md.append("|---|---:|---:|---:|")
            for _, row in top.iterrows():
                md.append(
                    f"| `{row['tool_name']}` | {int(row['attempted_count'])} | "
                    f"{int(row['succeeded_count'])} | {row['error_rate']:.3f} |"
                )
        md.append("")

    md.append("## Detailed file-category counts (totals across seeds)")
    md.append("")
    md.append("| Condition | RST sphinx | RST non-sphinx | XML inputFiles | XML workspace | XSD schema | xmllint | Glob | Grep |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for label, fa_agg, tu_agg in rows:
        md.append(
            f"| {label} | {fa_agg.get('rst_sphinx',0)} | "
            f"{fa_agg.get('rst_nonsphinx',0)} | {fa_agg.get('xml_inputfiles',0)} | "
            f"{fa_agg.get('xml_workspace',0)} | {fa_agg.get('xsd_schema',0)} | "
            f"{fa_agg.get('bash_xmllint',0)} | {fa_agg.get('glob_calls',0)} | "
            f"{fa_agg.get('grep_calls',0)} |"
        )
    md.append("")

    out_md = Path(args.write_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md) + "\n")
    print(f"\nWrote {out_md}")

    out_json = Path(args.out_base) / "comparison_4cond.json"
    out_json.write_text(json.dumps(detailed, indent=2, default=str))
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()

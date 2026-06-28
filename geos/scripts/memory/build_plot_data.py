#!/usr/bin/env python3
"""Build per-seed CSV for plotting harness-stack effectiveness.

Produces two CSVs:

1. `misc/memory_artifacts/plot_data_per_seed.csv` — one row per (condition, seed)
   with aggregate stats: mean fa0 TreeSim, n_scored, n_failed, mean_elapsed,
   mean_rag_calls, mean_mem_calls, mean_tool_calls, mean_tokens_in/out,
   total_cost_usd.

2. `misc/memory_artifacts/plot_data_per_task.csv` — one row per
   (condition, seed, task) with task-level fa0, elapsed, tool counts, etc.

Usage:
  python scripts/memory/build_plot_data.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, stdev


REPO = Path("/home/matt/sci/repo3")
SCORES = REPO / "misc" / "memory_artifacts" / "scores"
PAC1_SCORES = REPO / "misc" / "pac1" / "scores"

# Map condition → list of (seed_label, run_dir, score_json)
CONDITIONS = [
    ("A1_noplug",             [("s1", REPO / "data/eval/claude_code_no_plugin/noplug_mm_v2",
                                 Path("/data/shared/geophysics_agent_data/data/eval/results/noplug_mm_v2/claude_code_no_plugin")),
                                ("s2", REPO / "data/eval/claude_code_no_plugin/noplug_mm_v2_s2",
                                 SCORES / "noplug_mm_v2_s2_summary.json")]),
    ("A2_plug_nohook",        [("s1", REPO / "data/eval/claude_code_repo3_plugin/plug_mm_v2_seed2",
                                 Path("/data/shared/geophysics_agent_data/data/eval/results/plug_mm_v2_seed2/claude_code_repo3_plugin")),
                                ("s2", REPO / "data/eval/claude_code_repo3_plugin_nohook/plug_mm_v2_s2",
                                 SCORES / "plug_mm_v2_s2_summary.json")]),
    ("A3_plug_hook",          [("s1", REPO / "data/eval/claude_code_repo3_plugin/pac1_plug_hook_s1",
                                 PAC1_SCORES / "e23_summary.json"),
                                ("s2", REPO / "data/eval/claude_code_repo3_plugin/pac1_plug_hook_s2",
                                 PAC1_SCORES / "e23s2_summary.json"),
                                ("s3", REPO / "data/eval/claude_code_repo3_plugin/pac1_plug_hook_s3",
                                 PAC1_SCORES / "a3_s3_summary.json")]),
    ("A4_plug_mem_nohook",    [("s1", REPO / "data/eval/claude_code_repo3_plugin_gmemsilent_nohook/pac1_plug_mem_nohook_s1",
                                 PAC1_SCORES / "a4prime_s1_summary.json"),
                                ("s2", REPO / "data/eval/claude_code_repo3_plugin_gmemsilent_nohook/pac1_plug_mem_nohook_s2",
                                 PAC1_SCORES / "a4prime_s2_summary.json")]),
    ("A5_plug_mem_hook",      [("s1", REPO / "data/eval/claude_code_repo3_plugin_gmemsilent/pac1_plug_mem_hook_s1",
                                 PAC1_SCORES / "e24_summary.json"),
                                ("s2", REPO / "data/eval/claude_code_repo3_plugin_gmemsilent/pac1_plug_mem_hook_s2",
                                 PAC1_SCORES / "e24s2_summary.json"),
                                ("s3", REPO / "data/eval/claude_code_repo3_plugin_gmemsilent/pac1_plug_mem_hook_s3",
                                 PAC1_SCORES / "e24s3_summary.json")]),
    ("M_placebo",             [(f"s{i}",
                                 REPO / f"data/eval/claude_code_repo3_plugin_m_placebo/mem_placebo_s{i}",
                                 SCORES / f"mem_placebo_s{i}_summary.json") for i in [1,2,3]]),
    ("M1_u_cheatsheet_ungrounded", [(f"s{i}",
                                      REPO / f"data/eval/claude_code_repo3_plugin_m1u/mem_m1u_s{i}",
                                      SCORES / f"mem_m1u_s{i}_summary.json") for i in [1,2,3]]),
    ("M1_g_cheatsheet_grounded",   [(f"s{i}",
                                      REPO / f"data/eval/claude_code_repo3_plugin_m1g/mem_m1g_s{i}",
                                      SCORES / f"mem_m1g_s{i}_summary.json") for i in [1,2,3]]),
    ("M3_g_tool_grounded",         [(f"s{i}",
                                      REPO / f"data/eval/claude_code_repo3_plugin_m3g/mem_m3g_s{i}",
                                      SCORES / f"mem_m3g_s{i}_summary.json") for i in [1,2,3]]),
    ("M3_g_tool_grounded_hinted",  [("s1",
                                      REPO / "data/eval/claude_code_repo3_plugin_m3g_hinted/mem_m3g_hinted_s1",
                                      SCORES / "mem_m3g_hinted_s1_summary.json")]),
    ("M4_u_items_ungrounded",      [(f"s{i}",
                                      REPO / f"data/eval/claude_code_repo3_plugin_m4u/mem_m4u_s{i}",
                                      SCORES / f"mem_m4u_s{i}_summary.json") for i in [1,2,3]]),
    ("M4_g_items_grounded",        [(f"s{i}",
                                      REPO / f"data/eval/claude_code_repo3_plugin_m4g/mem_m4g_s{i}",
                                      SCORES / f"mem_m4g_s{i}_summary.json") for i in [1,2,3]]),
]

# API-contamination exclusion flags (from openrouter_contamination_note.md)
CONTAMINATED = {
    ("M4_u_items_ungrounded", "s3"): "402 credit exhaustion (13/17 tasks)",
    ("M3_g_tool_grounded", "s2"): "403 weekly key limit (17/17 tasks)",
    ("M3_g_tool_grounded", "s3"): "403 weekly key limit (17/17 tasks)",
}


def scan_run(run_dir: Path) -> dict:
    """Aggregate per-task status.json into run-level stats."""
    n_tasks = 0
    n_success = 0
    n_api_error = 0
    elapsed_list = []
    rag_calls_list = []
    mem_calls_list = []
    all_tool_counts_list = []
    tokens_in_list = []
    tokens_out_list = []
    cost_list = []
    per_task_rows = []
    if not run_dir.is_dir():
        return {"run_dir": str(run_dir), "missing": True}
    for task_dir in sorted(run_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        sj = task_dir / "status.json"
        if not sj.exists():
            continue
        try:
            d = json.loads(sj.read_text())
        except json.JSONDecodeError:
            continue
        n_tasks += 1
        resp = d.get("latest_agent_response", "") + " ".join(d.get("latest_stderr", []) or [])
        api_err = any(s in resp for s in ["API Error: 402", "API Error: 403",
                                            "Insufficient credits", "Key limit exceeded"])
        if api_err:
            n_api_error += 1
        elif d.get("process_status") == "success":
            n_success += 1
        elapsed = d.get("elapsed_seconds")
        if elapsed: elapsed_list.append(elapsed)
        tc = d.get("per_tool_counts", {}) or {}
        rag = sum(v for k, v in tc.items() if "geos-rag" in k)
        mem = tc.get("mcp__memory__memory_lookup", 0)
        total_tools = sum(tc.values())
        rag_calls_list.append(rag)
        mem_calls_list.append(mem)
        all_tool_counts_list.append(total_tools)
        # Token counts aren't in status.json for every agent key; skip if absent
        # OpenRouter cost per task
        cost = d.get("openrouter_cost_usd")
        if isinstance(cost, (int, float)):
            cost_list.append(cost)
        per_task_rows.append({
            "task": task_dir.name,
            "process_status": d.get("process_status", "?"),
            "api_error": api_err,
            "elapsed_sec": elapsed,
            "rag_calls": rag,
            "mem_calls": mem,
            "total_tool_calls": total_tools,
            "openrouter_cost_usd": cost,
        })
    return {
        "n_tasks": n_tasks,
        "n_success": n_success,
        "n_api_error": n_api_error,
        "mean_elapsed_sec": mean(elapsed_list) if elapsed_list else None,
        "mean_rag_calls": mean(rag_calls_list) if rag_calls_list else None,
        "mean_mem_calls": mean(mem_calls_list) if mem_calls_list else None,
        "mean_tool_calls": mean(all_tool_counts_list) if all_tool_counts_list else None,
        "total_cost_usd": sum(cost_list) if cost_list else None,
        "per_task": per_task_rows,
    }


def load_scores_path(p: Path) -> dict[str, float]:
    """Returns task→treesim. Handles both aggregate summary.json and per-task eval_jsons dir."""
    if p.is_dir():
        # Per-task *_eval.json files
        out = {}
        for f in p.glob("*_eval.json"):
            task = f.stem.replace("_eval", "")
            try:
                d = json.loads(f.read_text())
                ts = d.get("treesim")
                out[task] = float(ts) if isinstance(ts, (int, float)) else 0.0
            except Exception:
                out[task] = 0.0
        return out
    if p.exists():
        try:
            d = json.loads(p.read_text())
            return {r["experiment"]: (float(r.get("treesim") or 0)) for r in d.get("results", [])}
        except Exception:
            return {}
    return {}


def main() -> int:
    per_seed_rows = []
    per_task_rows_all = []
    for cond_name, seeds in CONDITIONS:
        for seed, run_dir, score_path in seeds:
            contam_flag = CONTAMINATED.get((cond_name, seed), "")
            stats = scan_run(run_dir)
            scores = load_scores_path(score_path.resolve() if score_path else Path())
            # fa0 = mean with failures treated as 0 over 17 tasks
            tasks = ["ExampleDPWellbore","AdvancedExampleExtendedDruckerPrager","ExampleMandel",
                     "AdvancedExampleModifiedCamClay","ExampleIsothermalLeakyWell","ExampleEDPWellbore",
                     "AdvancedExampleDeviatedElasticWellbore","kgdExperimentValidation",
                     "ExampleThermalLeakyWell","AdvancedExampleCasedContactThermoElasticWellbore",
                     "AdvancedExampleDruckerPrager","TutorialSneddon","AdvancedExampleViscoDruckerPrager",
                     "pknViscosityDominated","buckleyLeverettProblem","TutorialPoroelasticity",
                     "ExampleThermoporoelasticConsolidation"]
            scored_vals = [scores.get(t, 0.0) for t in tasks]
            fa0_mean = mean(scored_vals) if scored_vals else 0.0
            per_seed_rows.append({
                "condition": cond_name,
                "seed": seed,
                "contaminated": contam_flag,
                "fa0_mean_treesim": round(fa0_mean, 4),
                "n_tasks": stats.get("n_tasks"),
                "n_success": stats.get("n_success"),
                "n_api_error": stats.get("n_api_error"),
                "mean_elapsed_sec": round(stats.get("mean_elapsed_sec") or 0, 1),
                "mean_rag_calls": round(stats.get("mean_rag_calls") or 0, 2),
                "mean_mem_calls": round(stats.get("mean_mem_calls") or 0, 2),
                "mean_tool_calls": round(stats.get("mean_tool_calls") or 0, 2),
                "total_cost_usd": round(stats.get("total_cost_usd") or 0, 4),
            })
            # per-task rows
            for t_stats in stats.get("per_task", []):
                task = t_stats["task"]
                per_task_rows_all.append({
                    "condition": cond_name,
                    "seed": seed,
                    "contaminated": contam_flag,
                    "task": task,
                    "treesim": scores.get(task, 0.0),
                    **{k: v for k, v in t_stats.items() if k != "task"},
                })

    # Write per-seed CSV
    per_seed_csv = REPO / "misc" / "memory_artifacts" / "plot_data_per_seed.csv"
    with per_seed_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_seed_rows[0].keys()))
        w.writeheader()
        for r in per_seed_rows:
            w.writerow(r)
    print(f"wrote {per_seed_csv} ({len(per_seed_rows)} rows)")

    # Per-task CSV
    per_task_csv = REPO / "misc" / "memory_artifacts" / "plot_data_per_task.csv"
    with per_task_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_task_rows_all[0].keys()))
        w.writeheader()
        for r in per_task_rows_all:
            w.writerow(r)
    print(f"wrote {per_task_csv} ({len(per_task_rows_all)} rows)")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

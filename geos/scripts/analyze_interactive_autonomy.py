#!/usr/bin/env python3
"""Aggregate scores + supervisor-call telemetry across the interactive-
autonomy study runs and emit a single JSON + markdown report.

Run AFTER scripts/score_interactive_autonomy.sh has populated the
_results subtree with per-run _summary.json files.

Outputs:
    docs/2026-05-04_interactive-autonomy-results.md
    data/eval/interactive_autonomy_2026-05-03/_results/aggregate.json
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path
from statistics import mean

ROOT = Path("data/eval/interactive_autonomy_2026-05-03")
RES_ROOT = ROOT / "_results"
OUT_AGG = RES_ROOT / "aggregate.json"
# DO NOT overwrite the curated morning report. Auto-table goes here.
OUT_MD = Path("docs/2026-05-04_interactive-autonomy-autotable.md")

# 8 study tasks
TASKS = [
    "ExampleMandel",
    "ExampleDPWellbore",
    "ExampleEDPWellbore",
    "ExampleIsothermalLeakyWell",
    "ExampleThermalLeakyWell",
    "TutorialPoroelasticity",
    "TutorialSneddon",
    "ExampleThermoporoelasticConsolidation",
]


# --------------------------------------------------------------------- #
# Score loading
# --------------------------------------------------------------------- #


def load_summaries() -> list[dict]:
    rows = []
    for p in sorted(RES_ROOT.glob("*/*/*/_summary.json")):
        # _results/<mode_diff>/<run>/<agent>/_summary.json
        d = json.loads(p.read_text())
        parts = p.relative_to(RES_ROOT).parts
        mode_diff = parts[0]
        run_name = parts[1]
        agent = parts[2]
        results = d.get("results", [])
        for r in results:
            task_name = r.get("task") or r.get("experiment") or r.get("task_name")
            rows.append({
                "mode_diff": mode_diff,
                "run_name": run_name,
                "agent": agent,
                "task": task_name,
                "treesim": r.get("treesim_failures_as_zero",
                                 r.get("treesim", 0.0)),
                "scored": r.get("scored", True),
                "status": r.get("status"),
                "n_total_tool_calls": r.get("n_total_tool_calls"),
            })
    return rows


# --------------------------------------------------------------------- #
# Supervisor telemetry
# --------------------------------------------------------------------- #


QUESTION_KEYWORDS = {
    "T1": ["output", "vtk", "restart", "log", "frequency", "interval",
           "schedule"],
    "T2": ["tolerance", "newton", "solver", "iteration", "discretis",
           "discretiz", "time step", "preconditioner", "linear solver",
           "element type"],
    "T3": ["density", "viscosity", "porosity", "permeabil", "biot",
           "modulus", "compress", "rock", "material", "relperm"],
    "T4": ["domain", "geometry", "well location", "injection rate",
           "duration", "load", "boundary", "applied", "history"],
    "procedural": ["where do i", "filename", "file name", "name the",
                   "format", "convention"],
    "clarification": ["could you confirm", "do you mean", "is that",
                      "to clarify", "i want to confirm", "please confirm"],
}


def categorise_question(q: str) -> str:
    ql = q.lower()
    scores: dict[str, int] = collections.Counter()
    for cat, kws in QUESTION_KEYWORDS.items():
        for kw in kws:
            if kw in ql:
                scores[cat] += 1
    if not scores:
        return "other"
    return max(scores.items(), key=lambda kv: kv[1])[0]


def load_supervisor_calls() -> list[dict]:
    """Walk all run dirs, gather supervisor_calls.jsonl entries.
    Path: data/eval/interactive_autonomy_2026-05-03/<mode_diff>/<agent>/<run>/<task>/supervisor_calls.jsonl
    """
    calls = []
    for p in sorted(ROOT.glob("mode*_*/ia_*/*/*/supervisor_calls.jsonl")):
        parts = p.relative_to(ROOT).parts
        mode_diff = parts[0]
        agent = parts[1]
        run_name = parts[2]
        task = parts[3]
        try:
            with p.open() as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "question" not in rec:
                        continue
                    rec_out = {
                        "mode_diff": mode_diff,
                        "agent": agent,
                        "run_name": run_name,
                        "task": task,
                        "question": rec.get("question", ""),
                        "answer": rec.get("answer", ""),
                        "category": categorise_question(rec.get("question", "")),
                        "prompt_tokens": rec.get("prompt_tokens"),
                        "completion_tokens": rec.get("completion_tokens"),
                        "latency_seconds": rec.get("latency_seconds"),
                    }
                    calls.append(rec_out)
        except OSError:
            continue
    return calls


# --------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------- #


def aggregate_scores(rows: list[dict]) -> dict:
    """Group by (mode_diff, agent) and compute means + per-task scores.

    Each (mode_diff, agent) combination has 1 seed in this study, so
    the "mean" is over tasks within the combo.
    """
    by_combo: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_combo[(r["mode_diff"], r["agent"])].append(r)
    out = {}
    for (md, ag), recs in by_combo.items():
        ts = [r["treesim"] for r in recs if r.get("treesim") is not None]
        out[f"{md}/{ag}"] = {
            "mode_diff": md,
            "agent": ag,
            "n_tasks": len(recs),
            "treesim_mean": round(mean(ts), 4) if ts else None,
            "treesim_min": round(min(ts), 4) if ts else None,
            "treesim_max": round(max(ts), 4) if ts else None,
            "n_failed": sum(1 for r in recs if r.get("status") and r["status"] != "success"),
            "per_task": {r["task"]: round(r.get("treesim") or 0.0, 4) for r in recs},
        }
    return out


def aggregate_calls(calls: list[dict]) -> dict:
    by_combo: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for c in calls:
        by_combo[(c["mode_diff"], c["agent"])].append(c)
    out = {}
    for (md, ag), recs in by_combo.items():
        cats = collections.Counter(c["category"] for c in recs)
        by_task = collections.Counter(c["task"] for c in recs)
        prompt_tot = sum((c.get("prompt_tokens") or 0) for c in recs)
        comp_tot = sum((c.get("completion_tokens") or 0) for c in recs)
        out[f"{md}/{ag}"] = {
            "mode_diff": md,
            "agent": ag,
            "n_calls": len(recs),
            "n_tasks_with_calls": len(by_task),
            "calls_per_task": {t: by_task[t] for t in by_task},
            "category_counts": dict(cats),
            "prompt_tokens_total": prompt_tot,
            "completion_tokens_total": comp_tot,
        }
    return out


# --------------------------------------------------------------------- #
# Report writer
# --------------------------------------------------------------------- #


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        lines.append("| " + " | ".join("" if x is None else str(x) for x in r) + " |")
    return "\n".join(lines)


def render_report(scores: dict, calls: dict, raw_calls: list[dict]) -> str:
    out = ["# Interactive autonomy + difficulty ramp — results",
           "",
           "*Auto-generated by `scripts/analyze_interactive_autonomy.py`. "
           "See `docs/2026-05-03_interactive-autonomy-design.md` for the "
           "study design.*",
           ""]

    # ---- Score table ----
    out.append("## TreeSim by (mode, difficulty, config)")
    out.append("")
    rows = []
    for combo_key, s in sorted(scores.items()):
        rows.append([
            s["mode_diff"], s["agent"], str(s["n_tasks"]),
            f"{s['treesim_mean']:.4f}" if s["treesim_mean"] is not None else "—",
            f"{s['treesim_min']:.3f}" if s["treesim_min"] is not None else "—",
            f"{s['treesim_max']:.3f}" if s["treesim_max"] is not None else "—",
            str(s["n_failed"]),
        ])
    out.append(md_table(
        ["mode_diff", "agent", "n", "TreeSim mean", "min", "max", "fails"],
        rows,
    ))
    out.append("")

    # ---- Per-task breakdown ----
    out.append("## Per-task TreeSim")
    out.append("")
    all_tasks = sorted({t for s in scores.values() for t in s["per_task"]})
    headers = ["task"] + [k for k in sorted(scores)]
    rows = []
    for t in all_tasks:
        row = [t]
        for k in sorted(scores):
            v = scores[k]["per_task"].get(t)
            row.append(f"{v:.3f}" if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows))
    out.append("")

    # ---- Supervisor calls ----
    if calls:
        out.append("## Supervisor consultation rates")
        out.append("")
        rows = []
        for k, c in sorted(calls.items()):
            cats_str = ", ".join(f"{k2}={v2}" for k2, v2 in sorted(c["category_counts"].items()))
            rows.append([
                c["mode_diff"], c["agent"], str(c["n_calls"]),
                str(c["n_tasks_with_calls"]),
                cats_str or "—",
                str(c["prompt_tokens_total"]),
                str(c["completion_tokens_total"]),
            ])
        out.append(md_table(
            ["mode_diff", "agent", "calls", "tasks_w_calls",
             "categories", "prompt_tok", "comp_tok"],
            rows,
        ))
        out.append("")

        # ---- Sample questions per combo ----
        out.append("## Sample supervisor questions")
        out.append("")
        by_combo = collections.defaultdict(list)
        for c in raw_calls:
            by_combo[(c["mode_diff"], c["agent"])].append(c)
        for (md, ag), recs in sorted(by_combo.items()):
            out.append(f"### {md} / {ag}")
            for c in recs[:4]:
                q = c["question"].strip().replace("\n", " ")
                a = c["answer"].strip().replace("\n", " ")[:160]
                out.append(f"- **[{c['task']}, {c['category']}]** Q: {q[:180]}")
                out.append(f"    A: {a}")
            out.append("")

    return "\n".join(out)


# --------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------- #


def main() -> int:
    if not RES_ROOT.exists():
        print(f"no _results dir at {RES_ROOT}", file=sys.stderr)
        return 1
    rows = load_summaries()
    calls = load_supervisor_calls()
    score_agg = aggregate_scores(rows)
    call_agg = aggregate_calls(calls)
    OUT_AGG.write_text(json.dumps({
        "scores_by_combo": score_agg,
        "supervisor_by_combo": call_agg,
        "n_score_rows": len(rows),
        "n_supervisor_calls": len(calls),
    }, indent=2))
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_report(score_agg, call_agg, calls))
    print(f"score rows: {len(rows)}")
    print(f"supervisor calls: {len(calls)}")
    print(f"-> {OUT_AGG}")
    print(f"-> {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

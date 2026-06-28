#!/usr/bin/env python3
"""Stage 3: aggregate per-task diagnoses into a paper-ready narrative.

Reads <llm_dir>/*.llm.json (Stage 2 outputs).
Groups by (agent[, run]) — defaults to per-agent (collapsing seeds).

Computes:
  - failure category distribution
  - top failing sections (weighted by treesim shortfall)
  - severity distribution
  - diff between agents (e.g. F0 baseline vs F4 best): what F4 fixes, what remains

Calls DSv4-pro for a narrative synthesis when --narrate is passed.

Outputs:
  - <out>/aggregate.json — structured stats
  - <out>/aggregate.md — markdown report
  - <out>/per_task_table.csv — flat table for paper
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

DEEPSEEK_BASE = "https://api.deepseek.com"


def load_diagnoses(llm_dir: Path) -> list[dict]:
    out = []
    for p in sorted(llm_dir.glob("*.llm.json")):
        try:
            d = json.loads(p.read_text())
            out.append(d)
        except Exception as e:
            print(f"[skip] {p.name}: {e}", file=sys.stderr)
    return out


def aggregate(diagnoses: list[dict], group_by_run: bool = False) -> dict:
    by_cell: dict[str, list[dict]] = defaultdict(list)
    for d in diagnoses:
        key = d["agent"] if not group_by_run else f"{d['agent']}__{d['run']}"
        by_cell[key].append(d)

    out = {}
    for cell, items in by_cell.items():
        cats = Counter()
        sections = Counter()
        severities = Counter()
        scores = []
        section_failure_weight: dict[str, float] = defaultdict(float)
        per_task_rows = []
        for d in items:
            diag = d.get("diagnosis") or {}
            ts = d.get("treesim")
            if ts is not None:
                scores.append(ts)
            cat = diag.get("failure_category", "unknown")
            sec = diag.get("primary_failure_section", "?")
            sev = diag.get("severity", "unknown")
            cats[cat] += 1
            sections[sec] += 1
            severities[sev] += 1
            shortfall = max(0.0, 1.0 - (ts or 1.0))
            section_failure_weight[sec] += shortfall
            per_task_rows.append({
                "task": d["task"],
                "run": d["run"],
                "treesim": ts,
                "category": cat,
                "section": sec,
                "severity": sev,
                "root_cause": diag.get("root_cause", ""),
                "would_have_helped": diag.get("would_have_helped", ""),
            })
        out[cell] = {
            "n_tasks": len(items),
            "treesim_mean": round(mean(scores), 4) if scores else None,
            "treesim_median": round(median(scores), 4) if scores else None,
            "category_dist": dict(cats),
            "section_dist": dict(sections),
            "severity_dist": dict(severities),
            "section_failure_weight": {k: round(v, 4) for k, v in sorted(section_failure_weight.items(), key=lambda x: -x[1])},
            "per_task": per_task_rows,
        }
    return out


def diff_cells(agg: dict, baseline: str, best: str) -> dict:
    if baseline not in agg or best not in agg:
        return {"error": f"missing cell — agg has {list(agg.keys())}"}
    b = agg[baseline]
    bb = agg[best]
    # task-level join
    base_by = {(r["task"], r["run"][-2:] if r["run"] else ""): r for r in b["per_task"]}
    # naive: just compare per-task by task name (ignoring run/seed)
    by_task_b: dict[str, list[dict]] = defaultdict(list)
    by_task_bb: dict[str, list[dict]] = defaultdict(list)
    for r in b["per_task"]:
        by_task_b[r["task"]].append(r)
    for r in bb["per_task"]:
        by_task_bb[r["task"]].append(r)
    common = sorted(set(by_task_b) & set(by_task_bb))
    deltas = []
    for t in common:
        b_ts = mean([r["treesim"] for r in by_task_b[t] if r["treesim"] is not None])
        bb_ts = mean([r["treesim"] for r in by_task_bb[t] if r["treesim"] is not None])
        deltas.append({
            "task": t,
            "baseline_treesim": round(b_ts, 4),
            "best_treesim": round(bb_ts, 4),
            "delta": round(bb_ts - b_ts, 4),
            "baseline_category": Counter(r["category"] for r in by_task_b[t]).most_common(1)[0][0],
            "best_category": Counter(r["category"] for r in by_task_bb[t]).most_common(1)[0][0],
            "baseline_section": Counter(r["section"] for r in by_task_b[t]).most_common(1)[0][0],
            "best_section": Counter(r["section"] for r in by_task_bb[t]).most_common(1)[0][0],
        })
    deltas.sort(key=lambda x: x["delta"], reverse=True)
    return {
        "baseline": baseline,
        "best": best,
        "n_common_tasks": len(common),
        "task_deltas": deltas,
        "biggest_gains": deltas[:5],
        "biggest_regressions": [d for d in deltas if d["delta"] < 0][:5],
        "fixed_categories": [
            d for d in deltas if d["delta"] > 0.05 and d["baseline_category"] != d["best_category"]
        ][:10],
    }


def write_report(agg: dict, diff: dict | None, out: Path, narrative: str | None) -> None:
    lines: list[str] = []
    lines.append("# Bottleneck analysis — auto-generated\n")
    if narrative:
        lines.append("## Synthesis (DSv4-pro)\n\n" + narrative.strip() + "\n")
    lines.append("## Per-cell summary\n")
    for cell in sorted(agg.keys()):
        s = agg[cell]
        lines.append(f"### {cell}  (n={s['n_tasks']}, treesim mean={s['treesim_mean']})\n")
        lines.append("**Failure category distribution:**\n")
        lines.append("```\n" + json.dumps(s["category_dist"], indent=2) + "\n```\n")
        lines.append("**Failing section distribution:**\n")
        lines.append("```\n" + json.dumps(s["section_dist"], indent=2) + "\n```\n")
        lines.append("**Section failure weight** (sum of (1 - treesim) per task, by section):\n")
        lines.append("```\n" + json.dumps(s["section_failure_weight"], indent=2) + "\n```\n")
    if diff:
        lines.append(f"## Comparison: {diff['baseline']} vs {diff['best']}\n")
        lines.append(f"n_common_tasks: {diff['n_common_tasks']}\n")
        lines.append("\n### Biggest gains (best > baseline)\n")
        for d in diff["biggest_gains"]:
            lines.append(f"- **{d['task']}**: {d['baseline_treesim']} → {d['best_treesim']} (Δ {d['delta']:+}); "
                         f"category {d['baseline_category']} → {d['best_category']}, section {d['baseline_section']} → {d['best_section']}")
        lines.append("\n### Biggest regressions (best < baseline)\n")
        for d in diff["biggest_regressions"]:
            lines.append(f"- **{d['task']}**: {d['baseline_treesim']} → {d['best_treesim']} (Δ {d['delta']:+}); "
                         f"category {d['baseline_category']} → {d['best_category']}, section {d['baseline_section']} → {d['best_section']}")
    out.write_text("\n".join(lines))


def write_csv(agg: dict, out_csv: Path) -> None:
    rows = []
    for cell, s in agg.items():
        for r in s["per_task"]:
            row = {"cell": cell, **r}
            rows.append(row)
    if not rows:
        return
    cols = ["cell", "task", "run", "treesim", "category", "section", "severity", "root_cause", "would_have_helped"]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def narrate(client: OpenAI, model: str, agg: dict, diff: dict | None, max_tokens: int = 6000) -> str:
    """Send aggregated stats to DSv4-pro and ask for a paper-ready narrative."""
    prompt_data = {"per_cell": {}}
    for cell, s in agg.items():
        prompt_data["per_cell"][cell] = {
            "n_tasks": s["n_tasks"],
            "treesim_mean": s["treesim_mean"],
            "category_dist": s["category_dist"],
            "section_dist": s["section_dist"],
            "section_failure_weight": dict(list(s["section_failure_weight"].items())[:10]),
            "sample_root_causes": [r["root_cause"] for r in s["per_task"][:6] if r.get("root_cause")],
            "sample_would_have_helped": [r["would_have_helped"] for r in s["per_task"][:6] if r.get("would_have_helped")],
        }
    if diff:
        prompt_data["comparison"] = {
            "baseline": diff["baseline"],
            "best": diff["best"],
            "biggest_gains": diff["biggest_gains"],
            "biggest_regressions": diff["biggest_regressions"],
            "fixed_categories": diff["fixed_categories"],
        }
    baseline_cell = diff["baseline"] if diff else "autocamp_F0"
    best_cell = diff["best"] if diff else "autocamp_F4"
    user = (
        "You are writing the 'Bottleneck Analysis' section for a NeurIPS paper on coding-agent harnesses for the GEOS XML benchmark. "
        "Produce a tight, evidence-based narrative (~400-600 words, markdown). "
        f"The BASELINE cell is `{baseline_cell}` and the BEST-CONFIG cell is `{best_cell}` — anchor the narrative on these two unless you have a specific reason to discuss another. "
        "Other cells in the data are alternative configurations; mention them only when they directly clarify a baseline-vs-best contrast.\n\n"
        f"Sections: (1) Baseline weaknesses — what does `{baseline_cell}` get wrong most often, and why; "
        f"(2) Adapter impact — for `{best_cell}` specifically, which bottlenecks are fixed (vs `{baseline_cell}`) and which remain; "
        "(3) Implications — concrete adapter-design takeaways (each takeaway must cite a failure category or section).\n\n"
        "STATISTICS (JSON):\n```json\n" + json.dumps(prompt_data, indent=2)[:8000] + "\n```\n\n"
        "Constraints: be specific (cite section names like 'Solvers', 'Events'); no hedging; no headings beyond the three sections; no bullet lists longer than 4 items."
    )
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user}],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return r.choices[0].message.content or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--baseline", help="cell name (agent) for the baseline (e.g. autocamp_F0)")
    ap.add_argument("--best", help="cell name (agent) for the best config (e.g. autocamp_F4)")
    ap.add_argument("--narrate", action="store_true", help="call DSv4-pro for narrative")
    ap.add_argument("--narrate-model", default="deepseek-v4-pro")
    ap.add_argument("--group-by-run", action="store_true", help="separate by run/seed instead of merging")
    args = ap.parse_args()

    llm_dir = Path(args.llm_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    diagnoses = load_diagnoses(llm_dir)
    print(f"loaded {len(diagnoses)} diagnoses")
    agg = aggregate(diagnoses, group_by_run=args.group_by_run)
    print(f"aggregated into {len(agg)} cells")

    diff = None
    if args.baseline and args.best:
        diff = diff_cells(agg, args.baseline, args.best)

    narrative = None
    if args.narrate:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            env_path = Path(__file__).resolve().parents[2] / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
        if not api_key or OpenAI is None:
            print("DEEPSEEK_API_KEY missing or openai not installed — skipping narration")
        else:
            client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE)
            print(f"narrating with {args.narrate_model}...")
            narrative = narrate(client, args.narrate_model, agg, diff)

    (out_dir / "aggregate.json").write_text(json.dumps({"agg": agg, "diff": diff}, indent=2))
    write_report(agg, diff, out_dir / "aggregate.md", narrative)
    write_csv(agg, out_dir / "per_task_table.csv")
    print(f"wrote {out_dir}/{{aggregate.json, aggregate.md, per_task_table.csv}}")


if __name__ == "__main__":
    main()

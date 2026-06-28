#!/usr/bin/env python3
"""Paper-ready efficiency table for Phase 2 cells.

For each cell × seed × task, extract from events.jsonl:
  - n_turns (assistant messages)
  - n_tools (tool_use events)
  - tools_before_first_write
  - elapsed_s (from status.json)
Aggregate per cell across all (seed, task). Pair with quality.

Output: docs/2026-05-02_efficiency-table.md
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path("/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01")
OUT = Path("/home/matt/sci/repo3/docs/2026-05-02_efficiency-table.md")

CELLS_P2 = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "SE"]
SEEDS = ["s1", "s2", "s3"]

QWEN_CELLS = [
    ("qwen baseline (F0-eq)", "xmodel_baseline", "qwen_qwen3.6-27b_baseline_s1"),
    ("qwen best (F4-eq)",     "xmodel_best",     "qwen_qwen3.6-27b_best_s1"),
]


def parse_events(events_path: Path) -> dict:
    n_assistant = n_tools = first_write = -1
    has_write = False
    tool_idx = 0
    with events_path.open() as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            t = e.get("type")
            if t == "assistant":
                msg = e.get("message", {})
                n_assistant += 1
                # check for tool_use blocks
                for block in msg.get("content", []) or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        n_tools += 1
                        tool_idx += 1
                        if not has_write and block.get("name") == "Write":
                            has_write = True
                            first_write = tool_idx
    return {
        "n_turns": max(0, n_assistant + 1),
        "n_tools": max(0, n_tools + 1),
        "tools_before_first_write": first_write if has_write else None,
    }


def parse_status(status_path: Path) -> dict:
    try:
        s = json.loads(status_path.read_text())
        return {"elapsed_s": s.get("elapsed_seconds"), "process_status": s.get("process_status")}
    except Exception:
        return {}


def load_quality(cell: str) -> dict:
    """Per-(seed, task) treesim. Returns {(seed, task): score}."""
    out = {}
    for seed in SEEDS:
        sp = ROOT / "_results" / f"autocamp_{cell}_{seed}" / f"autocamp_{cell}" / "_summary.json"
        if not sp.exists():
            continue
        d = json.loads(sp.read_text())
        for r in d.get("results", []):
            task = r.get("experiment")
            ts = r.get("treesim")
            if task and ts is not None:
                out[(seed, task)] = ts
    return out


def collect_cell(cell: str) -> dict:
    rows = []
    qmap = load_quality(cell)
    cell_dir = ROOT / "dsv4" / f"autocamp_{cell}"
    if not cell_dir.exists():
        return {"cell": cell, "rows": []}
    for seed_dir in sorted(cell_dir.iterdir()):
        seed = seed_dir.name
        if seed not in [f"autocamp_{cell}_{s}" for s in SEEDS]:
            continue
        seed_id = seed.split("_")[-1]
        for task_dir in sorted(seed_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task = task_dir.name
            events = task_dir / "events.jsonl"
            status = task_dir / "status.json"
            if not events.exists():
                continue
            ev = parse_events(events)
            st = parse_status(status)
            row = {"seed": seed_id, "task": task, **ev, **st}
            row["quality"] = qmap.get((seed_id, task))
            rows.append(row)
    return {"cell": cell, "rows": rows}


def collect_xmodel(label: str, agent: str, run: str) -> dict:
    """Collect for one (agent, run) cell from xmodel/ subtree."""
    rows = []
    # quality
    sp = ROOT / "_results" / run / f"autocamp_{agent}" / "_summary.json"
    qmap = {}
    if sp.exists():
        d = json.loads(sp.read_text())
        for r in d.get("results", []):
            ts = r.get("treesim")
            if ts is not None:
                qmap[r.get("experiment")] = ts
    cell_dir = ROOT / "xmodel" / f"autocamp_{agent}" / run
    if not cell_dir.exists():
        return {"cell": label, "rows": []}
    for task_dir in sorted(cell_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        task = task_dir.name
        events = task_dir / "events.jsonl"
        status = task_dir / "status.json"
        if not events.exists():
            continue
        ev = parse_events(events)
        st = parse_status(status)
        row = {"seed": "s1", "task": task, **ev, **st, "quality": qmap.get(task)}
        rows.append(row)
    return {"cell": label, "rows": rows}


def fmt(v, prec=1):
    if v is None:
        return "—"
    return f"{v:.{prec}f}"


def aggregate(rows: list[dict]) -> dict:
    valid = [r for r in rows if r.get("n_tools")]
    if not valid:
        return {}
    g = lambda k: [r[k] for r in valid if r.get(k) is not None]
    tools = g("n_tools")
    turns = g("n_turns")
    elapsed = g("elapsed_s")
    quality = g("quality")
    twfw = g("tools_before_first_write")
    return {
        "n_runs": len(valid),
        "tools_mean": statistics.mean(tools) if tools else None,
        "tools_median": statistics.median(tools) if tools else None,
        "turns_mean": statistics.mean(turns) if turns else None,
        "elapsed_mean": statistics.mean(elapsed) if elapsed else None,
        "twfw_mean": statistics.mean(twfw) if twfw else None,
        "twfw_median": statistics.median(twfw) if twfw else None,
        "quality_mean": statistics.mean(quality) if quality else None,
        "quality_std": statistics.stdev(quality) if len(quality) > 1 else None,
        "n_with_write": sum(1 for r in valid if r.get("tools_before_first_write")),
    }


def main():
    table = []
    for cell in CELLS_P2:
        d = collect_cell(cell)
        agg = aggregate(d["rows"])
        agg["cell"] = cell
        table.append(agg)

    qwen_table = []
    for label, agent, run in QWEN_CELLS:
        d = collect_xmodel(label, agent, run)
        agg = aggregate(d["rows"])
        agg["cell"] = label
        qwen_table.append(agg)

    # Find F0 baseline for delta cols
    f0 = next((r for r in table if r.get("cell") == "F0"), {})

    md = ["# Paper-ready efficiency table — Phase 2 (DSv4-flash, 17 tasks × 3 seeds)\n"]
    md.append(
        "*Generated 2026-05-02 from `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01`. "
        "Per-cell aggregates over all (seed × task) pairs (≤51 runs).*\n"
    )
    md.append("## Quality + efficiency\n")
    md.append("| cell | n | quality | Δq | tools | Δtools | turns | wall (s) | tools-before-Write |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in table:
        if not r:
            continue
        dq = r.get("quality_mean", 0) - (f0.get("quality_mean") or 0) if r.get("quality_mean") and f0.get("quality_mean") else None
        dt = r.get("tools_mean", 0) - (f0.get("tools_mean") or 0) if r.get("tools_mean") and f0.get("tools_mean") else None
        md.append(
            f"| {r['cell']} | {r.get('n_runs','—')} | "
            f"{fmt(r.get('quality_mean'), 3)} ± {fmt(r.get('quality_std'), 3)} | "
            f"{('+' if dq and dq >= 0 else '') + fmt(dq, 3) if dq is not None else '—'} | "
            f"{fmt(r.get('tools_mean'), 0)} | "
            f"{('+' if dt and dt >= 0 else '') + fmt(dt, 0) if dt is not None else '—'} | "
            f"{fmt(r.get('turns_mean'), 0)} | "
            f"{fmt(r.get('elapsed_mean'), 0)} | "
            f"{fmt(r.get('twfw_mean'), 0)} |"
        )

    md.append("\n## Smaller-model anchor: qwen3.6-27b (Phase 4, 1 seed × 17 tasks)\n")
    md.append("| cell | n | quality | tools | turns | wall (s) | tools-before-Write |")
    md.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in qwen_table:
        if not r:
            continue
        md.append(
            f"| {r['cell']} | {r.get('n_runs','—')} | "
            f"{fmt(r.get('quality_mean'), 3)} ± {fmt(r.get('quality_std'), 3)} | "
            f"{fmt(r.get('tools_mean'), 0)} | "
            f"{fmt(r.get('turns_mean'), 0)} | "
            f"{fmt(r.get('elapsed_mean'), 0)} | "
            f"{fmt(r.get('twfw_mean'), 0)} |"
        )

    md.append("\n## Reading guide\n")
    md.append("- **n** = (seed, task) pairs observed (max 51 = 17 tasks × 3 seeds for DSv4; 17 for qwen 1-seed).")
    md.append("- **quality** = TreeSim mean ± std across runs (timeouts/failures excluded; see results doc for failures-as-0 numbers).")
    md.append("- **Δq, Δtools** = vs F0 baseline (no plugin, no Stop hook, no MCP, no memory).")
    md.append("- **tools-before-Write** = mean number of tool calls before the first Write tool. Lower = faster path to authoring.")
    md.append("\nF0 is the unaugmented DSv4-flash baseline. SE uses `plugin_evolving/v3` (DSv4-validated agent-authored plugin).")
    md.append("F0–F7 are the 2^(4-1) Resolution-IV factorial cells over {RAG, SR-hook, xmllint MCP, memory}.")
    md.append("Qwen baseline ≡ F0-equivalent on qwen3.6-27b. Qwen best ≡ F4-equivalent (xmllint MCP + plugin v3).")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(md) + "\n")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

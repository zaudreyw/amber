#!/usr/bin/env python3
"""F0 vs SE trajectory diff: structured per-task analysis.

Produces a JSON report comparing F0 (no plugin) and SE (plugin_evolving/v3)
trajectories on matched (task, seed) pairs. Identifies where SE compressed
work that F0 did the long way.

Per-pair metrics:
  - total tools, turns, wall, input tokens
  - tools-before-first-Write (how much exploration before generation)
  - files read (set), files SE read but F0 didn't, vice versa
  - first 10 tool calls (sequence, for qualitative pattern extraction)
  - read-back count (Reads of /workspace/inputs/ after first Write)

Aggregates across (task, seed) pairs.

Usage:
  python3 scripts/trajectory_diff.py [--out path]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from collections import Counter

ROOT = Path("/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/dsv4")
TASKS = [
    "AdvancedExampleCasedContactThermoElasticWellbore",
    "AdvancedExampleDeviatedElasticWellbore",
    "AdvancedExampleDruckerPrager",
    "AdvancedExampleExtendedDruckerPrager",
    "AdvancedExampleModifiedCamClay",
    "AdvancedExampleViscoDruckerPrager",
    "buckleyLeverettProblem",
    "ExampleDPWellbore",
    "ExampleEDPWellbore",
    "ExampleIsothermalLeakyWell",
    "ExampleMandel",
    "ExampleThermalLeakyWell",
    "ExampleThermoporoelasticConsolidation",
    "kgdExperimentValidation",
    "pknViscosityDominated",
    "TutorialPoroelasticity",
    "TutorialSneddon",
]
SEEDS = ["s1", "s2", "s3"]


def load_trajectory(events_path: Path) -> dict:
    """Walk one events.jsonl and emit a structured summary."""
    n_turns = 0
    tool_calls: list[tuple[str, dict]] = []  # (tool_name, input)
    files_read: list[str] = []  # Read tool calls
    in_tok = 0
    out_tok = 0

    if not events_path.exists():
        return {}

    for line in events_path.open():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") != "assistant":
            continue
        n_turns += 1
        msg = e.get("message", {}) or {}
        u = msg.get("usage", {}) or {}
        in_tok += int(u.get("input_tokens", 0) or 0)
        in_tok += int(u.get("cache_read_input_tokens", 0) or 0)
        out_tok += int(u.get("output_tokens", 0) or 0)
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            name = c.get("name", "")
            inp = c.get("input", {}) or {}
            tool_calls.append((name, inp))
            if name == "Read":
                fp = inp.get("file_path", "")
                if fp:
                    files_read.append(fp)

    # Find first Write
    first_write_idx = next(
        (i for i, (n, _) in enumerate(tool_calls) if n == "Write"),
        None,
    )

    # Tools before first Write
    n_tools_before_write = first_write_idx if first_write_idx is not None else len(tool_calls)

    # Read-backs: Reads of /workspace/inputs/ AFTER first Write
    read_backs = 0
    if first_write_idx is not None:
        for n, inp in tool_calls[first_write_idx + 1 :]:
            if n == "Read":
                fp = inp.get("file_path", "")
                if fp.startswith("/workspace/inputs/"):
                    read_backs += 1

    # First 10 tool calls (compact form)
    first_10 = []
    for n, inp in tool_calls[:10]:
        if n == "Read":
            arg = inp.get("file_path", "")
        elif n == "Glob":
            arg = inp.get("pattern", "")
        elif n == "Grep":
            arg = inp.get("pattern", "")
        elif n == "Write":
            arg = inp.get("file_path", "")
        elif n == "Bash":
            arg = (inp.get("command", "") or "")[:80]
        elif n == "TodoWrite":
            arg = f"({len((inp.get('todos') or []))} todos)"
        else:
            arg = str(inp)[:80]
        first_10.append({"tool": n, "arg": arg})

    return {
        "n_turns": n_turns,
        "n_tools": len(tool_calls),
        "n_tools_before_first_write": n_tools_before_write,
        "n_read_backs": read_backs,
        "files_read": files_read,
        "files_read_unique": sorted(set(files_read)),
        "first_10_calls": first_10,
        "input_tokens_total": in_tok,
        "output_tokens_total": out_tok,
    }


def task_seed_dir(cell: str, seed: str, task: str) -> Path:
    return ROOT / f"autocamp_{cell}" / f"autocamp_{cell}_{seed}" / task


def diff_pair(task: str, seed: str) -> dict:
    """Diff one (task, seed) pair across F0 and SE."""
    f0 = load_trajectory(task_seed_dir("F0", seed, task) / "events.jsonl")
    se = load_trajectory(task_seed_dir("SE", seed, task) / "events.jsonl")
    if not f0 or not se:
        return {}

    f0_files = set(f0["files_read_unique"])
    se_files = set(se["files_read_unique"])

    return {
        "task": task,
        "seed": seed,
        "F0": {
            "turns": f0["n_turns"],
            "tools": f0["n_tools"],
            "tools_before_first_write": f0["n_tools_before_first_write"],
            "read_backs": f0["n_read_backs"],
            "input_tokens": f0["input_tokens_total"],
            "first_10_calls": f0["first_10_calls"],
            "n_files_read_unique": len(f0_files),
        },
        "SE": {
            "turns": se["n_turns"],
            "tools": se["n_tools"],
            "tools_before_first_write": se["n_tools_before_first_write"],
            "read_backs": se["n_read_backs"],
            "input_tokens": se["input_tokens_total"],
            "first_10_calls": se["first_10_calls"],
            "n_files_read_unique": len(se_files),
        },
        "delta": {
            "turns": f0["n_turns"] - se["n_turns"],
            "tools": f0["n_tools"] - se["n_tools"],
            "tools_before_write": f0["n_tools_before_first_write"]
            - se["n_tools_before_first_write"],
            "input_tokens": f0["input_tokens_total"] - se["input_tokens_total"],
            "files_F0_only": sorted(f0_files - se_files),
            "files_SE_only": sorted(se_files - f0_files),
            "files_both_read": sorted(f0_files & se_files),
        },
    }


def aggregate(pairs: list[dict]) -> dict:
    """Roll up across all (task, seed) pairs."""
    if not pairs:
        return {}

    def avg(field_path):
        # field_path like ["F0", "turns"]
        vals = []
        for p in pairs:
            cur = p
            for k in field_path:
                cur = cur.get(k)
                if cur is None:
                    break
            if isinstance(cur, (int, float)):
                vals.append(cur)
        return sum(vals) / len(vals) if vals else 0

    return {
        "n_pairs": len(pairs),
        "F0": {
            "avg_turns": avg(["F0", "turns"]),
            "avg_tools": avg(["F0", "tools"]),
            "avg_tools_before_write": avg(["F0", "tools_before_first_write"]),
            "avg_read_backs": avg(["F0", "read_backs"]),
            "avg_input_tokens": avg(["F0", "input_tokens"]),
            "avg_files_read_unique": avg(["F0", "n_files_read_unique"]),
        },
        "SE": {
            "avg_turns": avg(["SE", "turns"]),
            "avg_tools": avg(["SE", "tools"]),
            "avg_tools_before_write": avg(["SE", "tools_before_first_write"]),
            "avg_read_backs": avg(["SE", "read_backs"]),
            "avg_input_tokens": avg(["SE", "input_tokens"]),
            "avg_files_read_unique": avg(["SE", "n_files_read_unique"]),
        },
        "avg_delta": {
            "turns": avg(["delta", "turns"]),
            "tools": avg(["delta", "tools"]),
            "tools_before_write": avg(["delta", "tools_before_write"]),
            "input_tokens": avg(["delta", "input_tokens"]),
        },
    }


def files_F0_reads_SE_skips(pairs: list[dict]) -> Counter:
    """Across all pairs, which files does F0 read but SE doesn't?

    These are candidate compression targets.
    """
    counter = Counter()
    for p in pairs:
        for f in p.get("delta", {}).get("files_F0_only", []):
            counter[f] += 1
    return counter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(
            "/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/F0_vs_SE_diff.json"
        ),
    )
    args = ap.parse_args()

    pairs = []
    for task in TASKS:
        for seed in SEEDS:
            d = diff_pair(task, seed)
            if d:
                pairs.append(d)

    agg = aggregate(pairs)
    f0_only_files = files_F0_reads_SE_skips(pairs)

    # Top compression candidates
    top_f0_only = f0_only_files.most_common(30)

    # Highest-delta pairs (where SE saved the most turns)
    pairs_sorted = sorted(pairs, key=lambda p: -p["delta"]["turns"])

    report = {
        "aggregate": agg,
        "compression_candidates_top30": [
            {"file": f, "F0_seeds_reading_it_SE_didnt": n}
            for f, n in top_f0_only
        ],
        "pairs_by_largest_savings": [
            {
                "task": p["task"],
                "seed": p["seed"],
                "F0_turns": p["F0"]["turns"],
                "SE_turns": p["SE"]["turns"],
                "delta_turns": p["delta"]["turns"],
                "delta_tools": p["delta"]["tools"],
                "delta_tools_before_write": p["delta"]["tools_before_write"],
                "files_F0_only_count": len(p["delta"]["files_F0_only"]),
            }
            for p in pairs_sorted[:10]
        ],
        "all_pairs": pairs,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    # Print quick summary
    print(f"=== Aggregate over {agg['n_pairs']} pairs ===")
    print(
        f"  F0 avg: {agg['F0']['avg_turns']:.1f} turns, "
        f"{agg['F0']['avg_tools']:.1f} tools, "
        f"{agg['F0']['avg_tools_before_write']:.1f} tools-before-write, "
        f"{agg['F0']['avg_files_read_unique']:.1f} files-read-unique"
    )
    print(
        f"  SE avg: {agg['SE']['avg_turns']:.1f} turns, "
        f"{agg['SE']['avg_tools']:.1f} tools, "
        f"{agg['SE']['avg_tools_before_write']:.1f} tools-before-write, "
        f"{agg['SE']['avg_files_read_unique']:.1f} files-read-unique"
    )
    print(
        f"  delta : -{agg['avg_delta']['turns']:.1f} turns, "
        f"-{agg['avg_delta']['tools']:.1f} tools, "
        f"-{agg['avg_delta']['tools_before_write']:.1f} tools-before-write"
    )
    print()
    print("=== Top 10 largest-savings pairs ===")
    for p in pairs_sorted[:10]:
        print(
            f"  {p['task']:<55} {p['seed']}  "
            f"F0={p['F0']['turns']:>3} SE={p['SE']['turns']:>3} "
            f"Δ={p['delta']['turns']:+d} turns, "
            f"{len(p['delta']['files_F0_only'])} files F0-only"
        )
    print()
    print("=== Top 15 files F0 reads but SE skips ===")
    for f, n in f0_only_files.most_common(15):
        print(f"  {n:>2}× {f}")
    print()
    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()

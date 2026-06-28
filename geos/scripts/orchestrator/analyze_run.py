#!/usr/bin/env python3
"""Quick analysis of an orchestrator run.

Walks each task's claude_stdout.json (stream-json), counts:
- Subagent invocations (Agent tool calls) — by subagent_type.
- Tool-use events by tool name.
- Final XML presence + xmllint pass.
- Wall time and (input,output) tokens summed.

Output: stdout table + JSON to <run_dir>/_analysis.json.

Usage:
    python -m scripts.orchestrator.analyze_run \\
        --run-dir data/eval/orchestrator_dsv4flash/smoke_sneddon_v2
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[2]


def analyze_one_task(task_dir: Path) -> dict:
    out: dict = {
        "task": task_dir.name,
        "subagent_invocations": Counter(),
        "tool_use_counts": Counter(),
        "n_events": 0,
        "n_assistant_messages": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "duration_ms": None,
        "result_subtype": None,
        "xml_files": [],
        "xmllint_pass": None,
        "exit_code": None,
        "elapsed_seconds": None,
    }
    stream_path = task_dir / "claude_stdout.json"
    status_path = task_dir / "status.json"
    inputs_dir = task_dir / "inputs"

    if status_path.exists():
        try:
            st = json.loads(status_path.read_text())
            out["exit_code"] = st.get("exit_code")
            out["elapsed_seconds"] = st.get("elapsed_seconds")
        except json.JSONDecodeError:
            pass

    if stream_path.exists():
        for line in stream_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            out["n_events"] += 1
            t = ev.get("type")
            if t == "assistant":
                out["n_assistant_messages"] += 1
                msg = ev.get("message", {})
                usage = msg.get("usage", {}) or {}
                out["input_tokens"] += usage.get("input_tokens", 0) or 0
                out["output_tokens"] += usage.get("output_tokens", 0) or 0
                out["cache_read_tokens"] += usage.get("cache_read_input_tokens", 0) or 0
                for c in msg.get("content", []):
                    if c.get("type") == "tool_use":
                        name = c.get("name", "?")
                        out["tool_use_counts"][name] += 1
                        if name in ("Task", "Agent"):
                            sub = c.get("input", {}).get("subagent_type", "?")
                            out["subagent_invocations"][sub] += 1
            elif t == "result":
                out["result_subtype"] = ev.get("subtype")
                out["duration_ms"] = ev.get("duration_ms")

    if inputs_dir.exists():
        out["xml_files"] = sorted(p.name for p in inputs_dir.glob("*.xml"))

    if out["xml_files"]:
        # Try xmllint against schema (if available locally)
        schema = "/data/shared/geophysics_agent_data/data/GEOS/src/coreComponents/schema/schema.xsd"
        if Path(schema).exists():
            xml_path = inputs_dir / out["xml_files"][0]
            try:
                r = subprocess.run(
                    ["xmllint", "--schema", schema, "--noout", str(xml_path)],
                    capture_output=True, text=True, timeout=30,
                )
                out["xmllint_pass"] = r.returncode == 0
                if not out["xmllint_pass"]:
                    out["xmllint_stderr"] = r.stderr[:500]
            except (FileNotFoundError, subprocess.TimeoutExpired):
                out["xmllint_pass"] = None

    # Convert Counters to dicts for JSON
    out["subagent_invocations"] = dict(out["subagent_invocations"])
    out["tool_use_counts"] = dict(out["tool_use_counts"])
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", type=Path, required=True)
    args = p.parse_args()

    if not args.run_dir.exists():
        print(f"ERROR: run-dir does not exist: {args.run_dir}")
        return 1

    task_dirs = sorted(d for d in args.run_dir.iterdir() if d.is_dir() and (d / "inputs").exists())
    print(f"Analyzing {len(task_dirs)} task dirs in {args.run_dir}")

    per_task = []
    print(f"\n{'task':<50} {'sub':>4} {'tool':>5} {'in_tok':>8} {'out_tok':>7} {'sec':>5} {'xml':<6} {'xlint':<6}")
    print("-" * 110)
    for td in task_dirs:
        a = analyze_one_task(td)
        per_task.append(a)
        sub_n = sum(a["subagent_invocations"].values())
        tool_n = sum(a["tool_use_counts"].values())
        xml = "Y" if a["xml_files"] else "-"
        xlint = "Y" if a["xmllint_pass"] else ("N" if a["xmllint_pass"] is False else "?")
        print(f"{a['task'][:50]:<50} {sub_n:>4} {tool_n:>5} {a['input_tokens']:>8} {a['output_tokens']:>7} {a['elapsed_seconds'] or '?':>5} {xml:<6} {xlint:<6}")

    # Aggregate
    n = len(per_task)
    sub_total = sum(sum(a["subagent_invocations"].values()) for a in per_task)
    tool_total = sum(sum(a["tool_use_counts"].values()) for a in per_task)
    in_tok_total = sum(a["input_tokens"] for a in per_task)
    out_tok_total = sum(a["output_tokens"] for a in per_task)
    n_xml = sum(1 for a in per_task if a["xml_files"])
    n_xlint = sum(1 for a in per_task if a["xmllint_pass"])

    sub_by_type = Counter()
    tool_by_name = Counter()
    for a in per_task:
        sub_by_type.update(a["subagent_invocations"])
        tool_by_name.update(a["tool_use_counts"])

    summary = {
        "run_dir": str(args.run_dir),
        "n_tasks": n,
        "n_subagent_invocations_total": sub_total,
        "n_tool_uses_total": tool_total,
        "input_tokens_total": in_tok_total,
        "output_tokens_total": out_tok_total,
        "n_with_xml": n_xml,
        "n_xmllint_pass": n_xlint,
        "subagent_invocations_by_type": dict(sub_by_type),
        "tool_use_by_name": dict(tool_by_name),
        "per_task": per_task,
    }

    out_path = args.run_dir / "_analysis.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nWritten: {out_path}")
    print(f"Subagent invocations by type: {dict(sub_by_type)}")
    print(f"Top tools: {dict(sorted(tool_by_name.items(), key=lambda x: -x[1])[:8])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

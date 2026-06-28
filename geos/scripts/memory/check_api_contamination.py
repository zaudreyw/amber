#!/usr/bin/env python3
"""Detect OpenRouter API contamination (402 credit / 403 quota) in run directories.

Scans status.json files for HTTP 402/403 error signatures and reports per-seed
counts. Critical diagnostic to run before interpreting scores — an apparent
"low score" may actually be API-error contamination and should be excluded.

Usage:
  python scripts/memory/check_api_contamination.py <run_root>
  python scripts/memory/check_api_contamination.py data/eval/claude_code_repo3_plugin_m4u/mem_m4u_s3

  # Or batch-scan all memory ablation runs:
  python scripts/memory/check_api_contamination.py --scan-memory-matrix
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ERROR_SIGNATURES = [
    ("HTTP_402_credits", ["402", "Insufficient credits"]),
    ("HTTP_403_key_limit", ["403", "Key limit exceeded"]),
    ("HTTP_429_rate_limit", ["429", "Rate limit"]),
    ("HTTP_401_auth", ["401", "Unauthorized"]),
]


def scan_run(run_dir: Path) -> dict:
    out = {
        "run_dir": str(run_dir),
        "n_tasks": 0,
        "n_clean": 0,
        "errors_by_type": {name: 0 for name, _ in ERROR_SIGNATURES},
        "contaminated_tasks": [],
    }
    if not run_dir.is_dir():
        out["missing"] = True
        return out
    for task_dir in run_dir.iterdir():
        if not task_dir.is_dir():
            continue
        status = task_dir / "status.json"
        if not status.exists():
            continue
        out["n_tasks"] += 1
        try:
            d = json.loads(status.read_text())
        except json.JSONDecodeError:
            continue
        resp = d.get("latest_agent_response", "") or ""
        stderr = " ".join(d.get("latest_stderr", []) or [])
        blob = f"{resp} {stderr}"
        matched = False
        for name, sigs in ERROR_SIGNATURES:
            if all(s in blob for s in sigs):
                out["errors_by_type"][name] += 1
                out["contaminated_tasks"].append(
                    {"task": task_dir.name, "error_type": name}
                )
                matched = True
                break
        if not matched and d.get("process_status") == "success":
            out["n_clean"] += 1
    return out


def verdict(result: dict) -> str:
    n_errors = sum(result["errors_by_type"].values())
    n_total = result["n_tasks"]
    if n_errors == 0:
        return "CLEAN"
    if n_errors >= n_total * 0.5:
        return "EXCLUDE_SEED"
    return "PARTIAL_CONTAMINATION"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path, nargs="?", default=None)
    p.add_argument("--scan-memory-matrix", action="store_true",
                   help="Scan all memory ablation runs in data/eval/")
    args = p.parse_args(argv)

    runs_to_scan: list[Path] = []
    if args.scan_memory_matrix:
        data_eval = Path("/home/matt/sci/repo3/data/eval")
        for agent in ["claude_code_repo3_plugin_m_placebo",
                      "claude_code_repo3_plugin_m1u",
                      "claude_code_repo3_plugin_m1g",
                      "claude_code_repo3_plugin_m3g",
                      "claude_code_repo3_plugin_m4u",
                      "claude_code_repo3_plugin_m4g"]:
            agent_dir = data_eval / agent
            if not agent_dir.exists():
                continue
            for run_dir in agent_dir.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith("mem_"):
                    runs_to_scan.append(run_dir)
    elif args.run_dir:
        runs_to_scan = [args.run_dir]
    else:
        p.error("provide run_dir or --scan-memory-matrix")

    any_bad = False
    print(f"{'Run':70} {'n':>3} {'clean':>5} {'402':>4} {'403':>4} {'429':>4} {'401':>4} Verdict")
    for run_dir in sorted(runs_to_scan):
        r = scan_run(run_dir)
        short = str(run_dir).replace("/home/matt/sci/repo3/data/eval/", "")
        v = verdict(r)
        if v != "CLEAN":
            any_bad = True
        e = r["errors_by_type"]
        print(f"{short:70} {r['n_tasks']:>3} {r['n_clean']:>5} "
              f"{e['HTTP_402_credits']:>4} {e['HTTP_403_key_limit']:>4} "
              f"{e['HTTP_429_rate_limit']:>4} {e['HTTP_401_auth']:>4} "
              f"{v}")
    return 1 if any_bad else 0


if __name__ == "__main__":
    sys.exit(main())

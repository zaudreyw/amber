#!/usr/bin/env python3
"""Dynamic Cheatsheet — Cumulative (DC-CU) batched orchestrator.

Runs a set of test tasks in batches. Each batch uses the CURRENT cheatsheet.
After each batch, calls an LLM curator with (previous cheatsheet, batch
trajectories) to produce the NEXT cheatsheet. Repeats for all batches.

Preserves intra-batch parallelism (6 workers) while applying test-time
learning between batches.

Usage:
  python scripts/memory/dc_cu_orchestrate.py \
      --tasks-json misc/memory_split.json \
      --tasks-key test \
      --agent claude_code_repo3_plugin_memshort_dccu \
      --model deepseek/deepseek-v3.2 \
      --batch-size 6 \
      --out-cheatsheet plugin/cheatsheet_dccu.md \
      --run-name dccu_run1

Prereqs:
  - An agent entry in run_experiment.py with the given name, whose
    cheatsheet_path is `out-cheatsheet` (the mutable file).
  - The mutable cheatsheet file MUST exist before first batch
    (orchestrator seeds it with a minimal procedural opener or empty file).
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "memory"))
from build_cheatsheet import summarize_trajectory, openrouter_chat

SEED_CHEATSHEET = """# GEOS XML Authoring Cheatsheet (dynamic)

*This cheatsheet evolves after each batch of completed tasks. Apply what's relevant; task-specific requirements override.*

## Meta-strategy
- Before writing any XML, run at least one `mcp__geos-rag__search_*` query to find a similar validated example and `Read` that file.
- After writing files, `Read` them back to verify every major section from the specification is present. Do not exit without this verification step.
"""


CURATOR_PROMPT = """# CHEATSHEET CURATOR

You maintain an evolving cheatsheet that helps an AI agent author correct GEOS simulation XML files. GEOS is a multiphysics simulator; tasks provide a natural-language spec and the agent must produce the XML under /workspace/inputs/. The agent has RAG tools over the GEOS source + docs.

You are receiving:
- **PREVIOUS CHEATSHEET**: the cheatsheet as of the last batch.
- **BATCH TRAJECTORIES**: compact summaries of each task the agent just completed, with final TreeSim scores (0-1, 1=perfect match to hidden ground truth) and per-section scores.

Your job: produce the UPDATED cheatsheet after integrating lessons from this batch.

## Principles
- **Keep it concise.** Target 600-1200 tokens total. Cut low-value entries to keep room for new ones.
- **Actionable over descriptive.** Each entry should let a future agent decide faster or avoid a mistake.
- **Transferable over task-specific.** Do NOT reference specific task names, exact coordinates, or specific physics-modes (unless the mode-specific rule is a clear family-wide pattern). Focus on patterns that help across task families.
- **Mark evidence.** Each entry should cite which task(s) or score(s) support it.
- **Merge duplicates.** If a new-batch lesson overlaps with an existing entry, sharpen the existing one instead of duplicating.
- **Preserve good.** If an existing entry is still useful, keep it — do NOT rewrite the whole cheatsheet from scratch.
- **Prune bad.** If an existing entry was contradicted by this batch's evidence, remove or correct it.

## Structure
Use Markdown with these section headers (add/skip as relevant):
- ## Meta-strategy
- ## RAG usage
- ## XML structure
- ## Mesh / Geometry
- ## Solvers
- ## Constitutive / Materials
- ## Field specifications
- ## Common mistakes
- ## Failure modes (agent-behavior, not XML-content)

## Output
Output ONLY the updated cheatsheet in Markdown. No preamble, no commentary. The file will be written verbatim as the next batch's cheatsheet.

---

## PREVIOUS CHEATSHEET

{previous_cheatsheet}

---

## BATCH TRAJECTORIES

{batch_trajectories}

---

Now output the UPDATED cheatsheet.
"""


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def run_batch(run_name: str, agent: str, tasks: list[str], model: str, timeout: int, workers: int, experiments_dir: Path, gt_dir: Path, tmp_parent: Path) -> int:
    """Invoke run_experiment.py on the given tasks. Returns exit code."""
    cmd = [
        "uv", "run", "python", "scripts/run_experiment.py",
        "--run", run_name,
        "--agents", agent,
        "--include", *tasks,
        "--claude-model", model,
        "--workers", str(workers),
        "--timeout", str(timeout),
        "--experiments-dir", str(experiments_dir),
        "--ground-truth-dir", str(gt_dir),
        "--tmp-geos-parent", str(tmp_parent),
    ]
    print(f"\n>>> {' '.join(cmd)}\n")
    p = subprocess.run(cmd, cwd=REPO_ROOT)
    return p.returncode


def build_batch_trajectories_text(run_name: str, agent: str, tasks: list[str], max_chars_per_task: int = 8000) -> str:
    """Read events.jsonl + status.json for each task in the batch, produce compact summary."""
    agent_root = REPO_ROOT / "data" / "eval" / agent / run_name
    parts: list[str] = []
    for t in tasks:
        td = agent_root / t
        events = td / "events.jsonl"
        status = td / "status.json"
        summary_lines = [f"### {t}"]
        if status.exists():
            s = json.loads(status.read_text())
            summary_lines.append(
                f"status: {s.get('status')}  elapsed: {s.get('elapsed_seconds', 0):.0f}s  "
                f"tool_calls: {s.get('total_tool_calls')}  rag_calls: {sum((s.get('rag_tool_counts') or {}).values())}  "
                f"inputs_present: {s.get('workspace_inputs_present')}"
            )
        # Trajectory summary (compact) — score is unknown at curator time (scoring happens after run completes)
        if events.exists():
            traj = summarize_trajectory(events, Path("/nonexistent"), max_chars=max_chars_per_task)
            parts.append("\n".join(summary_lines) + "\n\n" + traj)
        else:
            parts.append("\n".join(summary_lines) + "\n(no events.jsonl)")
    return "\n\n---\n\n".join(parts)


def curate(prev_cheatsheet: str, batch_text: str, max_tokens: int = 1800) -> str:
    prompt = CURATOR_PROMPT.format(
        previous_cheatsheet=prev_cheatsheet or "(empty)",
        batch_trajectories=batch_text,
    )
    reply = openrouter_chat(
        [{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return reply.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-json", type=Path, required=True)
    ap.add_argument("--tasks-key", default="test", help="Key in the JSON (e.g., 'test').")
    ap.add_argument("--agent", required=True)
    ap.add_argument("--model", default="deepseek/deepseek-v3.2")
    ap.add_argument("--batch-size", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out-cheatsheet", type=Path, required=True,
                    help="Mutable cheatsheet file. Must match the agent's cheatsheet_path.")
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--experiments-dir", type=Path,
                    default=Path("/data/shared/geophysics_agent_data/data/eval/experiments"))
    ap.add_argument("--ground-truth-dir", type=Path,
                    default=Path("/data/shared/geophysics_agent_data/data/eval/experiments_gt"))
    ap.add_argument("--tmp-parent", type=Path,
                    default=Path("/data/matt/geos_eval_tmp"))
    ap.add_argument("--seed", action="store_true",
                    help="Initialize cheatsheet with a minimal procedural seed (default: start empty)")
    ap.add_argument("--archive-dir", type=Path, default=None,
                    help="If set, copy each batch's cheatsheet + per-task outputs into this archive dir")
    args = ap.parse_args()

    tasks = json.loads(args.tasks_json.read_text())[args.tasks_key]
    print(f"Orchestrator: {len(tasks)} tasks in {args.tasks_key}; batch={args.batch_size}")

    # Initialize cheatsheet
    args.out_cheatsheet.parent.mkdir(parents=True, exist_ok=True)
    if args.seed:
        args.out_cheatsheet.write_text(SEED_CHEATSHEET)
        print(f"Seeded cheatsheet -> {args.out_cheatsheet}")
    else:
        args.out_cheatsheet.write_text("")  # empty
        print(f"Empty cheatsheet -> {args.out_cheatsheet}")

    archive = args.archive_dir
    if archive:
        archive.mkdir(parents=True, exist_ok=True)

    batches = list(chunk(tasks, args.batch_size))
    for bi, batch in enumerate(batches, 1):
        print(f"\n{'='*70}\n  BATCH {bi}/{len(batches)}: {len(batch)} tasks\n{'='*70}")
        print("Cheatsheet size: {} chars".format(len(args.out_cheatsheet.read_text())))

        t0 = time.time()
        exit_code = run_batch(
            run_name=f"{args.run_name}_b{bi}",
            agent=args.agent,
            tasks=batch,
            model=args.model,
            timeout=args.timeout,
            workers=args.workers,
            experiments_dir=args.experiments_dir,
            gt_dir=args.ground_truth_dir,
            tmp_parent=args.tmp_parent,
        )
        batch_wall = time.time() - t0
        print(f"\nBatch {bi} wall: {batch_wall:.0f}s, exit={exit_code}")

        # Archive the cheatsheet that this batch saw
        if archive:
            (archive / f"cheatsheet_b{bi:02d}_input.md").write_text(args.out_cheatsheet.read_text())

        # Build trajectories text for curator
        print("Building trajectories text for curator...")
        batch_text = build_batch_trajectories_text(
            run_name=f"{args.run_name}_b{bi}",
            agent=args.agent,
            tasks=batch,
            max_chars_per_task=6000,
        )

        # Curate: PREV + batch -> new cheatsheet
        print("Calling curator LLM (deepseek-v3.2 via OpenRouter)...")
        prev = args.out_cheatsheet.read_text() or "(empty)"
        try:
            new_cs = curate(prev, batch_text, max_tokens=1800)
            args.out_cheatsheet.write_text(new_cs + "\n")
            print(f"Updated cheatsheet -> {args.out_cheatsheet} ({len(new_cs)} chars)")
        except Exception as e:
            print(f"CURATOR FAILED: {e}. Keeping previous cheatsheet.")

        if archive:
            (archive / f"cheatsheet_b{bi:02d}_output.md").write_text(args.out_cheatsheet.read_text())
            (archive / f"batch_b{bi:02d}_trajectories.txt").write_text(batch_text)

    print(f"\nDONE: processed {len(batches)} batches. Final cheatsheet: {args.out_cheatsheet}")


if __name__ == "__main__":
    main()

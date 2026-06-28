#!/usr/bin/env python3
"""
Amber MD agent runner + evaluator.

Sends a simulation specification to Claude, which writes all Amber MD
input files (tleap.in, mdin_min.in, mdin_heat.in, mdin_equil.in,
mdin_prod.in) using a write_file tool. Results land in results/<run>/inputs/.
If a ground truth directory is supplied, evaluation metrics are printed
and saved alongside the results.

Usage:
    uv run python run_amber.py --task tasks/example_protein_md --run run1
    uv run python run_amber.py --task tasks/example_protein_md --run run1 \
        --ground-truth tasks/example_protein_md/ground_truth
    uv run python run_amber.py --task tasks/example_protein_md --run run1 \
        --model claude-opus-4-8
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import openai

REPO_ROOT = Path(__file__).parent
AGENTS_MD_PATH = REPO_ROOT / "amber_md" / "run" / "AMBER_AGENTS.md"

WRITE_FILE_TOOL = {
    "name": "write_file",
    "description": (
        "Write a file to the workspace. Use simple relative paths like "
        "'tleap.in', 'mdin_min.in', 'mdin_heat.in', 'mdin_equil.in', "
        "'mdin_prod.in'. Subdirectories are also fine, e.g. 'scripts/prep.sh'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative file path, e.g. 'mdin_min.in' or 'tleap.in'",
            },
            "content": {
                "type": "string",
                "description": "Full content to write to the file",
            },
        },
        "required": ["path", "content"],
    },
}


def _strip_workspace_prefix(path_str: str) -> str:
    for prefix in ["/workspace/inputs/", "/workspace/"]:
        if path_str.startswith(prefix):
            return path_str[len(prefix):]
    return path_str


def _bar(score: float, width: int = 20) -> str:
    filled = int(round(score * width))
    return "█" * filled + "░" * (width - filled)


def run_amber_task(
    task_instructions: str,
    run_name: str,
    ground_truth_dir: Path | None = None,
    model: str = "claude-sonnet-4-6",
) -> dict:
    results_dir = REPO_ROOT / "results" / run_name
    inputs_dir = results_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    if not AGENTS_MD_PATH.exists():
        print(f"ERROR: system prompt not found at {AGENTS_MD_PATH}", file=sys.stderr)
        sys.exit(1)
    system_prompt = AGENTS_MD_PATH.read_text()

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not api_key:
        print("ERROR: set ANTHROPIC_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    use_openrouter = bool(base_url and "openrouter" in base_url)

    started = datetime.now()
    print(f"{'='*60}")
    print(f"  Amber MD run: {run_name}")
    print(f"  Model:        {model}")
    print(f"  Output:       {inputs_dir}")
    print(f"  Backend:      {'OpenRouter' if use_openrouter else base_url or 'api.anthropic.com (default)'}")
    print(f"  Started:      {started.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    user_message = (
        "--- BEGIN SIMULATION SPECIFICATION ---\n"
        f"{task_instructions.strip()}\n"
        "--- END SIMULATION SPECIFICATION ---\n\n"
        "Write all required input files using the write_file tool. "
        "Use simple filenames (tleap.in, mdin_min.in, mdin_heat.in, "
        "mdin_equil.in, mdin_prod.in). Do not use /workspace/inputs/ "
        "prefixes — just the filename."
    )

    files_written: list[str] = []
    step = 0

    if use_openrouter:
        # OpenRouter uses OpenAI-compatible API
        or_client = openai.OpenAI(api_key=api_key, base_url=base_url)
        # OpenRouter requires provider-prefixed model names for non-OpenAI models
        or_model = model if "/" in model else f"anthropic/{model}"

        WRITE_FILE_TOOL_OAI = {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": WRITE_FILE_TOOL["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative file path, e.g. 'mdin_min.in'"},
                        "content": {"type": "string", "description": "Full content to write to the file"},
                    },
                    "required": ["path", "content"],
                },
            },
        }

        messages: list[dict] = [{"role": "user", "content": user_message}]

        while True:
            step += 1
            print(f"[Step {step}] Querying {or_model} via OpenRouter...")

            response = or_client.chat.completions.create(
                model=or_model,
                max_tokens=8192,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                tools=[WRITE_FILE_TOOL_OAI],
                tool_choice="auto",
            )

            choice = response.choices[0]
            msg = choice.message

            if msg.content and msg.content.strip():
                snippet = msg.content.strip()[:300].replace("\n", " ")
                print(f"  [Agent] {snippet}{'...' if len(msg.content.strip()) > 300 else ''}")

            messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

            tool_results = []
            for tc in msg.tool_calls or []:
                if tc.function.name == "write_file":
                    args = json.loads(tc.function.arguments)
                    raw_path = args.get("path", "unknown")
                    clean_path = _strip_workspace_prefix(raw_path)
                    content = args.get("content", "")

                    target = inputs_dir / clean_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content)
                    files_written.append(clean_path)
                    print(f"  [Written] {clean_path}  ({len(content):,} bytes)")

                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": f"Written: {clean_path}",
                    })

            if choice.finish_reason == "stop":
                print("\n[Agent finished]\n")
                break

            if choice.finish_reason == "tool_calls" and tool_results:
                messages.extend(tool_results)
            else:
                print(f"\n[Stopped — reason: {choice.finish_reason}]\n")
                break

            if step >= 30:
                print("\n[Step limit reached — stopping]\n")
                break

    else:
        # Direct Anthropic API
        client = anthropic.Anthropic(api_key=api_key, **({"base_url": base_url} if base_url else {}))

        messages = [{"role": "user", "content": user_message}]

        while True:
            step += 1
            print(f"[Step {step}] Querying {model}...")

            response = client.messages.create(
                model=model,
                max_tokens=8192,
                system=system_prompt,
                tools=[WRITE_FILE_TOOL],
                messages=messages,
            )

            tool_results = []
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    snippet = block.text.strip()[:300].replace("\n", " ")
                    print(f"  [Agent] {snippet}{'...' if len(block.text.strip()) > 300 else ''}")

                elif block.type == "tool_use" and block.name == "write_file":
                    raw_path = block.input.get("path", "unknown")
                    clean_path = _strip_workspace_prefix(raw_path)
                    content = block.input.get("content", "")

                    target = inputs_dir / clean_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content)
                    files_written.append(clean_path)
                    print(f"  [Written] {clean_path}  ({len(content):,} bytes)")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Written: {clean_path}",
                    })

            if response.stop_reason == "end_turn":
                print("\n[Agent finished]\n")
                break

            if response.stop_reason == "tool_use" and tool_results:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                print(f"\n[Stopped — reason: {response.stop_reason}]\n")
                break

            if step >= 30:
                print("\n[Step limit reached — stopping]\n")
                break

    elapsed = (datetime.now() - started).total_seconds()

    print(f"{'='*60}")
    print(f"  Files written: {len(files_written)}")
    for f in files_written:
        size = (inputs_dir / f).stat().st_size
        print(f"    {f}  ({size:,} bytes)")
    print(f"  Elapsed:       {elapsed:.1f}s")
    print(f"{'='*60}\n")

    # --- Evaluation ---
    metrics: dict | None = None

    if ground_truth_dir is not None and ground_truth_dir.exists():
        print(f"Evaluating against ground truth: {ground_truth_dir}\n")
        from amber_md.eval.judge_amber import evaluate_amber_dirs
        result = evaluate_amber_dirs(ground_truth_dir, inputs_dir)

        metrics = {
            "overall_score_01": result.overall_score,
            "overall_score_10": round(result.overall_score * 10, 2),
            "stage_scores": result.stage_scores,
            "file_presence": result.file_presence,
            "details": result.details,
        }

        print(f"  Overall   {_bar(result.overall_score)}  {result.overall_score:.4f} / 1.0"
              f"   ({result.overall_score * 10:.2f} / 10)\n")
        print("  Per-stage breakdown:")
        for stage, score in result.stage_scores.items():
            print(f"    {stage:10s}  {_bar(score)}  {score:.4f}")
        print()
        print("  File presence:")
        for fname, present in result.file_presence.items():
            mark = "✓" if present else "✗"
            print(f"    {mark}  {fname}")
        print()

    elif ground_truth_dir is not None:
        print(f"[No evaluation] Ground truth dir not found: {ground_truth_dir}\n")
    else:
        print("[No evaluation] Pass --ground-truth <dir> to score this run.\n")

    # --- Save summary ---
    summary = {
        "run_name": run_name,
        "model": model,
        "started": started.isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "steps": step,
        "files_written": files_written,
        "inputs_dir": str(inputs_dir),
        "ground_truth_dir": str(ground_truth_dir) if ground_truth_dir else None,
        "metrics": metrics,
    }
    summary_path = results_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"Summary saved → {summary_path}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Amber MD agent runner + evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--task", required=True,
        help="Path to task directory containing instructions.txt",
    )
    parser.add_argument(
        "--run", default="run1",
        help="Run name; results land at results/<run>/ (default: run1)",
    )
    parser.add_argument(
        "--ground-truth", default=None, metavar="DIR",
        help="Ground truth directory for evaluation (optional)",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-6",
        help="Claude model (default: claude-sonnet-4-6)",
    )
    args = parser.parse_args()

    task_dir = Path(args.task)
    instructions_path = task_dir / "instructions.txt"
    if not instructions_path.exists():
        print(f"ERROR: {instructions_path} not found", file=sys.stderr)
        sys.exit(1)

    run_amber_task(
        task_instructions=instructions_path.read_text(),
        run_name=args.run,
        ground_truth_dir=Path(args.ground_truth) if args.ground_truth else None,
        model=args.model,
    )


if __name__ == "__main__":
    main()

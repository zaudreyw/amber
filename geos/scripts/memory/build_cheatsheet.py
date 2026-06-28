#!/usr/bin/env python3
"""Build a frozen cheatsheet from plugin-run4 train-split trajectories.

Pipeline:
  1. Read memory_split.json (train/test task lists).
  2. For each train task, summarize the agent trajectory from events.jsonl
     (thinking blocks, RAG queries, files written) + eval per-section scores.
  3. Call deepseek-v3.2 via OpenRouter once per train task -> 3-5 lessons.
  4. Aggregate all lessons in one more deepseek call -> deduped cheatsheet.
  5. Write to <out>. Default: plugin/cheatsheet.md.

Usage:
  python scripts/memory/build_cheatsheet.py \
      --split misc/memory_split.json \
      --run-dir /data/shared/.../repo3_eval_run4 \
      --scored-dir /data/shared/.../results/repo3_eval_run4/claude_code_repo3_plugin \
      --out plugin/cheatsheet.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_MODEL = "deepseek/deepseek-v3.2"


def openrouter_chat(messages: list[dict], max_tokens: int = 800, temperature: float = 0.3) -> str:
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY not set")
    body = json.dumps({
        "model": OR_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        OR_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/matt-seb-ho/repo3",
            "X-Title": "repo3 memory-cheatsheet generator",
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as e:
            if attempt == 2:
                raise
            print(f"  openrouter retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))


def summarize_trajectory(events_path: Path, eval_path: Path, max_chars: int = 20000) -> str:
    """Compact rendering of events.jsonl + eval: thinking text, RAG queries,
    files written, per-section scores. Truncates at max_chars.
    """
    lines_out: list[str] = []
    task_name = events_path.parent.name
    lines_out.append(f"TASK: {task_name}")

    if eval_path.exists():
        ev = json.loads(eval_path.read_text())
        lines_out.append(f"FINAL_TREESIM: {ev.get('treesim', '?'):.3f}")
        sections = ev.get("treesim_section_scores", {})
        if sections:
            lo = sorted(sections.items(), key=lambda x: x[1])[:4]
            hi = sorted(sections.items(), key=lambda x: -x[1])[:4]
            lines_out.append("SECTION_SCORES_LOW:  " + ", ".join(f"{k}={v:.2f}" for k, v in lo))
            lines_out.append("SECTION_SCORES_HIGH: " + ", ".join(f"{k}={v:.2f}" for k, v in hi))

    lines_out.append("\n=== TRAJECTORY ===")

    if not events_path.exists():
        lines_out.append("(no events.jsonl)")
        return "\n".join(lines_out)[:max_chars]

    turn = 0
    for raw in events_path.read_text().splitlines():
        if not raw.strip():
            continue
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        turn += 1
        msg = ev.get("message", {})
        for block in msg.get("content", []):
            btype = block.get("type")
            if btype == "thinking":
                txt = block.get("thinking", "").strip()
                if txt:
                    lines_out.append(f"\n[T{turn} thinking]\n{txt[:1200]}")
            elif btype == "text":
                txt = block.get("text", "").strip()
                if txt:
                    lines_out.append(f"\n[T{turn} text]\n{txt[:800]}")
            elif btype == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {}) or {}
                if "mcp__geos-rag" in name:
                    q = inp.get("query", "") or inp.get("question", "")
                    lines_out.append(f"[T{turn} RAG {name.split('__')[-1]}] q={q[:200]!r}")
                elif name in ("Write", "Edit"):
                    fp = inp.get("file_path", "")
                    lines_out.append(f"[T{turn} {name}] path={fp}")
                elif name in ("Read", "Glob", "Grep", "Bash"):
                    # Summarize briefly
                    summary = (
                        inp.get("file_path")
                        or inp.get("pattern")
                        or inp.get("command", "")[:100]
                    )
                    lines_out.append(f"[T{turn} {name}] {summary!s:.100}")
    full = "\n".join(lines_out)
    if len(full) > max_chars:
        # Keep first 30% and last 60% (cuts middle)
        head = int(max_chars * 0.3)
        tail = int(max_chars * 0.6)
        full = full[:head] + "\n...[TRUNCATED MIDDLE]...\n" + full[-tail:]
    return full


LESSON_PROMPT = """You are analyzing a trajectory of an AI coding agent that authored a GEOS
simulation XML file. GEOS is a multiphysics simulator; tasks require the
agent to produce a valid XML in `inputs/` that matches a hidden reference.
The agent had access to RAG tools (search_navigator, search_schema,
search_technical) over GEOS documentation and example XMLs.

Below is a compact trajectory + the final TreeSim score (1.0 = perfect
match to ground-truth XML). Per-section scores indicate which XML blocks
(Solvers, Mesh, Events, Constitutive, ...) were most right/wrong.

**Your job:** extract 3-5 SHORT, TRANSFERABLE lessons that would help a
FUTURE agent working on a DIFFERENT GEOS task do better. Lessons must be:
- ACTIONABLE ("when doing X, prefer Y because Z"), not generic advice
- TASK-INDEPENDENT — no task names, no task-specific XML values
- CONCISE — one sentence each
- GROUNDED in this trajectory (reference what the agent did/didn't do)

If the score is high, focus on successful patterns to replicate.
If the score is low, focus on mistakes to avoid.

Output format:
```
LESSON 1: <one sentence>
LESSON 2: <one sentence>
LESSON 3: <one sentence>
LESSON 4 (optional): <one sentence>
LESSON 5 (optional): <one sentence>
```

Trajectory:
---
{trajectory}
---
"""


AGGREGATE_PROMPT = """You are assembling a frozen, pre-learned CHEATSHEET for an AI agent that
authors GEOS simulation XML files. The cheatsheet will be prepended to the
agent's system prompt on every future task.

Below are raw lessons extracted from {n_tasks} past agent trajectories
(paired with their TreeSim scores). Produce a SHORT, CLEAN, DEDUPED
cheatsheet at most ~700 tokens in Markdown.

Requirements:
- Group lessons by theme (e.g., "RAG usage", "XML structure", "Solver
  configuration", "Mesh/Geometry", "Events", "Common mistakes"). Use
  ## headers for themes.
- Merge duplicates and near-duplicates; keep the sharpest phrasing.
- Prune lessons that are already obvious from standard GEOS documentation
  (e.g., "XML must be well-formed" is trivial and should be dropped).
- Keep only lessons that are actionable in the middle of a trajectory,
  not retrospective analyses.
- Open with a 2-line purpose statement: "This cheatsheet distills
  patterns that helped past CC+plugin runs on GEOS XML tasks. Apply
  these when relevant; ignore when they conflict with the user's
  task-specific requirements."

Raw lessons:
---
{lessons}
---
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True,
                    help="Root of per-task trajectories (e.g., .../repo3_eval_run4)")
    ap.add_argument("--scored-dir", type=Path, required=True,
                    help="Dir with <task>_eval.json files")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--lessons-out", type=Path, default=None,
                    help="Optional: write per-task raw lessons for debugging")
    ap.add_argument("--max-tasks", type=int, default=None,
                    help="Smoketest: cap number of train tasks processed")
    args = ap.parse_args()

    split = json.loads(args.split.read_text())
    train = split["train"][: args.max_tasks] if args.max_tasks else split["train"]
    print(f"Extracting lessons from {len(train)} train tasks via OpenRouter deepseek-v3.2")

    all_lessons: list[tuple[str, float, str]] = []  # (task, score, lessons_text)
    for i, task in enumerate(train, 1):
        events = args.run_dir / task / "events.jsonl"
        evalf = args.scored_dir / f"{task}_eval.json"
        if not events.exists():
            print(f"  [{i}/{len(train)}] {task}: NO events.jsonl, skipping")
            continue
        summary = summarize_trajectory(events, evalf)
        try:
            score = split["train_treesim_ref"].get(task, 0.0)
        except AttributeError:
            score = 0.0
        prompt = LESSON_PROMPT.format(trajectory=summary)
        t0 = time.time()
        try:
            reply = openrouter_chat(
                [{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.2,
            )
        except Exception as e:
            print(f"  [{i}/{len(train)}] {task}: FAILED {e}")
            continue
        dt = time.time() - t0
        print(f"  [{i}/{len(train)}] {task} (score={score:.3f}) -> {len(reply)} chars in {dt:.1f}s")
        all_lessons.append((task, score, reply.strip()))

    if args.lessons_out:
        args.lessons_out.parent.mkdir(parents=True, exist_ok=True)
        with args.lessons_out.open("w") as f:
            for task, score, lessons in all_lessons:
                f.write(f"### {task}  (treesim={score:.3f})\n{lessons}\n\n")
        print(f"\nRaw lessons -> {args.lessons_out}")

    # Aggregate
    lessons_concat = "\n\n".join(
        f"[{task} treesim={score:.2f}]\n{lessons}"
        for task, score, lessons in all_lessons
    )
    agg = AGGREGATE_PROMPT.format(n_tasks=len(all_lessons), lessons=lessons_concat)
    print(f"\nAggregating {len(all_lessons)} lesson-sets into cheatsheet...")
    cheatsheet = openrouter_chat(
        [{"role": "user", "content": agg}],
        max_tokens=1200,
        temperature=0.3,
    ).strip()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# GEOS XML Authoring Cheatsheet\n\n"
        f"*Generated {time.strftime('%Y-%m-%d')} from {len(all_lessons)} "
        f"train-split trajectories of repo3_eval_run4 (plugin + deepseek-v3.2).*\n\n"
    )
    args.out.write_text(header + cheatsheet + "\n")
    print(f"\nCheatsheet -> {args.out} ({len(cheatsheet)} chars)")


if __name__ == "__main__":
    main()

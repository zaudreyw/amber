#!/usr/bin/env python3
"""Take the F0 vs SE diff JSON and ask DeepSeek to extract compression
patterns from the top-N highest-savings (task, seed) pairs.

Output: a markdown writeup at docs/2026-05-02_F0_vs_SE_trajectory_diff.md.

Cheap: ~10K input × N pairs to DeepSeek's standard endpoint, well under $1.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

DIFF_JSON = Path(
    "/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/F0_vs_SE_diff.json"
)
OUT_DOC = Path("/home/matt/sci/repo3/docs/2026-05-02_F0_vs_SE_trajectory_diff.md")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"  # the cheap general-purpose model

V3_CONTEXT = """
The SE cell has access to a `plugin_evolving/v3/` plugin with these assets:
  - PRIMER.md (custom GEOS primer)
  - skills/copy-dependencies.md  (when to copy related files like tables/, .geos)
  - skills/triaxial-driver-setup.md  (recipe for triaxial driver tasks)
  - agents/dependency-copier.md  (subagent that copies dependent files)
  - memory/cheatsheet.md  (m1u-distilled GEOS XML cheatsheet)
  - hooks/verify_outputs.py  (Stop hook with parse-check)
  - mcp_servers: xmllint  (proactive XML validation)

The F0 cell has none of these — just AGENTS.md (post-strip, harness contract)
+ the 5-line GEOS_PRIMER_contract.md.
""".strip()


SYSTEM_PROMPT = """You are analyzing differences between two agent trajectories
on the same GEOS XML authoring task. F0 is a no-plugin baseline; SE has a custom
plugin (skills, memory, hooks) that compresses common patterns.

Your job: given the first 10 tool calls of each agent on a single
(task, seed) pair, identify what compression pattern SE used to skip work
that F0 had to do explicitly. Be concise — 2-4 short bullets per pair.

Focus on:
  - What did F0 do (e.g. multi-step search/grep) that SE replaced (e.g. went
    directly to a known file)?
  - Which SE plugin asset is doing the work (cheatsheet? skill? hook?)?
  - Is the pattern generalizable to other tasks, or task-specific?

Be honest: if the SE compression isn't obvious from the call sequences,
say so. Don't invent patterns.
""".strip()


def call_deepseek(messages: list[dict]) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        # Try .env load
        env_path = Path("/home/matt/sci/repo3/.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DEEPSEEK_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        sys.exit("DEEPSEEK_API_KEY not set")

    resp = requests.post(
        DEEPSEEK_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "temperature": 0.2},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def fmt_pair_for_llm(pair: dict) -> str:
    """Render one (task, seed) pair compactly for the LLM."""
    f0_calls = "\n".join(
        f"  {i+1:>2}. {c['tool']:<12} {c['arg'][:120]}"
        for i, c in enumerate(pair["F0"]["first_10_calls"])
    )
    se_calls = "\n".join(
        f"  {i+1:>2}. {c['tool']:<12} {c['arg'][:120]}"
        for i, c in enumerate(pair["SE"]["first_10_calls"])
    )
    f0_only = pair["delta"]["files_F0_only"][:8]
    f0_only_txt = "\n".join(f"  - {f}" for f in f0_only) or "  (none in top)"
    return f"""TASK: {pair["task"]}  SEED: {pair["seed"]}
F0 (no-plugin): {pair["F0"]["turns"]} turns total, {pair["F0"]["tools"]} tool calls, {pair["F0"]["tools_before_first_write"]} tools before first Write
SE (plugin v3): {pair["SE"]["turns"]} turns total, {pair["SE"]["tools"]} tool calls, {pair["SE"]["tools_before_first_write"]} tools before first Write
SAVINGS: F0 - SE = {pair["delta"]["turns"]} turns, {pair["delta"]["tools"]} tools.

F0's first 10 tool calls:
{f0_calls}

SE's first 10 tool calls:
{se_calls}

Files F0 read that SE didn't (top 8):
{f0_only_txt}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-n", type=int, default=5, help="how many top-savings pairs to analyze")
    ap.add_argument("--diff", type=Path, default=DIFF_JSON)
    ap.add_argument("--out", type=Path, default=OUT_DOC)
    args = ap.parse_args()

    diff = json.loads(args.diff.read_text())
    agg = diff["aggregate"]
    pairs = diff["all_pairs"]

    pairs_sorted = sorted(pairs, key=lambda p: -p["delta"]["turns"])
    top = pairs_sorted[: args.top_n]

    # Build the LLM call: one big batch covering top-N pairs
    block = "\n\n---\n\n".join(fmt_pair_for_llm(p) for p in top)
    user_msg = f"""{V3_CONTEXT}

I will give you {len(top)} (task, seed) pairs where SE saved the most turns vs F0.
For each pair, identify the compression pattern: what did F0 do that SE skipped, and
which SE plugin asset is responsible.

After analyzing all pairs, write a final 'Cross-pair patterns' section listing
the 2-4 patterns that recurred across multiple pairs and what skill/memory/tool
in v3 (or a candidate v4) could absorb each.

Markdown output. No preamble.

{block}
"""

    print(f"Calling DeepSeek with {len(top)} pairs (~{len(user_msg)} chars input)...")
    response = call_deepseek(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
    )
    print("Got response, writing markdown.")

    # Aggregate stats for the doc header
    f0a = agg["F0"]
    sea = agg["SE"]
    da = agg["avg_delta"]

    md = f"""# F0 vs SE trajectory diff

*Generated 2026-05-02 from `{args.diff}` via DeepSeek summary of top
{args.top_n} highest-savings (task, seed) pairs.*

## Aggregate ({agg["n_pairs"]} pairs)

| metric | F0 (no plugin) | SE (plugin v3) | Δ (F0−SE) |
|---|---:|---:|---:|
| avg turns | {f0a["avg_turns"]:.1f} | {sea["avg_turns"]:.1f} | **+{da["turns"]:.1f}** |
| avg tools | {f0a["avg_tools"]:.1f} | {sea["avg_tools"]:.1f} | **+{da["tools"]:.1f}** |
| avg tools-before-first-Write | {f0a["avg_tools_before_write"]:.1f} | {sea["avg_tools_before_write"]:.1f} | **+{da["tools_before_write"]:.1f}** |
| avg unique files read | {f0a["avg_files_read_unique"]:.1f} | {sea["avg_files_read_unique"]:.1f} | +{f0a["avg_files_read_unique"] - sea["avg_files_read_unique"]:.1f} |
| avg input tokens | {f0a["avg_input_tokens"]/1e6:.2f}M | {sea["avg_input_tokens"]/1e6:.2f}M | +{(f0a["avg_input_tokens"] - sea["avg_input_tokens"])/1e6:.2f}M |
| avg read-backs | {f0a["avg_read_backs"]:.1f} | {sea["avg_read_backs"]:.1f} | +{f0a["avg_read_backs"] - sea["avg_read_backs"]:.1f} |

**Most of the savings come from "tools before first Write"** — the
exploration phase. F0 averages {f0a['avg_tools_before_write']:.0f} search/read calls before
emitting its first XML; SE averages {sea['avg_tools_before_write']:.0f}. SE jumps to canonical
files faster.

## Top {args.top_n} highest-savings (task, seed) pairs

| task | seed | F0 turns | SE turns | Δ |
|---|:-:|---:|---:|---:|
"""
    for p in top:
        md += f"| {p['task']} | {p['seed']} | {p['F0']['turns']} | {p['SE']['turns']} | +{p['delta']['turns']} |\n"

    md += f"""
## Top files F0 reads but SE skips

These are the files that appear in F0 trajectories but not in matched SE
trajectories — candidate compression targets.

| reads | file |
|---:|---|
"""
    for entry in diff["compression_candidates_top30"][:20]:
        md += f"| {entry['F0_seeds_reading_it_SE_didnt']}× | `{entry['file']}` |\n"

    md += f"""
## Per-pair pattern analysis (DeepSeek)

{response}

## Source

- Diff JSON: `{args.diff}`
- Script: `scripts/trajectory_diff.py`
- Summary script: `scripts/trajectory_diff_summarize.py`
- v3 plugin assets: `/home/matt/sci/repo3/plugin_evolving/v3/`
"""

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md)
    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()

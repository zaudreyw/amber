#!/usr/bin/env python3
"""Take the trajectory patterns JSON and ask DeepSeek to synthesize
concrete v4 plugin artifacts: cheatsheet content, lookup tables, skill
recipes, and "don't do this" warnings.

Output: docs/2026-05-02_v4_design_proposal.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

PATTERNS_JSON = Path(
    "/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/patterns.json"
)
OUT_DOC = Path("/home/matt/sci/repo3/docs/2026-05-02_v4_design_proposal.md")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"


SYSTEM_PROMPT = """You are designing v4 of a self-evolving plugin for an
LLM agent that authors GEOS XML input files. v3 already saved ~12 turns
per task vs the no-plugin baseline (F0). Your job: design v4 content
that captures the patterns identified by trajectory mining, to push
F0's 73 tools-before-first-Write closer to ~30 (a target ~50%
reduction).

Be concrete. Output should be ready-to-paste content — actual cheatsheet
entries, actual lookup tables, actual skill files. Don't write meta-prose
about what to do; write the thing itself.

Write under tight token budget. The cheatsheet sits in the system prompt
on every task, so each line of it costs ~4 input tokens × every task ×
every seed. Be ruthless about value-per-token.
""".strip()


def call_deepseek(messages: list[dict]) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
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
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def fmt_canonical(d: dict) -> str:
    """Render task_canonical_files compactly."""
    lines = []
    for task, top in d.items():
        if not top:
            lines.append(f"  {task}: (no canonical found)")
            continue
        files = [t["file"].replace("/geos_lib/inputFiles/", "") for t in top[:5]]
        lines.append(f"  {task}:")
        for f, t in zip(files, top[:5]):
            lines.append(f"    {f}  ({t['n_distinct_runs']} runs)")
    return "\n".join(lines)


def fmt_hpp_lookup(entries: list[dict]) -> str:
    lines = []
    for e in entries:
        hdr = e["header"].replace("/geos_lib/src/coreComponents/", "")
        prec = "; ".join(p["pattern"] for p in e["preceding_grep_patterns"][:3] if p["pattern"])
        lines.append(f"  {e['total_reads']}× {hdr}  (greps: {prec})")
    return "\n".join(lines)


def fmt_dead(entries: list) -> str:
    return "\n".join(f"  {n}× {pat[:70]}" for pat, n in entries[:15])


def fmt_cross_task(entries: list[dict]) -> str:
    return "\n".join(f"  {e['pattern']}: {e['n_tasks']} tasks, {e['n_uses']} uses" for e in entries[:15])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patterns", type=Path, default=PATTERNS_JSON)
    ap.add_argument("--out", type=Path, default=OUT_DOC)
    args = ap.parse_args()

    p = json.loads(args.patterns.read_text())

    user_msg = f"""Trajectory mining results from a 17-task GEOS XML benchmark
across 5 cells (F0 no-plugin, F2 SR+memory, F4 xmllint+memory, F6 SR+xmllint,
SE plugin v3) × 3 seeds.

## Per-task canonical files (read in last 10 calls before first Write, in ≥3 successful runs)
{fmt_canonical(p["task_canonical_files"])}

## Top constitutive C++ headers read, with the Grep pattern that preceded each
{fmt_hpp_lookup(p["constitutive_name_to_header"][:15])}

## Cross-task Grep patterns (used in 3+ tasks, followed by a productive Read)
{fmt_cross_task(p["cross_task_grep_patterns"])}

## Top dead Grep patterns in F0 (NOT followed by a Read in next 5 calls — wasted)
{fmt_dead(p["dead_search_patterns"]["grep_dead_top20"])}

## Top live Grep patterns in F0 (followed by a productive Read)
{fmt_dead(p["dead_search_patterns"]["grep_live_top20"])}

---

Design v4 plugin artifacts. Produce these sections, in this order, as
ready-to-paste markdown:

### 1. cheatsheet.md (replaces v3's m1u-distilled cheatsheet)
A concise GEOS authoring cheatsheet. Must include:
  - **Task → canonical-example mapping** for the 17 tasks. Pull the
    top 1-3 most-canonical XML files per task. Format as a compact table
    (task name → 1-3 paths under /geos_lib/inputFiles/). Be terse.
  - **Constitutive class → header file** mapping for the top ~10 most-read
    headers, so the agent doesn't have to Grep-then-Read to find attribute
    names. Compact table.
  - **Common solver names** the agent should grep for (SinglePhasePoromechanics,
    SolidMechanicsLagrangianFEM, etc) — list ~10 with their physics meaning.
  - **"Don't grep for these"** anti-patterns from the dead-pattern list:
    overly-vague terms like 'class', 'public:', single-letter terms.

### 2. skills/ — recipe files for high-frequency task families
Look at canonical files. Identify task families that share canonical files
(e.g. multiple "*PoroDruckerPrager*Wellbore" files → "drucker-prager-wellbore"
family; multiple "kgd*" files → "kgd-fracture" family). For each family,
write a one-page skill describing what to do.

Don't write more than 4 skills. The skill should be: when to invoke,
which canonical XMLs to Read, what attributes/sections to copy verbatim,
what to adapt.

### 3. memory/anti-patterns.md
The 5-10 things F0 wastes time on. One line each. Format:
  - "Don't <action>; instead <better-action>"

### 4. Estimated savings
Estimate how many tools/turns this v4 set saves vs F0, and which v3 cells
might further benefit. Be honest — if a section won't save much, say so.
"""

    print(f"Calling DeepSeek with ~{len(user_msg)} chars input...")
    response = call_deepseek(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
    )
    print("Got response, writing markdown.")

    md = f"""# v4 plugin design proposal — derived from trajectory patterns

*Generated 2026-05-02 from `{args.patterns}` via DeepSeek synthesis.
Empirical patterns mined from 17 tasks × 5 cells × 3 seeds = 255 trajectories.*

## How this was generated

`scripts/trajectory_patterns.py` mines the trajectories for:
- Per-task canonical files (read in the last 10 calls before first Write, in ≥3 successful runs)
- Constitutive C++ headers and the Grep patterns that lead to them
- Cross-task recurring Grep patterns
- Dead patterns (Grep with no follow-up Read)

`scripts/trajectory_patterns_synthesize.py` (this script) feeds the
mining results to DeepSeek with a focused design prompt. Output below.

---

{response}

---

## Source

- Patterns JSON: `{args.patterns}`
- Mining script: `scripts/trajectory_patterns.py`
- Synthesis script: `scripts/trajectory_patterns_synthesize.py`
- Trajectory diff (sibling analysis): `docs/2026-05-02_F0_vs_SE_trajectory_diff.md`
- Main campaign writeup: `docs/2026-05-02_autonomous-campaign-results.md`
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md)
    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()

---
id: D-002
title: "Extended-session plan: post-advisor-brief, paper-quality sprint"
date: 2026-04-20
dag_nodes: [E03, E06, I06, I10, I11]
links:
  supersedes: []
  related_to: [D-001]
---

# D-002 — Extended session plan (post-deadline)

User is sleeping; no more deadlines for this session. Goal: maximize
paper quality. Advisor brief (XN-006) is already good for tomorrow's
check-in. Below is the plan for what to do with the remaining compute
time.

## Current state as of this decision

| Result | Verdict |
|---|---|
| Plugin beats no-plugin on deepseek (+0.178) | POSITIVE, solid |
| Plugin beats no-plugin on minimax (+0.102) | POSITIVE, cross-model |
| Long cheatsheet memory (E04, -0.322) | NEGATIVE |
| Short cheatsheet memory (E05, -0.270) | NEGATIVE |
| Filetree injection (E07, -0.227) | NEGATIVE |
| Plugin mechanism (XN-008: semantic/schema/variant disambiguation) | CHARACTERIZED |
| Primer-minimal (E08) | RUNNING |
| Memory-in-workspace-file (E09) | QUEUED |

Hypotheses remaining live:
- **H1.** Memory works IF delivered via a non-system-prompt channel (file, MCP tool).
- **H2.** Memory needs to be more concrete (example-mapping) rather than abstract rules.
- **H3.** Primer content barely matters; RAG does all the work.
- **H4.** Multi-seed would tighten +0.178 / +0.102 claims.
- **H5.** Plugin attribution (skill vs MCP) matters for where to invest.
- **H6.** Hard-mode eval set would let us show harder-to-solve tasks
  where adaptations have more room to shine.

## Prioritization (~decreasing paper-value × ~increasing effort)

### Tier 1 — do this session
1. **E08 primer-minimal** (running; ~20 min more) — tests H3.
2. **E09 memory-as-workspace-file** (ready to launch) — tests H1.
3. **Multi-seed E03 replication** (deepseek, 2-3 more seeds) — firms
   H4. Cheap; ~30 min per seed.
4. **Plugin attribution (E10):** skill-only plugin variant on 17 test
   (no MCP wiring). Tests H5. Cheap; 1 run.

### Tier 2 — do after Tier 1 if still have budget
5. **G-Memory-lite: example-based memory as MCP tool.** Port lite
   version from geos_agent/modules/memory/gmemory/. Frozen-at-test-time
   to preserve parallelism. Tests H2 + H1 simultaneously.
6. **Hard-mode eval set generation.** Find mine_examples_v3 design;
   generate "hard" task variants that remove inferable values from the
   spec. Don't run experiments yet — just prepare the task set.
7. **Opus cross-model paired** (if OpenRouter API key has room) — 3rd
   model generalization claim. Expensive (~$200 for 17 tasks
   plugin+no-plugin); defer unless clear budget.

### Tier 3 — explicitly deferred
- Gemma-4-31B cross-model: low priority.
- Full G-Memory port with graph/FINCH: too heavy for remaining time.
- Full hard-mode eval run: defer to next session.

## Detailed plan for Tier 1+2

### Step 1: E08 (primer-minimal) — running
Expected finish: ~30 min from launch at ~13:55. Done by ~14:25.
Score immediately, compare to E03 on the 17-task test subset.

**Pre-registered interpretation:**
- If E08 paired mean > 0.80: primer content barely matters. Simplify.
- If E08 paired mean 0.70-0.80: primer content helps but plugin does
  most of the work.
- If E08 paired mean < 0.70: primer content is a real load-bearing
  part of the design; preserve or carefully redesign.

### Step 2: E09 (memory-as-workspace-file)
Launch after E08 completes. Uses `cheatsheet_abstract.md` (pitfalls +
shortcuts, ~550 tokens) copied to `/workspace/CHEATSHEET.md`; system
prompt contains only a 2-line pointer. Same 17 test tasks, workers=12.

**Pre-registered interpretation:**
- If E09 mean > 0.83 (>= plugin-only): memory is NOT dead; delivery
  channel matters. Unlocks G-Memory-lite direction.
- If E09 mean 0.70-0.83: memory-via-file has some effect but not
  decisive. Probably try to iterate on content.
- If E09 mean < 0.70: memory-via-file also fails. Content itself is
  the issue regardless of channel. Memory direction effectively dead
  for this model.

### Step 3: Multi-seed E03 replication
Re-run plugin+no-plugin on 36 tasks with deepseek, 2 more seeds.
Get std on the +0.178 delta. 2×36=72 task-runs, workers=12, ~45 min
wall. Cost: ~$35-50.

### Step 4: Plugin attribution (E10 skill-only)
Make a `claude_code_skillonly` agent: plugin-loaded (skill prompt
present) but MCP server disabled (no `mcp__geos-rag__*` tools). This
tests whether the skill prompt alone produces the win, or whether the
RAG MCP tools are what matters.

Expected: if skill-only scores near plugin-only (0.83), skill prompt
was doing heavy lifting. If skill-only is near no-plugin (0.65), RAG
tools are the driver. Most likely intermediate.

### Step 5: G-Memory-lite (if Step 2 showed signal)
Design:
- Build a frozen example-memory: `{ task_keyword: [reference_xml_paths] }`
  derived from 18 train trajectories' most-read files.
- Expose as an MCP tool: `memory_lookup(task_topic) -> list[str]`.
- Agent calls it early; gets concrete file paths.

Alternative if Step 2 failed: try trajectory-based memory. Agent-written
post-task summaries stored with embeddings; future tasks retrieve
similar past trajectories.

### Step 6: Hard-mode eval prep
Look at `mine_examples2.py` and user's brief on difficulty tiers. Draft
a spec for hard-mode: which config values to withhold (per difficulty
category: software_default, standard_numerics, domain_inferrable,
problem_defining). Produce a hard-mode task set (not run yet).

## Budget + guardrails

- **Cost cap:** Stop spending if total session cost exceeds ~$200.
  Current spend: ~$120 (E04-E07 ~$60 + E06 minimax $58).
- **Rate-limit check:** Monitor deepseek/OpenRouter 429s. 12 workers
  showed no issue; 24 (2 concurrent runs) may trigger. If so, step back.
- **Checkpoint:** After each tier, update `checkpoint.md` + hub SoK.

## Exit conditions (when to stop and sleep)

- Tier 1 complete, Tier 2 in progress or complete → good stopping point
  for the user to wake up to.
- Any experiment showing evidence of corruption (e.g., multiple
  redacted_thinking in a row without clear cause) → halt immediately,
  log the finding, skip to writeup.
- Budget cap hit.

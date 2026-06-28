---
id: D-001
title: "Memory-on-top-of-plugin experiment design (I10)"
date: 2026-04-20
dag_nodes: [I06, I10]
links:
  derived_from: [E03]
  related_to: [I06, I07]
---

# D-001 — Memory-on-top-of-plugin design

## Context

E03 resolved positively: plugin wins over no-plugin by +0.175 TreeSim on
deepseek-v3.2 at model parity. The next research contribution is to show
that **adaptations stack** — adding a memory/cheatsheet on top of the
plugin yields further gains. This is also the user's highest-priority
intervention direction per `misc/geophys_todo.md`.

## Design choices

### Memory form: frozen pre-learned textual cheatsheet
- **Why frozen, not continual.** User explicitly favors this for
  parallelism: continual memory means task n must finish before task n+1
  can run. Frozen memory is produced once on a train subset, then held
  constant across the test evaluation.
- **Why cheatsheet (flat text), not Mem0/BoT/GMemory.** Fastest to
  implement; matches the existing system-prompt injection path for the
  GEOS primer; comparable to prior work (cheatsheet is the baseline
  every memory paper ablates against). If cheatsheet shows lift, we can
  justify upgrading to a richer memory module in future work.

### Memory source: plugin trajectories from `repo3_eval_run4`
- Use the existing plugin+deepseek trajectories we just scored.
- **Split: 18 train / 18 test** from the 36-task set (see split below).
- **No task appears in both train and test** — prevents evaluation
  contamination.

### Lesson extraction protocol
For each train task we have:
- `events.jsonl` — full CC trajectory (thinking blocks, tool calls, file
  writes)
- `inputs/*.xml` — the agent-produced XML
- The TreeSim score + per-section scores (from `*_eval.json`)

Extraction prompt (to an LLM — use deepseek-v3.2 via OpenRouter to keep
cost low): given trajectory + score + per-section breakdown, extract
3-5 short "lessons" in the form "when doing X, prefer Y because Z."
Focus on cross-task-transferable patterns:
- Common RAG-tool usage patterns that led to high scores
- Common XML structural decisions that the agent got right (or wrong)
- Which GEOS modules/tags tend to co-occur
- Anti-patterns (what the agent did that led to low scores)

Aggregate all per-task lessons into a single cheatsheet via a second
LLM call: de-duplicate, cluster by theme, produce a ~500-800 token
doc. Cap length to keep system-prompt cost low.

### Injection: `--append-system-prompt` alongside `AGENTS.md` + primer
The existing runner already concatenates `AGENTS.md` + GEOS primer and
passes as `--append-system-prompt`. Add the cheatsheet as a third
section. No agent-side changes required. New agent key:
`claude_code_repo3_plugin_memcheatsheet`.

### Evaluation: run on the 18 test tasks, compare paired
- Condition A (baseline, already scored): plugin on 18 test tasks from
  `repo3_eval_run4`
- Condition B (new): plugin+cheatsheet on same 18 test tasks — new run
- Metric: paired TreeSim delta across 18 tasks; report mean, per-task
  wins/losses, and pass >=0.7 rate.

### Split choice (18/18)
Split mechanism: sort the 36 tasks by TreeSim score in E03 (plugin+ds),
then assign odd-index to train, even-index to test. This ensures both
subsets cover the full difficulty range — avoids the failure mode where
memory is trained on easy tasks and tested on hard tasks (or vice versa).

Written to `misc/memory_split.json`.

### Fairness / fairness checks
- Same model across A and B (deepseek-v3.2).
- Same timeout (20 min).
- Same containerization and contamination setup.
- `n_params` not applicable (same model, same harness).
- Per-task `eval_metadata.json` provenance cross-check before reporting.

## What can go wrong (pre-registration)

- **Regression to the mean:** E03 test-set scores may drop naturally;
  important to compare A vs B on same tasks, not E03-full vs B.
- **Cheatsheet cost bloat:** if cheatsheet grows past ~1500 tokens, it
  may harm tool-following by diluting the instruction signal. Cap strict.
- **Contamination between plugin trajectories and test tasks:** ensured
  impossible by task-level split.
- **Lesson extraction may produce GEOS-specific advice that's identical
  to what the primer already says.** Counter: filter extracted lessons
  against primer content; keep only novel statements.
- **Memory may help ONLY on tasks where no-plugin also failed** (same
  pattern as plugin's gain over no-plugin). Would still be a real result
  but less dramatic.

## Smoketest gate

Before the full 18-task run: run 2 of the test tasks with the
cheatsheet, verify CC actually reads/uses it (grep agent outputs for
cheatsheet content), verify no crashes in the MCP preflight. Only
launch full run after smoketest passes.

## Success criteria (pre-registered)

- Primary: paired mean TreeSim(B) - TreeSim(A) >= +0.03 on 18 test tasks.
  This is roughly half the size of the plugin-over-baseline effect
  (+0.175) — a real but modest stacking gain.
- Secondary: pass >=0.7 rate improvement of at least 2 tasks (+11pp).

If the delta is <0 or flat: memory does not help on easy-task setting;
re-consider intervention (primer variations, file-tree injection, or
harder difficulty setting).

## Out of scope (deferred)

- Continual memory (per-task updates) — I06 open for future.
- Memory as MCP tool rather than system-prompt inject — deferred.
- Multi-seed variance on memory-enhanced run — deferred.
- Cross-model generalization — deferred.

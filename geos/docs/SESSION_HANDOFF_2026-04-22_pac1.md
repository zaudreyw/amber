# Session Handoff — 2026-04-22 (post-PAC-1 sleep session)

*Written at end of a ~2h /sleep session that ran PAC-1 Phase A + B1 on
v2+minimax. Read this cold, then `misc/pac1/scores/pac1_final_summary.md`
for full numbers.*

## TL;DR

The project's paper story is **{RAG, Memory, Self-Refinement} as a stack
of CC adjustments**. This sleep session established multi-seed evidence
that the stack beats baseline but **components do not stack additively**:
once RAG+SR (or RAG+Mem) is in place, adding the third component adds
variance without net mean gain.

**The strongest single story is RAG + Self-Refinement (cell A3)**:
+0.155 fa0 TreeSim over baseline at σ=0.017 across 2 seeds. Essentially
deterministic.

**The full stack (A5)** wins on mean (+0.110) but with σ=0.252 across 3
seeds — not yet statistically significant.

## First actions when resuming

1. Read `misc/pac1/scores/pac1_final_summary.md` — full multi-seed results.
2. Read `.copilot/checkpoint.md` — working state at sleep exit.
3. Read `.copilot/hub.md` State of Knowledge — updated 2026-04-21 end-of-sleep.
4. Skim `research_log.md` LOG-2026-04-21-5/6/7/8 for the narrative of
   how the Phase A seed-1 "stack loses" reading got reversed by seed 2.
5. If answering user questions about memory specifically, also read
   `docs/MEMORY_PRIMER.md` (written earlier in the session).

## Campaign state

PAC-1 design: `decisions/D-005_pac1-ablation-campaign.md` and
`docs/XN-013_pac1-phase-a-ablation.md`.

### Multi-seed results (fa0 TreeSim, 17 v2 tasks, minimax-m2.7)

| Cell | Config | n | Mean | Std | Δ vs A1 |
|:-:|---|:-:|---:|---:|---:|
| A1 | baseline (no-plug) | 1 | 0.497 | — | — |
| A2 | RAG only | 1 | 0.440 | — | -0.058 |
| **A3** | **RAG + SR** | **2** | **0.653** | **0.017** | **+0.155** |
| A4 | RAG + Mem (old AQ) | 1 | 0.725 | — | +0.228 |
| A4' | RAG + Mem (new infra) | 2 | 0.661 | 0.184 | +0.164 |
| **A5** | **FULL STACK** | **3** | **0.607** | 0.252 | **+0.110** |

Run names (for file lookups):
- A1: `noplug_mm_v2` → `data/eval/claude_code_no_plugin/noplug_mm_v2`
- A2: `plug_mm_v2_seed2` → `data/eval/claude_code_repo3_plugin/plug_mm_v2_seed2`
- A3: `pac1_plug_hook_s1`, `pac1_plug_hook_s2` → `data/eval/claude_code_repo3_plugin/`
- A4: `gmemsilent_mm_v2` → `data/eval/claude_code_repo3_plugin_gmemsilent/`
- A4': `pac1_plug_mem_nohook_s{1,2}` → `data/eval/claude_code_repo3_plugin_gmemsilent_nohook/`
- A5: `pac1_plug_mem_hook_s{1,2,3}` → `data/eval/claude_code_repo3_plugin_gmemsilent/`

All score summaries: `misc/pac1/scores/*.json`.

### Component definitions

- **RAG** = `plugin_enabled`: 3-DB ChromaDB MCP + `geos-rag` skill.
- **Memory** = `memory_enabled` + `memory_prompt_hint=False`: silent MCP
  `memory_lookup` tool (lexical token-overlap over 18 train-task entries).
  **Never called** in any A4/A4'/A5 run — its effect is pure tool-list-shape.
- **SR** = `stop_hook_enabled`: `plugin/hooks/verify_outputs.py` rejects
  `end_turn` when `/workspace/inputs/` lacks parseable XML; forces re-entry.

New agent key added this session:
`claude_code_repo3_plugin_gmemsilent_nohook` (gmemsilent + `stop_hook_enabled: False`).

### Key findings

1. **Full stack beats baseline on mean** (+0.110) but not significantly at n=3.
2. **Components do not stack**. Adding a second component to RAG+one yields
   ~zero marginal gain (A5-A3 = -0.045, A5-A4' = -0.053).
3. **SR is the variance-reduction component**: A3 σ=0.017 vs A4' σ=0.184.
4. **RAG alone ≤ baseline** (-0.058). Plugin only valuable when paired
   with SR or Mem.
5. **A5 seed variance story**: seeds are 0.317, 0.729, 0.776. Seed 1 was
   an outlier; typical is ~0.75. Don't generalize from single-seed A5.
6. Per-task analysis of A5 seed variance confirms catastrophic-rescue
   bimodality (XN-009 pattern): individual tasks swing from ~0.1 to ~1.0.

### Revised paper-ready claims (preliminary, n=1-3)

- **A ✓**: RAG+SR robustly beats CC baseline (+0.155 fa0 TreeSim, σ=0.017).
- **B partial**: Silent memory helps via tool-list-shape, high variance
  without SR.
- **C weakened**: Components do NOT stack additively. Once RAG+SR or
  RAG+Mem is in place, the third adds nothing on mean.
- **D ✓**: SR's contribution is variance reduction, not mean improvement.

## Critical confounds found this session

1. **Seed variance** is the dominant noise source, especially on the
   rescue-fragile tasks (Sneddon / Mandel / DPWellbore). A5 seed 1 was a
   0.317 outlier; seeds 2,3 at 0.729/0.776. Beware single-seed claims.
2. **AskUserQuestion tool-list change**: E18 (old-infra) had AQ in tool
   list; E23/E24 (new-infra) don't (XN-010 Fix #1 removed it). So the
   E18→E24 comparison has TWO config differences, not one. A4' was run
   specifically to give a matched-infra hook-off comparison.
3. **Memory never called** — verify with JSON-parse of `tool_use` events,
   not grep (which also matches tool-list declarations). Earlier counts
   of "17/17 memory calls" were a grep error; corrected to 0/17.

## Open questions (ordered by priority)

1. **Multi-seed A1 and A2** to n=3 for proper error bars on deltas.
   ~$12. Highest priority.
2. **One more seed of A3** (+$3) to firm up the "stable positive" claim.
3. **Per-task variance decomposition** — which specific tasks drive A4'
   and A5's σ? Is it the rescue tasks only?
4. **Phase C embedding memory** still deferred: blocked on
   `OPENAI_API_KEY` (only OpenRouter available locally). Implementation
   drafted but deleted; see git history for `plugin/scripts/memory_mcp_dense.py`
   and `scripts/memory/build_gmem_dense_index.py`.
5. **Codex CLI adversarial review** also blocked (D-006, same as D-003).
   Install `codex` and run before paper claims.
6. **A6 cell** (no-plug + SR) requires refactoring hook wiring out of
   the plugin block. Deferred as PAC-1b.

## Operational gotchas

- Always pass `--tmp-geos-parent /data/matt/geos_eval_tmp` to
  `run_experiment.py`. Default `/data/shared/geophysics_agent_data/data/eval/tmp_geos`
  is not writable by `matt`.
- `plugin/hooks/verify_outputs.py` was created 2026-04-21 12:08 UTC.
  Any run BEFORE that is hook-OFF regardless of agent config.
- `verify_hook_events.jsonl` lives at `<task>/.verify_hook_events.jsonl`,
  NOT at `<task>/inputs/.verify_hook_events.jsonl`.
- Brian has concurrent runs on gemma/qwen models via OpenRouter; no
  rate-limit collision observed with minimax at workers=12.
- Scoring script output: `<run>_summary.json` has per-task results in
  `.results[]`; `.results[*].experiment` is task name, `.results[*].treesim`
  is the score. Summary block at `.summary.treesim.with_failures_as_zero_mean`
  is the fa0 number reported throughout.

## Files created / modified this session

New:
- `docs/MEMORY_PRIMER.md` — meeting primer on all memory variants (for user's meeting prep)
- `docs/XN-013_pac1-phase-a-ablation.md` — PAC-1 design + results
- `.copilot/decisions/D-005_pac1-ablation-campaign.md` — campaign decision
- `.copilot/decisions/D-006_pac1-adversarial-review-unavailable.md` — skip log
- `misc/pac1/scores/{e23,e23s2,e24,e24s2,e24s3,a4prime_s1,a4prime_s2}_summary.json`
- `misc/pac1/scores/phase_a_summary.md`, `pac1_final_summary.md`
- Run dirs under `data/eval/*/pac1_*`

Modified:
- `scripts/run_experiment.py` — added `claude_code_repo3_plugin_gmemsilent_nohook` agent key
- `.copilot/method_tree.jsonl` — E23, E23s2, E24, E24s2, E24s3, E25, E26 + E23-RESULT / E24-RESULT
- `.copilot/hub.md` — State of Knowledge updated with PAC-1 findings
- `.copilot/research_log.md` — LOG-2026-04-21-5/6/7/8
- `.copilot/checkpoint.md` — end-of-sleep working state
- `.copilot/status.md` — phase TEST, researcher present, cycle 3

Pending cleanup:
- Old `docs/MEMORY_PRIMER.md` note: "dense memory deferred" — still true;
  kept for user reference.
- Git status: ~20 new/modified files; no commits made this session. User
  decides when to commit.

## Recommended first moves for new session

1. `/pickup` — re-orients from `checkpoint.md` + `hub.md`.
2. If user wants to push PAC-1 forward: launch multi-seed A1 and A2
   (n=3 each). Template:
   ```
   uv run python scripts/run_experiment.py \
     --run pac1_noplug_s2 --agents claude_code_no_plugin \
     --include <17 test tasks> --timeout 1200 --workers 12 \
     --tmp-geos-parent /data/matt/geos_eval_tmp \
     --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template
   ```
3. If user wants to revisit the "stack doesn't beat baseline" framing:
   re-read `misc/pac1/scores/pac1_final_summary.md` §"Paper-ready story"
   and discuss.
4. If user wants to pursue embedding memory (E27?): need OpenAI API key
   OR Docker image with sentence-transformers + HF cache mount.
5. If user wants to install codex: prior sessions have notes in D-003 /
   RN-002 on the install path; follow those before running adversarial
   review on PAC-1 findings.

## Sleep exit counters (2026-04-21 end)

- Cycles completed: 3 of 20.
- Hours used: ~2 of 8.
- Cost: ~$22 across 8 new 17-task runs + smoketest.
- Consecutive no-improvement: 0.
- Consecutive errors: 0.
- Exit reason: campaign deliverable complete; findings substantive
  enough to warrant user review before further compute.

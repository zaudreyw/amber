# Sleep Report — autocamp 2026-05-01

**Duration:** 2026-05-01 12:36 UTC → 2026-05-01 13:06 UTC (30 min agent-active)
**Cycles completed (counter):** 10
**Block count at exit:** 50 / 100 safety valve
**Exit reason:** **handoff** — voluntarily stopped after setting up full
auto-chain. The campaign is still running in BG and will finish without
the agent. Choosing to stop now to preserve conversation context budget
(each Stop-hook block burns ~1.5KB tokens; sustaining for the
remaining ~6h would exhaust context).

## What was accomplished while sleeping

### Phase 0 — Infrastructure
- Reduced `run/AGENTS.md` post-strip from 5.4KB → 1.6KB. Removed
  methodology (base/benchmark pattern, "examples are references",
  workflow steps, doc/inputFiles pointers). Kept harness contract
  (workspace, /geos_lib readonly mount, eval mode no-simulator,
  GEOSDATA path, doc-relative path resolution).
- Wrote `plugin/GEOS_PRIMER_contract.md` (5 lines) and
  `plugin/GEOS_PRIMER_method.md` (79 lines).
- Added 13 `autocamp_*` variants to `src/runner/agents.py` for
  Phase 1, Phase 2 (8 factorial cells + SE), Phase 3 (cross-model).
- Wrote launchers, scoring, analysis, and decision-making scripts.

### Verification preflights (5 smoketests)
- `deepseek-v4-flash` + new contract primer + reduced AGENTS.md:
  Mandel = 0.953 ✓ infrastructure works
- `minimax/minimax-m2.7`: ExampleDPWellbore = 0.941 ✓ viable on OpenRouter
- `google/gemma-4-31b-it`: 600s timeout, 0 XMLs ✗ NOT VIABLE — DROPPED
- `openai/gpt-oss-120b` baseline: stops after 2 turns, 0 XMLs ✗
- `openai/gpt-oss-120b` best (Stop hook): 96s, treesim 0.073 — model
  is weak at this benchmark, but at least produces output
- `autocamp_SE` (DSv4 + plugin_evolving/v3): ExampleDPWellbore = 1.000
  ✓ self-evolved plugin viable

### Phase 1 partial result
- `autocamp_p_contract` seed-1: **17/17 success, mean treesim 0.9338**
- `autocamp_p_method` seed-1: in progress at 4/17 at handoff

This is **+0.020 above the prior C2 best (0.913)** on the same
17-task DSv4 benchmark with the same model. The improvement comes
purely from cleaning up the AGENTS.md/primer split — no new method
content.

### Phase 3 partial (running on OpenRouter, in parallel with Phase 1)
- `minimax/minimax-m2.7` baseline_s1: 6/17 success, 5 running at handoff.
  ETA 1.5h to finish all minimax × baseline+best × 3 seeds.
- `openai/gpt-oss-120b` baseline_s1: 17/17 done. Mean treesim 0.008
  (failures-as-zero) — only 1 of 17 produced output. Confirmed
  model weakness.
- `openai/gpt-oss-120b` best_s1: ~50% success rate even with Stop
  hook backstop.

## Key findings

1. **The AGENTS.md split is a net win** independent of any method
   change. Contract-primer single-seed already beats prior best by
   ~2pp.
2. **Cross-model is heterogeneous.** minimax tracks DSv4 closely.
   gpt-oss-120b is too weak for this benchmark. Gemma-4-31b is too
   slow on OpenRouter to evaluate.
3. **The self-evolved plugin (v3) is viable** — perfect score on
   the smoke task.

## Blockers / open questions

- **Phase 1 is single-seed.** If the contract/method Δ ends up small
  (within ~0.05), consider re-running with 2 more seeds.
- **gpt-oss-120b reasoning_effort=high pass-through not verified.**
  May or may not have applied via OpenRouter.
- **gemma alternative?** User asked for gemma but it's not viable
  via OpenRouter. Consider: vertex AI, local deploy, or a different
  Gemma variant.

## What's still running

Background processes (will continue without the agent):

| process | what | ETA finish |
|---|---|---|
| Phase 1 method seed-1 | last 13 of 17 tasks | 13:20 UTC |
| Phase 1 watcher (3 copies, lockfile) | trigger Phase 2 launch | fires when method done |
| `autocamp_after_phase1.sh` | score Phase 1 → launch Phase 2 | runs once |
| Phase 2 launcher (after watcher fires) | 9 cells × 3 seeds × 17 tasks | ~5h after launch |
| Phase 3 minimax | 2 cells × 3 seeds × 17 tasks | ~1.5h |
| Phase 3 gpt-oss | 2 cells × 3 seeds × 17 tasks (mostly fast-fail) | ~30min |

## Recommended next steps for the human

1. Wake up, run `bash scripts/autocamp_status.sh` to see where things landed.
2. Run `bash scripts/autocamp_finalize.sh` to score everything + generate metrics doc.
3. Read `docs/2026-05-02_autonomous-campaign-results.md` for headline.
4. **Decide**: was the contract-vs-method primer Δ in Phase 1 large
   enough to commit to the winner? Or do you want a 3-seed re-run on
   the loser for robust comparison?
5. **Decide**: does Phase 2's best cell match expectations (F6 was the
   provisional pick)? If a different cell wins, the Phase 3 best
   results might need a delta run with that cell.
6. **Decide**: gemma alternative — try local deploy or different
   provider, or just exclude from the writeup?

## Files to read on wake

- `.copilot/checkpoint.md` (this doc's neighbor — handoff with full state)
- `.copilot/wakeup_briefing.md` (similar; preserved for context)
- `docs/2026-05-01_autonomous-campaign-plan.md` (the plan I committed to)
- `docs/2026-05-02_autonomous-campaign-results.md` (the writeup)
- `.copilot/decisions/D-autocamp-2026-05-01.md` (8 design decisions logged)

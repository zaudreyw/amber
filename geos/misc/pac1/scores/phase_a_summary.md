# PAC-1 Phase A single-seed results (2026-04-21)

All runs on v2 specs (experiments_test36_template) + minimax-m2.7 + 17 test tasks + workers=12.

## Results table (failures-as-zero TreeSim)

| Cell | RAG | Mem | SR | Run | Scored | fa0 |
|:-:|:-:|:-:|:-:|---|:-:|---:|
| A1 | ✗ | ✗ | ✗ | E16 noplug_mm_v2 | 15/17 | 0.497 |
| A2 | ✓ | ✗ | ✗ | E17 plug_mm_v2_seed2 | 13/17 | 0.440 |
| A3 | ✓ | ✗ | ✓ | E23 pac1_plug_hook_s1 | 17/17 | **0.664** |
| A4 | ✓ | ✓ | ✗ | E18 gmemsilent_mm_v2 | 17/17 | **0.725** |
| A5 | ✓ | ✓ | ✓ | E24 pac1_plug_mem_hook_s1 | 17/17 | **0.317** |

## Paired deltas (fa0 on 17 test tasks)

| Comparison | Delta | W/L | Note |
|---|---:|:-:|---|
| A3-A1 (RAG+SR vs baseline) | +0.167 | 11/6 | — |
| **A5-A1 (FULL STACK vs baseline HEADLINE)** | **-0.180** | 5/12 | **STACK LOSES** |
| A4-A1 (RAG+Mem vs baseline) | +0.228 | 12/4 | strongest positive |
| A2-A1 (RAG alone vs baseline) | -0.058 | 7/8 | near-zero |
| A3-A2 (+SR over plug) | +0.225 | 11/5 | diff-seed |
| A4-A2 (+Mem over plug) | +0.286 | 13/4 | diff-seed |
| **A5-A3 (+Mem over plug+SR)** | **-0.347** | 3/13 | **NEGATIVE INTERACTION** |
| A5-A4 (+SR over plug+Mem) | -0.408 | 2/15 | diff-seed + AQ confound |

## Critical confounds found mid-analysis

1. **Seed variance**: A2/A4 are prior runs on "seed 2". A1 is a prior run. A3/A5 are new runs today. So all comparisons except A5-A3 mix seeds.
2. **AskUserQuestion tool list change**: E18 tool list INCLUDES AskUserQuestion (29 tools); E23/E24 tool lists do NOT (26 and 28 tools). Tool was removed in an intervening session (XN-010 Fix #1). So A4-vs-A5 comparison has TWO config differences, not one.
3. **Memory never called**: `mcp__memory__memory_lookup` tool_use count is 0/17 in BOTH E18 and E24 (earlier claim of "17/17 calls" was based on grep of tool-list declaration string, not actual tool_use events). So retrieval content doesn't explain any difference.

## Clean paired comparison: A5 vs A3

- **Both same session, same infrastructure, same seed family.**
- **Only difference: memory tool present in tool list (uncalled) in A5.**
- **A5-A3 = -0.347 fa0** on 17-task paired; A5 loses on 13, wins on 3.
- Hook intervention count: A3=7 (4 no_xml + 3 parse_error), A5=12 (9 no_xml + 3 parse_error).
- **Adding an un-called memory tool induces more empty-completion attempts AND degrades XML quality on tasks that do complete.** Strong negative tool-list-shape effect.

## Per-task regression pattern A4 (E18) → A5 (E24)

Tasks with biggest regressions (A4 - A5):
- ViscoDruckerPrager: 0.998 → 0.083 (-0.915)
- DPWellbore: 0.978 → 0.141 (-0.837)
- CasedContactThermoElastic: 0.847 → 0.057 (-0.790)
- DeviatedElasticWellbore: 0.879 → 0.137 (-0.742)
- kgdExperimentValidation: 0.903 → 0.287 (-0.616)

Only 2 tasks improve: ThermoporoelasticConsolidation (+0.356) and buckleyLeverett (+0.108).

## Interpretation

**The three components do not stack.** Each component added individually to
RAG gives a positive delta; combining Memory + SR produces a catastrophic
regression. The mechanism is NOT memory-content poisoning (memory is
never called). It's a tool-list-shape interaction: the memory tool's
mere presence in the tool list (with hook active, no AskUserQuestion)
makes the agent more prone to empty-completion attempts, and the hook's
re-entries don't recover quality.

**Possible paper-ready story:** "silent tools help when the agent
ignores them; active safety nets help when errors happen; combining
them is not additive and in our setup produces a large negative
interaction."

**Required before any claim:**
- Multi-seed A5 (E24 config) to confirm the regression is not a single-seed outlier.
- Run A4 equivalent with current infrastructure (hook-off + AskUserQuestion removed) to
  disambiguate the A4 vs A5 drop.
- Consider running A5 without memory tool but with AskUserQuestion put back, to isolate
  which tool-list change matters.

## Operational

- E23 run dir: data/eval/claude_code_repo3_plugin/pac1_plug_hook_s1
- E24 run dir: data/eval/claude_code_repo3_plugin_gmemsilent/pac1_plug_mem_hook_s1
- Score JSONs: misc/pac1/scores/e23_summary.json, e24_summary.json
- Log: misc/pac1/phase_a_summary.md (this file)

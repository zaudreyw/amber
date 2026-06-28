---
id: XN-013
title: "PAC-1 Phase A — {RAG, Memory, Self-Refinement} ablation on v2+minimax (17-task)"
date: 2026-04-21
dag_nodes: [I05, I11, E16, E17, E18, E20-COMPLETE, E23, E24]
links:
  derived_from: [E18, E20-COMPLETE, D-005]
  related_to: [I05, I06, I10, I11, I12, I13]
---

# XN-013 — PAC-1 Phase A design + execution log

*Status: IN PROGRESS (sleeping session 2026-04-21, PAC-1 D-005).*
*Complements the prior session's narrow E20 hook ablation (XN-012)
with a full 17-task sweep.*

## Relationship to prior work

XN-012 (prior session, 2026-04-21) ran a NARROW hook ablation: 4
E17-failure tasks × 3 runs × 4 cells = 48 runs. Finding: hook does not
significantly rescue the minimax empty-completion failure (Δ -0.112
fa0 TreeSim vs nohook, p≈0.31, n=12). Also: E17's 4/17 failure pattern
did not reproduce. Recommendation: "Ship hook as safety net, not as
paper contribution."

PAC-1 XN-013 is complementary: full 17-task sweep, fewer cells, set up
for Phase B multi-seeding. Primary question is no longer "does the hook
rescue?" but "what is each component's marginal TreeSim contribution
across the full test set, with paper-grade statistical support?"

## Goal

Firmly establish: (a) the {RAG + Memory + Self-Refinement} stack
outperforms vanilla CC on the GEOS XML authoring task, and (b) each
component contributes or at worst doesn't hurt. Single canonical testbed:
v2 specs + minimax-m2.7 + 17 test tasks + `failures-as-zero` TreeSim as
the headline metric.

## Mapping components to agent keys

| Component | Config flag | Artifact |
|---|---|---|
| RAG | `plugin_enabled` | 3-DB ChromaDB MCP + `geos-rag` skill |
| Memory | `memory_enabled + memory_prompt_hint=False` | `plugin/scripts/memory_mcp.py` (18 frozen entries, silent) |
| Self-Refinement (SR) | `stop_hook_enabled` | `plugin/hooks/verify_outputs.py` — rejects `end_turn` when `/workspace/inputs/` lacks parseable XML |

**Important timeline note:** `verify_outputs.py` was created at
2026-04-21 12:08 UTC. E16/E17/E18 all completed before that. So all three
existing runs are **hook-OFF**, regardless of the agent's default flag at
the time they're later re-read.

## Phase A cells (descoped to 5; 2 new runs)

Descoped from 8 to 5 because prior session's narrow E20 already covered
the noop-tool hypothesis (A5n0/A5n1 equivalents). A6 (no-plug+SR) still
deferred due to hook-wiring coupling.

| Cell | RAG | Mem | SR | Run name | Agent key | Status |
|:-:|:-:|:-:|:-:|---|---|---|
| A1 | ✗ | ✗ | ✗ | `noplug_mm_v2` | `claude_code_no_plugin` | E16 — DONE |
| A2 | ✓ | ✗ | ✗ | `plug_mm_v2_seed2` | `claude_code_repo3_plugin_nohook` | E17 — DONE |
| A3 | ✓ | ✗ | ✓ | `pac1_plug_hook_s1` (E23) | `claude_code_repo3_plugin` | NEW |
| A4 | ✓ | ✓ | ✗ | `gmemsilent_mm_v2` | `claude_code_repo3_plugin_gmemsilent` (hook-off at E18 time) | E18 — DONE |
| A5 | ✓ | ✓ | ✓ | `pac1_plug_mem_hook_s1` (E24) | `claude_code_repo3_plugin_gmemsilent` (hook now on) | NEW |

### Why the noop-tool cells matter

XN-010 §5 noted E18 had zero `failed_no_outputs` on the same 4 tasks E17
failed, and speculated "adding any extra tool to the tool list subtly
changes the message shape enough to suppress the minimax empty-completion
tendency." If A5n0 (no memory, just a no-op tool) also wins over A2,
*memory's headline contribution is really a tool-list-shape effect*.
That would sharply alter the paper's memory narrative.

### A6 deferred

A6 (no-plug + hook, no memory) would isolate SR's contribution
independent of RAG. Requires refactoring the Stop-hook registration out
of the plugin block (currently wired via `--settings` under
`plugin_dir` logic; gated by `if enable_plugin`). Planned for PAC-1b.

## Scoring

Both scored-only AND failures-as-zero means (per XN-011) reported for
every cell. Primary comparison metric = failures-as-zero paired deltas
on the 17-task subset.

## Analysis plan (after all 4 new runs score)

**Headline:**
- A5 vs A1 = full stack vs baseline.

**Per-component attribution (failures-as-zero, paired):**
- RAG contribution = {A2-A1, A3-A1} (SR off vs SR on with matched memory off).
- Memory contribution = {A4-A2, A5-A3} (SR off vs SR on with matched RAG on).
- SR contribution = {A3-A2, A5-A4} (matched RAG+memory states).

**Tool-list-shape confound:**
- A5n0-A2 = "does any extra MCP tool help?" If ≥ A4-A2, memory content doesn't matter — tool-list presence does.
- A5n1-A5n0 = SR effect with a noop tool, for comparison with A3-A2.

## Pre-registered thresholds

- **Headline pass:** A5 - A1 ≥ +0.10 failures-as-zero single-seed. Phase B multi-seed required for any paper claim.
- **Component pass:** median of the two attribution rows per component ≥ 0. Confidence intervals with overlap-zero allowed only for "doesn't hurt" framing.
- **Surprise trigger:** any row reversing sign from expected → dispatch reviewer + research-reflect.

## Execution plan

### Smoketest (before full runs)

Run 2 tasks per new cell (4 new cells × 2 tasks = 8 smoketest runs),
tasks chosen to exercise both the rescue-task and easy-task regimes.
Verify:
- MCP preflight passes for each cell.
- Memory tool shows in tool list for A5 (check `events.jsonl` system init).
- Noop MCP shows up for A5n0/A5n1.
- Hook fires on A3/A5/A5n1 — forces re-entry if end_turn w/o XML.
- Zero infrastructure crashes.

Tasks chosen for smoketest: `TutorialSneddon` (rescue, fragile),
`ExampleMandel` (rescue, fragile). Reason: if these complete at plausible
scores, the pipeline works; if they fail-no-outputs uniformly, something
is broken at the provider level for that config.

### Full Phase A run

After smoke passes, launch the 4 new 17-task runs in sequence (not
parallel — OpenRouter rate-limit safe at workers=12 per run, but 4×12
concurrent requests risks 429s). Estimated ~20 minutes total wall-clock.

Command template:
```bash
uv run python scripts/run_experiment.py \
  --run pac1_plug_hook_s1 \
  --agents claude_code_repo3_plugin \
  --include <17 test tasks> \
  --timeout 1200 --workers 12 \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template
```

Then score each with `batch_evaluate.py --experiments-dir <run-path>`
against `/data/shared/.../experiments_gt` and record per-task TreeSim +
failures-as-zero summary.

### Cost estimate

Per 17-task run on minimax: ~$2-4 (E18 cost ~$3, the other runs similar).
Total Phase A new-run cost: ~$10-16.

## Open risks

- **Single-seed everywhere** — every claim from Phase A is at most
  preliminary. Phase B multi-seed (≥3 seeds on A1/A3/A5 at minimum) is
  mandatory before any paper claim.
- **Minimax empty-completion is stochastic** — different runs of the
  same config may have different failure counts on the 4 problem tasks.
  The hook should flatten this, but the hook has its own failure mode
  (what if the model re-enters and produces another empty completion?).
  Monitor closely.
- **A6 absence** — can't fully isolate SR contribution without running
  on no-plug. Note as limitation; plan PAC-1b.

## Smoketest log

### Smoketest — 2026-04-21 19:45 UTC

Smoketest: 2 tasks (TutorialSneddon, ExampleMandel) × 2 new agents (A3, A5). Total 4 runs at workers=4.

- Elapsed 216-485s per task (well within 1200s budget).
- All 4 status=success.
- Hook fired 4× on stop checks — all `xml_clean:allow`, no rescue needed in smoke.
- MCP wiring confirmed: both `geos-rag: connected` and `memory: connected` on gmemsilent agent.
- One operational fix: default `--tmp-geos-parent` points at `/data/shared/...` which is not writable by `matt`; must override to `/data/matt/geos_eval_tmp`.

**Decision**: proceed to full Phase A.

## Full Phase A results (single-seed, 2026-04-21 20:00-20:22 UTC)

### Results table (fa0 TreeSim on 17 test tasks)

| Cell | RAG | Mem | SR | Run | Scored | fa0 |
|:-:|:-:|:-:|:-:|---|:-:|---:|
| A1 | ✗ | ✗ | ✗ | E16 | 15/17 | 0.497 |
| A2 | ✓ | ✗ | ✗ | E17 | 13/17 | 0.440 |
| A3 | ✓ | ✗ | ✓ | **E23** | 17/17 | **0.664** |
| A4 | ✓ | ✓ | ✗ | E18 | 17/17 | **0.725** |
| A5 | ✓ | ✓ | ✓ | **E24** | 17/17 | **0.317** |

### Paired deltas (fa0)

| Comparison | Δ | W/L | Seed |
|---|---:|:-:|---|
| A3-A1 RAG+SR vs baseline | +0.167 | 11/6 | diff |
| **A5-A1 FULL STACK vs baseline** | **-0.180** | 5/12 | diff |
| A4-A1 RAG+Mem vs baseline | +0.228 | 12/4 | diff |
| A2-A1 RAG alone vs baseline | -0.058 | 7/8 | diff |
| A3-A2 +SR over plug | +0.225 | 11/5 | diff |
| A4-A2 +Mem over plug | +0.286 | 13/4 | diff |
| **A5-A3 +Mem over plug+SR** | **-0.347** | 3/13 | **SAME** (cleanest paired) |
| A5-A4 +SR over plug+Mem | -0.408 | 2/15 | diff + AQ confound |

### Key findings (single seed, caveats)

1. **The stack does NOT outperform baseline on this seed** (A5-A1 = -0.180). Contradicts the user's headline target.
2. **Each component alone (with RAG) is positive** (A3-A2 = +0.225; A4-A2 = +0.286).
3. **Combining Memory + SR with RAG is catastrophically negative** (A5-A3 = -0.347 paired). Large and systematic (3/13 tasks win).
4. **Memory is never called** in either A4 or A5 (mem=0 tool_use events across all 17 tasks in both runs). The effect is NOT memory-retrieval poisoning.
5. **Tool-list-shape confound**: A4 (E18) tool list INCLUDES AskUserQuestion (29 tools); A5 (E24) tool list does NOT (28 tools; AQ removed in intervening session). So A5-A4 is confounded by TWO config differences, not one.
6. **Hook interventions are ~2× more frequent in A5 than A3**: E23 had 4 no_xml + 3 parse_error = 7 hook rescues; E24 had 9 no_xml + 3 parse_error = 12. Adding an *un-called* memory tool correlates with more empty-completion attempts AND worse XML on tasks that do complete.

### Interpretation (tentative)

The three components DO NOT stack in this single-seed Phase A. A tool-list-shape interaction between the silent memory tool and the Stop hook appears to make the agent more prone to empty-completion attempts and to producing lower-quality XML that passes the hook check but scores poorly on TreeSim. The mechanism is NOT memory-content (memory never called); it is either (a) combined tool-list shape + hook alter agent behavior, or (b) single-seed variance on the rescue-fragile tasks.

### Per-task regression A4 (E18) → A5 (E24)

Biggest drops: ViscoDruckerPrager -0.915, DPWellbore -0.837, CasedContactThermoElastic -0.790, DeviatedElasticWellbore -0.742, kgdExperimentValidation -0.616, IsothermalLeakyWell -0.528, DruckerPrager -0.512, ExtendedDP -0.484, ModifiedCamClay -0.467, ThermalLeakyWell -0.432, TutorialPoroelasticity -0.426, ExampleMandel -0.226, Sneddon -0.157, EDPWellbore -0.151, pkn -0.122.

Only 2 tasks improve in A5: ExampleThermoporoelasticConsolidation +0.356, buckleyLeverett +0.108.

## Required follow-up before any paper claim

1. **Seed 2 of A5 (full stack)** — does the -0.180-vs-baseline regression reproduce? LAUNCHED 2026-04-21T20:22.
2. **Seed 2 of A3** — establishes A3 variance for paired comparison. LAUNCHED 2026-04-21T20:22.
3. **A4' run: plug+mem+nohook on CURRENT infra (no AskUserQuestion)**. Needed to disambiguate the A5-A4 drop (hook vs AQ-removal). Requires a new agent key `claude_code_repo3_plugin_gmemsilent_nohook`. DEFERRED one cycle.
4. **If A5 seed 2 reproduces**: the negative interaction is real; paper story shifts to "silent tools help when ignored; active safety nets help alone; combining them is not additive."
5. **If A5 seed 2 rebounds**: single-seed outlier; multi-seed the full campaign to firm up each delta.

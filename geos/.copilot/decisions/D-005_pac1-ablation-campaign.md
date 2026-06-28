---
id: D-004
title: "PAC-1: paper-ready ablation campaign — stack vs baseline + per-component attribution"
date: 2026-04-21
dag_nodes: [I05, I11, E16, E17, E18]
links:
  derived_from: [E18, I11]
  related_to: [I05, I06, I10]
---

# D-004 — PAC-1 ablation campaign

## Context

User's framing (2026-04-21 conversation): the project's contribution is a
bundle of CC adjustments = {RAG, Memory, Self-Refinement}. The paper
needs to firmly establish (a) the full stack outperforms the CC baseline,
and (b) each component either contributes or at least doesn't hurt.

Current evidence is all single-seed and scattered across confounded runs
(mixed v1/v2 specs, mixed presence of the Stop hook). Need to rebuild the
evidence on the canonical v2+minimax testbed with clean factorization.

## Component definitions (fixed for the paper)

| Component | Mechanism | Config flag |
|---|---|---|
| **RAG** | 3-DB ChromaDB MCP + `geos-rag` skill; tools: `search_technical`, `search_navigator`, `search_schema` | `plugin_enabled` |
| **Memory** | frozen 18-task `memory_lookup` MCP tool, silent delivery (no system-prompt instruction) | `memory_enabled + memory_prompt_hint=False` |
| **Self-Refinement** | `plugin/hooks/verify_outputs.py` Stop hook — rejects `end_turn` when `/workspace/inputs/` lacks parseable XML; forces re-entry with a complaint | `stop_hook_enabled` |

## Phase A — 2×2×2 single-seed ablation (now)

Eight cells on v2 specs + minimax-m2.7, workers=12, 1200s timeout, 17 test tasks.

| Cell | RAG | Mem | SR | Run name | Agent key | Status |
|---|:-:|:-:|:-:|---|---|---|
| A1 | ✗ | ✗ | ✗ | `noplug_mm_v2` (E16) | `claude_code_no_plugin` | DONE |
| A2 | ✓ | ✗ | ✗ | `plug_mm_v2_seed2` (E17) | `claude_code_repo3_plugin_nohook` | reuse or re-run |
| A3 | ✓ | ✗ | ✓ | `pac1_plug_hook` | `claude_code_repo3_plugin` | NEW |
| A4 | ✓ | ✓ | ✗ | `pac1_plug_mem_nohook` | new (see below) | NEW |
| A5 | ✓ | ✓ | ✓ | `pac1_plug_mem_hook` | `claude_code_repo3_plugin_gmemsilent` | may reuse E18 |
| A6 | ✗ | ✗ | ✓ | `pac1_noplug_hook` | new (see below) | NEW |
| A7 | ✗ | ✓ | ✗ | `pac1_noplug_mem_nohook` | new | DEFER |
| A8 | ✗ | ✓ | ✓ | `pac1_noplug_mem_hook` | new | DEFER |

A7/A8 (no-plug with memory) are second-order — they test "does memory
alone help without RAG." Deferred unless Phase A surprises.

Two NEW agent keys needed:
- `claude_code_repo3_plugin_gmemsilent_nohook` — gmemsilent + `stop_hook_enabled: False`
- `claude_code_no_plugin_hook` — no-plug variant with hook ON (requires checking that the hook's XML-parse check is reasonable against a vanilla-CC trajectory)

## Scoring protocol

All runs scored with `batch_evaluate.py` reporting **both** the scored-only
mean AND the failures-as-zero mean (per XN-011). Paper's primary number is
failures-as-zero — it treats `failed_no_outputs` as part of the system's
behavior, which is exactly what the Stop hook is supposed to reduce.

All comparisons paired on same task set, same seed.

## Analysis plan

After Phase A, produce a single table with all 6 cells × failures-as-zero
TreeSim. Attribution reads:
- **RAG contribution** = A3 − A1 (with SR held on) and A2 − A1 (SR off).
- **Memory contribution** = A5 − A3 (with RAG+SR) and A4 − A2 (without SR).
- **SR contribution** = A3 − A2 (RAG only), A5 − A4 (RAG+Mem), A6 − A1 (alone).
- **Stack vs baseline** = A5 − A1.
- **Interactions** = A5 − (A1 + RAG_delta + Mem_delta + SR_delta).

If any component's marginal contribution is negative across all its rows,
flag for Phase B multi-seed before declaring dead.

## Phase B — multi-seed (after Phase A)

Take the 3 most informative cells from Phase A (minimum: A1, A5, and
whichever single-component-stripped cell has the smallest margin to A5)
and run 2 additional seeds each. Gives n=3 per cell → crude std error.
If any marginal claim reverses under multi-seed, that's the real result.

## Phase C — embedding memory (E19), parallelizable with A/B

Separate decision: D-005 (to be written) will cover the embedding
re-implementation of memory_lookup. Independent of PAC-1 ablations.

## Smoketest gate

Before launching the 6 Phase A runs as background workloads, verify on 2
tasks per new config that (a) the agent runs end-to-end, (b) the hook
fires when inputs are empty, (c) the memory tool is discoverable in
`memory_enabled` cells, (d) the noop path doesn't regress.

## Pre-registered success criteria

- **Headline:** A5 (full stack) > A1 (baseline) on failures-as-zero TreeSim by >= +0.10 on single seed, confirmed multi-seed in Phase B with 95% CI excluding 0.
- **Component contribution (each component must pass):**
  - RAG: median of (A3-A1, A2-A1) > 0 on failures-as-zero.
  - Memory: median of (A5-A3, A4-A2) > 0 OR confidence interval includes 0 ("doesn't hurt").
  - SR: median of (A3-A2, A5-A4, A6-A1) > 0 OR CI includes 0.
- **No regression across any marginal contribution** on the headline metric.

## What could go wrong

- **Any single-seed cell landing on an unlucky seed** reverses a claim. Phase B is mandatory before any paper claim.
- **Component interactions** — full stack's gain may not equal sum of component gains. Flag interaction terms explicitly in the paper.
- **Hook side effects on high-scoring runs.** If the hook sometimes flags false positives and forces re-entries on runs that would have scored well, SR could *hurt* on some cells. Ablations catch this.

## Honesty / framing

The PAC-1 design is deliberately post-hoc for some cells (reusing E16,
possibly E17/E18). If a reviewer asks, note that these reused cells are
single-seed and Phase B re-samples them. The campaign is not purely
pre-registered — it's a structured redo of the evidence after realizing
on 2026-04-21 that most prior comparisons were confounded by v1/v2 spec
mismatch and the Stop hook being added mid-stream.

## Next concrete steps

1. Add 2 new agent keys to `scripts/run_experiment.py` AGENTS dict.
2. Write XN-012 campaign design note referencing this decision.
3. Launch Phase A smoketest (2 tasks per new cell).
4. Launch Phase A full (17 tasks × 6 new cells in parallel, workers=12).
5. Score all runs; produce PAC-1 results table.
6. Review with user; if clean, commit to Phase B multi-seed.

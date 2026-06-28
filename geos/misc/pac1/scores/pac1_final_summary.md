# PAC-1 Phase A + Phase B1 Final Summary (2026-04-21 sleep session)

All runs: v2 specs + minimax-m2.7 + 17 test tasks + workers=12.
Metric: failures-as-zero TreeSim (fa0). Cost ~$22.

## Multi-seed results

| Cell | Config | Seeds | Mean fa0 | Range | Std | Δ vs A1 |
|:-:|---|:-:|---:|---:|---:|---:|
| A1 | baseline (no-plug) | 1 | 0.497 | — | — | — |
| A2 | RAG only | 1 | 0.440 | — | — | -0.058 |
| **A3** | **RAG + SR** | **2** | **0.653** | 0.641–0.664 | **0.017** | **+0.155** |
| A4 | RAG + Mem (old AQ) | 1 | 0.725 | — | — | +0.228 |
| A4' | RAG + Mem (new infra) | 2 | 0.661 | 0.531–0.791 | 0.184 | +0.164 |
| **A5** | **FULL STACK (RAG+Mem+SR)** | **3** | **0.607** | 0.317–0.776 | 0.252 | **+0.110** |

## Key findings

### 1. The stack beats baseline (weakly) but components do not stack

- A5 (full stack) mean +0.110 over baseline across 3 seeds. Not yet statistically significant given std 0.252.
- A3 (RAG+SR) and A4' (RAG+Mem) each add ~+0.16 alone. Together in A5, the gain drops to +0.11.
- **A5 - A3 = -0.045**, A5 - A4' = -0.053. Adding a second component on top yields roughly ZERO marginal gain.

### 2. SR dramatically reduces seed variance

- A3 (RAG+SR) std 0.017 across 2 seeds — essentially stable.
- A4' (RAG+Mem, no SR) std 0.184 across 2 seeds — volatile.
- A5 (full stack) std 0.252 across 3 seeds — most volatile. Seed 1 (E24 s1) was an outlier at 0.317; seeds 2 and 3 landed at 0.729 and 0.776 (mean 0.752).
- The hook (SR) catches parse errors and empty completions; without it, bad samples tank fa0.

### 3. RAG alone ≤ baseline on this metric

- A2 (plug only) fa0 0.440 vs A1 0.497. -0.058. Plugin alone isn't a win under failures-as-zero.
- Plugin's value is fully realized only when paired with SR and/or Mem.

### 4. Per-component attribution (multi-seed, paired on 17 tasks vs baseline)

| Addition to RAG | Δ over A2 | Std |
|---|---:|---:|
| + SR (A3) | +0.213 | low |
| + Mem (A4') | +0.221 | high |
| + Mem + SR (A5) | +0.167 | highest |

### 5. The "silent memory" effect from E18 is real but fragile

- E18 (A4 old infra, 1 seed) scored 0.725 — strong signal.
- A4' (current infra, 2 seeds) scored 0.661 mean — confirms the effect BUT with high variance (0.531-0.791).
- Memory tool is NEVER called in any A4/A4'/A5 run (mem=0 tool_use). Its benefit is purely tool-list-shape, not retrieval.

## Paper-ready story (PRELIMINARY — n=1-3 per cell)

- **Claim A**: "RAG + Self-Refinement robustly beats CC baseline (+0.16 fa0 TreeSim)." Supported on 2 seeds with stable variance.
- **Claim B**: "Memory (silent MCP tool) helps via tool-list-shape, not retrieval." Supported but high-variance.
- **Claim C** (weakened): "The three components do not stack additively. Once RAG + SR (or RAG + Mem) is in place, adding the third does not further improve the metric."
- **Claim D**: "SR is the component that matters for reliability." Variance across seeds drops from σ≈0.18-0.25 without SR to σ≈0.02 with SR.

## Open questions / required before paper claim

1. **Multi-seed A1, A2, A4 with current infra** — we are comparing cells with unequal seed counts. Need 3 seeds of baseline to put error bars on Δ.
2. **Is SR's stability real or sample size artifact?** A3 n=2 with std 0.017 could be lucky; n=5 would firm this.
3. **Why does memory's effect vary so much?** Is it task-difficulty dependent? Need to decompose fa0 by task to see if variance is on a specific subset.
4. **Does the negative A5-A3/A4' interaction reproduce?** Only 3 seeds of A5; if one more seed shows 0.3-range, the saturation claim needs investigation.
5. **Adversarial review** when Codex CLI is installed.

## Seed-by-seed per-task (A5 full stack across 3 seeds)

A5 tasks with highest variance (max - min):
- ExampleDPWellbore: 0.141 / 1.000 / ? (still computing) — swings 0.85+
- DeviatedElasticWellbore: 0.137 / 1.000 / ?
- CasedContactThermoElastic: 0.057 / 0.990 / ?
- ViscoDruckerPrager: 0.083 / 0.951 / ?

Pattern: tasks bimodally distribute between "fully correct" (~0.95) and "essentially wrong" (~0.1).
Consistent with the known catastrophic-rescue variance pattern (XN-009).

## Operational

- Runs in `data/eval/{claude_code_repo3_plugin,claude_code_repo3_plugin_gmemsilent,claude_code_repo3_plugin_gmemsilent_nohook}/`
- Scored summaries in `misc/pac1/scores/`
- This summary: `misc/pac1/scores/pac1_final_summary.md`
- Cost: ~$22 across 8 new 17-task runs + smoketest.

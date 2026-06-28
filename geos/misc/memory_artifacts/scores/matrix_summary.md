# Memory Ablation Matrix — Results

_Generated: 2026-04-22_

## Per-condition mean fa0 TreeSim (17 v2 tasks, minimax-m2.7)

| Condition | n seeds | mean fa0 | std | Δ vs A3 mean | Wilcoxon p | wins/ties/losses |
|---|:-:|---:|---:|---:|---:|---|
| A3 (RAG+SR) baseline | 3 | 0.524 | 0.223 | — | — | — |
| A4p_RAG_Mem_noSR | 2 | 0.661 | 0.184 | +0.137 | 0.057 | 10/0/7 |
| A5_RAG_Mem_SR | 3 | 0.607 | 0.252 | +0.083 | 0.225 | 10/0/7 |
| placebo | 3 | 0.373 | 0.049 | -0.152 | 0.015 | 6/0/11 |
| M1-u | 3 | 0.796 | 0.057 | +0.272 | 0.000 | 16/0/1 |
| M1-g | 3 | 0.766 | 0.046 | +0.242 | 0.003 | 13/0/4 |
| M3-g | 3 | 0.094 | 0.162 | -0.430 | 0.000 | 0/0/17 |
| M4-u | 3 | 0.537 | 0.333 | +0.013 | 0.890 | 7/0/10 |
| M4-g | 3 | 0.469 | 0.299 | -0.055 | 0.145 | 5/0/12 |

## Decision-gate status

**Claim A (outcome):** Memory variant beats A3 by ≥ +0.05 mean AND Wilcoxon p ≤ 0.10 AND std ≤ max(A3 std, 0.08).
  - PASS: M1-u, M1-g

**Claim B (attribution — grounded distillation is a method contribution):**
  - M1-g − M1-u: mean fa0 delta = -0.030 (FAIL at +0.04 threshold)
  - M4-g − M4-u: mean fa0 delta = -0.068 (FAIL at +0.04 threshold)

**Claim C (locus — external injection beats tool-locus):**
  - M4-g − M3-g: mean fa0 delta = +0.376 (weakened — tool-list-shape confound, RN-003 P2 #5)

**Placebo sanity:** If placebo is near zero vs A3, primer-injection is null-effect and memory content lift is real.
  - placebo − A3: mean fa0 delta = -0.152, wins 6/11

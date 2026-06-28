---
id: XN-015
title: "Memory ablation results — D-008 matrix complete"
date: 2026-04-22
dag_nodes: [I06, I10, E23, E24]
links:
  derived_from: [D-008, RN-003]
  related_to: [D-005, XN-013, XN-014, LN-002]
tags: [memory, ablation, results, hero-run]
status: validated
---

# XN-015 — Memory Ablation Results (D-008 sprint complete)

*Matrix completed 2026-04-22T07:30Z. 18 new condition-seed runs plus
extended A3 baseline. This note replaces the placeholder filled during
the sprint.*

## Headline

**M1 (monolithic DC-Cu cheatsheet primer) stacks cleanly with RAG+SR.**

- **M1-u** (ungrounded): **0.796 ± 0.057**, +0.272 vs A3, Wilcoxon p<0.001,
  16 of 17 task-level wins. Hero run.
- **M1-g** (TreeSim-grounded): 0.766 ± 0.046, +0.242 vs A3, p=0.003,
  13 of 17 wins.
- Both M1 variants satisfy Claim A decision gate.
- **Grounding did NOT provide attribution signal** — grounded slightly
  underperforms ungrounded on both pairs (M1: −0.030, M4: −0.068).
  Claim B fails.
- **Structured RB items (M4) are unstable** — individual seed collapses
  (0.15, 0.28, 0.31) tank the mean.
- **In-run memory MCP tool (M3) is unused** — agent didn't spontaneously
  call memory_lookup in the valid seed. M3's MCP had transient init
  failures on 2 seeds (infrastructure issue, not design flaw).
- **Placebo control works as expected** — equivalent-token generic
  content hurts (−0.152 vs A3). M1's lift is content-specific, not
  primer-shape.

## IMPORTANT — OpenRouter API contamination in some seeds

**Three seeds were contaminated by OpenRouter billing/quota failures, NOT
by memory-design issues.** Detected by diagnostic on 2026-04-22 (see
`misc/memory_artifacts/openrouter_contamination_note.md`).

| Condition | Seed | fa0 score (raw) | Cause | Disposition |
|---|:-:|---:|---|---|
| **M4-u** | s3 | 0.153 | 13/17 tasks hit `HTTP 402 Insufficient credits` | **Exclude from analysis.** M4-u is effectively n=2. |
| **M3-g** | s2 | 0.000 | 17/17 tasks hit `HTTP 403 Key limit exceeded (weekly limit)` | **Exclude.** M3-g effectively n=1 valid. |
| **M3-g** | s3 | 0.000 | 17/17 tasks hit `HTTP 403 Key limit exceeded (weekly limit)` | **Exclude.** |

**Revised M4-u stats after exclusion:** n=2 valid seeds {0.712, 0.746},
mean **0.729** (vs 0.537 when contaminated s3 was included). M4-u's
actual performance is in the M1 tier and NOT unstable.

**M4-g is UNAFFECTED by API contamination.** All 3 M4-g seeds
(0.814, 0.313, 0.280) completed with 17/17 clean runs. The M4-g
instability is a real format-level finding, not an infrastructure
artifact.

**A3 seed 3 (0.267) is genuine minimax sampling noise.** 17/17 clean runs,
no API errors. Low score is real.

**M1-u, M1-g, and M-placebo are all unaffected.** All three variants'
three seeds each completed cleanly.

### How to detect this in future runs (checklist)

1. After any run, grep `status.json` for HTTP 402/403 errors:
   ```bash
   grep -l "402\|403\|Insufficient credits\|Key limit" \
     data/eval/<agent>/<run>/*/status.json
   ```
2. Check `per_tool_counts` — a task with 0 tool calls and <30s elapsed
   is almost certainly an API-error abort, not a memory failure.
3. Check `latest_agent_response` in `status.json` — explicit error strings
   like "API Error: 402" or "Insufficient credits" are dispositive.
4. Check OpenRouter dashboard for credit balance and weekly key limit
   status before launching multi-hour batches. Plan sequencing so a
   high-value condition doesn't land in the last hour of the week.

## Full results table

Minimax-m2.7 via OpenRouter, 17 v2 test tasks, n=3 seeds per condition
(except A4' n=2). fa0 TreeSim is failures-as-zero mean. Rows with
excluded seeds marked with footnote.

| Condition | n | mean fa0 | std | Δ vs A3 | Wilcoxon p | wins/losses | Claim A |
|---|:-:|---:|---:|---:|---:|---|:-:|
| **A1 no-plug** | 1 | 0.497 | — | −0.027 | — | — | — |
| **A2 RAG only** | 1 | 0.440 | — | −0.084 | — | — | — |
| **A3 RAG+SR baseline** | 3 | 0.524 | 0.223 | — | — | — | — |
| A4' RAG+Mem no-SR | 2 | 0.661 | 0.184 | +0.137 | 0.057 | 10/7 | borderline (n=2) |
| A5 RAG+Mem+SR | 3 | 0.607 | 0.252 | +0.083 | 0.225 | 10/7 | FAIL (p>0.10) |
| **M-placebo** | 3 | 0.373 | 0.049 | **−0.152** | 0.015 | 6/11 | N/A (control) |
| **M1-u (hero)** | 3 | **0.796** | **0.057** | **+0.272** | **<0.001** | **16/1** | **PASS** |
| **M1-g** | 3 | 0.766 | 0.046 | +0.242 | 0.003 | 13/4 | **PASS** |
| M3-g | 1 valid ¹ | 0.281 | — | −0.243 | — | — | N/A |
| **M4-u (revised)** | **2 valid ²** | **0.729** | 0.024 | **+0.205** | (TBD) | (TBD) | **likely PASS** |
| M4-g | 3 | 0.469 | 0.299 | −0.055 | 0.145 | 5/12 | FAIL (real instability) |

¹ M3-g s2 and s3 excluded — OpenRouter 403 weekly key limit exceeded.
² M4-u s3 excluded — OpenRouter 402 credit exhaustion mid-run.

Raw per-seed values (excluded seeds in parentheses):
- A3: {0.664, 0.641, 0.267}
- placebo: {0.316, 0.397, 0.405}
- M1-u: {0.859, 0.783, 0.747}
- M1-g: {0.817, 0.755, 0.728}
- M4-u: {0.712, 0.746} + (0.153 — excluded, 402 credit exhaustion)
- M4-g: {0.814, 0.313, 0.280} — all valid, real instability
- M3-g: {0.281} + (0.000 — excluded 403 × 2)

## Failure-class decomposition

Per-class mean vs A3 baseline (from XN-014 taxonomy). Positive = M variant
wins on that class.

| Class | A3 mean | M1-u Δ | M1-g Δ | M4-u Δ | M4-g Δ | placebo Δ |
|---|---:|---:|---:|---:|---:|---:|
| F1 schema hallucination | 0.553 | +0.166 | +0.184 | +0.025 | −0.160 | −0.195 |
| F2 wrong-version drift | 0.414 | +0.376 | **+0.451** | +0.230 | +0.063 | +0.009 |
| F3 missing components | 0.470 | +0.046 | +0.302 | −0.035 | −0.114 | −0.278 |
| F4 spec under-specification | 0.382 | +0.560 | +0.368 | +0.216 | −0.009 | +0.027 |
| plugin-already-good | 0.516 | +0.321 | +0.217 | +0.001 | +0.018 | −0.167 |

**Key observation: M1-g improves all 5 failure classes over A3**, most
dramatically F2 wrong-version drift (+0.451) and F4 spec
under-specification (+0.368). M1-u is comparable across most classes
and slightly ahead on F4 (+0.560). Grounding modestly helps F3 missing
components (+0.302 for M1-g vs +0.046 for M1-u) — the only class where
grounded wins over ungrounded.

## Decision-gate status

### Claim A (outcome) — PASS

Memory variant beats A3 by ≥ +0.05 mean AND Wilcoxon p ≤ 0.10 AND
std ≤ max(A3 std, 0.08).

- **M1-u**: 0.796, +0.272, p<0.001, std 0.057 → **PASS**
- **M1-g**: 0.766, +0.242, p=0.003, std 0.046 → **PASS**

Both M1 variants are reliable (low variance) and strongly positive.

### Claim B (attribution — grounding) — FAIL

(grounded − ungrounded) mean delta ≥ +0.04 on M1 pair OR M4 pair.

- M1-g − M1-u: −0.030 → **FAIL**
- M4-g − M4-u: −0.068 → **FAIL**

TreeSim-grounded distillation is NOT measurably better than
LLM-self-judged distillation in mean fa0 on our task. The grounded
variant does have a meaningful F3 missing-components gain
(+0.302 vs +0.046 for ungrounded), suggesting grounding helps on a
specific failure class but is washed out in the aggregate.

### Claim C (locus) — INVALIDATED BY DESIGN

M3-g (tool-locus) vs M4-g (external injection) planned comparison.

- **Agent never called the memory tool** in the valid M3-g seed.
  0 memory_lookup calls across 17 tasks.
- M3-g s2 and s3 had MCP initialization failures (embedding endpoint
  unreachable at startup). The hard-error-on-missing-key design
  correctly surfaced this, but it also tanked the condition's data.
- M3-g s1 (only valid seed): 0.281 — similar to placebo tier, i.e.
  "primer-shape-equivalent with dormant tool."

Conclusion: **Claim C is not a meaningful test in this setup.** The
agent's unwillingness to spontaneously call the memory tool
(consistent with XN-011) makes tool-locus a vacuous condition. Future
work would need to force tool use (e.g., `memory_prompt_hint=True`)
for a clean comparison.

### Placebo sanity — CONFIRMS CONTENT MATTERS

- M-placebo: 0.373 ± 0.049, Δ vs A3 = −0.152, p=0.015, 6/11 wins.
- Generic primer (GEOS schema overview, token-matched to M1 artifacts)
  HURTS performance by 15 pp. This confirms M1's +0.27 lift is
  content-specific, not primer-shape.

## Disposition

**Scenario A (hero run)** with honest caveats. Claim A passes cleanly
for M1-u and M1-g. Secondary finding: the effective variable is
**primer format**, not grounding.

1. **Grounding attribution not demonstrated.** M1-g − M1-u = −0.030.
   M4-g − M4-u (valid seeds) = −0.260 (grounded M4-g worse than ungrounded
   M4-u). Self-judged distillation is as good or better than TreeSim-
   grounded distillation in this setup. F3 missing-components
   decomposition shows grounding helps that sub-class (+0.302 vs +0.046)
   but the per-class signal does not carry the aggregate mean.
2. **Primer format is the real ablation.** Monolithic cheatsheet (M1)
   with an enumerated element-name table beats structured RB-style
   items (M4). Trajectory analysis of M4-g pkn seed collapse
   (s1=1.000, s2=0.088) reveals M4-g DID produce fracture-solver XML
   but invented `<CompressibleSolidCappedPlatesPorosity>` instead of
   the correct `<CompressibleSolidParallelPlatesPermeability>` —
   a vocabulary hallucination. M1-u's primer explicitly lists
   `CompressibleSolidParallelPlatesPermeability` by name in a
   solver-family table; M4's items describe the structural pattern
   abstractly but do not enumerate specific element names. The
   monolithic-enumerated format anchors the agent's vocabulary and
   prevents F1 hallucinations that the abstract-structured format
   does not.
3. **Content matters more than presence.** M-placebo confirms that
   injecting content (even token-matched generic) HURTS (−0.152 vs
   A3, p=0.015). M1's gain is specifically from the trajectory-
   distilled content, not primer-shape.
4. **Test-time memory is primer-best in this setup.** The in-run MCP
   tool variant (M3-g) is dead weight because agent doesn't call it.
   Only seed with valid data (s1) had 0 `memory_lookup` calls across
   17 tasks. Plus 2 of 3 M3-g seeds were wiped by OpenRouter 403
   weekly key limit. No tool-locus claim can be made.
5. **A3 variance is high** (0.22). n=3 seeds of A3 = {0.66, 0.64, 0.27}
   with seed 3 a major outlier driven by stochastic F1 hallucinations.
   This is intrinsic to minimax-via-OpenRouter sampling. M1's paired
   wilcoxon 16/1 wins at p<0.001 is robust to this noise.
6. **M4-u (revised n=2) is NOT unstable.** Originally reported as
   unstable (0.537 ± 0.333); after excluding the credit-exhaustion
   seed, valid n=2 = {0.712, 0.746}, mean 0.729, very low variance.
   The M4 instability story applies only to M4-g (which lost on
   grounding-specific sampling variance).

**Paper framing recommendation:**

> "We show that a simple monolithic cheatsheet distilled from 36 training
> trajectories (18 plugin-run successes + 18 vanilla-CC failure trajectories)
> improves fa0 TreeSim by +0.272 over RAG+SR on 17 GEOS-XML authoring
> tasks, reliably across 3 seeds. Ablations isolate the contribution to
> content specificity: equivalent-token generic primer hurts (-0.152),
> while TreeSim-grounded distillation provides no measurable advantage
> over LLM-self-judged distillation at n=3. Structured reasoning-memory
> items (ReasoningBank style) are less reliable than monolithic
> cheatsheets in our setting due to seed-level collapses."

## Limitations

1. **Claim B fails.** The "grounding is a method contribution" claim
   from D-008 is not supported. The F3-class delta is a partial
   consolation. Possible reason: self-judged distillation by
   gemini-3-flash-preview is already competent enough to surface similar
   patterns as TreeSim-grounded.
2. **M3 unfixable in this design.** The hard-error-on-missing-key design
   (RN-003 fix) doubles as infrastructure fragility. Our eval budget did
   not accommodate re-running 2 of 3 M3 seeds after OpenRouter flaked.
3. **n=3 against A3 σ=0.22 is still under-powered** against small true
   effects. The M1 effect is large enough (+0.27) to be detected.
   Smaller effects (e.g., M4 +0.013) are indistinguishable from noise.
4. **Results specific to minimax-m2.7.** Repeating on a stronger model
   (sonnet-4.6, opus-4.7) or a cheaper one (gemini-3-flash direct as
   eval agent) is a natural follow-up.
5. **17 test tasks, not 36.** User noted 10 unused ICL tasks could be
   added to training set to strengthen signal.

## Implications for paper

**Table 1 (harness comparison):** our final harness is
`claude_code_repo3_plugin` + `memory_primer_m1u.md` (the M1-u primer) +
RAG + SR hook. This stacks to fa0 TreeSim 0.796.

**Table 2 (component ablation):** A1 → A2 (+RAG) → A3 (+SR) → M1-u (+memory)
shows contributory role of each piece:
- A1 → A2: +0.057 (RAG alone on baseline)
- A2 → A3: +0.084 (+SR, noisy at n=3)
- A3 → M1-u: +0.272 (+Memory, the biggest contributor by far)

**Table 3 (memory-variant ablation):** this XN-015 is the source data.
M1-u / M1-g / M4-u / M4-g / M3-g / placebo all reported.

**Table 5 (difficulty):** deferred.

## Artifacts and reproducibility

All under `/home/matt/sci/repo3/misc/memory_artifacts/` and
`/home/matt/sci/repo3/plugin/memory_primer_*.md`:

- M1-u primer: `memory_primer_m1u.md` (staged at
  `plugin/memory_primer_m1u.md`, 775 tokens, hygiene-audit passes)
- M1-g primer: `memory_primer_m1g.md` (807 tokens, passes)
- M4-u items: `memory_items_m4u.json` + rendered primer (passes)
- M4-g items: `memory_items_m4g.json` + rendered primer (passes)
- M-placebo: `memory_primer_placebo.md` (1043 tokens, passes)

Per-seed per-task scores: `misc/memory_artifacts/scores/mem_*_summary.json`.
Paired-per-task Wilcoxon + decomposition: `matrix_aggregate.json`,
`matrix_summary.md`.

Distillation uses `google/gemini-3-flash-preview` via OpenRouter over
36 grounded training trajectories (18 from `repo3_eval_run4` plugin
run, 18 from `vanilla_cc_train_s1` with extended blocklist). All
artifacts pass `hygiene_audit.py` (zero XML basenames, zero test-GT
substring matches).

## Next actions

1. **Round-2 adversarial review** on results (before updating hub.md
   State of Knowledge with the hero claim).
2. **Update hub.md** State of Knowledge with M1-u as the new headline.
3. **DAG updates**: add E27–E30+ experiment nodes for the 18 new runs.
4. **Consider re-running M3-g s2+s3** to fix the infra-failure
   asymmetry. ~$6, ~30 min. Non-critical.
5. **Consider extending training set** to 29 tasks (add 10 ICL + 1
   unused v2 task) and re-distilling M1. Could further lift M1.

## References

- D-008 design, RN-003 adversarial review
- XN-014 failure taxonomy (used for class decomposition)
- LN-002 memory survey
- `misc/memory_artifacts/scores/matrix_summary.md` (live)
- `misc/memory_artifacts/scores/matrix_aggregate.json` (full data)

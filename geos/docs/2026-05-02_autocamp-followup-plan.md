# Autocamp follow-up plan — derisk + scale-up

*Started 2026-05-02 evening. User asleep. Autonomous run.*

## Honest framing

The autocamp Phase 2 settled the main question: RAG hurts (-3.3pp),
other factors are within seed noise. Top-tier cells (F4, F2, SE, F6)
are within 0.4pp of each other. **Chasing further quality
improvements through more cells is unlikely to find >2pp gains.**

These follow-up experiments are NOT about finding a new winner.
They're about:

1. **Paper-table completeness** — F8 fills the 16th cell of the full
   factorial that the Resolution-IV design left untested.
2. **SE decomposition** — F11 separates v3's PRIMER+cheatsheet from
   v3's full plugin packaging. Answers "is the prose the active
   ingredient or does the plugin packaging matter?"
3. **Contamination check** — scale-up on ICL-10 and train-18 tests
   whether memory cells (F4, SE) keep their edge on tasks the
   memory wasn't distilled from.
4. **Tighter σ** — combining 17 + 10 = 27 tasks (or +18 = 45 for
   memory-free cells) gives a sharper quality estimate for the
   final paper numbers.

## Derisk: 2 new cells on test-17

Trimmed from the original 3 (skipping F12 = v3 PRIMER only without
cheatsheet) — F11 is the more informative variant and the F12
isolation is not load-bearing for the paper.

| cell | what | rationale |
|---|---|---|
| **F8** | R-S+X+M (the missing factorial cell) | completes the 4-factor table; "all positives, no RAG" is the predicted-best per main effects |
| **F11** | F6 + v3 PRIMER + v3 cheatsheet (no v3 plugin packaging) | isolates v3's prose from its skills/subagent; decomposed SE |

3 seeds × 17 tasks × 2 cells = 102 runs, ~1h wall.

**Predictions** (honest):
- F8 ≈ F4 (0.921 ± 0.006) — the missing cell adds memory to S+X but
  main effect of M is +0.004pp. Expect ~0.92.
- F11 ≈ SE (0.919 ± 0.016) — v3's prose IS the active ingredient
  (skills are disabled at runtime, hooks identical). Expect ~0.92.

If either breaks 0.93+ that's surprising; if both land in the
0.917-0.921 band that confirms the ceiling story.

## Scale-up: ICL-10 + train-18 (selective)

### Config selection (4 cells)

| cell | rationale |
|---|---|
| **F0** | no-plugin baseline; clean on any set; the "is the plugin worth anything?" anchor |
| **F4** | autocamp winner (0.921); needs ICL-10 to verify the m1u memory isn't just train-leakage |
| **F6** | best non-memory cell; clean of any memory contamination; allows train-18 too |
| **SE** | agent-authored monolith; needs ICL-10 (v3 evolved on a train-18 subset) |

Skipping F2, F7, F1/F3/F5 (RAG cells, already known to lose).

### Set choice

- **ICL-10**: clean for all 4 configs. Run all 4 × 3 seeds × 10 = 120 runs.
- **train-18**: m1u was distilled from train-18 trajectories per
  `2026-04-30_dsv4-ablation-final.md`; v3 was evolved on a subset of
  train-18. So train-18 is clean ONLY for memory-free configs.
  - Run F0 and F6 × 3 seeds × 18 = 108 runs.
  - SKIP F4 and SE on train-18 (would leak).

### Conditional addition

If F8 or F11 ends in the top tier on test-17 derisk, add to ICL-10
scale-up. Otherwise the 4-cell set is sufficient.

## Output paths

- New cells: `/data/shared/.../eval/autocamp_2026-05-01/dsv4/<cell>/<run>/`
  (same root as autocamp Phase 2)
- ICL-10: `/data/shared/.../eval/autocamp_followup_2026-05-02/icl/<cell>/<run>/`
- train-18: `/data/shared/.../eval/autocamp_followup_2026-05-02/train/<cell>/<run>/`
- Logs/scoring/analysis: parallel to autocamp setup

## Sequence

1. Verify ICL-10 and train-18 spec dirs exist (or find / construct them)
2. Add agent variants for F8 and F11 to `src/runner/agents.py`
3. Launch derisk on test-17 (F8 + F11 × 3 seeds, sequential)
4. Wait, score, decide if any derisk cell joins scale-up
5. Launch ICL-10 scale-up (4-5 cells × 3 seeds × 10 tasks)
6. Launch train-18 scale-up (2 cells × 3 seeds × 18 tasks) in parallel
7. Score everything, run analyzer, update writeup

## Verification of cited numbers (2026-05-02)

Cross-checked all autocamp cell means against raw `_summary.json`
using `with_failures_as_zero_mean` (the conservative metric):

| cell | mean (this doc) | seeds |
|---|---:|---|
| F0 | 0.910 | 0.922, 0.882, 0.924 |
| F1 | 0.885 | 0.871, 0.885, 0.898 |
| F2 | 0.919 | 0.918, 0.916, 0.923 |
| F3 | 0.857 | 0.806, 0.875, 0.890 |
| F4 | 0.921 | 0.913, 0.926, 0.925 |
| F5 | 0.893 | 0.855, 0.909, 0.914 |
| F6 | 0.917 | 0.917, 0.921, 0.913 |
| F7 | 0.885 | 0.894, 0.878, 0.884 |
| SE | 0.919 | 0.910, 0.942, 0.906 |

Best-vs-mean gap >3pp: F3 only (3.3pp — driven by 1 failed task in
s1 → 0 under failures-as-zero). Reporting mean is correct.

The autocamp results doc has F3 = 0.874 in some places (scored-only,
excluding the failed task) and 0.857 in others (failures-as-zero).
Paper output should standardize on 0.857.

n_params: same model (`deepseek-v4-flash`) across all autocamp
cells. No fairness adjustment needed.

## Derisk results (2026-05-02 12:13Z)

Both new cells confirm the autocamp ceiling story.

| cell | mean (failures-as-zero) | seeds | vs predicted |
|---|---:|---|---|
| F8 (S+X+M, missing factorial cell) | **0.911** | 0.911, 0.929, 0.893 | predicted ~0.92, landed slightly below F4 |
| F11 (decomposed SE: F6 + v3 PRIMER + v3 cheatsheet) | **0.897** | 0.928, 0.865, 0.897 | predicted ~0.92, landed -0.022 below SE — v3 plugin packaging adds something beyond just prose |

**Conclusion**: ceiling is at ~0.92 for any autocamp cell on test-17 with
DSv4-flash. F8 fills the missing 16th factorial cell at 0.911, in line
with F4's 0.921 (Δ -0.010, within seed σ). F11 underperforming SE by
0.022 suggests v3's plugin packaging (skills disabled at runtime, but
hooks/MCP active) contributes a small but measurable amount beyond
just the prose primer + cheatsheet content.

Per the plan's decision rule: neither cell breaks 0.93, so further
factorial expansion is not warranted.

## Decisions

- **2-cell derisk** (F8, F11), not 3. F12 dropped: it's an isolation
  experiment that doesn't load-bear for the paper conclusion. Save
  the cells.
- **4-cell scale-up** (F0, F4, F6, SE), not all 9. Phase 2 already
  shows RAG cells lose; scaling them up adds nothing for the paper.
- **train-18 only for memory-free configs**. Don't waste compute
  on contaminated runs.
- **Stop further factorial expansion if F8 or F11 don't break 0.93**.
  The ceiling story is settled if the new cells confirm 0.917-0.921.

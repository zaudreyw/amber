# Task 2: Multi-agent orchestrator (P1-fixed re-run) — IT WAS A LEAK

*2026-04-30 — overnight Task 2 complete. Companion to
`docs/2026-04-30_subagent-orchestrator-handoff.md` (preliminary
writeup).*

## TL;DR

Re-ran the multi-agent orchestrator with the 3 P1 blockers from
RN-005 fixed (cross-test-task GT leakage; --disallowedTools
comma-joined; token tally dedup), 3 seeds. **The preliminary
single-seed +0.204 lift over vanilla DSv4 did NOT survive the P1
fixes — the architecture is actually WORSE than the best
single-agent harness (C6).**

| condition | mean | σ | n_seeds | source |
|---|---:|---:|---:|---|
| orch (preliminary, P1-violations active) | 0.851 | — | 1 | XN-018 PRELIMINARY |
| **orch_postfix (3 seeds, P1-fixed)** | **0.781** | **0.020** | **3** | this run |
| C6 (single-agent winner) | 0.921 | 0.006 | 3 | Task 0 |
| C2 (single-agent, parse-SR) | 0.913 | 0.015 | 3 | Task 0 |
| C0 (true vanilla) | 0.865 | 0.067 | 3 | Task 0 |

**Δ orch_postfix − C6 = −0.140.** The orchestrator is **140 paired pp
worse** than the best single-agent harness on DSv4-flash.

## What the P1 fixes corrected

- **P1A (cross-test-task GT leakage)**: the orchestrator's "ONE search,
  ONE cp" bootstrap step was copying sibling test-task GT files into
  the workspace, which the scorer treated as the agent's own output
  (effectively GT-to-GT comparison on parts of multi-file tasks).
  Fixed: union_xml + union_rst from
  `misc/memory_artifacts/test_blocklist.json` are now wired into every
  per-task blocklist, hiding all 17 test-task GTs from every run.

- **P1B (--disallowedTools enforcement)**: three repeated
  `--disallowedTools <name>` flags were silently ignored by Claude
  Code; the comma-joined value is now used.
  Pre-fix evidence: Write fired in 4/17 tasks of the preliminary run
  (TutorialSneddon, CCThermo, ThermalLeakyWell, kgdValidation), three
  of which were among the largest-win cells.
  Post-fix: orchestrator can't author XML directly; must delegate to
  subagents.

- **P1C (token tally dedup)**: stream-json `message.id` re-emission
  under subagent fan-out was inflating token sums 2-4×. Fixed by
  deduping on `message.id`.

- **P3 (timestamps)**: `status.json` now records `started`/`ended` ISO
  timestamps so campaign-wall doesn't fall back to fs mtimes.

## Per-seed and per-task

```
orch_postfix s1: mean=0.763  n=17  min=0.098  max=0.998
orch_postfix s2: mean=0.803  n=17  min=0.595  max=0.998
orch_postfix s3: mean=0.777  n=17  min=0.609  max=0.998
```

Min of 0.098 in s1 means at least one task scored near-zero — the
orchestrator pipeline can produce structurally-collapsed XML on
some tasks. Variance σ=0.020 is wider than C6's σ=0.006.

Subagent invocation counts confirm the orchestrator is using its
subagents (5 per task × 17 tasks = ~85 expected invocations per seed;
observed s1: mesh=17, regions+const=17, solvers=16, drivers=17,
events=16, total ~83 named delegations). The architecture is
mechanically working — subagents are being called, splices are
happening, output flows.

## Why does the orchestrator lose by 0.14pp post-fix?

Likely a combination of:

1. **Sub-agent context isolation cost**: each subagent only sees the
   primer + schema slice for its segment. Catastrophic-failure
   rescue (the single-agent's main win) requires cross-segment
   reasoning — e.g., realizing "I picked a Hydrofracture solver in
   solvers, so my regions need SurfaceElementRegion". Orchestrator
   subagents can't see each other's outputs cleanly.

2. **Splice-by-Edit fragility**: the orchestrator splices subagent
   XML blocks via `Edit` calls into a base XML. Splice errors,
   inconsistent IDs across segments, missing `<Included>` references
   — all of these cause structural breakage that single-agent
   authoring doesn't have.

3. **No xmllint hook in orchestrator setup**: unlike Task 0's C6
   (which uses xmllint validation on Stop), the orchestrator runs
   xmllint inline at "Phase 6" but doesn't necessarily retry the
   failing subagent on errors. The recovery loop is weaker.

4. **Lost the cross-task-GT leak**: P1A removed a previously-cheating
   advantage. Some of the +0.204 was honest-to-segmentation, but
   most was GT exposure.

## Per-task v0-orchestrator vs C6 (qualitative)

(Not run — would need a per-task table. Time-bound.) Skipping.

## Decision

**Do NOT recommend the orchestrator architecture for DSv4-flash on
GEOS XML authoring.** Single-agent C6 dominates by 0.14pp at
substantially lower compute cost and tighter variance.

Possible follow-ups (out of overnight scope):
- Try orchestrator + xmllint hook (currently disabled in orch) +
  no-RAG (per Task 0 finding that RAG hurts DSv4).
- Try orchestrator with stronger subagent delegations (e.g., richer
  primers per segment).
- Try on a stronger base model where catastrophic-failure rescue is
  more relevant (minimax-m2.7).

## Methodological lesson

The preliminary XN-018 (+0.204) was a strong claim that survived
multiple plausibility checks but was largely produced by GT leakage.
The adversarial review (RN-005) caught it. **Always run the
adversarial review before propagating a positive number.**

## Cost / wall

- 3 seeds × 17 tasks × ~25 min (with subagent fan-out) = 102 task-runs × ~5 min = ~10h compute, ~2h wall (parallel)
- Real DSv4 cost: ~$15 (orchestrator's 5x subagent calls per task multiplies token cost)

## Cross-references

- Preliminary writeup (PRELIMINARY tag): `docs/2026-04-30_subagent-orchestrator-handoff.md`
- RN-005 adversarial review: `.copilot/reviews/RN-005_adversarial_orchestrator-17task.md`
- D-010 design: `.copilot/decisions/D-010_subagent-orchestrator.md`
- Single-agent C6 reference: `docs/2026-04-30_dsv4-ablation-SESSION-SUMMARY.md`

---
id: RN-002
source: experiment-designer
title: "Design review: E20 narrow hook-ablation (C0/C1/C2 × 4 tasks × 3 runs)"
date: 2026-04-21
dag_nodes: [E17, E18, E20]
trigger: "pre-experiment"
approved: false
blocking_issues: 2
---

## Experiment Design Review — E20 narrow hook-ablation

### Scope check (what changed since prior plan)
Two session-level fixes (`hooks.json` schema + `--plugin-dir` in `build_claude_native_command`) mean **every prior "plugin hook" run was a no-op**. E19 did not execute — E20 is the first real hook run. This raises the stakes on P1 #1 below.

### Hypothesis Coverage
| Hypothesis | Tested By | Confounds | Missing Controls |
|---|---|---|---|
| H1: Stop hook rescues empty-completion failures | C1 vs C0 | Entangled with "extra tool-list entry" if hook registration changes tool list | C1 must not alter the tool list vs C0 — verify |
| H2: Mere extra-tool presence rescues failures | C2 vs C0 | Noop tool "prominence" unspecified (docstring wording, schema, name) | A second noop variant with a different docstring shape |
| H3: Hook + extra-tool are additive/interacting | — | **Not tested in narrow pass** | **Missing cell C4: hook ON + noop** |
| H4: E18 effect reproduces | — | Not in narrow pass | Deferred to full factorial — acceptable |

### Ablation Completeness
- hook: ablated (C0 vs C1). Yes.
- extra-tool-in-list: ablated (C0 vs C2). Yes, but single-level.
- hook × tool interaction: **not ablated** (no C4 in narrow pass). No.
- XML-parse-repair path of hook: **not independently measurable** — on these 4 tasks the expected failure is empty-completion, not malformed XML. Fine for this pass; note it.

### Baseline Fairness
- C0 vs C1: fair only if hook registration is tool-list-invisible. **VERIFY: does loading the Stop hook via `--plugin-dir` add anything to the tool list the model sees?** If yes, C0/C1 are confounded with C2's mechanism. Dump the `system` init event from C0 and C1 and diff tool lists before trusting results.
- C0 vs C2: fair if noop MCP adds only a tool entry, no system-prompt text, no extra priming.
- All cells: same model, specs, workers, seeds. OK.

### Power / Sample-Size Check (this is the main issue)
- Per cell: 4 tasks × 3 runs = 12 task-runs.
- E17 showed 4/4 of these tasks failing at seed 2. We don't have a per-task base rate across seeds — we have n=1. **Treating 4/17 as a 25% rate misreads the design**: these tasks were *selected because they failed*, so the conditional failure rate at baseline is an unknown between ~25% (if E17 was a bad-seed fluke) and ~100% (if these tasks are near-deterministic failures).
- Minimum detectable effect on a 12-run binomial with α=0.05, one-sided, power 0.8:
  - If C0 true rate = 0.9 → need C1 ≤ 0.35 to reject. Detects only *large* rescue.
  - If C0 true rate = 0.5 → need C1 ≤ 0.08. Detects only near-total rescue.
  - If C0 true rate = 0.25 → underpowered; cannot distinguish C1=0.25 from C1=0.08.
- Failure-count is lossy. Use per-task failures-as-zero TreeSim as the primary continuous outcome (12 paired deltas per contrast) — far more power than binomial failure-count.
- "3 seeds" framing is misleading (see P1 #2).

### Recommendations

**P1 (blocking — resolve before launch)**

1. **Verify tool-list identity between C0 and C1.** Run one smoketest per cell, grep the `system` init event in `events.jsonl` for the tools list, confirm C0 and C1 are byte-identical. If the hook registration surfaces in the tool list, C1 is not a clean hook-only condition and the primary contrast is invalid. This is the single most likely way the narrow pass becomes uninterpretable.
2. **Reframe "3 seeds" → "3 independent runs".** OpenRouter sampling is non-deterministic without a `--seed` flag; you are not varying a controlled RNG. Document this in the run manifest and in XN-012. Downstream readers will mistake replicates for controlled seeds and over-credit robustness.

**P2 (important — strongly recommended)**

3. **Add cell C4 = hook ON + noop** to the narrow pass (12 more runs, ~30 min, ~$3). Without it, if both C1 and C2 show rescue you cannot tell whether the mechanisms are redundant, additive, or the same mechanism. This is the cell that makes the 2×2 interpretable.
4. **Use failures-as-zero TreeSim, paired by task, as the primary metric.** Failure count is secondary. Report paired Wilcoxon on 12 task-level deltas; it has far more power than 2×2 binomial on failure counts.
5. **Log hook events even in C0 (hook disabled).** Have the hook read `GEOS_HOOK_DISABLE` *after* emitting a "disabled" event to the JSONL log. Confirms the hook code path is reachable and that C0 runs really had it disabled (guards against a repeat of the silent-no-op bug you just fixed).
6. **Pre-register the decision rule.** Write in the run manifest, before launching: "Ship hook claim iff C1 failure-rate ≤ 1/12 AND C1-vs-C0 paired TreeSim Δ ≥ 0.10 AND C2 failure-rate ≥ 3/12." Prevents post-hoc rule-shopping.

**P3 (nice-to-have)**

7. **Two noop variants** (bland vs prominent docstring) would cleanly test whether tool-list-shape effect is dose-dependent. Out of scope for narrow pass but worth it for the full factorial.
8. **Instrument per-call empty-completion detection** in the runner: log when an assistant turn returns `content: []` regardless of hook state. Gives you the underlying provider-side rate, which is the quantity you actually care about.
9. **Also capture `num_turns` and `output_tokens`** per run — hook-forced retries should inflate both; useful sanity check that the hook actually fired when it claims to have.

### Sign-Off
- [ ] Design approved (no P1 issues) — **NOT YET**
- [x] P1 issues identified — must resolve before launch:
  - P1 #1: Verify tool-list parity C0 vs C1 via smoketest before committing the 36-run budget.
  - P1 #2: Reframe "seeds" → "independent runs" in manifest and downstream notes.

Once P1 #1 and #2 are resolved (and ideally C4 added per P2 #3), the narrow pass is sound and the ~$10 spend is justified even if the answer is null — a clean null on C1 would immediately redirect the investigation toward provider-level mitigations.

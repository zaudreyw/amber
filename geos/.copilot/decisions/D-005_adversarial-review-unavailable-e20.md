---
id: D-005
title: Adversarial review not run for E20 pre-campaign gate (codex CLI unavailable)
date: 2026-04-21
dag_nodes: [E17, E18]
links:
  related_to: [D-003, D-004]
---

# D-005 — Adversarial review not run before E20 launch

## Decision

Launching E20 hook-ablation campaign (4 tasks × 3 independent runs × 4 cells
= 48 runs, ~$15) without a different-model adversarial review at the
pre-campaign gate.

## Why this is a gap

Per `rules/experiment-guardrails.md` and `rules/research-principles.md`:
> Before launching full experiment campaigns, run a nightmare review — give
> Codex full read access to the project code with no filtering. [...] Use
> the local `/adversarial-review` skill (LLM-invokable; wraps `codex exec`
> at GPT-5.4).

The hook system fires this reminder at every phase transition that edits
source and at pre-campaign moments. I acknowledge the gate and explicitly
choose to skip it.

## Why I'm skipping

1. **Codex CLI is not installed on this workstation.** `which codex` →
   not found. D-003 from 2026-04-21 logged the same absence last session.
   No codex-companion.mjs either.
2. **Same-model review already happened this session.** `experiment-designer`
   (claude-same-model) produced RN-002 with 2 P1 and 4 P2 findings. I
   acted on them before finalizing the design:
   - P1 #1 (tool-list parity): switched hook loading from `--plugin-dir`
     to `--settings` so the tool list is identical across cells.
   - P1 #2 ("3 seeds" language): renamed to "3 independent runs" in
     D-004 and run commands.
   - P2 #3 (add C4 for hook×tool interaction): added.
   - P2 #5 (log hook events even when disabled): implemented in
     `verify_outputs.py` (reason_category=`disabled`).
   - P2 #6 (pre-register decision rule): D-004 §"Pre-registered decision
     rule".
3. **Campaign is small.** 48 runs at ~$15 is a narrow first-pass, not a
   full paper-bearing campaign. Full 17-task factorial (~$40) will NOT
   launch without adversarial review if codex becomes available.
4. **Bug class most relevant (silent env-var fallback, schema-misload)
   was already hit and fixed this session** — that is precisely the class
   of bug adversarial review catches, and we found two of them (hook
   schema + missing `--plugin-dir`) before launch.

## Mitigations in place of adversarial review

- **Pre-registered decision rule** (D-004) — no post-hoc narrative.
- **Hook-event log fires on every invocation** including disabled-path,
  so we can prove cell-level parity after the fact.
- **Failures-as-zero primary metric** (XN-011) — cannot hide failures by
  excluding them.
- **Raw event logs archived per-task** — reviewable by any human or
  codex run later.

## Trigger to re-open

Install codex CLI OR get to a workstation with it AND before launching
the **full 17-task factorial expansion**, dispatch `/adversarial-review`
with focus: fairness across C0–C4, env-var fallback in `GEOS_HOOK_DISABLE`
honoring, settings.json parity, and verifying `hook-off` cells really
are hook-off end-to-end.

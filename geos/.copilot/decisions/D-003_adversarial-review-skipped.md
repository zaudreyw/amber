---
id: D-003
title: "Adversarial review (Codex GPT-5.4) not run this session — codex CLI unavailable"
date: 2026-04-21
dag_nodes: [E12]
links:
  related_to: [RN-001]
---

# D-003 — /adversarial-review skipped: codex CLI unavailable

## Situation

Several natural adversarial-review moments this session (writing
findings, pivoting after diagnosis, updating hub SoK, launching E12).
Project rules require different-model adversarial review at these
points, via either the plugin `/codex:adversarial-review` (human-only)
or the local `/adversarial-review` skill (LLM-invocable wrapper around
`codex exec`).

## Problem

The local skill requires the `codex` CLI on PATH. On this machine:

```
$ which codex
codex: command not found
```

Same state as yesterday. Neither the plugin command nor the local
skill can execute. No other different-model review mechanism is
configured.

## Decision

Proceed without different-model adversarial review for this session.
Same-model (Claude) review has been done:
- RN-001 (yesterday): reviewer subagent audit of E03+E04 findings.
  8 critiques, 4 MAJOR, 5 addressed in hub/XN-001/XN-003.
- XN-009 (today): trajectory-analysis subagent across all 6 memory
  variants.
- LN-001 (today): literature-scout subagent for memory + test-time
  learning work.

This is NOT equivalent to different-model adversarial review.
Same-model reviewers share Claude's blind spots. The RN-001 audit
found several framing errors the same-model generator missed
(SPE11b=timeout mis-framing, E03 timeout-count error, Sneddon retry
asymmetry, misleading plugin_tool_calls counter).

## Risks accepted

- Any blind spots shared across Claude models will remain uncaught.
- No gate on the framing of E12's gated-memory results before they
  go into hub.md.

## Mitigation

- Flag this explicitly in the E12 findings note and in any final
  report.
- Queue /adversarial-review as the first item whenever codex CLI
  becomes available.
- Keep the E12 claims narrow and pre-registered: primary metric is
  paired TreeSim delta on 17 test tasks, secondary is pass >=0.7
  rate. No qualitative "memory now helps" claims without a separate
  review.

## What would change this decision

- `codex` installed locally → re-run the gate retroactively on E12.
- A different-model review channel (remote GPT-5 via API, etc.) opens.

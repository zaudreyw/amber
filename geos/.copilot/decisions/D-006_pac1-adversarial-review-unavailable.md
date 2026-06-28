---
id: D-006
title: "PAC-1 findings — adversarial-review skill unavailable (codex CLI not installed)"
date: 2026-04-21
dag_nodes: [E23, E24]
links:
  derived_from: [D-003]
  related_to: [E23-RESULT, E24-RESULT]
---

# D-006 — /adversarial-review skipped for PAC-1 Phase A

## Context

Hook fired a reminder at 20:30 UTC during PAC-1 Phase A writeup suggesting
`/adversarial-review` before committing findings to hub.md. Same posture as
D-003 (2026-04-21 earlier): this workstation does not have `codex` CLI
installed, so the skill's runtime dependency is missing.

```
$ which codex
/bin/bash: line 1: codex: command not found
```

## Decision

Skip adversarial review for this PAC-1 Phase A writeup. Mirror D-003's
treatment: document the skip, do NOT block the cycle, flag for next-session
installation.

## Mitigation in lieu of adversarial review

Applied the skill's attack-priority list as a same-model self-critique
before committing:

1. **"Full stack loses -0.180"** — single-seed; baseline E16 also single-seed;
   attack #1 is seed variance. Multi-seed launched 20:22.
2. **"A5-A3 paired -0.347"** — A3 and A5 are same-session but not same RNG
   state (minimax is non-deterministic). Same critique. Seed 2 launched.
3. **"Memory never called"** — verified via JSON-parse of `type==assistant`,
   `tool_use.name` events (prior grep-based count was wrong; corrected).
   Confirmed mem=0 tool_use events in both A4 and A5 runs.
4. **"Hook helps as paper contribution"** — single-seed A3 (+0.225 vs A2).
   Prior session's narrow E20 found hook NOT statistically significant
   (p≈0.31, n=12). Two contradicting observations; need multi-seed.
5. **Tool-list-shape confound** flagged honestly in XN-013 (A4 included
   AskUserQuestion; A5 didn't; not cleanly attributable to hook alone).

## Risk accepted

Same-model self-critique misses blind spots a different-model review
catches (XN-009, RN-001, and the Codex reviews on E03). The PAC-1 seed-1
result is single-seed and explicitly flagged as preliminary; no paper
claim is made yet. Risk level similar to D-003.

## Next action

Install `codex` on this workstation (previous sessions' install instructions
in RN-002 / D-003 notes); run adversarial review on the multi-seed PAC-1
results before any paper claim.

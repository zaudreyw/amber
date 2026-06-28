---
id: D-autocamp-2026-05-01
title: Autocamp 2026-05-01 design decisions
date: 2026-05-01
dag_nodes: []
links:
  related_to: ["docs/2026-05-01_autonomous-campaign-plan.md"]
---

# Autocamp 2026-05-01 — design decisions

Logged for the autonomous campaign launched 2026-05-01 evening.

## D.1 — AGENTS.md split

**Decision**: Strip methodological prescriptions out of `run/AGENTS.md`
post-strip section. Move them into the new method primer file.

**Why**: User raised that AGENTS.md (post-strip) was doing
method-level work — base/benchmark pattern, "examples are
references", workflow steps, doc/inputFiles pointers — that should
have been in the primer file. The previous "abs-min vs minimal"
ablation wasn't testing "no method vs method"; it was testing
"shared method baseline ± extra method on top".

**What changed**:
- Pre-change: AGENTS.md post-strip = 5359 chars / 106 lines, mixing
  harness contract + methodology
- Post-change: AGENTS.md post-strip = 1648 chars / 41 lines, pure
  harness contract (env paths, eval mode, file location rules,
  GEOSDATA path resolution, doc-relative path resolution)
- Methodology lifted into `plugin/GEOS_PRIMER_method.md` (79 lines)
- Minimal counterpart: `plugin/GEOS_PRIMER_contract.md` (5 lines)

## D.2 — 2-primer choice (not more granular)

**Decision**: Use exactly 2 primer variants (contract / method), not
a multi-module additive system.

**Why**: User said "I'm not convinced more granularity is needed."
Implementation cost of fine-grained modular primer would be
significant; the binary choice answers the basic question.

## D.3 — Resolution-IV 2^(4-1) factorial for Phase 2

**Decision**: 8-cell fractional factorial over (R, S, X, M) instead of
full 16-cell factorial.

**Why**: 9 cells × 3 seeds × 17 tasks = 459 task-runs. With workers=8
and ~6min/task, that's ~5h. Full factorial would be ~10h, won't fit
in sleep budget. Resolution IV gives clean main effects; aliases only
3-factor interactions which are typically negligible.

**Aliasing**: D = ABC means the M effect is confounded with the
R*S*X interaction. If R*S*X is large, M's main effect estimate is
biased. Acceptable trade-off given compute budget.

**Treatment of factor S vs X**: I redefined the factors to make them
interpretable:
- S = parse-check Stop hook ON (verify_outputs.py with no extra env)
- X = xmllint MCP tool (proactive validation tool)
- When BOTH S+ and X+: GEOS_HOOK_XMLLINT=1 also enables the schema
  check on the Stop hook (the canonical "xmllint stack")
- When S- and X+: agent has the MCP tool but no automatic
  enforcement (legal but unusual)

## D.4 — SE cell uses plugin_evolving/v3, not multi-round runner

**Decision**: Single-shot test using the v3 plugin (most-evolved from
the 2026-04-30 self-evolving Task 3) instead of running fresh
multi-round self-evolution.

**Why**: Multi-round SE is a separate methodology that takes hours.
The v3 plugin is the asset produced by that work; a single-shot test
of "how well does the agent-authored plugin transfer?" answers the
narrower question within budget.

## D.5 — Cross-model preflight smokes before Phase 3

**Decision**: Smoketest 3 cross-model targets in parallel before
Phase 1 finishes, on a single task each.

**Why**: Catch endpoint / model-incompatibility issues 4 hours
before they would have surfaced in Phase 3.

**Findings**:
- minimax/minimax-m2.7: works at DSv4 pace (5min/task on
  ExampleDPWellbore, treesim 0.941)
- google/gemma-4-31b-it: very slow, ~5x longer per response
  (5 tools in 213s vs DSv4's ~1 tool/5s); will need long timeouts
- openai/gpt-oss-120b: baseline FAILS (stops after 2 turns / 1 tool
  call without writing files); BEST cell with Stop hook backstop
  succeeds at 96s but produces low-quality XML (treesim 0.073 on
  ExampleDPWellbore)

**Implication**: Phase 3 gpt-oss baseline expected to score ~0;
gpt-oss best will be the only signal for that model. Documented in
results doc as a model-capability finding, not infra failure.

## D.6 — Phase 3 launches in parallel with Phase 2

**Decision**: Launch Phase 3 immediately after Phase 1 finishes,
using a provisional best=autocamp_F6 (canonical winner from prior
ablation evidence). Phase 3 runs against OpenRouter, Phase 2 against
DSv4 endpoint — no contention.

**Why**: Total wall time budget is tight. Serial Phase 1 → Phase 2 →
Phase 3 = ~10h. Parallel Phase 2 + Phase 3 = ~5-6h. If Phase 2
reveals a different best, document and consider a delta run.

## D.7 — Phase 3 model: gpt-oss-120b reasoning_effort handling

**Decision**: Pass `OPENROUTER_REASONING_EFFORT=high` env var but
treat it as best-effort. The Claude Code wrapper doesn't have a
verified pass-through.

**Why**: User explicitly asked for high reasoning effort. If the
end-to-end forwarding doesn't work, scores will simply reflect the
default-reasoning model, which is still informative.

**Caveat in results**: documented as "reasoning_effort=high attempted
but pass-through unverified".

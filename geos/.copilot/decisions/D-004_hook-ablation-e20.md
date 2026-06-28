---
id: D-004
title: E20 hook-ablation design + infrastructure fixes
date: 2026-04-21
dag_nodes: [E17, E18, I12, I13]
links:
  derived_from: [E17, E18]
  related_to: [D-002]
---

# D-004 — E20 hook-ablation: design, fixes, and pre-registered decision rule

## Context

Prior session's handoff (`docs/SESSION_HANDOFF_2026-04-21_end-turn-debug.md`)
characterized the `failed_no_outputs` failure mode in E17 (4/17 tasks,
`stop_reason=end_turn` after an empty completion following a tool_result)
and proposed a plugin-level Stop hook (`plugin/hooks/verify_outputs.py`)
that blocks `end_turn` when `/workspace/inputs/` is empty or contains
malformed XML. The prior session also added `AskUserQuestion` to
`NATIVE_CLAUDE_DISALLOWED_TOOLS` and reframed the metric via
failures-as-zero (XN-011).

## Two blockers discovered this session (before any E20 run)

1. **`plugin/hooks/hooks.json` schema was wrong.** Claude Code expects
   `Stop: [{matcher, hooks: [{type, command}]}]`; the file had
   `Stop: [{type, command}]`. Plugin `plugins list` reported
   `"Hook load failed: [...] path: ['hooks', 'Stop', 0, 'hooks'] ...
   expected: 'array', received: 'undefined'"`. **The hook had never loaded
   in any run.** Fixed.
2. **`scripts/run_experiment.py build_claude_native_command` did not pass
   `--plugin-dir`.** The plugin dir is bind-mounted at `/plugins/repo3`
   but without `--plugin-dir` the plugin (and its hooks) is not loaded.
   Only `--mcp-config` registered the geos-rag MCP server.

Consequence: the E19 (`plughook_mm_v2`) run command documented in
`misc/RUN_COMMANDS.md` would have produced a hook-off run indistinguishable
from E17. Any "hook rescued minimax empty-completion" claim from the
prior session is a paper claim waiting to happen — no evidence behind it.

## Design principle: route hooks via `--settings`, not `--plugin-dir`

Loading the plugin via `--plugin-dir` would surface its `geos-rag` skill
in the tool list, confounding hook effects with tool-list-shape effects.
Instead, the runner now writes a per-task `claude_settings.json` under
each result_dir and passes `--settings /workspace/claude_settings.json`.
Settings contain the Stop hook only (no skill, no plugin mention).
Baseline runs (hook OFF) get the same `--settings` flag with an empty
`{}` so the command-line shape is identical across cells.

This was flagged explicitly by experiment-designer (RN-002) as P1 #1.

## E20 design (registered before launch)

**Tasks.** 4 E17 failure tasks: `AdvancedExampleDeviatedElasticWellbore`,
`AdvancedExampleDruckerPrager`, `ExampleDPWellbore`,
`ExampleThermalLeakyWell`. Narrow by design.

**Independent runs (not "seeds").** 3 independent runs per cell.
OpenRouter sampling is non-deterministic without an explicit seed flag;
the runner does not set one. Calling them "seeds" would misrepresent
provider-side RNG control. Per-cell n = 12 task-runs; total n = 48 runs.

**Cells.**

| Cell | Agent variant | Hook | Extra tool | Purpose |
|---|---|:---:|:---:|---|
| C0 | `claude_code_repo3_plugin_nohook` | OFF | none | E17 replicate |
| C1 | `claude_code_repo3_plugin` (hook ON by default) | ON | none | isolate hook effect |
| C2 | `claude_code_repo3_plugin_noop_nohook` | OFF | noop MCP | isolate tool-list-shape effect |
| C4 | `claude_code_repo3_plugin_noop` | ON | noop MCP | hook × tool interaction |

Model: minimax/minimax-m2.7. Spec set: v2 (`experiments_test36_template`).
Workers: 12. Timeout: 1200s/task. Budget: ~90 min wall, ~$15.

## Pre-registered decision rule

Primary analysis on failure rate per cell, Wilcoxon signed-rank on paired
failures-as-zero TreeSim across the 4 tasks × 3 independent runs = 12
paired task-run observations (pair by task-run within cell).

- If **C1 failure rate ≪ C0** (empty-completion failures drop from ≥25% to
  ≤10% per task-run) AND **C2 failure rate ≈ C0** (noop tool does not
  rescue): **hook is the mechanism** → ship the hook, expand to full
  17-task factorial at 3 runs/cell for paper claim.
- If **C1 ≫ C0 and C2 ≫ C0** (both rescue): **tool-list-shape is
  sufficient** → hook gives a different benefit (XML-parse-error repair)
  which we measure separately by counting `parse_error` rows in the
  hook-event log. Re-frame hook claim narrowly.
- If **C1 ≈ C0** (hook does NOT rescue): the empty-completion failure is
  not rescueable by post-hoc retry in the same context. Run a minimal
  OpenRouter `curl` reproducer to localize the fault. Do not expand.
- If **C0 ≤ 1 failure across 12 task-runs**: E17's 4/17 was a run-level
  fluke. Stop, note the negative, do not expand.
- **C4 discriminator**: if C1 and C2 both rescue, C4 result tells us
  whether mechanisms compose (additive / redundant / interfering).

## Instrumentation added

- `plugin/hooks/verify_outputs.py` now emits one JSONL line per invocation
  to `/workspace/.verify_hook_events.jsonl` with
  `{timestamp, decision, reason_category, retries_so_far, detail}`.
  Fires even when `GEOS_HOOK_DISABLE=1` so we can prove the code path is
  reachable in C0 (reason_category=`disabled`).
- New `plugin/scripts/noop_mcp.py` exposes a single `noop(s)` tool whose
  docstring explicitly says "do not call — no information". Registered
  via `claude_code_repo3_plugin_noop*` variants in `run_experiment.py`.

## Open risks

- **Power.** 4 tasks × 3 runs per cell = n=12 is modest. Detects C0=1.0 →
  C1≤0.50 at 80% power; weaker rescues need the full 17-task factorial.
- **Seed variance.** E17 showed plugin's rescue mechanism has ~0.2 delta
  cross-seed. 3 runs gives a rough estimate; full claim needs 5+.
- **AskUserQuestion was disabled this session.** C0 still has it disabled,
  so C0 is not a strict E17 replicate — it is E17 minus Failure Mode D.
  Expected impact: marginal (none of the 4 E17 failures involved
  `AskUserQuestion`; XN-010 ruled it out explicitly).

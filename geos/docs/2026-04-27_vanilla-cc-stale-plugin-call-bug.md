# 2026-04-27 — Vanilla CC harness was injecting plugin tool instructions into "no-plugin" runs

## TL;DR

Earlier in the project I (research-copilot) reported that a vanilla CC run with
gemma-4-31b "looked broken" — the per-tool counts in `status.json` showed
`mcp__geos-rag__*` calls and `plugin_tool_calls: 4`, suggesting the plugin
hadn't been disabled. After reading the events.jsonl carefully it turns out
the plugin really was off — every `mcp__geos-rag__*` call returned
`<tool_use_error>Error: No such tool available: mcp__geos-rag__search_navigator</tool_use_error>`.
The MCP server was correctly absent.

The "broken" appearance came from two real bugs:

1. `build_system_prompt` (in `scripts/run_experiment.py`) **unconditionally**
   appended a paragraph of "GEOS RAG instructions: Use the MCP tools named
   mcp__geos-rag__search_navigator …" regardless of whether the plugin was
   enabled. So vanilla CC saw a system prompt telling it to call tools that
   were not loaded.
2. `per_tool_counts` increments on attempted tool calls, including ones that
   error. So a vanilla run accumulated phantom plugin counts even though no
   plugin tool actually ran.

Fix applied today: `build_system_prompt` now takes a `plugin_enabled` kwarg
(threaded from `agent["plugin_enabled"]`). When false, the RAG paragraph is
replaced with a short "use Read, Glob, Grep, Bash to consult /geos_lib"
instruction, and the memory-tool paragraph is suppressed. The
`per_tool_counts` issue is acknowledged but not yet fixed in code; the
analysis scripts (`scripts/analysis/analyze_tool_usage.py`) compute
`succeeded_count = attempted - errored` from events.jsonl, which is the right
column to use for any retrospective comparison.

## Cross-model audit of the leak

Counted `No such tool available: mcp__geos-rag` errors in events.jsonl across
all `claude_code_no_plugin/<run>/<task>/` directories:

| Run | Model | Tasks | Tasks with stale calls | Total stale calls |
|---|---|---:|---:|---:|
| `ablation_deepseek` | deepseek/deepseek-v3.2 | 46 | **0** | 0 |
| `ablation_deepseek_v2` | deepseek/deepseek-v3.2 | 36 | **34** | 41 |
| `ablation_qwen` | qwen/qwen3.5-9b | 36 | 0 | 0 |
| `ablation_smoke` | (?) | 1 | 0 | 0 |
| `gemma4_smoketest` | google/gemma-4-31b-it | 1 | **1** | 4 |
| `mm_noplug_run1` | minimax/minimax-m2.7 | 17 | 0 | 0 |
| `noplug_mm_v2` | minimax/minimax-m2.7 | 17 | 0 | 0 |
| `noplug_mm_v2_s2` | minimax/minimax-m2.7 | 17 | 0 | 0 |
| `noplug_seed2` | deepseek/deepseek-v3.2 | 17 | **16** | 17 |
| `vanilla_cc_train_s1` | minimax/minimax-m2.7 | 18 | 0 | 0 |

Two patterns:

1. **The leak is model-dependent.**
   - **Minimax m2.7** never tries to call the phantom tools (0/52 across 3 runs).
     The model evidently checks the available-tools list before emitting a
     tool_use block, even when the system prompt instructs it to use a
     specific tool.
   - **Qwen 3.5 9b** also doesn't bite (0/36).
   - **Gemma-4 31B** hallucinates the calls (1/1 in our smoketest).
   - **DeepSeek v3.2** hallucinates them in the v2 ablation (94%) and in the
     seed-2 reseed (94%) but not in the original v1 run.
2. **DeepSeek v1 vs v2 split correlates with `primer_in_system_prompt`.**
   `ablation_deepseek` (2026-04-19 morning) has `primer_in_system_prompt: None`,
   while `ablation_deepseek_v2` (afternoon, same day) has `True`. The codepath
   was changed between those two runs to inject the GEOS primer into the
   system prompt. That same change-set evidently introduced the unconditional
   RAG-instructions block — which is why DeepSeek started biting after that
   point. (Worth double-checking via git history if anyone re-investigates.)

## Implications for prior reported numbers

- All `claude_code_no_plugin` runs *with the leak* (DeepSeek v2, gemma4
  smoketest, noplug_seed2) inflated their `plugin_tool_calls` and
  `total_tool_calls` counters with phantom calls. Any prior comparison that
  relied on `status.json` directly is contaminated. The analysis scripts now
  emit `succeeded_count` (events.jsonl, `is_error: false` or no result block)
  which is the source of truth.
- For Minimax m2.7 and Qwen the existing scores are untouched — those models
  never bit, so the system-prompt mistake was inert.
- Gemma-4 31B and DeepSeek v3.2 *under the v2 prompt* presumably wasted some
  turns on phantom calls. That likely shaved their effective compute. Any
  future model comparison that includes them should ideally rerun with the
  fix in place.

## Action items

- [x] Fix `build_system_prompt` to suppress the RAG paragraph when
      `plugin_enabled=False`.
- [ ] Optional follow-up: change `per_tool_counts` aggregation to exclude
      tool_use blocks whose matching tool_result has `is_error: true`.
      Defer until refactor — touching the counts module mid-conversation
      is risky.
- [ ] When we run new vanilla baselines (e.g., DSv4-flash later today), the
      results will be on the fixed harness. Earlier baselines stay as-is in
      tables but get a footnote.
- [ ] Brian should know that runs labeled "no_plugin" were not 100% clean for
      DeepSeek v3.2 / gemma-4 — the fix is upstream of any re-run.

## Pointers
- Fix: `scripts/run_experiment.py` — `build_system_prompt` (function around
  line 531) and its call site around line 1559.
- Source-of-truth tool-call counts:
  `scripts/analysis/analyze_tool_usage.py` (succeeded_count column).
- Original investigation transcript: this conversation, 2026-04-27.

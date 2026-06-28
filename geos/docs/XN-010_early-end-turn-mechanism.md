# XN-010 — Mechanism of the premature `end_turn` failure mode

**Date:** 2026-04-21
**Status:** root cause identified (high-confidence)

## 1. What we saw

In `E17 (plug_mm_v2_seed2)`, 4/17 tasks hit `status: failed_no_outputs`:

- `AdvancedExampleDeviatedElasticWellbore` — 35.4 s, 0 XML written
- `AdvancedExampleDruckerPrager` — 43.5 s, 0 XML written
- `ExampleDPWellbore` — 38.7 s, 0 XML written
- `ExampleThermalLeakyWell` — 27.3 s, 0 XML written

Each run was far under the 1200 s wall-clock, had a successful provider call, exit code 0, and ended with `stop_reason: end_turn`, `terminal_reason: completed`. No XML ever reached `/workspace/inputs/`.

## 2. Event-log pattern (identical across all four failures)

Example: `ExampleThermalLeakyWell/events.jsonl` (10 events):

```
0 system  (init — lists tools, model=minimax/minimax-m2.7)
1 assistant  text[100]         ← ONE assistant message, ONE API turn
2 assistant  thinking[962]
3 assistant  tool_use[search_technical]
4 assistant  tool_use[search_schema]
5 assistant  tool_use[search_technical]
6 assistant  redacted_thinking[1381]       (= base64 duplicate of event 2)
7 user       tool_result[4128]
8 user       tool_result[21837]
9 user       tool_result[4118]
10 result   num_turns=4 stop=end_turn result_len=0
```

Events 1–6 all share the **same message id** (`...lYRPDJgFLHDaTJWdUH3N`) — a single assistant turn that emitted thinking + 3 `tool_use` blocks. Tool results came back. Then the runner sent the tool-results back to the provider for a 4th turn.

**That 4th turn produced no content at all.** There is no assistant message in the log between event 9 (last tool_result) and event 10 (RESULT). No text, no thinking, no tool call, no error. The `result` field is the empty string. Output-tokens across all turns is only 386 — consistent with the first turn accounting for everything and the 4th turn adding zero.

This is identical in the other three failures (`num_turns` 4/7/8 — sometimes a few successful reasoning-tool cycles, then a single empty completion).

## 3. Why this becomes `end_turn`

Claude Code's agent loop is "while the model's latest response contains `tool_use`, execute them and loop; otherwise stop." An **empty** assistant completion contains no `tool_use`, so the loop exits. `stop_reason` is reported as `end_turn` by the provider/OpenRouter adapter because the completion finished with no explicit tool-call continuation.

**This is the user's stated hypothesis, and it is correct:** the OpenRouter → minimax path is occasionally returning a completion with `content: []` (or equivalent empty string) after a tool-result user message. That empty response gets faithfully translated into an `end_turn` by the harness. There is no logic in Claude Code that distinguishes "model gave up with nothing to say" from "model decided it was done and had nothing further to add."

## 4. Ruling out the alternatives

- **Max-tokens cap**: ruled out. `modelUsage.minimax/minimax-m2.7.maxOutputTokens = 32000`; actual `output_tokens = 386`. No CLI flag sets max_tokens in `build_claude_native_command`; the default provider cap applies. Not hit.
- **Context-window overflow**: ruled out. `input_tokens = 28827` of a 200k window.
- **API error**: ruled out. `is_error=false`, `terminal_reason=completed`, exit 0.
- **Hidden reasoning**: ruled out (cf. Finding 9 in `SESSION_MAP_2026-04-21.md`). `redacted_thinking` blocks are base64 duplicates of the visible `thinking`, not encrypted content. There is no reasoning we cannot read.
- **`AskUserQuestion` deadlock**: not the cause in E17 — none of the four failing traces contained an `AskUserQuestion` call. But it **is** the cause in separate incidents (E12 Sneddon, E01 Sneddon), and is Failure mode D in the session map.
- **Agent "decided" to stop**: the last visible thinking in each failure states forward intent ("Let me now search for …"). There is no visible deliberation about stopping.

## 5. Ancillary evidence

- E18 (same config + memory MCP tool available in tool list) had **zero** such failures on the same 4 tasks. Likely explanation: adding any extra tool to the tool list subtly changes the message shape enough to suppress the minimax empty-completion tendency — this is circumstantial support that the failure is provider/model-side rather than harness-side.
- Deepseek-v3.2 shows the same mode far less frequently, and typically only when a long cheatsheet is in the system prompt (E04/E05) — i.e. empty completions correlate with particular context shapes on OSS-model providers.

## 6. Fixes planned in this session

1. **Remove `AskUserQuestion` from the tool list.** Closes Failure mode D outright. Non-interactive eval cannot answer questions anyway.
2. **Add a Stop hook (plugin/hooks/verify_outputs.py) that rejects `end_turn` when `/workspace/inputs/` is missing `*.xml` files or contains malformed XML.** This gives the model a free re-entry with a concrete complaint ("you ended your turn without producing any XML — write the files now"), converting a soft provider-side empty completion into a forced second chance in the same context.
3. **Optional self-reflection variant** (off by default) — when inputs exist and parse, optionally ask a sub-agent to critique the XML before the main agent is allowed to stop.
4. **Metric fix**: track the failures as score=0 in batch-evaluation output, alongside scored-only mean.

The Stop-hook approach is strictly better than a runner-level retry (which already exists with `--pseudo-tool-retries`) because it keeps the model's full tool-use context rather than restarting from scratch — cheaper, preserves in-progress reasoning, and targets the exact failure we see.

## 7. Open questions

- Does a minimal `curl` reproducer against OpenRouter (same messages) also yield an empty completion? Would distinguish "deterministic adapter bug" from "stochastic model artifact". Not pursued this session.
- Does adding any no-op tool to the tool list also avoid the failure (independent of memory)? Can be tested cheaply.
- Does the Stop-hook retry actually recover — or does the model produce another empty completion on the next call? To be measured by rerunning E17 with the hook enabled.

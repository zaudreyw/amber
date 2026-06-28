# Session handoff — 2026-04-21 end-turn debug

**Why this doc exists.** Work happened in a Claude Code session launched from
the wrong part of the tree, so the next session (in the correct location,
with the right skills/hooks active) needs to pick up cold. This is a
self-contained catch-up: read top-to-bottom, then jump to §7 for what to do
next.

Previous session's cwd: `/home/matt/sci/repo3/`. All referenced paths are
relative to that.

## 1. What we were debugging

`failed_no_outputs`: the agent ends its turn well before the wall-clock
timeout without producing any XML. In E17 (`plug_mm_v2_seed2`, plugin +
minimax + v2 specs), 4/17 tasks hit this:

- `AdvancedExampleDeviatedElasticWellbore` (35 s)
- `AdvancedExampleDruckerPrager` (43 s)
- `ExampleDPWellbore` (39 s)
- `ExampleThermalLeakyWell` (27 s)

All ended with `stop_reason=end_turn`, `is_error=false`, exit 0, and
`result: ""` in the stream-json output.

## 2. Mechanism we identified (high confidence)

Full writeup: `docs/XN-010_early-end-turn-mechanism.md`.

In the event log of each failure, the pattern is identical:

1. One assistant message (same message id across all its parts) containing
   text + thinking + N `tool_use` blocks + a `redacted_thinking` block.
2. The tool_results come back (one user message per tool call).
3. The next API call returns **nothing**: no assistant message appears in
   the log between the last `tool_result` and the `RESULT` line. `result`
   is the empty string. Output-tokens across the run equals roughly what
   turn 1 would have cost alone.

CC's agent loop continues as long as the latest model response contains at
least one `tool_use`. An empty completion contains none, so the loop exits
and the RESULT carries `stop_reason=end_turn`.

Ruled out:
- **Max-tokens cap** — `modelUsage.maxOutputTokens=32000`, actual
  `output_tokens=386` in the cheapest failure. No `--max-tokens` style
  flag is set in `scripts/run_experiment.py`; provider default applies.
- **Context overflow** — `input_tokens ≈ 28k` of a 200k window.
- **API error** — exit 0, `terminal_reason=completed`.
- **Hidden reasoning** — `redacted_thinking` blocks are
  base64-encoded duplicates of the visible `thinking` block in the same
  message, per SESSION_MAP Finding 9. We can read everything.
- **Agent "decided" to stop** — last visible thinking in each failure
  states forward intent ("let me now search for …").

So the failure is **OpenRouter → minimax occasionally returning an empty
completion after a `tool_result`**, faithfully translated by the harness
into `end_turn`. Not a CC bug; not a prompting mistake; provider-side
noise that the harness can't distinguish from a legitimate stop.

`AskUserQuestion` is a separate failure mode (D in the SESSION_MAP) —
we removed it; see §3.

## 3. Fixes landed this session

Three commits on `main`, ahead of `origin/main`:

- `63e5e2c [FEAT] plugin Stop hook + disable AskUserQuestion`
- `50c1f7b [FEAT] batch_evaluate: report failures-as-zero alongside scored-only`
- `ebdc215 [DOCS] RUN_COMMANDS: add E19 plughook_mm_v2 command`

### 3.1 `AskUserQuestion` removed from the tool list

`scripts/run_experiment.py`:
```python
NATIVE_CLAUDE_DISALLOWED_TOOLS = ("Skill", "AskUserQuestion")
# passed as a repeated --disallowedTools flag per entry
```
Closes SESSION_MAP Failure mode D (non-interactive deadlock on ambiguous
tasks). Unrelated to the primary empty-completion mechanism, but a known
source of a related symptom and free to fix.

### 3.2 Plugin Stop hook

Files:
- `plugin/hooks/hooks.json` — plugin hook manifest (auto-discovered at
  plugin root)
- `plugin/hooks/verify_outputs.py` — hook script

On `Stop`, the hook inspects `/workspace/inputs/`:
- **No `.xml` files present** → emits `{decision: "block", reason: ...}`
  asking the agent to write the requested XML before ending.
- **Any XML fails `xml.etree.ElementTree.parse`** → blocks with the file
  name and parse-error detail.
- **Everything clean** → allows the stop.

Knobs (env vars, all optional):
- `GEOS_HOOK_DISABLE=1` — no-op the hook.
- `GEOS_HOOK_MAX_RETRIES` — cap on consecutive blocks per task
  (default 2). Counter persists in `<cwd>/.verify_retry_count` for the
  duration of the task workspace.
- `GEOS_HOOK_INPUTS_DIR` — override the inputs path; defaults to
  `$CLAUDE_PROJECT_DIR/inputs` if set, else `/workspace/inputs`.
- `GEOS_HOOK_SELF_REFLECT=1` — optional intrinsic-review pass (**off by
  default**). When clean XML is present, the hook blocks *once* with a
  self-review prompt asking the agent to re-read each file and verify
  solver/physics consistency, cross-references, and `<Included>` usage
  before truly stopping. The flag is consumed the first time it fires
  (`.verify_reflected` sentinel) so it cannot loop.

`run_experiment.py` forwards `GEOS_HOOK_DISABLE`, `GEOS_HOOK_MAX_RETRIES`,
`GEOS_HOOK_SELF_REFLECT` into the container via `-e`.

Hook is **plugin-only**: vanilla `claude_code_no_plugin` does not pick it
up. This matches the "plugin customization" framing — the hook is part of
our value-add on top of stock CC.

### 3.3 Failures-as-zero metric

`scripts/eval/batch_evaluate.py` now prints two means and writes both to
the `--output` summary JSON:

- **Scored-only mean** (previous default): excludes tasks where the
  scorer errored / no XML existed.
- **Failures-as-zero mean**: same aggregate, but every non-scored task
  contributes 0 to the mean.

Re-reported numbers (full writeup: `docs/XN-011_failures-as-zero-reframe.md`):

| Run | Scored/Total | Scored TreeSim | Failures-as-0 TreeSim |
|---|---:|---:|---:|
| E16 no-plug + mm + v2       | 15/17 | 0.564 | **0.497** |
| E17 plug + mm + v2 (seed 2) | 13/17 | 0.575 | **0.440** |
| E18 plug + mm + v2 + gmem   | 17/17 | 0.725 | **0.725** |

Under failures-as-zero:
- plug vs no-plug **flips sign** to -0.057 (noisy, single seed — likely
  within variance per SESSION_MAP Finding 2).
- plug+gmem vs plug grows to **+0.285**.
- plug+gmem vs no-plug grows to **+0.228**.

Memory win is sharper under the fair framing.

## 4. The open confound (read this before designing the ablation)

E18 (plug + gmem-silent) had **0 failures** on the same 4 tasks that E17
failed. The hook did not exist yet in E18. So the mechanism that rescued
E18 is *not* the hook — it was one of:

- **(a)** Having an extra tool in the tool list changes the provider's
  behavior (any tool, not specifically memory).
- **(b)** The memory-lookup tool's specific description shifts behavior.
- **(c)** Single-seed stochastic luck.
- **(d)** Something about the memory system prompt hint (though gmem is
  the *silent* variant with no system-prompt mention of memory).

We should not assume the hook prevents the failure until we measure it.
The hook's *guaranteed* benefit is the XML-parse-error repair path; the
empty-completion rescue path is the contested claim.

## 5. Proposed ablation (from the previous session's planning)

**Target subset**: the 4 tasks that failed in E17 (above) plus the 13
other E17 tasks for sanity. Minimax, v2 specs. **3 seeds per cell.**

| Cell | hook | extra-tool | purpose | expectation |
|---|:---:|:---:|---|---|
| **C0** | off | none (E17 replicate) | reproduce failure | ~3–5/17 `failed_no_outputs` per seed |
| **C1** | **on** | none | isolate hook effect | ≤1 failed/seed; matches C0 on scored-only TreeSim; beats on failures-as-zero |
| **C2** | off | dummy no-op MCP tool | isolate tool-list-shape effect | distinguishes "any extra tool fixes it" from "hook fixes it" |
| **C3** | off | gmem-silent (E18 replicate) | reproduce E18 | matches E18's 0/17 |
| **C4 (optional)** | on | gmem-silent | combined | score ≥ C1 and C3 |

**Required interpretations:**
- If C1 ≫ C0 (fewer failures) and C2 ≈ C0 → **hook is the mechanism**,
  ship the claim.
- If C1 ≫ C0 and C2 ≫ C0 → tool-list-shape is sufficient; hook provides
  a *different* benefit (XML-parse repair) that we should measure
  separately by counting block events on the `invalid XML` branch.
- If C1 ≈ C0 → the empty-completion failure is not rescueable by
  post-hoc retry (model keeps producing empty). Surprising; would
  re-orient us toward runner-level mitigations (different provider,
  different model, minimal curl reproducer).
- If C0 has ≤1 failure/seed → E17's 4/17 was itself a seed fluke; the
  whole investigation was chasing noise.

**Instrumentation to add before running:**

- Make the hook emit a one-line JSON log to
  `/workspace/.verify_hook_events.jsonl` on every invocation
  (`{timestamp, decision, reason_category, retries_so_far}`). Lets us
  count "rescues attempted" and "rescues succeeded" per task without
  parsing the stream-json.
- Run with `--include-hook-events` so hook lifecycle is in the primary
  `events.jsonl` too.
- Runner-level tool-counts aggregation in `status.json` should pick up a
  new `verify_hook_blocks` field — one-line add next to the existing
  `tool_counts` update.

**Dummy no-op tool for C2**: simplest is a new ~20-line MCP server in
`plugin/scripts/noop_mcp.py` exposing `noop(s: str) -> str` that echoes.
Register via a new agent variant `claude_code_repo3_plugin_noop` (mirrors
`claude_code_repo3_plugin_gmemsilent`'s shape in `run_experiment.py`,
without the memory-specific system-prompt bits).

**Budget**: 17 × 3 × 5 ≈ 255 runs × ~3 min minimax ≈ 12 h at workers=12;
~$100 at OpenRouter rates. Narrow first-pass: 4 problematic tasks × 3
seeds × C0/C1/C2 only ≈ 36 runs, ~1 h, ~$10. The narrow pass is the
single comparison that makes or breaks the hook claim — do it first, then
decide whether to expand to the full factorial.

## 6. Files to read in order, if catching up

1. `docs/XN-010_early-end-turn-mechanism.md` — the mechanism finding,
   with the event-log evidence that drove it.
2. `docs/XN-011_failures-as-zero-reframe.md` — metric change + re-reported
   E16/E17/E18 numbers.
3. `docs/SESSION_MAP_2026-04-21.md` §3 Failure mode A + Failure mode D —
   updated with fix pointers (2026-04-21 entries).
4. `plugin/hooks/verify_outputs.py` — the hook itself; short, tested.
5. `misc/RUN_COMMANDS.md` — bottom entry (E19) for the first hook-enabled
   rerun command and its evaluator invocation.
6. Last 3 commits on `main`: `git log --oneline -3`.

## 7. Suggested first moves in the new session

**Step 0**: verify the environment has what you expect — you mentioned
the previous session lacked skills/instructions/hooks because of the
wrong cwd. Check `claude --debug` on a no-op prompt in the target cwd
and confirm the plugin + its Stop hook are registered. If not, fix that
before anything else — the experiments rely on the hook being live.

**Step 1**: rebuild the docker image so the new `plugin/hooks/` dir is
in the container's mounted `/plugins/repo3`:
```bash
docker build -t geos-eval run/
```
(The plugin is bind-mounted at runtime so this might not actually be
required, but confirm the bind mount at line ~991 of
`scripts/run_experiment.py` — `-v {plugin_dir}:/plugins/repo3:ro`. If it
is bind-mounted, no rebuild needed.)

**Step 2**: add the hook-event log + `verify_hook_blocks` counter (§5
instrumentation). Small diff. Commit separately so it predates the
experimental runs.

**Step 3**: run the **narrow first-pass** (C0/C1/C2 × 3 seeds × 4
problematic tasks). Takes ~1 h, costs ~$10. Compare `failed_no_outputs`
counts and failures-as-zero TreeSim per cell. If the hook claim is
clear, expand to the full factorial (§5 table). If not, stop and revisit.

**Step 4**: once the factorial is in, write `docs/XN-012_hook-ablation.md`
with per-cell failure rates and per-task outcomes on the 4 problematic
tasks. Keep the conclusion honest — "if C2 also recovered, mere extra
tool in the list is the mechanism and the hook's real value is parse
repair."

## 8. Open questions I'd still like answered

- Does a minimal `curl` reproducer against OpenRouter (same messages,
  same model) also yield an empty completion? Would distinguish
  "deterministic adapter bug" from "stochastic model artifact." Not
  pursued this session. Cheap.
- On hook-triggered retry, does the model actually produce non-empty
  output, or does it return another empty completion (forcing a second
  block, exhausting `GEOS_HOOK_MAX_RETRIES`)? Will know after Step 3.
- Deepseek: does the same empty-completion failure happen at a lower
  rate, or is this minimax-specific? `claude_code_repo3_plugin + ds +
  v2` on the same 17-task set would answer this (one seed is enough
  for a first look).

## 9. Things not to re-derive

- `redacted_thinking` = base64 duplicate of visible `thinking` (Finding
  9). Don't re-investigate.
- Runner-level retry already exists (`--pseudo-tool-retries`, default
  1) and **does not** recover the empty-completion failure in practice
  (the retry also produced empty in the archived `attempt_1/` dirs of
  E17's failures). So don't bank on it. The Stop hook operates at a
  finer granularity — same context, model forced to respond again with
  a reason.
- Spec confound is fixed — use v2 (`experiments_test36_template`)
  unless explicitly doing a v1 regression check.

---

Previous session log, for reference only (don't try to resume from a
different cwd; copy-the-jsonl workaround gets messy with path
references):
```
/home/matt/.claude/projects/-home-matt-sci-repo3/b650270a-1bf3-4ad0-9651-fd83a6f6b232.jsonl
```

# Plugin Ablation — Findings Report

**Date:** 2026-04-20
**Author:** Claude Code (session transcript in `misc/`)
**Goal:** Measure the repo3 plugin's contribution by running vanilla Claude
Code (same container, same primer, same prompt) without the plugin / RAG / vector
DB, then comparing against plugin-enabled baselines.

## TL;DR

| Run | Agent | Model | Tasks | Mean TreeSim | Success (≥7) |
|---|---|---|:---:|:---:|:---:|
| `t1_cc_deepseek_clean2` (reference) | CC old harness | deepseek-v3.2 | 36 | 0.922 | 97% ⚠️ contaminated — 17/36 cheated |
| `repo3_eval_run2` (reference) | `claude_code_repo3_plugin` | minimax-m2.7 | 36 | 0.809 | 78% |
| **`ablation_deepseek_v2`** | `claude_code_no_plugin` | deepseek-v3.2 | 36 | **0.643** | **53%** |
| `ablation_qwen` | `claude_code_no_plugin` | qwen/qwen3.5-9b | 36 | — | 0% (all `failed_no_outputs`) |

**Headline:** on deepseek, removing the repo3 plugin costs roughly **0.17
TreeSim** and **25 percentage points** of ≥7 success versus the
plugin+minimax baseline. qwen3.5-9b is too small for this task's tool-use
format — it never writes a file.

## Runs

### `ablation_deepseek` (v1) — 46 tasks, deprecated

First attempted with the 600s default timeout, which turned out to be too
aggressive for deepseek on these tasks: **14/17 completed tasks timed out**
on the first pass. Relaunched with `--timeout 1200` mid-session. Final
tally on the 46-task superset: **34 success / 12 timeout (74%)**.

Kept as a side artifact; **not used for the comparison table** because
it ran against the pre-merge code path (primer copied to workspace +
prepend-read instruction, not primer-in-system-prompt), so it's not
apples-to-apples with `t1_cc_deepseek_clean2`.

**Paths:**
- Per-task outputs (46 dirs, each with `status.json`, `events.jsonl`,
  `stdout.txt`, `stderr.txt`, `inputs/`, `outputs/`, `eval_metadata.json`):
  `/home/matt/sci/repo3/data/eval/claude_code_no_plugin/ablation_deepseek/`
- Run log: `/home/matt/sci/repo3/misc/ablation_deepseek.log`
- Pre-relaunch 600s-timeout snapshots (42 task dirs, taken before the
  1200s relaunch overwrote them): `/home/matt/sci/repo3/misc/ablation_deepseek_600s_backup/`
- **Not scored** — no `_summary.json`.

### `ablation_deepseek_v2` — 36 tasks, primary result

Re-ran on just the 36-task `t1_cc_deepseek_clean2` subset with the merged
upstream code (primer in `--append-system-prompt`, unconditional
`--disallowedTools Skill`), 6 workers, 1200s timeout.

**First launch hit a bug:** for the ablation path the task prompt was
passed as a bare positional argument to the claude CLI, and
`build_task_prompt` produces a prompt that starts with
`--- BEGIN SIMULATION SPECIFICATION ---`. The CLI parsed `--- BEGIN ...`
as an unknown option and all 36 tasks exited in ~2 seconds with
`exit_code=1`. Fixed by inserting a `--` end-of-options separator before
the positional prompt (commit `230d6a0`). Failed artifacts archived at
`misc/ablation_deepseek_v2_failed_dash_bug/`.

**Results (re-launched, clean):** 33/36 success, 3/36 timeout.
Mean TreeSim **0.643**, **19/36 (53%) at ≥7**.

Per-task timeouts: `ExampleIsothermalLeakyWell`, `ExampleTFrac`,
`TutorialDeadOilEgg`. All three also ran 600–900s in `t1_cc_deepseek_clean2`,
so they're borderline at any reasonable timeout.

**Paths:**
- Per-task outputs: `/home/matt/sci/repo3/data/eval/claude_code_no_plugin/ablation_deepseek_v2/`
- Run log: `/home/matt/sci/repo3/misc/ablation_deepseek_v2.log`
- Scoring results dir (per-task `eval_result.json` + judge details):
  `/data/shared/geophysics_agent_data/data/eval/results/ablation_deepseek_v2/claude_code_no_plugin/`
- Aggregate scoring summary:
  `/data/shared/geophysics_agent_data/data/eval/results/ablation_deepseek_v2/claude_code_no_plugin/_summary.json`
- Scoring run log: `/home/matt/sci/repo3/misc/score_ablation_v2.log`
- Failed-first-launch artifacts (dash-prefix bug, 36 tasks that died in ~2s):
  `/home/matt/sci/repo3/misc/ablation_deepseek_v2_failed_dash_bug/`
  and `/home/matt/sci/repo3/misc/ablation_deepseek_v2_failed_dash_bug.log`

### `ablation_qwen` — 36 tasks, negative result

Same setup but `--claude-model qwen/qwen3.5-9b`. **0/36 success — all 36
`failed_no_outputs`.** The model exits cleanly (`stop_reason:"end_turn"`)
after ~3 turns of mostly `thinking` / `redacted_thinking` blocks, without
ever calling `Write` or `Edit`. Mean turns 3.5 vs ~37 for deepseek on the
same tasks.

Interpretation: qwen3.5-9b doesn't reliably follow Claude Code's tool-use
format. Would need a stronger qwen variant (the 235B reasoning model, or a
coder-tuned 32B+) to get a real comparison. This is a
capability-of-the-base-model ceiling, not a plugin issue.

**Paths:**
- Per-task outputs: `/home/matt/sci/repo3/data/eval/claude_code_no_plugin/ablation_qwen/`
- Run log: `/home/matt/sci/repo3/misc/ablation_qwen.log`
- **Not scored** — no point running the judge on empty `inputs/` dirs.

## Per-task v2 TreeSim distribution

Top of the distribution (v2 successes):

| Score | Task |
|---:|---|
| ≥0.9 | 8 tasks |
| 0.7–0.9 | 11 tasks |
| 0.5–0.7 | 10 tasks |
| 0.3–0.5 | 4 tasks |
| <0.3 | 3 tasks |

Lowest scorers worth flagging:
- `TutorialSneddon` 0.099 — effectively empty/wrong XML
- `AdvancedExampleCasedElasticWellboreImperfectInterfaces` 0.224
- `TutorialDeadOilEgg` 0.244 (also timed out)

Full per-task scores in
`/data/shared/.../eval/results/ablation_deepseek_v2/claude_code_no_plugin/_summary.json`.

## Cost / tokens

Cost totals below are claude CLI's self-reported `total_cost_usd`, which
is computed against Anthropic-scale pricing even when the traffic routes
through OpenRouter. **Real OpenRouter-billed cost for deepseek-v3.2 is a
small fraction of these numbers.** A post-hoc pass using
`compute_openrouter_cost` (added upstream) would produce the true spend.

| Run | Tasks | Claude CLI cost (self-reported) | Input tokens | Output tokens | Mean turns |
|---|---:|---:|---:|---:|---:|
| ablation_deepseek (v1, 46) | 34 w/ result | $182.05 | 58.0M | 481k | 32.3 |
| ablation_deepseek_v2 | 33 w/ result | $14.66 | 56.6M | 491k | 37.6 |
| ablation_qwen | 36 w/ result | $5.89 | 2.2M | 13k | 3.5 |

The v1 → v2 cost drop at similar token counts (12× cheaper for ~same
inputs) almost certainly reflects a pricing-tier / cache-hit / model-ID
difference in how the claude CLI self-reports cost, not a real spend
delta. Don't trust the absolute dollar figures; trust the token counts.

**Timeout-task cost tracking:** v1 and v2 only have cost for tasks that
emitted a `type:"result"` event (i.e. clean exits). Timed-out tasks have
no self-reported cost, but their per-generation OpenRouter IDs are
preserved in `events.jsonl` and can be summed via the
`compute_openrouter_cost` utility after the fact. Not done yet.

## Known issues encountered

1. **Stale 600s timeout.** The handoff's default was too low for deepseek;
   36% of `t1_cc_deepseek_clean2` tasks ran >600s. Fixed by bumping to
   1200s. Recommend updating `DEFAULT_TIMEOUT` if deepseek is a common
   target.
2. **`---` prompt prefix bug.** `build_task_prompt` emits a banner starting
   with `---`; when the ablation path passes the task prompt directly to
   claude CLI, the CLI parses it as an unknown option. Fixed in
   `230d6a0` by inserting `--` before the positional prompt. Non-ablation
   paths were unaffected because their prompts are prepended with
   instruction text that doesn't start with `-`.
3. **Cost fields missing in live `status.json`.** v1 ran from pre-upstream
   code that lacked `compute_openrouter_cost`; v2 has the hook but
   `openrouter_cost_usd` still isn't populated in status for the runs
   we looked at — worth a closer look as a separate task.
4. **`--pseudo-tool-retries` never fired.** Zero pseudo-tool calls across
   both deepseek runs. Retries aren't contributing to wall time.

## Recommended next steps

1. **Plugin + deepseek + v2 harness run.** The comparison that isolates
   plugin contribution is `claude_code_repo3_plugin` + deepseek-v3.2
   against this ablation. That run doesn't exist yet (only plugin+minimax
   does). Kicked-off command is in the handoff.
2. **Bigger qwen.** Retry the qwen ablation with a model that actually
   uses tools — e.g. `qwen/qwen-2.5-coder-32b-instruct` or
   `qwen/qwen3-235b-a22b`.
3. **Post-hoc cost backfill.** Run a pass over all `events.jsonl` files
   from v1/v2/qwen, call `compute_openrouter_cost` per task, patch
   `status.json`. Would give real OpenRouter-billed totals and cover
   timed-out tasks.
4. **Update `DEFAULT_TIMEOUT`.** Bump from 600s to 1200s in
   `scripts/run_experiment.py`, or make it model-dependent.

## Artifacts — index

Per-run artifacts are listed in each run's section above. Shared / cross-run
artifacts:

**Reference / comparison runs (not produced in this session):**
- `t1_cc_deepseek_clean2` task dirs:
  `/data/shared/geophysics_agent_data/data/eval/runs/t1_cc_deepseek_clean2/`
  (36 task dirs + `results.jsonl` + `summary.json`)

**Reusable inputs:**
- Handoff doc: `/home/matt/sci/repo3/misc/ablation_handoff.md`
- 36-task list (derived from t1): `/home/matt/sci/repo3/misc/t1_36_tasks.txt`
- Per-task instructions (shared with t1): `/data/shared/geophysics_agent_data/data/eval/experiments/<task>/instructions.txt`
- Ground truth: `/data/shared/geophysics_agent_data/data/eval/experiments_gt/`
- GEOS primer: `/home/brianliu/geophys-embodied-agent-framework/modules/profile/GEOS_PRIMER.md`
- Filtered GEOS scratch dir (hardlink target): `/data/matt/geos_eval_tmp/`

**Launch helpers used this session:**
- v2 auto-launcher (waited for v1 to exit): `/home/matt/sci/repo3/misc/launch_ablation_v2.sh`
- v2 launcher log: `/home/matt/sci/repo3/misc/launch_ablation_v2.waiter.log`

**Commits landed:**
- `60bb638` — add `claude_code_no_plugin` ablation agent
- `b16d8a6` — merge upstream (primer-in-system-prompt + `--disallowedTools`)
- `230d6a0` — `--` separator before prompt in claude_native docker command

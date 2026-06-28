# Ablation Run Handoff

**Goal:** run `claude_code_no_plugin` (vanilla CC, no repo3 plugin, no RAG, same
primer + prompt) on the 46-task suite with DeepSeek, then score it. This is the
ablation baseline for measuring the plugin's contribution.

## Current status

- **Not yet run successfully.** Last attempt failed all 46 tasks in 0.0s each
  because `matt` lacked docker group membership — no API calls made, no cost.
- **Fix applied:** `sudo usermod -aG docker matt` ran successfully. Group
  membership only takes effect in new login sessions.
- `geos-eval` docker image exists. `.env` is symlinked into the repo. The
  `claude_code_no_plugin` agent and `--claude-model` flag are wired up in
  `scripts/run_experiment.py`.
- There was a separate `geos-eval` container running in docker when last
  checked — unrelated to this run; leave it alone unless confirmed stale.

## Pre-flight (run these first, in order)

```bash
# 1. Confirm docker group is active in this shell:
docker ps
#    If "permission denied" → group isn't active. Options:
#      a) Open a fresh tmux window / terminal (new login shell inherits group)
#      b) `newgrp docker` (prompts for group password — may not work)
#      c) `ssh localhost` (fresh login if key-based ssh is set up)
#      d) Fallback: prefix every command with `sudo -E` (works, but outputs
#         end up owned by root — fix with `sudo chown -R matt:matt <dir>`)

# 2. Confirm env vars will resolve. OPENROUTER_API_KEY should be in /home/matt/sci/repo3/.env
#    (symlinked from /home/matt/sci/geos_agent/.env). run_experiment.py
#    promotes OPENROUTER_API_KEY → ANTHROPIC_AUTH_TOKEN at import time.
ls -la /home/matt/sci/repo3/.env

# 3. Confirm scratch dir (hardlink target, same FS as /data/shared/.../GEOS):
ls -ld /data/matt/geos_eval_tmp  # matt:matt, writable
```

## Run command

```bash
cd /home/matt/sci/repo3

python scripts/run_experiment.py \
  --run ablation_deepseek \
  --agents claude_code_no_plugin \
  --claude-model deepseek/deepseek-v3.2 \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --tmp-geos-parent /data/matt/geos_eval_tmp \
  > /home/matt/sci/repo3/misc/ablation_deepseek.log 2>&1 &
```

Expected runtime: ~1–2h wall with default 2 workers × 600s timeout × 46 tasks.
Each task writes a per-task dir with `status.json`, `events.jsonl`, `inputs/`,
`outputs/`, `eval_metadata.json`, etc. Prior failed attempts will be
overwritten — no manual cleanup needed.

### Monitor progress

```bash
# tail per-task status transitions and any errors
tail -F /home/matt/sci/repo3/misc/ablation_deepseek.log \
  | grep -E --line-buffered '^\[ *[0-9]+/[0-9]+\]|^Done:|Traceback|Error'
```

## Score it (when run finishes)

```bash
python scripts/eval/batch_evaluate.py \
  --experiments-dir /home/matt/sci/repo3/data/eval/claude_code_no_plugin/ablation_deepseek \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --results-dir /data/shared/geophysics_agent_data/data/eval/results/ablation_deepseek/claude_code_no_plugin \
  --output /data/shared/geophysics_agent_data/data/eval/results/ablation_deepseek/claude_code_no_plugin/_summary.json
```

Known quirk: one task (`AdvancedExampleDeviatedPoroElasticWellbore`) may
hit a `RecursionError` in `judge_geos.py` — it fails to score but doesn't
break the batch. Real evaluator bug, separate from the run.

## Comparison target

For context when reporting numbers, the two other runs to compare against
(both on the same 36-task subset of these 46):

| Run | Agent | Model | Mean TreeSim | Success (≥7) |
|---|---|---|:---:|:---:|
| `repo3_eval_run2` | `claude_code_repo3_plugin` | minimax-m2.7 | 0.809 | 78% |
| `t1_cc_deepseek_clean2` (shared) | CC old harness | deepseek-v3.2 | 0.922 | 97% (**contaminated — 17/36 tasks cheated**) |

The ablation (no plugin, same deepseek) vs the plugin run (minimax) isolates
plugin contribution *if* you also have a matching `claude_code_repo3_plugin`
+ deepseek run. If that run doesn't exist yet, kick one off in parallel with:

```bash
python scripts/run_experiment.py \
  --run plugin_deepseek \
  --agents claude_code_repo3_plugin \
  --claude-model deepseek/deepseek-v3.2 \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --tmp-geos-parent /data/matt/geos_eval_tmp
```

## Cheating audit (optional, for the ablation)

The containerized runner makes host filesystem cheating impossible — pristine
`/data/shared/.../data/GEOS` is not mounted, only the filtered copy at
`/geos_lib` inside the container. Network egress (e.g. `curl github.com`) is
NOT blocked; if concerned, spot-check a few `events.jsonl` files for Bash
tool calls hitting github.

# Run commands (Matt) — sanity-check reference vs Brian's

All experiments I launched this session, with the exact invocations. For comparison, Brian's E03 command (which he shared) is at the bottom. Common diffs are summarized at the end.

All runs are from `/home/matt/sci/repo3/` (uses `uv run python scripts/run_experiment.py ...`).

---

## E01 — ablation_deepseek_v2 (not launched this session, kept for reference)

Run by Matt earlier (predates this session). The exact command isn't in my history, but it's documented in `misc/ablation_findings.md` as:

```bash
uv run python scripts/run_experiment.py \
    --run ablation_deepseek_v2 \
    --agents claude_code_no_plugin \
    --claude-model deepseek/deepseek-v3.2 \
    --include <36 tasks from misc/t1_36_tasks.txt> \
    --workers 6 \
    --timeout 1200 \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt
```

Spec set: **`experiments` (v1)**.

---

## Environment assumed for every command below

```bash
V2_PATH=/data/shared/geophysics_agent_data/data/eval/experiments_test36_template
V1_PATH=/data/shared/geophysics_agent_data/data/eval/experiments
TEST_TASKS=$(python3 -c "import json; print(' '.join(json.load(open('/home/matt/sci/repo3/misc/memory_split.json'))['test']))")
cd /home/matt/sci/repo3
```

---

## E04 — mem_run1 (plugin + long system-prompt cheatsheet)

```bash
uv run python scripts/run_experiment.py \
    --run mem_run1 \
    --agents claude_code_repo3_plugin_mem \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 6 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1** (`experiments`).

---

## E05 — memshort_run1 (plugin + short cheatsheet)

```bash
uv run python scripts/run_experiment.py \
    --run memshort_run1 \
    --agents claude_code_repo3_plugin_memshort \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 6 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**.

---

## E06 — mm_noplug_run1 (no-plugin + minimax)

```bash
uv run python scripts/run_experiment.py \
    --run mm_noplug_run1 \
    --agents claude_code_no_plugin \
    --include $TEST_TASKS \
    --claude-model minimax/minimax-m2.7 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**. First run at workers=12 (concurrency test).

---

## E07 — tree_run1 (plugin + filetree index in system prompt)

```bash
uv run python scripts/run_experiment.py \
    --run tree_run1 \
    --agents claude_code_repo3_plugin_tree \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**.

---

## E08 — minprimer_run1 (plugin + minimal primer override)

```bash
uv run python scripts/run_experiment.py \
    --run minprimer_run1 \
    --agents claude_code_repo3_plugin \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --geos-primer-path /home/matt/sci/repo3/plugin/GEOS_PRIMER_minimal.md
```
Spec set: **v1**. Only run with a custom `--geos-primer-path`.

---

## E09 — memws_run1 (plugin + cheatsheet via /workspace/CHEATSHEET.md)

```bash
uv run python scripts/run_experiment.py \
    --run memws_run1 \
    --agents claude_code_repo3_plugin_memws \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**.

---

## E11 — gmem_run1 (plugin + G-memory MCP tool, with system-prompt hint)

```bash
uv run python scripts/run_experiment.py \
    --run gmem_run1 \
    --agents claude_code_repo3_plugin_gmem \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**. Uses `memory_mcp.py` without threshold.

---

## E12 — gmem_v2_run1 (G-memory + threshold + delay-trigger instruction)

```bash
uv run python scripts/run_experiment.py \
    --run gmem_v2_run1 \
    --agents claude_code_repo3_plugin_gmem \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**. Same CLI as E11; memory_mcp internals changed (min_score=0.6) between E11 and E12.

---

## E13 — gmemsilent_run1 (G-memory MCP, no system-prompt instruction)

```bash
uv run python scripts/run_experiment.py \
    --run gmemsilent_run1 \
    --agents claude_code_repo3_plugin_gmemsilent \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**.

---

## E14 — plugin_seed2 (plain plugin, deepseek, variance anchor)

```bash
uv run python scripts/run_experiment.py \
    --run plugin_seed2 \
    --agents claude_code_repo3_plugin \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**. This is THE direct plain-plugin replication; compare to Brian's E03 (which used v2 — expect mean drop due to specs, not just seed).

---

## E15 — noplug_seed2 (plain no-plugin, deepseek, variance anchor)

```bash
uv run python scripts/run_experiment.py \
    --run noplug_seed2 \
    --agents claude_code_no_plugin \
    --include $TEST_TASKS \
    --claude-model deepseek/deepseek-v3.2 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V1_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v1**.

---

## E16 — noplug_mm_v2 (no-plugin + minimax, canonical specs)

```bash
uv run python scripts/run_experiment.py \
    --run noplug_mm_v2 \
    --agents claude_code_no_plugin \
    --include $TEST_TASKS \
    --claude-model minimax/minimax-m2.7 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V2_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v2** (`experiments_test36_template`) — first run of mine on canonical specs.

---

## E17 — plug_mm_v2_seed2 (plain plugin + minimax, canonical specs, seed 2)

```bash
uv run python scripts/run_experiment.py \
    --run plug_mm_v2_seed2 \
    --agents claude_code_repo3_plugin \
    --include $TEST_TASKS \
    --claude-model minimax/minimax-m2.7 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V2_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v2**. Direct reproducibility attempt for Brian's E02 / E03 pattern.

---

## E18 — gmemsilent_mm_v2 (G-memory silent + minimax, canonical specs)

```bash
uv run python scripts/run_experiment.py \
    --run gmemsilent_mm_v2 \
    --agents claude_code_repo3_plugin_gmemsilent \
    --include $TEST_TASKS \
    --claude-model minimax/minimax-m2.7 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V2_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp
```
Spec set: **v2**. First memory run on canonical specs.

---

## Brian's E03 (for comparison — from message he sent):

```bash
python3 /home/brianliu/repo3/scripts/run_experiment.py \
    --run repo3_eval_run4 \
    --claude-model "deepseek/deepseek-v3.2" \
    --agents claude_code_repo3_plugin \
    --experiments-dir /home/brianliu/geophysics_agent/data/eval/experiments_test36_template \
    --results-root-dir /home/brianliu/geophysics_agent/data/eval \
    --ground-truth-dir /home/brianliu/geophysics_agent/data/eval/experiments_gt \
    --workers 8 \
    --dashboard
```

(Brian's E02 presumably used similar flags with `--claude-model minimax/minimax-m2.7`.)

---

## Diffs vs Brian's E03 (column = my runs default, row = Brian's)

| Flag | Matt (E04-E15) | Matt (E16-E18) | Brian (E03) |
|---|---|---|---|
| `--experiments-dir` | v1 (`experiments`) | v2 (`experiments_test36_template`) | v2 |
| `--ground-truth-dir` | `/data/shared/.../experiments_gt` | same | `/home/brianliu/.../experiments_gt` (same dir via different mount) |
| `--workers` | 12 (6 for E04, E05) | 12 | 8 |
| `--timeout` | 1200 (default) | 1200 | default = 1200 |
| `--dashboard` | not used | not used | **used** |
| `--tmp-geos-parent` | `/data/matt/geos_eval_tmp` | same | **not specified** (takes default = shared tmp_geos, brianliu-owned) |
| `--include` | 17 test tasks from `misc/memory_split.json` | same | **all 36** |
| `--claude-model` | deepseek/deepseek-v3.2 (E04-E14) or minimax (E06, E16-E18) | minimax-m2.7 | deepseek-v3.2 |
| python entry | `uv run python` | same | `python3` |

### The material diffs that affect results

- **Specs (v1 vs v2) — biggest confound.** Fixed by E16-E18 now using v2.
- **Task subset (17 vs 36).** Ours is always the 17 "test" subset from `memory_split.json`; Brian ran full 36. Per-task scores are directly comparable when both ran the same task.
- **Workers 12 vs 8** — doesn't affect per-task scores, only throughput. No rate-limiting issues observed either way.
- **tmp-geos-parent** — I use matt-writable `/data/matt/geos_eval_tmp`; Brian used default which falls back to brianliu-owned shared. Different hardlink trees but semantically identical contents.
- **python3 vs uv run python** — non-material. Both invoke the same script.
- **--dashboard** — UI-only, does not affect agent behavior.

### Conclusion

The only material difference between my canonical-recovery runs (E16-E18) and Brian's E02/E03 setup is the **task subset**: I evaluate 17 test tasks (from my memory_split), Brian evaluates all 36. Spec set, workers, timeout, and models are matched where intended.

Prior runs (E04-E15) additionally had the wrong spec set (v1). Those results are still valid for characterizing behavior on v1 specs but should NOT be compared to Brian's numbers as apples-to-apples.

---

## E19 — plughook_mm_v2 (plug + Stop hook + AskUserQuestion disabled)

Replicates E17 with two changes: (1) `AskUserQuestion` is now in
`--disallowedTools` (so the non-interactive harness never sees a blocked
question-deadlock turn), (2) the plugin's new `Stop` hook
(`plugin/hooks/verify_outputs.py`) blocks `end_turn` when
`/workspace/inputs/` is empty or has malformed XML and feeds a concrete
complaint back to the agent. Goal: measure how much of E17's 4 failures the
hook recovers, and whether it lifts the failures-as-zero mean to (or near)
E18's 0.725.

```bash
cd /home/matt/sci/repo3
V2_PATH=/data/shared/geophysics_agent_data/data/eval/experiments_test36_template
TEST_TASKS=$(python3 -c "import json; print(' '.join(json.load(open('/home/matt/sci/repo3/misc/memory_split.json'))['test']))")

uv run python scripts/run_experiment.py \
    --run plughook_mm_v2 \
    --agents claude_code_repo3_plugin \
    --include $TEST_TASKS \
    --claude-model minimax/minimax-m2.7 \
    --workers 12 \
    --timeout 1200 \
    --experiments-dir "$V2_PATH" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --tmp-geos-parent /data/matt/geos_eval_tmp

uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/claude_code_repo3_plugin/plughook_mm_v2 \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --results-dir data/eval/results/plughook_mm_v2 \
    --output data/eval/results/plughook_mm_v2_summary.json
```

Paired-compare vs E17:

```bash
uv run python misc/compare_runs_per_task.py \
    --run-a data/eval/claude_code_repo3_plugin/plug_mm_v2_seed2 \
    --run-b data/eval/claude_code_repo3_plugin/plughook_mm_v2 \
    --label-a "E17 plug" --label-b "E19 plug+hook"
```

*Not yet launched* — to run when docker image rebuild is convenient.

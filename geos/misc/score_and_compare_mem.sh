#!/usr/bin/env bash
# Score mem_run1 and compare against plugin-only on the 17 test tasks.
set -euo pipefail
cd /home/matt/sci/repo3

RESULTS_DIR=/data/shared/geophysics_agent_data/data/eval/results/mem_run1/claude_code_repo3_plugin_mem
mkdir -p "$RESULTS_DIR"

echo "=== Scoring mem_run1 ==="
uv run python scripts/eval/batch_evaluate.py \
  --experiments-dir /home/matt/sci/repo3/data/eval/claude_code_repo3_plugin_mem/mem_run1 \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --results-dir "$RESULTS_DIR" \
  2>&1 | tee misc/score_mem_run1.log

echo ""
echo "=== Paired compare: memory vs plugin-only on 17 test tasks ==="
# Filter the plugin-only results dir to just the 17 test tasks so we do a fair paired comparison.
TEST_DIR=/tmp/e03_test17
rm -rf "$TEST_DIR" && mkdir -p "$TEST_DIR"
python3 -c "
import json, shutil
from pathlib import Path
split = json.load(open('misc/memory_split.json'))
src = Path('/data/shared/geophysics_agent_data/data/eval/results/repo3_eval_run4/claude_code_repo3_plugin')
dst = Path('$TEST_DIR')
for t in split['test']:
    f = src / f'{t}_eval.json'
    if f.exists():
        shutil.copy(f, dst / f.name)
print(f'copied {len(list(dst.glob(\"*_eval.json\")))} files')
"

python3 misc/compare_runs.py \
  "$RESULTS_DIR" "memory" \
  "$TEST_DIR" "plugin" \
  2>&1 | tee misc/e04_vs_e03_test17.txt

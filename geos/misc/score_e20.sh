#!/bin/bash
# Score all 12 E20 (cell × run) result dirs via batch_evaluate.py.
# Produces per-task _eval.json files + summary JSON per cell/run.
set -euo pipefail
cd /home/matt/sci/repo3
source .venv/bin/activate 2>/dev/null || true

GT=/data/shared/geophysics_agent_data/data/eval/experiments_gt
CELLS="claude_code_repo3_plugin_nohook claude_code_repo3_plugin claude_code_repo3_plugin_noop_nohook claude_code_repo3_plugin_noop"
RUNS="e20_run1 e20_run2 e20_run3"

mkdir -p data/eval/results/e20

for CELL in $CELLS; do
  for RUN in $RUNS; do
    RESULT_DIR="data/eval/$CELL/$RUN"
    if [ ! -d "$RESULT_DIR" ]; then
      echo "skip (not yet generated): $RESULT_DIR"
      continue
    fi
    OUT_JSON="data/eval/results/e20/${CELL}__${RUN}_summary.json"
    echo "=== scoring $CELL / $RUN ==="
    uv run python scripts/eval/batch_evaluate.py \
      --experiments-dir "$RESULT_DIR" \
      --ground-truth-dir "$GT" \
      --output "$OUT_JSON" 2>&1 | tail -15
  done
done

echo
echo "=== Running analysis ==="
uv run python misc/analyze_e20.py

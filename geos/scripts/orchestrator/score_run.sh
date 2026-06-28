#!/usr/bin/env bash
# Score an orchestrator run with batch_evaluate.py.
#
# Usage:
#   bash scripts/orchestrator/score_run.sh <run_name> [agent_subdir]
#
# agent_subdir defaults to orchestrator_dsv4flash. Pass `orchestrator_mm27`
# for the OpenRouter-minimax fallback run.

set -euo pipefail

RUN_NAME="${1:?Usage: score_run.sh <run_name> [agent_subdir]}"
AGENT_SUBDIR="${2:-orchestrator_dsv4flash}"

EXP_DIR="/home/matt/sci/repo3/data/eval/${AGENT_SUBDIR}/${RUN_NAME}"
GT_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_gt"
RESULTS_DIR="/home/matt/sci/repo3/data/eval/results/${RUN_NAME}/${AGENT_SUBDIR}"
SUMMARY_OUT="${RESULTS_DIR}/_summary.json"

if [[ ! -d "$EXP_DIR" ]]; then
    echo "ERROR: experiments dir does not exist: $EXP_DIR"
    exit 1
fi

mkdir -p "$RESULTS_DIR"

cd /home/matt/sci/repo3
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir "$EXP_DIR" \
    --ground-truth-dir "$GT_DIR" \
    --results-dir "$RESULTS_DIR" \
    --output "$SUMMARY_OUT"

echo
echo "Score summary: $SUMMARY_OUT"
echo
# Also run the trace analysis
python -m scripts.orchestrator.analyze_run --run-dir "$EXP_DIR"

#!/usr/bin/env bash
# Score all autocamp 2026-05-01 runs. Discovers (agent, run) pairs from
# the dsv4/ and xmodel/ subtrees and scores each.
set -euo pipefail
cd /home/matt/sci/repo3

ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01"
GT_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_gt"

score_one() {
  local AGENT="$1" RUN="$2" SUBTREE="$3"
  local EXP_DIR="$ROOT/$SUBTREE/$AGENT/$RUN"
  local RESULTS_DIR="$ROOT/_results/$RUN/$AGENT"
  if [ ! -d "$EXP_DIR" ]; then
    echo "skip: $EXP_DIR not found"; return
  fi
  if [ -f "$RESULTS_DIR/_summary.json" ]; then
    echo "already scored: $RUN/$AGENT"; return
  fi
  mkdir -p "$RESULTS_DIR"
  echo "scoring: $AGENT/$RUN -> $RESULTS_DIR"
  uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir "$EXP_DIR" \
    --ground-truth-dir "$GT_DIR" \
    --results-dir "$RESULTS_DIR" \
    --output "$RESULTS_DIR/_summary.json"
}

# DSv4 subtree: <ROOT>/dsv4/<agent>/<run>/<task>/
for agent_dir in "$ROOT"/dsv4/*/; do
  AGENT=$(basename "$agent_dir")
  for run_dir in "$agent_dir"*/; do
    RUN=$(basename "$run_dir")
    score_one "$AGENT" "$RUN" "dsv4"
  done
done

# Cross-model subtree: <ROOT>/xmodel/<agent>/<run>/<task>/
for agent_dir in "$ROOT"/xmodel/*/; do
  AGENT=$(basename "$agent_dir")
  for run_dir in "$agent_dir"*/; do
    RUN=$(basename "$run_dir")
    score_one "$AGENT" "$RUN" "xmodel"
  done
done

echo "Done."

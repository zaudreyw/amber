#!/usr/bin/env bash
# Score follow-up scaleup runs at autocamp_followup_2026-05-02/{icl,train}/...
# Mirrors the pattern of score_autocamp.sh but for the scaleup root.
# Derisk runs (F8/F11) live at autocamp_2026-05-01/dsv4/ and are scored
# by score_autocamp.sh — no need to duplicate them here.
set -euo pipefail
cd /home/matt/sci/repo3

ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_followup_2026-05-02"
GT_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_gt"

score_one() {
  local AGENT="$1" RUN="$2" SUBTREE="$3"
  local EXP_DIR="$ROOT/$SUBTREE/$AGENT/$RUN"
  local RESULTS_DIR="$ROOT/_results_$SUBTREE/$RUN/$AGENT"
  if [ ! -d "$EXP_DIR" ]; then
    echo "skip: $EXP_DIR not found"; return
  fi
  if [ -f "$RESULTS_DIR/_summary.json" ]; then
    echo "already scored: $SUBTREE/$RUN/$AGENT"; return
  fi
  mkdir -p "$RESULTS_DIR"
  echo "scoring: $SUBTREE/$AGENT/$RUN -> $RESULTS_DIR"
  uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir "$EXP_DIR" \
    --ground-truth-dir "$GT_DIR" \
    --results-dir "$RESULTS_DIR" \
    --output "$RESULTS_DIR/_summary.json"
}

for SUBTREE in icl train; do
  [ -d "$ROOT/$SUBTREE" ] || { echo "no $ROOT/$SUBTREE"; continue; }
  for agent_dir in "$ROOT"/$SUBTREE/*/; do
    AGENT=$(basename "$agent_dir")
    for run_dir in "$agent_dir"*/; do
      RUN=$(basename "$run_dir")
      score_one "$AGENT" "$RUN" "$SUBTREE"
    done
  done
done

echo "Done."

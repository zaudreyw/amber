#!/usr/bin/env bash
# Score all interactive-autonomy runs.
set -euo pipefail
cd "$(dirname "$0")/.."

ROOT="$(pwd)/data/eval/interactive_autonomy_2026-05-03"
GT_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_gt"

score_one() {
  local MODE_DIFF="$1" AGENT="$2" RUN="$3"
  local EXP_DIR="$ROOT/$MODE_DIFF/$AGENT/$RUN"
  local RESULTS_DIR="$ROOT/_results/$MODE_DIFF/$RUN/$AGENT"
  if [ ! -d "$EXP_DIR" ]; then
    echo "skip: $EXP_DIR not found"; return
  fi
  if [ -f "$RESULTS_DIR/_summary.json" ]; then
    echo "already scored: $MODE_DIFF/$RUN/$AGENT"; return
  fi
  mkdir -p "$RESULTS_DIR"
  echo "scoring: $MODE_DIFF/$AGENT/$RUN -> $RESULTS_DIR"
  uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir "$EXP_DIR" \
    --ground-truth-dir "$GT_DIR" \
    --results-dir "$RESULTS_DIR" \
    --output "$RESULTS_DIR/_summary.json"
}

for md_dir in "$ROOT"/mode*_*/; do
  MD=$(basename "$md_dir")
  for agent_dir in "$md_dir"*/; do
    [ -d "$agent_dir" ] || continue
    AGENT=$(basename "$agent_dir")
    [ "$AGENT" = "_logs" ] && continue
    for run_dir in "$agent_dir"*/; do
      [ -d "$run_dir" ] || continue
      RUN=$(basename "$run_dir")
      score_one "$MD" "$AGENT" "$RUN"
    done
  done
done

echo "Done."

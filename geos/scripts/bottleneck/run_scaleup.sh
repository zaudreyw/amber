#!/bin/bash
# Bottleneck pipeline on the followup_2026-05-02 scaleup runs.
# ICL-10 (clean) + train-19 (memory-free clean only).
set -euo pipefail
cd "$(dirname "$0")/../.."

source .env

OUT=/data/matt/bn_scaleup
mkdir -p "$OUT"/{stage1_icl,stage2_icl,stage3_icl,stage1_train,stage2_train,stage3_train}

ROOT=/data/shared/geophysics_agent_data/data/eval/autocamp_followup_2026-05-02

# ICL-10 cells (all 6)
ICL_CELLS=(autocamp_F0 autocamp_F4 autocamp_F6 autocamp_SE autocamp_F8 autocamp_F11)
# Memory-free cells only on train-19 (no contamination)
TRAIN_CELLS=(autocamp_F0 autocamp_F6)

run_pipeline() {
  local SUBSET="$1"; shift   # "icl" or "train"
  local CELLS=("$@")

  local TRAJ_ROOT="$ROOT/$SUBSET"
  local EVAL_ROOT="$ROOT/_results_$SUBSET"

  if [ ! -d "$TRAJ_ROOT" ]; then
    echo "skip: $TRAJ_ROOT not found"
    return
  fi
  if [ ! -d "$EVAL_ROOT" ]; then
    echo "skip: $EVAL_ROOT not found — did scoring run?"
    return
  fi

  local STAGE1="$OUT/stage1_$SUBSET"
  local STAGE2="$OUT/stage2_$SUBSET"
  local STAGE3="$OUT/stage3_$SUBSET"

  ARGS=()
  for c in "${CELLS[@]}"; do ARGS+=( --agent "$c" ); done
  for c in "${CELLS[@]}"; do
    for s in 1 2 3; do
      ARGS+=( --run "${c##autocamp_}_${SUBSET}_s${s}" )
    done
  done

  echo "=== $SUBSET Stage 1 ==="
  python3 scripts/bottleneck/extract.py \
    --traj-root "$TRAJ_ROOT" \
    --eval-root "$EVAL_ROOT" \
    "${ARGS[@]}" \
    --out-dir "$STAGE1"

  echo "=== $SUBSET Stage 2 ==="
  python3 scripts/bottleneck/llm_per_task.py \
    --diag-dir "$STAGE1" \
    --out-dir "$STAGE2" \
    --eval-root "$EVAL_ROOT" \
    --model deepseek-v4-flash \
    --workers 16 --skip-existing

  echo "=== $SUBSET Stage 3 ==="
  python3 scripts/bottleneck/aggregate.py \
    --llm-dir "$STAGE2" \
    --out-dir "$STAGE3" \
    --baseline autocamp_F0 \
    --best autocamp_F4 \
    --narrate || true

  echo "=== $SUBSET DONE: $STAGE3/aggregate.md"
}

run_pipeline icl "${ICL_CELLS[@]}"
run_pipeline train "${TRAIN_CELLS[@]}"

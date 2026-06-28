#!/bin/bash
# End-to-end bottleneck pipeline on autocamp Phase 2 cells.
# Stage 1 (extract) → Stage 2 (DSv4-flash per task) → Stage 3 (DSv4-pro narrative).
set -euo pipefail
cd "$(dirname "$0")/../.."

source .env

OUT=/data/matt/bn_phase2
mkdir -p "$OUT"/{stage1,stage2,stage3}

PHASE2_ROOT=/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01

# Cells we care about for the bottleneck story
CELLS=(autocamp_F0 autocamp_F2 autocamp_F4 autocamp_F6 autocamp_SE)

# All seeds
RUNS=()
for c in "${CELLS[@]}"; do
  for s in 1 2 3; do
    RUNS+=( "${c}_s${s}" )
  done
done

# Stage 1: extract diagnostics
echo "=== Stage 1: extract ==="
ARGS=()
for c in "${CELLS[@]}"; do ARGS+=( --agent "$c" ); done
for r in "${RUNS[@]}"; do ARGS+=( --run "$r" ); done

python3 scripts/bottleneck/extract.py \
  --traj-root "$PHASE2_ROOT/dsv4" \
  --eval-root "$PHASE2_ROOT/_results" \
  "${ARGS[@]}" \
  --out-dir "$OUT/stage1"

# Stage 2: per-task DSv4-flash
echo "=== Stage 2: DSv4-flash per task ==="
python3 scripts/bottleneck/llm_per_task.py \
  --diag-dir "$OUT/stage1" \
  --out-dir "$OUT/stage2" \
  --eval-root "$PHASE2_ROOT/_results" \
  --model deepseek-v4-flash \
  --workers 16 --skip-existing

# Stage 3: aggregate + narrative (DSv4-pro)
echo "=== Stage 3: aggregate + narrate ==="
python3 scripts/bottleneck/aggregate.py \
  --llm-dir "$OUT/stage2" \
  --out-dir "$OUT/stage3" \
  --baseline autocamp_F0 \
  --best autocamp_F4 \
  --narrate

echo "=== DONE === results at $OUT/stage3/aggregate.md"

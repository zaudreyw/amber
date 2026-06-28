#!/usr/bin/env bash
# Fire the full DSv4 ablation matrix:
#   4 conditions × 3 seeds × 17 tasks = 204 task-runs
#   2 conditions in parallel × workers=4 each = 8 concurrent docker containers
#   Per-condition seeds run sequentially.
#
# Wall: ~3-4 hours total. Cost: ~$15-25 real DSv4 (CC reports much higher).
# Disk goes to /data/shared/.../dsv4_ablation_2026-04-29/
set -uo pipefail

cd /home/matt/sci/repo3
mkdir -p /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs

# Run a (condition, all 3 seeds) sequentially.
run_condition() {
  local COND="$1"
  for SEED in 1 2 3; do
    bash scripts/launch_dsv4_ablation.sh "$COND" "$SEED"
  done
}

# Group A: c0 + c2 in parallel (cheaper - C0 no plugin, C2 hook only).
# Group B: c3 + c4 in parallel (RAG conditions).
# Group A finishes, then group B starts. Avoids running too many concurrent
# vector-DB-loading containers and gives clear log separation.

echo "=== START Group A (C0 + C2) at $(date -u +%FT%TZ) ===" \
  | tee -a /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/_master.log

run_condition c0 &
PID_C0=$!
run_condition c2 &
PID_C2=$!
wait $PID_C0 $PID_C2

echo "=== START Group B (C3 + C4) at $(date -u +%FT%TZ) ===" \
  | tee -a /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/_master.log

run_condition c3 &
PID_C3=$!
run_condition c4 &
PID_C4=$!
wait $PID_C3 $PID_C4

echo "=== ALL DONE at $(date -u +%FT%TZ) ===" \
  | tee -a /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/_master.log

#!/usr/bin/env bash
# Launch C6/C7/C8/C9 × 3 seeds for the xmllint-split + prefix-probe ablation.
# Run pairs: C6+C7 in parallel, then C8+C9.
# 6 workers per (cond, seed) = 12 concurrent containers per group.
set -uo pipefail
cd /home/matt/sci/repo3
mkdir -p /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs

run_condition() {
  local COND="$1"
  for SEED in 1 2 3; do
    bash scripts/launch_dsv4_ablation.sh "$COND" "$SEED"
  done
}

echo "=== START Group C (C6 + C7) at $(date -u +%FT%TZ) ===" \
  | tee -a /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/_master_c6_c9.log

run_condition c6 &
PID_C6=$!
run_condition c7 &
PID_C7=$!
wait $PID_C6 $PID_C7

echo "=== START Group D (C8 + C9) at $(date -u +%FT%TZ) ===" \
  | tee -a /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/_master_c6_c9.log

run_condition c8 &
PID_C8=$!
run_condition c9 &
PID_C9=$!
wait $PID_C8 $PID_C9

echo "=== ALL DONE at $(date -u +%FT%TZ) ===" \
  | tee -a /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/_master_c6_c9.log

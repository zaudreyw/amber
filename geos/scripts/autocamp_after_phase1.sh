#!/usr/bin/env bash
# Run after Phase 1 finishes:
#   1. Score Phase 1 results
#   2. Pick winning primer
#   3. Launch Phase 2 (DSv4) in background
# Phase 3 was pre-launched in parallel — see logic below.
set -euo pipefail
cd /home/matt/sci/repo3

# Lockfile to prevent double-execution (multiple watchers may race)
LOCK="/tmp/autocamp_after_phase1.lock"
if ! ( set -o noclobber; > "$LOCK" ) 2>/dev/null; then
  echo "after-phase1 already running or completed (lock $LOCK exists). Exiting."
  exit 0
fi
trap 'rm -f "$LOCK.released"' EXIT  # leave the lock in place so future invocations skip
touch "$LOCK.released"

echo "=== After Phase 1 — score + decide + launch Phase 2 + Phase 3 ==="
date -u +%Y-%m-%dT%H:%M:%SZ

# 1. Score Phase 1
echo "--- scoring Phase 1 ---"
bash scripts/score_autocamp.sh

# 2. Pick winner
echo "--- choosing primer ---"
WINNER=$(python3 scripts/decide_phase1_winner.py 2>/tmp/phase1_decide_stderr.log | tail -1)
echo "Phase 1 winner: $WINNER"
echo "$WINNER" > /tmp/autocamp_phase1_winner.txt

# 3. Launch Phase 2 (DSv4 ablation)
echo "--- launching Phase 2 (DSv4) ---"
PHASE2_PRIMER="$WINNER" bash scripts/launch_autocamp_phase2.sh > /tmp/phase2_launcher.log 2>&1 &
PID_P2=$!
echo "Phase 2 PID: $PID_P2"

# Phase 3 was pre-launched in parallel with Phase 1 — don't double-launch.
# If Phase 3 isn't running, launch it now.
if ! pgrep -f "launch_autocamp_phase3" > /dev/null; then
  if [ ! -d "/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/xmodel" ] || [ -z "$(ls -A /data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/xmodel/ 2>/dev/null)" ]; then
    echo "--- launching Phase 3 (was not pre-launched) ---"
    PHASE3_BEST_CELL="autocamp_F6" PHASE3_PRIMER="$WINNER" \
      bash scripts/launch_autocamp_phase3.sh > /tmp/phase3_launcher.log 2>&1 &
    PID_P3=$!
    echo "Phase 3 PID: $PID_P3"
  else
    echo "--- Phase 3 already pre-launched, skipping ---"
  fi
else
  echo "--- Phase 3 already running, skipping ---"
fi

echo "Phase 2 ETA ~5h."
date -u +%Y-%m-%dT%H:%M:%SZ

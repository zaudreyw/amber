#!/usr/bin/env bash
# Rescore tasks that previously failed scoring after the _resolve_included cycle fix.
# For each run under /data/shared/.../results/, find task names present in the
# experiments dir but missing a *_eval.json in the results dir, and rescore them.
set -u
cd "$(dirname "$0")/.."

GT=/data/shared/geophysics_agent_data/data/eval/experiments_gt
RESULTS_ROOT=/data/shared/geophysics_agent_data/data/eval/results

for run in $(ls $RESULTS_ROOT); do
  resdir=$RESULTS_ROOT/$run
  agent_subdir=$(ls -d $resdir/*/ 2>/dev/null | head -1)
  [ -z "$agent_subdir" ] && continue
  agent=$(basename $agent_subdir)

  expdir=/home/matt/sci/repo3/data/eval/$agent/$run
  if [ ! -d "$expdir" ]; then
    expdir=/data/shared/geophysics_agent_data/data/eval/$agent/$run
  fi
  [ ! -d "$expdir" ] && continue

  missing=()
  for d in $expdir/*/; do
    name=$(basename $d)
    if [ ! -f "$agent_subdir/${name}_eval.json" ]; then
      missing+=("$name")
    fi
  done
  [ ${#missing[@]} -eq 0 ] && continue

  echo "### $run (agent=$agent) — rescoring ${#missing[@]} tasks: ${missing[*]}"
  uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir "$expdir" \
    --ground-truth-dir "$GT" \
    --results-dir "$agent_subdir" \
    --experiments "${missing[@]}" 2>&1 | tail -n +1
done

#!/bin/bash
# Quick-glance status for the running autocamp.
ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01"

echo "=== autocamp status @ $(date -u +%H:%M:%SZ) ==="
echo

echo "Active python run_experiment.py processes:"
ps -ef | grep -c "run_experiment.py" || true
ps -ef | grep "run_experiment.py" | grep -v grep | awk '{for(i=14;i<=NF;i++) if($i=="--run") {print "  ", $(i+1); break}}' | sort -u
echo

echo "Logs:"
ls -t "$ROOT/_logs/" 2>/dev/null | head -10 | sed 's/^/  /'
echo

echo "Per-cell progress (success / total):"
for sub in dsv4 xmodel; do
  for agent_dir in "$ROOT/$sub"/*/ ; do
    [ -d "$agent_dir" ] || continue
    AGENT=$(basename "$agent_dir")
    for run_dir in "$agent_dir"*/ ; do
      [ -d "$run_dir" ] || continue
      RUN=$(basename "$run_dir")
      n_total=$(find "$run_dir" -maxdepth 2 -name "events.jsonl" 2>/dev/null | wc -l)
      n_done=$(find "$run_dir" -name "status.json" -exec grep -l '"status": "success"' {} \; 2>/dev/null | wc -l)
      summary="$ROOT/_results/$RUN/$AGENT/_summary.json"
      score="—"
      if [ -f "$summary" ]; then
        score=$(python3 -c "
import json
d = json.load(open('$summary'))
m = d.get('summary',{}).get('overall_score',{}).get('scored_mean')
print(f'{m/10:.3f}' if m is not None else '—')
" 2>/dev/null)
      fi
      printf "  %-22s %-30s  %d/%d  treesim=%s\n" "$AGENT" "$RUN" "$n_done" "$n_total" "$score"
    done
  done
done

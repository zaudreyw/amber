#!/usr/bin/env bash
cd /home/matt/sci/repo3
ROOT=data/eval/interactive_autonomy_2026-05-03
for d in $ROOT/modeA_*/*/*/* $ROOT/modeB_*/*/*/*; do
  [ -d "$d" ] || continue
  [ -f "$d/status.json" ] || continue
  MD=$(echo "$d" | awk -F/ '{print $4}')
  AG=$(echo "$d" | awk -F/ '{print $5}' | sed 's/^ia_//' | sed 's/_interactive$/-int/' | sed 's/_noninteractive$//')
  TASK=$(basename "$d")
  python3 -c "import json,os
d=json.load(open('$d/status.json'))
ps=d.get('process_status','?'); el=int(d.get('elapsed_seconds',0)); t=d.get('total_tool_calls',0)
print(f'  ${MD:13s} ${AG:9s} ${TASK:42s} {ps:10s} elapsed={el}s tools={t}')"
done | sort
echo "---supervisor calls (any > 0)---"
find $ROOT -name supervisor_calls.jsonl 2>/dev/null | while read f; do
  n=$(wc -l < "$f")
  [ "$n" != "0" ] && echo "  $n  $f"
done

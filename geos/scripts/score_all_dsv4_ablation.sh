#!/usr/bin/env bash
# Score every (condition, seed) of dsv4_ablation_2026-04-29 that has all
# 17 tasks complete (status.json with exit_code != None).
#
# Idempotent: re-running re-scores. Skips conditions/seeds where output
# dir doesn't exist yet.
set -uo pipefail
cd /home/matt/sci/repo3

ROOT="/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29"

for COND in c0 c2 c3 c4 c5 c6 c7 c8 c9 c10 c11 cMPa cMPb; do
  case "$COND" in
    c0) AGENT="abl_c0_true_vanilla" ;;
    c2) AGENT="abl_c2_min_sr_no_rag" ;;
    c3) AGENT="abl_c3_min_rag_no_sr" ;;
    c4) AGENT="abl_c4_min_rag_sr" ;;
    c5) AGENT="abl_c5_dsv4_mem" ;;
    c6) AGENT="abl_c6_xmllint_hook" ;;
    c7) AGENT="abl_c7_xmllint_full_no_rag" ;;
    c8) AGENT="abl_c8_xmllint_full_rag" ;;
    c9) AGENT="abl_c9_no_prefix" ;;
    c10) AGENT="abl_c10_xmllint_hook_mem" ;;
    c11) AGENT="abl_c11_xmllint_full_mem" ;;
    cMPa) AGENT="abl_cMP_a_memp_on_c2" ;;
    cMPb) AGENT="abl_cMP_b_memp_on_c7" ;;
  esac
  for SEED in 1 2 3; do
    RUN_NAME="${COND}_dsv4_s${SEED}"
    RUN_DIR="$ROOT/$AGENT/$RUN_NAME"
    if [ ! -d "$RUN_DIR" ]; then
      continue
    fi
    # all 17 tasks must have status.json with exit_code present (non-None)
    NDONE=$(find "$RUN_DIR" -name status.json -exec python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    sys.exit(0 if d.get('exit_code') is not None else 1)
except Exception:
    sys.exit(1)
" {} \; -print 2>/dev/null | wc -l)
    if [ "$NDONE" -lt 17 ]; then
      echo "skip $RUN_NAME: only $NDONE/17 tasks finished"
      continue
    fi
    echo "scoring $RUN_NAME..."
    bash scripts/score_dsv4_ablation.sh "$COND" "$SEED" 2>&1 | tail -1
  done
done

# Print per-(cond,seed) means
echo ""
echo "=== Summary ==="
for COND in c0 c2 c3 c4 c5 c6 c7 c8 c9 c10 c11 cMPa cMPb; do
  case "$COND" in
    c0) AGENT="abl_c0_true_vanilla" ;;
    c2) AGENT="abl_c2_min_sr_no_rag" ;;
    c3) AGENT="abl_c3_min_rag_no_sr" ;;
    c4) AGENT="abl_c4_min_rag_sr" ;;
    c5) AGENT="abl_c5_dsv4_mem" ;;
    c6) AGENT="abl_c6_xmllint_hook" ;;
    c7) AGENT="abl_c7_xmllint_full_no_rag" ;;
    c8) AGENT="abl_c8_xmllint_full_rag" ;;
    c9) AGENT="abl_c9_no_prefix" ;;
    c10) AGENT="abl_c10_xmllint_hook_mem" ;;
    c11) AGENT="abl_c11_xmllint_full_mem" ;;
    cMPa) AGENT="abl_cMP_a_memp_on_c2" ;;
    cMPb) AGENT="abl_cMP_b_memp_on_c7" ;;
  esac
  for SEED in 1 2 3; do
    RUN_NAME="${COND}_dsv4_s${SEED}"
    SUM="$ROOT/_results/$RUN_NAME/$AGENT/_summary.json"
    if [ -f "$SUM" ]; then
      python3 -c "
import json
d = json.load(open('$SUM'))['summary']['treesim']
print(f'$RUN_NAME: mean={d[\"scored_mean\"]:.4f}  n_scored={d[\"scored_n\"]}  min={d[\"scored_min\"]:.3f}  max={d[\"scored_max\"]:.3f}')
"
    fi
  done
done

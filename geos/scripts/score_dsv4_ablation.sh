#!/usr/bin/env bash
# Score one (condition, seed) of the dsv4_ablation_2026-04-29 matrix.
# Writes per-task `<task>_eval.json` + a `_summary.json` to:
#   /data/shared/.../dsv4_ablation_2026-04-29/_results/<run_name>/<agent>/
#
# Usage:
#   ./scripts/score_dsv4_ablation.sh <condition> <seed>
set -euo pipefail
cd /home/matt/sci/repo3

COND="${1:?cond required}"
SEED="${2:?seed required}"

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
  *) echo "unknown condition: $COND" >&2; exit 2 ;;
esac

RUN_NAME="${COND}_dsv4_s${SEED}"
EXP_DIR="/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/${AGENT}/${RUN_NAME}"
GT_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_gt"
RESULTS_DIR="/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results/${RUN_NAME}/${AGENT}"

mkdir -p "$RESULTS_DIR"

uv run python scripts/eval/batch_evaluate.py \
  --experiments-dir "$EXP_DIR" \
  --ground-truth-dir "$GT_DIR" \
  --results-dir "$RESULTS_DIR" \
  --output "$RESULTS_DIR/_summary.json"

echo "wrote scores to $RESULTS_DIR"

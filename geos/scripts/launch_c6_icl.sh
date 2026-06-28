#!/usr/bin/env bash
# Run C6 (best hand-designed: min primer + xmllint hook, no RAG, no memory)
# × 3 seeds on the 10 ICL holdout tasks. To probe whether the ~0.60 mean
# we saw for v0/v3 on ICL-10 is intrinsic difficulty or test-17 selection bias.
set -uo pipefail
cd /home/matt/sci/repo3
source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
export GEOS_HOOK_XMLLINT=1

ICL_TASKS=(
  AdvancedExampleCasedThermoElasticWellbore
  AdvancedExamplePureThermalDiffusionWellbore
  AdvancedExampleThermoPoroElasticWellbore
  AdvancedExampleViscoExtendedDruckerPrager
  ExampleIsothermalHystInjection
  ExampleMCCWellbore
  ExampleProppantTest
  ExamplesingleFracCompression
  ExampleVerticalPoroElastoPlasticWellbore
  TutorialHydraulicFractureWithAdvancedXML
)

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/se_icl_2026-04-30"
mkdir -p "$RESULTS_ROOT/_logs"
EXP_DIR="/data/shared/geophysics_agent_data/data/eval/experiments"
GT_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_gt"

launch_one() {
  local SEED="$1"
  local RUN_NAME="c6_icl_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN_NAME}.log"
  echo "[*] launching C6 s${SEED} -> $LOG"
  python3 scripts/run_experiment.py \
    --run "$RUN_NAME" \
    --agents abl_c6_xmllint_hook \
    --workers 5 \
    --timeout 1500 \
    --strip-baked-primer \
    --geos-primer-path plugin/GEOS_PRIMER_minimal_vanilla.md \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir "$EXP_DIR" \
    --ground-truth-dir "$GT_DIR" \
    --include "${ICL_TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT" \
    --claude-model deepseek-v4-flash \
    >> "$LOG" 2>&1
  echo "[*] finished C6 s${SEED} rc=$?"
}

echo "=== START C6 on ICL-10 at $(date -u +%FT%TZ) ==="
for SEED in 1 2 3; do launch_one "$SEED" & done
wait
echo "=== DONE at $(date -u +%FT%TZ) ==="

#!/usr/bin/env bash
# Cross-task transfer eval: v0 vs v3 of the self-evolving plugin on the
# 10 ICL holdout tasks (never seen by the SEA's reflection rounds).
#
# 6 parallel runs (2 versions × 3 seeds), each with workers=5 internal,
# total ~30 concurrent CC processes. Expected wall ~15-25 min.
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
  local VERSION="$1"  # 0 or 3
  local SEED="$2"     # 1, 2, 3
  local PLUGIN_DIR="plugin_evolving/v${VERSION}"
  local PRIMER="$PLUGIN_DIR/PRIMER.md"
  local CHEATSHEET="$PLUGIN_DIR/memory/cheatsheet.md"
  local EFFECTIVE_PRIMER="$PLUGIN_DIR/_runtime_primer_icl_s${SEED}.md"

  cp "$PRIMER" "$EFFECTIVE_PRIMER"
  if [ -f "$CHEATSHEET" ]; then
    echo "" >> "$EFFECTIVE_PRIMER"
    echo "---" >> "$EFFECTIVE_PRIMER"
    echo "" >> "$EFFECTIVE_PRIMER"
    cat "$CHEATSHEET" >> "$EFFECTIVE_PRIMER"
  fi

  local RUN_NAME="se_icl_v${VERSION}_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN_NAME}.log"

  echo "[*] launching v${VERSION} s${SEED} -> $LOG"

  python3 scripts/run_experiment.py \
    --run "$RUN_NAME" \
    --agents abl_se_round \
    --workers 5 \
    --timeout 1500 \
    --strip-baked-primer \
    --geos-primer-path "$EFFECTIVE_PRIMER" \
    --plugin-dir "$PLUGIN_DIR" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir "$EXP_DIR" \
    --ground-truth-dir "$GT_DIR" \
    --include "${ICL_TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT" \
    --claude-model deepseek-v4-flash \
    >> "$LOG" 2>&1
  local rc=$?
  rm -f "$EFFECTIVE_PRIMER"
  echo "[*] finished v${VERSION} s${SEED} rc=$rc"
  return $rc
}

echo "=== START SE-ICL transfer eval at $(date -u +%FT%TZ) ==="
echo "    versions=v0,v3  seeds=1,2,3  tasks=${#ICL_TASKS[@]}"

# Launch all 6 in parallel
for VERSION in 0 3; do
  for SEED in 1 2 3; do
    launch_one "$VERSION" "$SEED" &
  done
done

wait
echo "=== DONE SE-ICL transfer eval at $(date -u +%FT%TZ) ==="

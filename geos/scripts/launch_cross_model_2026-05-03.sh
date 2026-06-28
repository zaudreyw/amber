#!/bin/bash
# Cross-model panel: Vanilla, X+M, SE × {minimax-m2.7, gemini-3-flash-preview}
# × test-17 × 1 seed.
# Default-off harness (GEOS_HOOK_POSTTOOLUSE unset → autocamp-experiment-state).
set -euo pipefail
cd "$(dirname "$0")/.."

source .env
export ANTHROPIC_BASE_URL="https://openrouter.ai/api"
export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/cross_model_2026-05-03"
mkdir -p "$RESULTS_ROOT/_logs"

TEST17=(
  AdvancedExampleCasedContactThermoElasticWellbore
  AdvancedExampleDeviatedElasticWellbore
  AdvancedExampleDruckerPrager
  AdvancedExampleExtendedDruckerPrager
  AdvancedExampleModifiedCamClay
  AdvancedExampleViscoDruckerPrager
  buckleyLeverettProblem
  ExampleDPWellbore
  ExampleEDPWellbore
  ExampleIsothermalLeakyWell
  ExampleMandel
  ExampleThermalLeakyWell
  ExampleThermoporoelasticConsolidation
  kgdExperimentValidation
  pknViscosityDominated
  TutorialPoroelasticity
  TutorialSneddon
)

# (cell, primer, xmllint_env, extra_flags)
declare -a CELLS=(
  "autocamp_F0|plugin/GEOS_PRIMER_contract.md|0|"
  "autocamp_F4|plugin/GEOS_PRIMER_contract.md|0|"
  "autocamp_SE|plugin_evolving/v3/PRIMER.md|1|--plugin-dir plugin_evolving/v3"
)

run_cell_model() {
  local AGENT="$1" PRIMER="$2" XMLLINT="$3" EXTRA="$4" MODEL="$5"
  local MODEL_TAG=$(echo "$MODEL" | tr '/' '_')
  local CELL_TAG="${AGENT##autocamp_}"
  local RUN="${MODEL_TAG}_${CELL_TAG}_s1"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  echo "  launching $RUN at $(date -u +%H:%M:%SZ)"
  GEOS_HOOK_XMLLINT="$XMLLINT" \
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents "$AGENT" \
    --workers 4 --timeout 1800 \
    --strip-baked-primer \
    --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TEST17[@]}" \
    --results-root-dir "$RESULTS_ROOT/${MODEL_TAG}" \
    --claude-model "$MODEL" \
    $EXTRA \
    > "$LOG" 2>&1
}

# Sequential: model × cell. Two models × three cells = 6 launches.
for MODEL in "minimax/minimax-m2.7" "google/gemini-3-flash-preview"; do
  for spec in "${CELLS[@]}"; do
    IFS='|' read -r agent primer xmllint extra <<< "$spec"
    run_cell_model "$agent" "$primer" "$xmllint" "$extra" "$MODEL"
  done
done

echo "=== CROSS-MODEL COMPLETE at $(date -u +%H:%M:%SZ) ==="

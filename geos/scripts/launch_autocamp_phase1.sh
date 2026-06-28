#!/bin/bash
# Phase 1: primer screen — contract vs method, 1 seed × 17 tasks each on DSv4-flash.
# Output: /data/shared/.../eval/autocamp_2026-05-01/dsv4/<agent>/<run>/<task>/
set -euo pipefail
cd "$(dirname "$0")/.."

source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
export GEOS_HOOK_XMLLINT=0  # explicitly off for Phase 1

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01"
mkdir -p "$RESULTS_ROOT/_logs"

run_phase1() {
  local AGENT="$1"  PRIMER="$2"
  local RUN="${AGENT}_s1"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  echo "=== Launching $RUN ($AGENT, primer=$PRIMER) at $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG"
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents "$AGENT" \
    --workers 5 --timeout 1200 \
    --strip-baked-primer \
    --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include AdvancedExampleCasedContactThermoElasticWellbore \
              AdvancedExampleDeviatedElasticWellbore \
              AdvancedExampleDruckerPrager \
              AdvancedExampleExtendedDruckerPrager \
              AdvancedExampleModifiedCamClay \
              AdvancedExampleViscoDruckerPrager \
              buckleyLeverettProblem \
              ExampleDPWellbore \
              ExampleEDPWellbore \
              ExampleIsothermalLeakyWell \
              ExampleMandel \
              ExampleThermalLeakyWell \
              ExampleThermoporoelasticConsolidation \
              kgdExperimentValidation \
              pknViscosityDominated \
              TutorialPoroelasticity \
              TutorialSneddon \
    --results-root-dir "$RESULTS_ROOT/dsv4" \
    --claude-model deepseek-v4-flash \
    >>"$LOG" 2>&1
}

# Run sequentially (not parallel) since they share the DSv4 endpoint
run_phase1 autocamp_p_contract plugin/GEOS_PRIMER_contract.md
run_phase1 autocamp_p_method   plugin/GEOS_PRIMER_method.md

echo "=== Phase 1 launches complete at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# Chain into the after-Phase-1 automation (score → decide → Phase 2 launch)
echo "--- chaining into autocamp_after_phase1.sh ---"
bash "$(dirname "$0")/autocamp_after_phase1.sh"

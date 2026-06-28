#!/bin/bash
# Re-launch Phase 2 seeds 2 + 3 only (after DSv4 balance was refilled).
# Seed 1 is already complete and kept as-is.
set -euo pipefail
cd "$(dirname "$0")/.."

source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

PRIMER="${PHASE2_PRIMER:-plugin/GEOS_PRIMER_contract.md}"
echo "Primer: $PRIMER"

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01"
mkdir -p "$RESULTS_ROOT/_logs"

TASKS=(
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

run_seed() {
  local AGENT="$1" SEED="$2" XMLLINT_ENV="$3"
  shift 3
  local RUN="${AGENT}_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  GEOS_HOOK_XMLLINT="$XMLLINT_ENV" \
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents "$AGENT" \
    --workers 8 --timeout 1500 \
    --strip-baked-primer \
    --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT/dsv4" \
    --claude-model deepseek-v4-flash \
    "$@" \
    > "$LOG" 2>&1
}

for SEED in 2 3; do
  echo "=== SEED $SEED start at $(date -u +%H:%M:%SZ) ==="
  run_seed autocamp_F0 $SEED 0
  run_seed autocamp_F1 $SEED 0
  run_seed autocamp_F2 $SEED 0
  run_seed autocamp_F3 $SEED 0
  run_seed autocamp_F4 $SEED 0
  run_seed autocamp_F5 $SEED 0
  run_seed autocamp_F6 $SEED 1
  run_seed autocamp_F7 $SEED 1
  run_seed autocamp_SE $SEED 1 \
    --plugin-dir plugin_evolving/v3 \
    --geos-primer-path plugin_evolving/v3/PRIMER.md
  echo "=== SEED $SEED done at $(date -u +%H:%M:%SZ) ==="
done

echo "=== Phase 2 seeds 2+3 complete at $(date -u +%H:%M:%SZ) ==="

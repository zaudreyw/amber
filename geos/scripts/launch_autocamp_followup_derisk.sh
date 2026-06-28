#!/bin/bash
# Derisk: F8 (missing factorial cell) + F11 (decomposed SE) on test-17.
# Both have memory; F8 uses m1u (same as F4), F11 uses v3 cheatsheet.
# F11 also overrides primer to plugin_evolving/v3/PRIMER.md
set -euo pipefail
cd "$(dirname "$0")/.."

source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01"
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

run_seed() {
  # $1=cell, $2=seed, $3=xmllint env, $4+=extra flags
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
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TEST17[@]}" \
    --results-root-dir "$RESULTS_ROOT/dsv4" \
    --claude-model deepseek-v4-flash \
    "$@" \
    > "$LOG" 2>&1
}

for SEED in 1 2 3; do
  echo "=== SEED $SEED start at $(date -u +%H:%M:%SZ) ==="
  # F8: contract primer + xmllint stack (S+X+M no RAG)
  run_seed autocamp_F8 $SEED 1 \
    --geos-primer-path plugin/GEOS_PRIMER_contract.md
  # F11: v3 PRIMER + xmllint stack + v3 cheatsheet (no RAG, no skills via plugin)
  run_seed autocamp_F11 $SEED 1 \
    --geos-primer-path plugin_evolving/v3/PRIMER.md
  echo "=== SEED $SEED done at $(date -u +%H:%M:%SZ) ==="
done

echo "=== Derisk complete at $(date -u +%H:%M:%SZ) ==="

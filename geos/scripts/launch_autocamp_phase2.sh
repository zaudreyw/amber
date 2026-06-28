#!/bin/bash
# Phase 2: DSv4 fractional factorial ablation. 9 cells × 3 seeds × 17 tasks.
# Cells: F0..F7 (Resolution-IV 2^(4-1)) + SE.
# PRIMER picked by user via $PHASE2_PRIMER env var (defaults to method).
set -euo pipefail
cd "$(dirname "$0")/.."

source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

# Primer selection — exported by caller. Default = method (will be set
# after Phase 1 result; if Phase 1 hasn't decided, method is the safer
# bet because it includes the doc/inputFiles pointers).
PRIMER="${PHASE2_PRIMER:-plugin/GEOS_PRIMER_method.md}"
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
  # $1=cell-name, $2=seed#, $3=xmllint env value (0 or 1), $4-...=extra flags
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

# Cell -> xmllint-env mapping. X=+ requires GEOS_HOOK_XMLLINT=1 in env.
# F0 R-S-X-M- : xmllint=0
# F1 R+S-X-M+ : xmllint=0
# F2 R-S+X-M+ : xmllint=0
# F3 R+S+X-M- : xmllint=0
# F4 R-S-X+M+ : xmllint=1
# F5 R+S-X+M- : xmllint=1
# F6 R-S+X+M- : xmllint=1
# F7 R+S+X+M+ : xmllint=1
# SE          : xmllint=1, plugin override

for SEED in 1 2 3; do
  echo "=== SEED $SEED start at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  # F4, F5 have stop_hook=False, so GEOS_HOOK_XMLLINT has no effect (no
  # hook to fire). F6, F7 are S+X+ — schema check via hook is active.
  run_seed autocamp_F0 $SEED 0
  run_seed autocamp_F1 $SEED 0
  run_seed autocamp_F2 $SEED 0
  run_seed autocamp_F3 $SEED 0
  run_seed autocamp_F4 $SEED 0
  run_seed autocamp_F5 $SEED 0
  run_seed autocamp_F6 $SEED 1
  run_seed autocamp_F7 $SEED 1
  # SE: override plugin-dir + primer to plugin_evolving/v3/
  run_seed autocamp_SE $SEED 1 \
    --plugin-dir plugin_evolving/v3 \
    --geos-primer-path plugin_evolving/v3/PRIMER.md
  echo "=== SEED $SEED done at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
done

echo "=== Phase 2 launches complete at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

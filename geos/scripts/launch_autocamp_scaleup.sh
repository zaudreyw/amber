#!/bin/bash
# Scale-up: run selected cells on ICL-10 and train-19.
# Sequence:
#   - Phase A (ICL-10): all selected cells × 3 seeds (clean for all configs)
#   - Phase B (train-19): memory-free cells only × 3 seeds (clean for those)
# Caller may set SCALEUP_CELLS to override the cell list.
set -euo pipefail
cd "$(dirname "$0")/.."

source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_followup_2026-05-02"
mkdir -p "$RESULTS_ROOT/_logs"

ICL10=(
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

TRAIN19=(
  AdvancedExampleCasedElasticWellbore
  AdvancedExampleCasedElasticWellboreImperfectInterfaces
  AdvancedExampleDeviatedPoroElasticWellbore
  AdvancedExampleViscoModifiedCamClay
  AdvancedExampleWellboreNonLinearThermalDiffusionTemperatureDependentSinglePhaseThermalConductivity
  AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity
  ExampleKirschWellbore
  ExampleSPE11b
  ExampleTFrac
  faultVerification
  kgdToughnessDominated
  kgdViscosityDominated
  pennyFracToughnessDominated
  pennyFracViscosityDominated
  relaxationTest
  triaxialDriverExample
  TutorialCO2FieldCase
  TutorialDeadOilBottomLayersSPE10
  TutorialDeadOilEgg
)

# Per-cell config: agent_name|primer_path|xmllint_env|optional_extra_flags
# Order: F0 (baseline) → F6 (no-mem winner) → F4 (mem winner) → SE (monolith) → F8 (factorial gap) → F11 (decomposed SE)
declare -a CELLS=(
  "autocamp_F0|plugin/GEOS_PRIMER_contract.md|0|"
  "autocamp_F6|plugin/GEOS_PRIMER_contract.md|1|"
  "autocamp_F4|plugin/GEOS_PRIMER_contract.md|0|"
  "autocamp_SE|plugin_evolving/v3/PRIMER.md|1|--plugin-dir plugin_evolving/v3"
  "autocamp_F8|plugin/GEOS_PRIMER_contract.md|1|"
  "autocamp_F11|plugin_evolving/v3/PRIMER.md|1|"
)

# Memory-free cells eligible for train-19 evaluation
MEMORY_FREE=("autocamp_F0" "autocamp_F6")

is_memory_free() {
  local name="$1"
  for n in "${MEMORY_FREE[@]}"; do
    [[ "$n" == "$name" ]] && return 0
  done
  return 1
}

run_one() {
  # $1=agent_name $2=primer $3=xmllint $4=extra_flags $5=set_label (icl|train) $6=seed $7=tasks_var
  local AGENT="$1" PRIMER="$2" XMLLINT="$3" EXTRA="$4" SET="$5" SEED="$6" TASKS_VAR="$7"
  local RUN="${AGENT##autocamp_}_${SET}_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  local TASKS_REF="$TASKS_VAR[@]"
  local -a TASKS=("${!TASKS_REF}")

  GEOS_HOOK_XMLLINT="$XMLLINT" \
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents "$AGENT" \
    --workers 8 --timeout 1500 \
    --strip-baked-primer \
    --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_from_mined_specs \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT/${SET}" \
    --claude-model deepseek-v4-flash \
    $EXTRA \
    > "$LOG" 2>&1
}

# Phase A: ICL-10 — all cells × 3 seeds
echo "=== Phase A: ICL-10 start at $(date -u +%H:%M:%SZ) ==="
for SEED in 1 2 3; do
  for spec in "${CELLS[@]}"; do
    IFS='|' read -r agent primer xmllint extra <<< "$spec"
    echo "  ICL-10 $agent s$SEED at $(date -u +%H:%M:%SZ)"
    run_one "$agent" "$primer" "$xmllint" "$extra" "icl" "$SEED" "ICL10"
  done
done
echo "=== Phase A done at $(date -u +%H:%M:%SZ) ==="

# Phase B: train-19 — memory-free cells only × 3 seeds
# Override experiments-dir to test36_template (which has these tasks)
echo "=== Phase B: train-19 start at $(date -u +%H:%M:%SZ) ==="
run_train() {
  local AGENT="$1" PRIMER="$2" XMLLINT="$3" SEED="$4"
  local RUN="${AGENT##autocamp_}_train_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  GEOS_HOOK_XMLLINT="$XMLLINT" \
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents "$AGENT" \
    --workers 8 --timeout 1500 \
    --strip-baked-primer \
    --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TRAIN19[@]}" \
    --results-root-dir "$RESULTS_ROOT/train" \
    --claude-model deepseek-v4-flash \
    > "$LOG" 2>&1
}
for SEED in 1 2 3; do
  echo "  train F0 s$SEED at $(date -u +%H:%M:%SZ)"
  run_train autocamp_F0 plugin/GEOS_PRIMER_contract.md 0 $SEED
  echo "  train F6 s$SEED at $(date -u +%H:%M:%SZ)"
  run_train autocamp_F6 plugin/GEOS_PRIMER_contract.md 1 $SEED
done
echo "=== Phase B done at $(date -u +%H:%M:%SZ) ==="

echo "=== SCALEUP COMPLETE at $(date -u +%H:%M:%SZ) ==="

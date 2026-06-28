#!/bin/bash
# Phase 3: cross-model — launch 3 models IN PARALLEL on OpenRouter.
# Each model runs its own 2 cells × 3 seeds × 17 tasks.
# Caller exports PHASE3_BEST_CELL (default autocamp_F6) and
# PHASE3_PRIMER (default plugin/GEOS_PRIMER_method.md).
set -euo pipefail
cd "$(dirname "$0")/.."

source .env

BEST_CELL="${PHASE3_BEST_CELL:-autocamp_F6}"
PRIMER="${PHASE3_PRIMER:-plugin/GEOS_PRIMER_method.md}"
echo "Best DSv4 cell (used for xmodel best): $BEST_CELL"
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

run_xmodel_cell() {
  # $1=cell-agent, $2=seed#, $3=model-slug, $4=xmllint env (0/1)
  local AGENT="$1" SEED="$2" MODEL="$3" XMLLINT_ENV="$4"
  local MODEL_TAG=$(echo "$MODEL" | tr '/' '_')
  local SHORT="${AGENT##autocamp_xmodel_}"
  local RUN="${MODEL_TAG}_${SHORT}_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/xmodel_${RUN}.log"
  echo "  launching $RUN"
  ANTHROPIC_BASE_URL="https://openrouter.ai/api" \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  GEOS_HOOK_XMLLINT="$XMLLINT_ENV" \
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents "$AGENT" \
    --workers 5 --timeout 1800 \
    --strip-baked-primer \
    --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT/xmodel" \
    --claude-model "$MODEL" \
    > "$LOG" 2>&1
}

run_model_full() {
  # $1=model — runs that model's 2 cells × 3 seeds sequentially
  local MODEL="$1"
  local MODEL_TAG=$(echo "$MODEL" | tr '/' '_')
  echo "=== $MODEL start at $(date -u +%H:%M:%SZ) ==="
  for SEED in 1 2 3; do
    run_xmodel_cell autocamp_xmodel_baseline $SEED "$MODEL" 0
    run_xmodel_cell autocamp_xmodel_best     $SEED "$MODEL" 1
  done
  echo "=== $MODEL done at $(date -u +%H:%M:%SZ) ==="
}

# Launch models in PARALLEL.
#
# 2026-05-01 preflight finding: google/gemma-4-31b-it timed out at 600s
# with 9 tool calls and zero XML files written on the smoke task.
# Gemma is bottlenecked at <1 tool/min — too slow to complete a 17-task
# evaluation in any reasonable wall-time budget. Skipping gemma cells.
#
# Gemma run kept commented for reference / future re-test.
run_model_full "minimax/minimax-m2.7"        > "$RESULTS_ROOT/_logs/xmodel_minimax_runner.log" 2>&1 &
PID_MINIMAX=$!
# run_model_full "google/gemma-4-31b-it"     > "$RESULTS_ROOT/_logs/xmodel_gemma_runner.log" 2>&1 &
# PID_GEMMA=$!
run_model_full "openai/gpt-oss-120b"         > "$RESULTS_ROOT/_logs/xmodel_gptoss_runner.log" 2>&1 &
PID_GPTOSS=$!

echo "Parallel PIDs: minimax=$PID_MINIMAX gpt-oss=$PID_GPTOSS"

wait $PID_MINIMAX
echo "minimax done at $(date -u +%H:%M:%SZ)"
wait $PID_GPTOSS
echo "gpt-oss done at $(date -u +%H:%M:%SZ)"

echo "=== Phase 3 launches complete at $(date -u +%H:%M:%SZ) ==="

#!/bin/bash
# Qwen3.6-27B cross-model run.
# Phase A: baseline (F0 equivalent — no plugin, no MCP, no Stop hook), 1 seed × 17 tasks.
# Phase B (optional, gated on Phase A success + budget): best (xmllint MCP + plugin), 1 seed × 17 tasks.
#
# Per paper plan §5 Priority 1: "smaller-model alternative" smoke for
# regime-dependence claim. 1 seed is within plan.
# Per overnight-decisions doc: $50 budget cap.
set -euo pipefail
cd "$(dirname "$0")/.."

source .env

PHASE="${1:-A}"  # A or B
MODEL="qwen/qwen3.6-27b"
SEED="${SEED:-1}"
PRIMER="${PRIMER:-plugin/GEOS_PRIMER_contract.md}"

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

run_qwen_cell() {
  local AGENT="$1" XMLLINT_ENV="$2"
  local MODEL_TAG=$(echo "$MODEL" | tr '/' '_')
  local SHORT="${AGENT##autocamp_xmodel_}"
  local RUN="${MODEL_TAG}_${SHORT}_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/xmodel_${RUN}.log"
  echo "=== $RUN starting at $(date -u +%H:%M:%SZ) ==="
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
  echo "=== $RUN done at $(date -u +%H:%M:%SZ) ==="
}

case "$PHASE" in
  A) run_qwen_cell autocamp_xmodel_baseline 0 ;;
  B) run_qwen_cell autocamp_xmodel_best     1 ;;
  *) echo "usage: $0 [A|B]"; exit 1 ;;
esac

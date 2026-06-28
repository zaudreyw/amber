#!/usr/bin/env bash
# Launch the remaining 12 v2 tasks (the 17-task set minus the 5 already
# completed in orch_dsv4_5task_s1) on DSv4-flash direct, so they can be
# merged for a full 17-task comparison vs prior implementations.
#
# Usage:
#   bash scripts/orchestrator/launch_remaining_12.sh <run_name> [--fallback]

set -euo pipefail

RUN_NAME="${1:-orch_dsv4_remain12_s1}"
FALLBACK_FLAG="${2:-}"

# 17 v2 set MINUS the 5 already covered by orch_dsv4_5task_s1
# (TutorialSneddon, ExampleMandel, TutorialPoroelasticity,
#  AdvancedExampleDruckerPrager, buckleyLeverettProblem).
TASKS=(
    AdvancedExampleCasedContactThermoElasticWellbore
    AdvancedExampleDeviatedElasticWellbore
    AdvancedExampleExtendedDruckerPrager
    AdvancedExampleModifiedCamClay
    AdvancedExampleViscoDruckerPrager
    ExampleDPWellbore
    ExampleEDPWellbore
    ExampleIsothermalLeakyWell
    ExampleThermalLeakyWell
    ExampleThermoporoelasticConsolidation
    kgdExperimentValidation
    pknViscosityDominated
)

if [[ "$FALLBACK_FLAG" == "--fallback" ]]; then
    MODEL="deepseek/deepseek-v3.2"
    API_BASE="https://openrouter.ai/api"
    API_KEY_ENV="OPENROUTER_API_KEY"
    echo "[*] Fallback mode: OpenRouter $MODEL"
else
    MODEL="deepseek-v4-flash"
    API_BASE="https://api.deepseek.com/anthropic"
    API_KEY_ENV="DEEPSEEK_API_KEY"
    echo "[*] Primary mode: DeepSeek direct $MODEL"
fi

if [[ -z "${!API_KEY_ENV:-}" ]] && [[ -f .env ]]; then
    eval "$(grep -E "^${API_KEY_ENV}=" .env | sed 's/^/export /')"
fi
if [[ -z "${!API_KEY_ENV:-}" ]]; then
    echo "ERROR: $API_KEY_ENV not set."
    exit 1
fi
if [[ -z "${OPENROUTER_API_KEY:-}" ]] && [[ -f .env ]]; then
    eval "$(grep -E "^OPENROUTER_API_KEY=" .env | sed 's/^/export /')"
fi

mkdir -p /data/matt/geos_eval_tmp

LOGFILE="/tmp/orch_${RUN_NAME}.log"

echo "[*] Launching ${#TASKS[@]}-task orchestrator campaign (remaining-12)"
echo "    run_name : $RUN_NAME"
echo "    model    : $MODEL via $API_BASE"
echo "    log      : $LOGFILE"

python -m scripts.orchestrator.run_orchestrator_eval \
    --run "$RUN_NAME" \
    --include "${TASKS[@]}" \
    --workers 2 \
    --timeout 2400 \
    --strip-baked-primer \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --model "$MODEL" \
    --api-base "$API_BASE" \
    --api-key-env "$API_KEY_ENV" \
    2>&1 | tee "$LOGFILE"

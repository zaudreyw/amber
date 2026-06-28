#!/usr/bin/env bash
# Launch the full 17-task orchestrator campaign on DSv4-flash direct.
# Falls back to OpenRouter (deepseek-v3.2) if --fallback is passed.
#
# Run from repo root.
#
# Usage:
#   bash scripts/orchestrator/launch_full_17.sh <run_name> [--fallback]
#
# After it finishes, score with:
#   uv run python scripts/eval/batch_evaluate.py \
#     --experiments-dir data/eval/orchestrator_dsv4flash/<run_name> \
#     --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
#     --results-dir data/eval/results/<run_name>/orchestrator_dsv4flash

set -euo pipefail

RUN_NAME="${1:-orch_dsv4_s1}"
FALLBACK_FLAG="${2:-}"

# 17 v2 test tasks (from misc/memory_artifacts/test_blocklist.json keys).
TASKS=(
    AdvancedExampleCasedContactThermoElasticWellbore
    AdvancedExampleDeviatedElasticWellbore
    AdvancedExampleDruckerPrager
    AdvancedExampleExtendedDruckerPrager
    AdvancedExampleModifiedCamClay
    AdvancedExampleViscoDruckerPrager
    ExampleDPWellbore
    ExampleEDPWellbore
    ExampleIsothermalLeakyWell
    ExampleMandel
    ExampleThermalLeakyWell
    ExampleThermoporoelasticConsolidation
    TutorialPoroelasticity
    TutorialSneddon
    buckleyLeverettProblem
    kgdExperimentValidation
    pknViscosityDominated
)

# Choose model + endpoint
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

# Make sure key exists
if [[ -z "${!API_KEY_ENV:-}" ]]; then
    if [[ -f .env ]]; then
        eval "$(grep -E "^${API_KEY_ENV}=" .env | sed 's/^/export /')"
    fi
fi
if [[ -z "${!API_KEY_ENV:-}" ]]; then
    echo "ERROR: $API_KEY_ENV not set."
    exit 1
fi

# Also export OPENROUTER_API_KEY for the geos_rag_mcp embedding fallback.
if [[ -z "${OPENROUTER_API_KEY:-}" ]] && [[ -f .env ]]; then
    eval "$(grep -E "^OPENROUTER_API_KEY=" .env | sed 's/^/export /')"
fi

mkdir -p /data/matt/geos_eval_tmp

LOGFILE="/tmp/orch_${RUN_NAME}.log"

echo "[*] Launching ${#TASKS[@]}-task orchestrator campaign"
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

#!/usr/bin/env bash
# Reduced-scope launch — 5 representative v2 tasks across physics families.
# Used for the first orchestrator validation before committing to full 17-task.
#
# Usage:
#   bash scripts/orchestrator/launch_5task.sh <run_name> [--fallback]

set -euo pipefail

RUN_NAME="${1:-orch_dsv4_5task_s1}"
FALLBACK_FLAG="${2:-}"

TASKS=(
    TutorialSneddon
    ExampleMandel
    TutorialPoroelasticity
    AdvancedExampleDruckerPrager
    buckleyLeverettProblem
)

if [[ "$FALLBACK_FLAG" == "--fallback" ]]; then
    MODEL="deepseek/deepseek-v3.2"
    API_BASE="https://openrouter.ai/api"
    API_KEY_ENV="OPENROUTER_API_KEY"
    echo "[*] Fallback: OpenRouter $MODEL"
else
    MODEL="deepseek-v4-flash"
    API_BASE="https://api.deepseek.com/anthropic"
    API_KEY_ENV="DEEPSEEK_API_KEY"
    echo "[*] Primary: DeepSeek direct $MODEL"
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
echo "[*] Tasks: ${TASKS[*]}"
echo "[*] Log:   $LOGFILE"

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

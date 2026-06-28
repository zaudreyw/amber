#!/usr/bin/env bash
# Re-run orchestrator 3 seeds post-RN-005 P1 fixes.
# Writes to data/eval/orchestrator_dsv4flash/orch_dsv4_postfix_s{1,2,3}/.
# Cf. docs/2026-04-30_subagent-orchestrator-handoff.md "Action plan".
set -uo pipefail
cd /home/matt/sci/repo3

source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

mkdir -p /tmp/orch_logs

# 17 v2 tasks
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

# 3 seeds in parallel. workers=3 per seed = 9 task-batches concurrent.
# Each task spawns up to 5 subagents → ~15 effective concurrent containers.
for SEED in 1 2 3; do
  RUN_NAME="orch_dsv4_postfix_s${SEED}"
  echo "[*] Launching $RUN_NAME at $(date -u +%FT%TZ)"
  python -m scripts.orchestrator.run_orchestrator_eval \
    --run "$RUN_NAME" \
    --include "${TASKS[@]}" \
    --workers 3 \
    --timeout 2400 \
    --strip-baked-primer \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --model deepseek-v4-flash \
    --api-base "https://api.deepseek.com/anthropic" \
    --api-key-env "DEEPSEEK_API_KEY" \
    > "/tmp/orch_logs/${RUN_NAME}.log" 2>&1 &
done
wait
echo "[*] All 3 orchestrator seeds done at $(date -u +%FT%TZ)"

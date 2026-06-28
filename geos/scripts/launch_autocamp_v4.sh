#!/bin/bash
# v4 lookup-table experiment: same harness as SE (xmllint + plugin_enabled),
# but with plugin_evolving/v4/ — adds trajectory-mined task→canonical XML
# lookup, constitutive→header lookup, and anti-patterns to v3 cheatsheet.
#
# Usage: SEEDS="1 2 3" bash scripts/launch_autocamp_v4.sh
# Or:    SMOKE=1 bash scripts/launch_autocamp_v4.sh   (1 task, 1 seed)
set -euo pipefail
cd "$(dirname "$0")/.."

source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01"
mkdir -p "$RESULTS_ROOT/_logs"

if [ "${SMOKE:-0}" = "1" ]; then
  TASKS=(ExampleDPWellbore)
  SEEDS="1"
  RUN_SUFFIX="_smoke"
else
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
  SEEDS="${SEEDS:-1 2 3}"
  RUN_SUFFIX=""
fi

for SEED in $SEEDS; do
  RUN="autocamp_v4_s${SEED}${RUN_SUFFIX}"
  LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  echo "=== $RUN start at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  GEOS_HOOK_XMLLINT=1 \
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents autocamp_v4 \
    --workers 8 --timeout 1500 \
    --strip-baked-primer \
    --plugin-dir plugin_evolving/v4 \
    --geos-primer-path plugin_evolving/v4/PRIMER.md \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT/dsv4" \
    --claude-model deepseek-v4-flash \
    > "$LOG" 2>&1
  echo "=== $RUN done at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
done

#!/usr/bin/env bash
# Three parallel campaigns:
#   1. C6' on test-17  (abs-min primer + plugin + xmllint hook, no RAG, no memory)
#   2. C6' on ICL-10   (same setup, different task pool)
#   3. C1 redux on test-17 (no plugin + minimal_vanilla.md primer; sanity check)
#
# Total: 9 seeds (3 per cell), launched in parallel.
set -uo pipefail
cd /home/matt/sci/repo3
source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

ICL_TASKS=(
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

TEST17_TASKS=(
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

RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/c6prime_c1redux_2026-05-01"
mkdir -p "$RESULTS_ROOT/_logs"
EXP_ALL="/data/shared/geophysics_agent_data/data/eval/experiments"
EXP_TEST17="/data/shared/geophysics_agent_data/data/eval/experiments_test36_template"
GT_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_gt"

c6prime_test17() {
  local SEED="$1"
  local RUN="c6prime_test17_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  echo "[*] $RUN -> $LOG"
  GEOS_HOOK_XMLLINT=1 python3 scripts/run_experiment.py \
    --run "$RUN" --agents abl_c6_xmllint_hook \
    --workers 5 --timeout 1500 --strip-baked-primer \
    --geos-primer-path plugin/GEOS_PRIMER_absolute_min.md \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir "$EXP_TEST17" --ground-truth-dir "$GT_DIR" \
    --include "${TEST17_TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT" \
    --claude-model deepseek-v4-flash \
    >> "$LOG" 2>&1
  echo "[*] $RUN rc=$?"
}

c6prime_icl() {
  local SEED="$1"
  local RUN="c6prime_icl_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  echo "[*] $RUN -> $LOG"
  GEOS_HOOK_XMLLINT=1 python3 scripts/run_experiment.py \
    --run "$RUN" --agents abl_c6_xmllint_hook \
    --workers 5 --timeout 1500 --strip-baked-primer \
    --geos-primer-path plugin/GEOS_PRIMER_absolute_min.md \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir "$EXP_ALL" --ground-truth-dir "$GT_DIR" \
    --include "${ICL_TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT" \
    --claude-model deepseek-v4-flash \
    >> "$LOG" 2>&1
  echo "[*] $RUN rc=$?"
}

c1redux_test17() {
  local SEED="$1"
  local RUN="c1redux_test17_s${SEED}"
  local LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  echo "[*] $RUN -> $LOG"
  python3 scripts/run_experiment.py \
    --run "$RUN" --agents claude_code_no_plugin_minprimer \
    --workers 5 --timeout 1500 --strip-baked-primer \
    --geos-primer-path plugin/GEOS_PRIMER_minimal_vanilla.md \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir "$EXP_TEST17" --ground-truth-dir "$GT_DIR" \
    --include "${TEST17_TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT" \
    --claude-model deepseek-v4-flash \
    >> "$LOG" 2>&1
  echo "[*] $RUN rc=$?"
}

echo "=== START at $(date -u +%FT%TZ) — 9 seeds across 3 cells ==="
for SEED in 1 2 3; do
  c6prime_test17 "$SEED" &
  c6prime_icl    "$SEED" &
  c1redux_test17 "$SEED" &
done
wait
echo "=== DONE at $(date -u +%FT%TZ) ==="

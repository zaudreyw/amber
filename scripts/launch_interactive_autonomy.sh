#!/usr/bin/env bash
# Launcher for the interactive-autonomy + difficulty-ramp study.
# See docs/2026-05-03_interactive-autonomy-design.md.
#
# Usage:
#   scripts/launch_interactive_autonomy.sh <mode> <difficulty> [--smoke]
#     mode       : modeA (non-interactive) | modeB (interactive)
#     difficulty : medium | hard
#     --smoke    : optional; runs a single task (ExampleMandel)
#
# Each invocation runs ALL 8 tasks (or 1 with --smoke) on:
#   - ia_{F0,F4}_noninteractive   when mode = modeA
#   - ia_{F0,F4}_interactive      when mode = modeB
# Single seed by default. Override with $SEED.

set -euo pipefail
cd "$(dirname "$0")/.."
source .env

MODE="${1:?mode (modeA|modeB) required}"
DIFFICULTY="${2:?difficulty (medium|hard) required}"
SMOKE_FLAG="${3:-}"

case "$MODE" in
  modeA)   AGENTS=(ia_F0_noninteractive ia_F4_noninteractive) ;;
  modeB)   AGENTS=(ia_F0_interactive    ia_F4_interactive)    ;;
  modeBv1) AGENTS=(ia_F0_interactive_v1 ia_F4_interactive_v1) ;;
  *) echo "bad mode: $MODE" >&2; exit 2 ;;
esac

case "$DIFFICULTY" in
  medium|hard) ;;
  *) echo "bad difficulty: $DIFFICULTY" >&2; exit 2 ;;
esac

REPO_ROOT="$(pwd)"
EXP_ROOT="${REPO_ROOT}/data/eval/experiments_relaxed_${DIFFICULTY}"
SUPERVISOR_SPEC_DIR="/data/shared/geophysics_agent_data/data/eval/experiments_test36_template"

ALL_TASKS=(
  ExampleMandel
  ExampleDPWellbore
  ExampleEDPWellbore
  ExampleIsothermalLeakyWell
  ExampleThermalLeakyWell
  TutorialPoroelasticity
  TutorialSneddon
  ExampleThermoporoelasticConsolidation
)
if [ "$SMOKE_FLAG" = "--smoke" ]; then
  TASKS=(ExampleMandel)
else
  TASKS=("${ALL_TASKS[@]}")
fi

SEED="${SEED:-1}"

# DSv4-flash via DeepSeek-anthropic-compatible endpoint, matching AUTOCAMP.
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

# Match F4 baseline harness: strip baked AGENTS.md primer, use the
# `method` primer (the AUTOCAMP Phase 2 winner), enable xmllint env.
PRIMER="plugin/GEOS_PRIMER_method.md"
export GEOS_HOOK_XMLLINT=1   # only matters for cells with stop_hook_enabled

RESULTS_ROOT="${REPO_ROOT}/data/eval/interactive_autonomy_2026-05-03/${MODE}_${DIFFICULTY}"
mkdir -p "$RESULTS_ROOT/_logs"

SUPERVISOR_FLAG=()
if [ "$MODE" = "modeB" ] || [ "$MODE" = "modeBv1" ]; then
  SUPERVISOR_FLAG=(--supervisor-spec-dir "$SUPERVISOR_SPEC_DIR")
fi

for AGENT in "${AGENTS[@]}"; do
  RUN="${AGENT}_${DIFFICULTY}_s${SEED}"
  LOG="$RESULTS_ROOT/_logs/${RUN}.log"
  echo "=== launching $RUN ==="
  python3 scripts/run_experiment.py \
    --run "$RUN" \
    --agents "$AGENT" \
    --workers 4 --timeout 1500 \
    --strip-baked-primer \
    --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir "$EXP_ROOT" \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include "${TASKS[@]}" \
    --results-root-dir "$RESULTS_ROOT" \
    --claude-model deepseek-v4-flash \
    "${SUPERVISOR_FLAG[@]}" \
    > "$LOG" 2>&1 || {
      echo "  FAILED — see $LOG"
      tail -20 "$LOG"
      exit 1
    }
  echo "  done -> $LOG"
done

echo "=== $MODE @ $DIFFICULTY complete ==="

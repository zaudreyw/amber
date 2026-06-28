#!/usr/bin/env bash
# Run one round of the self-evolving agent on a slice of test tasks.
# Uses plugin_evolving/v{N}/ as the plugin dir; primer comes from the
# same dir's PRIMER.md.
#
# Usage:
#   bash scripts/self_evolving/run_round.sh <round> <task1> [<task2> ...]
#
# Example:
#   bash scripts/self_evolving/run_round.sh 0 ExampleMandel TutorialSneddon ...
set -euo pipefail
cd /home/matt/sci/repo3
source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
export GEOS_HOOK_XMLLINT=1

ROUND="${1:?round required}"
shift
TASKS=("$@")
[ "${#TASKS[@]}" -gt 0 ] || { echo "no tasks supplied"; exit 1; }

PLUGIN_DIR="plugin_evolving/v${ROUND}"
[ -d "$PLUGIN_DIR" ] || { echo "missing plugin dir: $PLUGIN_DIR"; exit 1; }

PRIMER_PATH="${PLUGIN_DIR}/PRIMER.md"
[ -f "$PRIMER_PATH" ] || { echo "missing primer: $PRIMER_PATH"; exit 1; }

# Memory cheatsheet: load from plugin_v{N}/memory/cheatsheet.md if present
CHEATSHEET_DIR="$PLUGIN_DIR/memory"
CHEATSHEET_PATH="$CHEATSHEET_DIR/cheatsheet.md"
CHEATSHEET_ARG=""
if [ -f "$CHEATSHEET_PATH" ]; then
  CHEATSHEET_ARG="--geos-primer-path $PRIMER_PATH"  # primer is already passed
  # Note: we don't have a CLI flag for cheatsheet override; the agent dict
  # would need to be customized per round. Workaround: prepend cheatsheet
  # content into PRIMER.md at run time. (Done below.)
fi

# Workaround for cheatsheet: temporarily concatenate cheatsheet into a
# round-effective primer file. We don't modify the original PRIMER.md
# (the agent's authored content); instead emit a temp file.
EFFECTIVE_PRIMER="$PLUGIN_DIR/_runtime_primer.md"
cp "$PRIMER_PATH" "$EFFECTIVE_PRIMER"
if [ -f "$CHEATSHEET_PATH" ]; then
  echo "" >> "$EFFECTIVE_PRIMER"
  echo "---" >> "$EFFECTIVE_PRIMER"
  echo "" >> "$EFFECTIVE_PRIMER"
  cat "$CHEATSHEET_PATH" >> "$EFFECTIVE_PRIMER"
fi

RUN_NAME="se_round${ROUND}_s1"
RESULTS_ROOT="/data/shared/geophysics_agent_data/data/eval/self_evolving_2026-04-30"
mkdir -p "$RESULTS_ROOT/_logs"
LOG_FILE="$RESULTS_ROOT/_logs/${RUN_NAME}.log"

echo "[*] SE round=$ROUND tasks=${#TASKS[@]} plugin=$PLUGIN_DIR" | tee "$LOG_FILE"

python3 scripts/run_experiment.py \
  --run "$RUN_NAME" \
  --agents abl_se_round \
  --workers 4 \
  --timeout 1500 \
  --strip-baked-primer \
  --geos-primer-path "$EFFECTIVE_PRIMER" \
  --plugin-dir "$PLUGIN_DIR" \
  --tmp-geos-parent /data/matt/geos_eval_tmp \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --include "${TASKS[@]}" \
  --results-root-dir "$RESULTS_ROOT" \
  --claude-model deepseek-v4-flash \
  >> "$LOG_FILE" 2>&1

echo "[*] Round $ROUND done at $(date -u +%FT%TZ)" >> "$LOG_FILE"
rm -f "$EFFECTIVE_PRIMER"

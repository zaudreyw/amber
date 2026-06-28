#!/usr/bin/env bash
# Full self-evolving experiment: 3 rounds of (run 6 tasks → reflect),
# starting from plugin v0 (blank scaffolding).
#
# Tasks split into thirds:
#   Round 0: tasks 1-6  (with v0)
#   Round 1: tasks 7-12 (with v1 = reflection on round 0)
#   Round 2: tasks 13-17 (with v2 = reflection on round 1)
#   (Optional) round 3: re-run all 17 with v3 = reflection on round 2
#
# Plus: a control run of all 17 with v0 (for blank-baseline comparison)
# already provided by C0 from Task 0 (mean 0.865 ± 0.067).
set -uo pipefail
cd /home/matt/sci/repo3

# 17 tasks deterministically split into thirds
TASKS_R0=(AdvancedExampleCasedContactThermoElasticWellbore AdvancedExampleDeviatedElasticWellbore AdvancedExampleDruckerPrager AdvancedExampleExtendedDruckerPrager AdvancedExampleModifiedCamClay AdvancedExampleViscoDruckerPrager)
TASKS_R1=(buckleyLeverettProblem ExampleDPWellbore ExampleEDPWellbore ExampleIsothermalLeakyWell ExampleMandel ExampleThermalLeakyWell)
TASKS_R2=(ExampleThermoporoelasticConsolidation kgdExperimentValidation pknViscosityDominated TutorialPoroelasticity TutorialSneddon)

echo "=== START SE evolution at $(date -u +%FT%TZ) ==="

# Round 0
echo "--- Round 0 (v0 plugin, 6 tasks) ---"
bash scripts/self_evolving/run_round.sh 0 "${TASKS_R0[@]}"

# Reflect 0 → 1
echo "--- Reflect v0 → v1 ---"
python3 scripts/self_evolving/reflect.py --from-version 0

# Round 1
echo "--- Round 1 (v1 plugin, 6 tasks) ---"
bash scripts/self_evolving/run_round.sh 1 "${TASKS_R1[@]}"

# Reflect 1 → 2
echo "--- Reflect v1 → v2 ---"
python3 scripts/self_evolving/reflect.py --from-version 1

# Round 2
echo "--- Round 2 (v2 plugin, 5 tasks) ---"
bash scripts/self_evolving/run_round.sh 2 "${TASKS_R2[@]}"

# Reflect 2 → 3 (optional final reflection for analysis)
echo "--- Reflect v2 → v3 (final) ---"
python3 scripts/self_evolving/reflect.py --from-version 2

# Round 3: re-run round 0's 6 tasks with v3, to compare v3 vs v0 head-to-head
echo "--- Round 3 (v3 plugin re-running round 0's 6 tasks) ---"
bash scripts/self_evolving/run_round.sh 3 "${TASKS_R0[@]}"

echo "=== DONE SE evolution at $(date -u +%FT%TZ) ==="

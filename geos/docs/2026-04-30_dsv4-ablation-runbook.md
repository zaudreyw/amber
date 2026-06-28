# DSv4 ablation runbook — exact commands used

*2026-04-30 — companion to `docs/2026-04-30_dsv4-ablation-final.md`.*

This file lists every command actually run for the DSv4 ablation
campaign, grouped by phase. Re-running these in order would reproduce
the campaign end-to-end.

## Where the configs live (per-run, post-hoc)

For every task that ran, the resolved config is also recorded in:

```
<results-root>/<agent>/<run>/<task>/eval_metadata.json
```

Example (vanilla DSv4):
- `agent`, `claude_model` (e.g., `deepseek-v4-flash`),
- `anthropic_base_url` (e.g., `https://api.deepseek.com/anthropic`),
- `geos_primer_path`, `plugin_enabled`, `requires_rag`,
- `mcp_config_path`, `vector_db_dir`, `filtered_geos_copy`,
- `blocked_gt_xml_filenames` (per-task), `blocked_rst_relpaths`.

Per-(cond,seed) logs at:
```
/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/<run_name>.log
```
Each log echoes the `run_experiment.py` resolved configuration block at
the top.

## Environment (every run)

```bash
cd /home/matt/sci/repo3
source .env                                          # loads DEEPSEEK_API_KEY
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
```

The `--strip-baked-primer` flag is required on every C0-C5 run because
AGENTS.md still has a `# GEOS Primer` block baked in; without the flag
the external `--geos-primer-path` is silently dropped.

Output dir uses the shared 140 TB volume (43 TB free):
```
--results-root-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29
```

## Phase 0 — Smoketest (1 task per cell)

Before launching the full matrix. TutorialSneddon picked because it's
the most demanding multi-variant task.

Wrapper command (parallel across 4 cells, single seed, single task):

```bash
mkdir -p /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs
cd /home/matt/sci/repo3
source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
for c in c0 c2 c3 c4; do
  case "$c" in
    c0) AGENT="abl_c0_true_vanilla";        PRIMER="plugin/GEOS_PRIMER_absolute_min.md" ;;
    c2) AGENT="abl_c2_min_sr_no_rag";       PRIMER="plugin/GEOS_PRIMER_minimal_vanilla.md" ;;
    c3) AGENT="abl_c3_min_rag_no_sr";       PRIMER="plugin/GEOS_PRIMER_minimal.md" ;;
    c4) AGENT="abl_c4_min_rag_sr";          PRIMER="plugin/GEOS_PRIMER_minimal.md" ;;
  esac
  python3 scripts/run_experiment.py \
    --run "smoke_${c}" --agents "$AGENT" --workers 1 --timeout 900 \
    --strip-baked-primer --geos-primer-path "$PRIMER" \
    --tmp-geos-parent /data/matt/geos_eval_tmp \
    --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --include TutorialSneddon \
    --results-root-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29 \
    --claude-model deepseek-v4-flash \
    > /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/smoke_${c}.log 2>&1 &
done
wait
```

## Phase 1 — Full matrix C0/C2/C3/C4 × 3 seeds

Driven by:
```
scripts/launch_dsv4_full_matrix.sh
```

Which loops Group A (C0+C2 in parallel, 3 seeds sequential each) then
Group B (C3+C4 same shape). The per-(cond,seed) launcher is:

```
scripts/launch_dsv4_ablation.sh <c0|c2|c3|c4|c5> <1|2|3>
```

Effective command for each launch (auto-built by the launcher script):

```bash
cd /home/matt/sci/repo3
source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

# C0 (true vanilla)
python3 scripts/run_experiment.py \
  --run "c0_dsv4_s${SEED}" \
  --agents abl_c0_true_vanilla \
  --workers 4 --timeout 1200 \
  --strip-baked-primer \
  --geos-primer-path plugin/GEOS_PRIMER_absolute_min.md \
  --tmp-geos-parent /data/matt/geos_eval_tmp \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --include AdvancedExampleCasedContactThermoElasticWellbore AdvancedExampleDeviatedElasticWellbore AdvancedExampleDruckerPrager AdvancedExampleExtendedDruckerPrager AdvancedExampleModifiedCamClay AdvancedExampleViscoDruckerPrager buckleyLeverettProblem ExampleDPWellbore ExampleEDPWellbore ExampleIsothermalLeakyWell ExampleMandel ExampleThermalLeakyWell ExampleThermoporoelasticConsolidation kgdExperimentValidation pknViscosityDominated TutorialPoroelasticity TutorialSneddon \
  --results-root-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29 \
  --claude-model deepseek-v4-flash

# C2 (min primer + plugin loaded, RAG off, SR settings on)
python3 scripts/run_experiment.py \
  --run "c2_dsv4_s${SEED}" \
  --agents abl_c2_min_sr_no_rag \
  --workers 4 --timeout 1200 \
  --strip-baked-primer \
  --geos-primer-path plugin/GEOS_PRIMER_minimal_vanilla.md \
  --tmp-geos-parent /data/matt/geos_eval_tmp \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --include <17-task list above> \
  --results-root-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29 \
  --claude-model deepseek-v4-flash

# C3 (min primer + RAG, no SR)
python3 scripts/run_experiment.py \
  --run "c3_dsv4_s${SEED}" \
  --agents abl_c3_min_rag_no_sr \
  --workers 4 --timeout 1200 \
  --strip-baked-primer \
  --geos-primer-path plugin/GEOS_PRIMER_minimal.md \
  ...

# C4 (min primer + RAG + SR)
python3 scripts/run_experiment.py \
  --run "c4_dsv4_s${SEED}" \
  --agents abl_c4_min_rag_sr \
  --workers 4 --timeout 1200 \
  --strip-baked-primer \
  --geos-primer-path plugin/GEOS_PRIMER_minimal.md \
  ...
```

Single end-to-end fire of the full matrix:
```bash
cd /home/matt/sci/repo3
nohup bash scripts/launch_dsv4_full_matrix.sh > /tmp/matrix.log 2>&1 &
```

## Phase 2 — Harvest 18 train tasks under C2 setup

Used as input to the memory-distillation pipeline.

```bash
cd /home/matt/sci/repo3
source .env
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

python3 scripts/run_experiment.py \
  --run "harvest_c2_dsv4_s1" \
  --agents abl_c2_min_sr_no_rag \
  --workers 6 --timeout 1500 \
  --strip-baked-primer \
  --geos-primer-path plugin/GEOS_PRIMER_minimal_vanilla.md \
  --extend-blocklist-with-test \
  --tmp-geos-parent /data/matt/geos_eval_tmp \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --include AdvancedExampleViscoModifiedCamClay kgdToughnessDominated triaxialDriverExample kgdViscosityDominated pennyFracViscosityDominated AdvancedExampleCasedElasticWellboreImperfectInterfaces ExampleKirschWellbore pennyFracToughnessDominated AdvancedExampleCasedElasticWellbore AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity TutorialDeadOilBottomLayersSPE10 TutorialDeadOilEgg relaxationTest AdvancedExampleDeviatedPoroElasticWellbore TutorialCO2FieldCase faultVerification ExampleTFrac AdvancedExampleWellboreNonLinearThermalDiffusionTemperatureDependentSinglePhaseThermalConductivity \
  --results-root-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29 \
  --claude-model deepseek-v4-flash \
  > /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_logs/harvest_c2_dsv4_s1.log 2>&1
```

`--extend-blocklist-with-test` is the hygiene flag: every train task's
file blocklist is augmented with the union of all 17 test-task GT
basenames so harvested trajectories cannot leak test-task content.

The 18 train tasks come from `misc/memory_split.json["train"]`.

## Phase 3 — Score harvest, ground, distill

```bash
cd /home/matt/sci/repo3

# 3a. Score the harvest with batch_evaluate
mkdir -p /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results/harvest_c2_dsv4_s1/abl_c2_min_sr_no_rag
uv run python scripts/eval/batch_evaluate.py \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/abl_c2_min_sr_no_rag/harvest_c2_dsv4_s1 \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --results-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results/harvest_c2_dsv4_s1/abl_c2_min_sr_no_rag \
  --output /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results/harvest_c2_dsv4_s1/abl_c2_min_sr_no_rag/_summary.json

# 3b. Symlink to the path the grounder expects
ln -sfn /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results/harvest_c2_dsv4_s1 \
        /data/shared/geophysics_agent_data/data/eval/results/harvest_c2_dsv4_s1

# 3c. Run the trajectory grounder against the DSv4 harvest
python3 scripts/memory/trajectory_grounder.py \
  --run-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/abl_c2_min_sr_no_rag/harvest_c2_dsv4_s1 \
  --split misc/memory_split.json \
  --out misc/memory_artifacts/grounded_train_reports_dsv4.json
# Output: 18 reports, all classified failure_mode='success' (median treesim 0.92).

# 3d. Distill an M1-u memory primer from the DSv4 grounded reports
echo "[]" > /tmp/empty_extra.json
export OPENROUTER_API_KEY=$(grep ^OPENROUTER_API_KEY .env | cut -d= -f2)
python3 scripts/memory/distiller.py \
  --variant M1-u \
  --reports misc/memory_artifacts/grounded_train_reports_dsv4.json \
  --extra-reports /tmp/empty_extra.json
# Output: misc/memory_artifacts/M1-u/artifact.md (835 tokens, hygiene PASS)

# 3e. Snapshot the new primer to a DSv4-specific filename
cp misc/memory_artifacts/M1-u/artifact.md plugin/memory_primer_dsv4_m1u.md
git checkout misc/memory_artifacts/M1-u/artifact.md   # restore the original minimax M1-u
```

Caveat: the distilled primer contains some plausible-sounding GEOS
hallucinations (e.g., `SolidMechanicsLagrangianSSLE`,
`BiotLinearPoromechanics`, `FractureManager`) — known M1-u risk
because all 18 train trajectories were classified as "success" so
there were no failure cases for the distiller to mine.

## Phase 4 — Run C5 (memory on top of C2)

C5 was launched via the same launcher script (case `c5` added):

```bash
cd /home/matt/sci/repo3
for s in 1 2 3; do
  bash scripts/launch_dsv4_ablation.sh c5 $s &
done
wait
```

Effective command:
```bash
python3 scripts/run_experiment.py \
  --run "c5_dsv4_s${SEED}" \
  --agents abl_c5_dsv4_mem \
  --workers 4 --timeout 1200 \
  --strip-baked-primer \
  --geos-primer-path plugin/GEOS_PRIMER_minimal_vanilla.md \
  --tmp-geos-parent /data/matt/geos_eval_tmp \
  --experiments-dir /data/shared/geophysics_agent_data/data/eval/experiments_test36_template \
  --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
  --include <17-task list above> \
  --results-root-dir /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29 \
  --claude-model deepseek-v4-flash
```

The `abl_c5_dsv4_mem` agent definition (`src/runner/agents.py`) carries
`cheatsheet_path: plugin/memory_primer_dsv4_m1u.md`, so the runner
prepends the memory primer to the system prompt automatically. The
`--geos-primer-path` is still the C2 minimal-vanilla primer — the
cheatsheet is delivered separately.

## Phase 5 — Score everything

```bash
cd /home/matt/sci/repo3
bash scripts/score_all_dsv4_ablation.sh
```

Internally this loops over every `(cond, seed)` that has 17/17 status
files complete, calls `batch_evaluate.py` against the GT, and writes a
`_summary.json` per run. Idempotent (re-runs re-score).

Single-(cond,seed) version: `scripts/score_dsv4_ablation.sh <c> <s>`.

## Phase 6 — Cross-condition analyzers

```bash
cd /home/matt/sci/repo3

# C2 vs C5 (does memory help on best harness?)
python3 scripts/analysis/ablation_analyzer.py \
  --cond-a-name "C2_no_mem" --cond-a-agent "abl_c2_min_sr_no_rag" \
  --cond-a-runs /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/abl_c2_min_sr_no_rag/c2_dsv4_s{1,2,3} \
  --cond-a-eval-root /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results \
  --cond-b-name "C5_dsv4_mem" --cond-b-agent "abl_c5_dsv4_mem" \
  --cond-b-runs /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/abl_c5_dsv4_mem/c5_dsv4_s{1,2,3} \
  --cond-b-eval-root /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results \
  --threshold 0.10 --focus both \
  --out docs/ablation_C2_vs_C5.md

# Other pairs follow the same shape — substitute cond names/agents/runs.
# All produced reports are committed at docs/ablation_<A>_vs_<B>.md
# with JSON sidecars at docs/ablation_<A>_vs_<B>.json.
```

The five paired analyses produced for this campaign:

| Pair | Question | Δ | Doc |
|---|---|---:|---|
| C1 → C0 | Strip workflow primer help? | +0.194 | `docs/ablation_C1_vs_C0.md` |
| C0 → C2 | Add SR/settings help? | +0.049 | `docs/ablation_C0_vs_C2.md` |
| C0 → C3 | Add RAG (no SR) help? | −0.018 | `docs/ablation_C0_vs_C3.md` |
| C2 → C4 | Add RAG to SR-baseline help? | −0.039 | `docs/ablation_C2_vs_C4.md` |
| C3 → C4 | Add SR to RAG-baseline help? | +0.015 | `docs/ablation_C3_vs_C4.md` |
| C2 → C5 | Add memory to C2 help? | −0.001 | `docs/ablation_C2_vs_C5.md` |

## Quick reproducer for the whole campaign

```bash
cd /home/matt/sci/repo3

# 1. Phase 1 — main matrix (~3.5h)
nohup bash scripts/launch_dsv4_full_matrix.sh > /tmp/matrix.log 2>&1 &
wait

# 2. Phase 2 — harvest (~30 min)
# ... see Phase 2 command above

# 3. Phase 3 — score + ground + distill (~5 min)
# ... see Phase 3 commands above

# 4. Phase 4 — C5 (~25 min wall, 3 seeds in parallel)
for s in 1 2 3; do bash scripts/launch_dsv4_ablation.sh c5 $s & done; wait

# 5. Phase 5 — score everything
bash scripts/score_all_dsv4_ablation.sh

# 6. Phase 6 — analyzer pairs
# ... see Phase 6 commands above
```

Total wall: ~4-4.5h. Real DSv4 cost: ~$19. Output: ~25 GB on the shared
volume.

## Files committed by this campaign

- **Launchers**: `scripts/launch_dsv4_ablation.sh`, `scripts/launch_dsv4_full_matrix.sh`
- **Scoring**: `scripts/score_dsv4_ablation.sh`, `scripts/score_all_dsv4_ablation.sh`
- **Analyzer**: `scripts/analysis/{tool_use_differ,treesim_xmllint_analyzer,ablation_analyzer,per_task_matrix}.py`
- **Primers**: `plugin/GEOS_PRIMER_absolute_min.md`, `plugin/memory_primer_dsv4_m1u.md`
- **Agent definitions**: `src/runner/agents.py` (5 new variants `abl_c0/c2/c3/c4/c5_*`)
- **Runner change**: `src/runner/{prompts/__init__.py,claude_settings.py,orchestrator.py}` — new `rag_enabled` flag decoupled from `plugin_enabled`
- **Per-pair reports**: `docs/ablation_*.md` + JSON sidecars
- **Writeup**: `docs/2026-04-30_dsv4-ablation-final.md`
- **Design doc**: `docs/2026-04-29_ablation-analyzer-design.md`

# File-access summary (406 tasks)
- Eval root: `/home/matt/sci/repo3/data/eval`
- Skipped tasks (no events.jsonl or parse error): 0
- Agent keys analysed: claude_code_no_plugin, claude_code_repo3_plugin, claude_code_repo3_plugin_m1u, claude_code_repo3_plugin_nohook

## Q1. Have any non-sphinx .rst files been read?

**Yes** — 20 distinct non-sphinx rst files were referenced, 33 total reads. Top 10:

| file_path | n_reads | first_seen_in (agent / run) |
|---|---:|---|
| `/geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst` | 4 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst` | 4 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst` | 3 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst` | 3 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst` | 2 | claude_code_no_plugin / noplug_mm_v2 |
| `/geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst` | 2 | claude_code_no_plugin / noplug_mm_v2_s2 |
| `/geos_lib/src/coreComponents/functions/docs/FunctionManager.rst` | 2 | claude_code_no_plugin / noplug_mm_v2 |
| `/geos_lib/src/coreComponents/constitutive/docs/BlackOilFluid.rst` | 1 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/TemperatureDependentSolidVolumetricHeatCapacity.rst` | 1 | claude_code_no_plugin / ablation_deepseek_v2 |
| `/geos_lib/src/coreComponents/constitutive/docs/FluidModels.rst` | 1 | claude_code_no_plugin / mm_noplug_run1 |

## Q2. Has xmllint ever been invoked?

**Yes.** 51 total invocations across 50 task-runs. Distribution by agent:

| agent | n_xmllint |
|---|---:|
| claude_code_no_plugin | 31 |
| claude_code_repo3_plugin | 13 |
| claude_code_repo3_plugin_m1u | 4 |
| claude_code_repo3_plugin_nohook | 3 |

## Top 15 most-read sphinx .rst files

| file_path | n_reads |
|---|---:|
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst` | 14 |
| `/geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst` | 13 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst` | 10 |
| `/geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst` | 8 |
| `/geos_lib/src/docs/sphinx/basicExamples/poromechanics/Example.rst` | 7 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst` | 7 |
| `/geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst` | 7 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst` | 6 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedElasticWellbore/Example.rst` | 6 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst` | 5 |
| `/geos_lib/src/docs/sphinx/developerGuide/KeyComponents/XML.rst` | 5 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedThermoElasticWellbore/Example.rst` | 5 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/Index.rst` | 5 |
| `/geos_lib/src/docs/sphinx/basicExamples/co2Injection/Example.rst` | 4 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/thermoPoromechanics/thermalConsolidation/Example.rst` | 4 |

## Top 15 most-read .xml example files (under inputFiles/)

| file_path | n_reads |
|---|---:|
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml` | 63 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml` | 45 |
| `/geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml` | 40 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml` | 29 |
| `/geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml` | 25 |
| `/geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml` | 25 |
| `/geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml` | 24 |
| `/geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_base.xml` | 24 |
| `/geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml` | 24 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml` | 24 |
| `/geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml` | 21 |
| `/geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml` | 20 |
| `/geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_base.xml` | 20 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml` | 19 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml` | 19 |

## Per-agent rollup (sums across runs/tasks)

| agent | n_tasks | rst_sphinx | rst_nonsphinx | xml_input | xml_workspace | xmllint | unique_files |
|---|---:|---:|---:|---:|---:|---:|---:|
| claude_code_no_plugin | 208 | 143 | 33 | 1183 | 485 | 31 | 1793 |
| claude_code_repo3_plugin | 117 | 27 | 0 | 281 | 284 | 13 | 563 |
| claude_code_repo3_plugin_m1u | 51 | 1 | 0 | 120 | 114 | 4 | 185 |
| claude_code_repo3_plugin_nohook | 30 | 0 | 0 | 23 | 79 | 3 | 76 |

## Output files

- `scripts/analysis/out_4cond/file_access/file_access_per_run.csv`
- `scripts/analysis/out_4cond/file_access/file_access_per_task.csv`
- `scripts/analysis/out_4cond/file_access/file_access_summary.csv` (per-run rollup)
- `scripts/analysis/out_4cond/file_access/file_access_glob_grep.csv`

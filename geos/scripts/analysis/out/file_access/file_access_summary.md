# File-access summary (908 tasks)
- Eval root: `/home/matt/sci/repo3/data/eval`
- Skipped tasks (no events.jsonl or parse error): 0
- Agent keys analysed: claude_code_no_plugin, claude_code_repo3_plugin, claude_code_repo3_plugin_gmem, claude_code_repo3_plugin_gmemsilent, claude_code_repo3_plugin_gmemsilent_nohook, claude_code_repo3_plugin_m1g, claude_code_repo3_plugin_m1u, claude_code_repo3_plugin_m3g, claude_code_repo3_plugin_m4g, claude_code_repo3_plugin_m4u, claude_code_repo3_plugin_m_placebo, claude_code_repo3_plugin_mem, claude_code_repo3_plugin_memshort, claude_code_repo3_plugin_memws, claude_code_repo3_plugin_nohook, claude_code_repo3_plugin_noop, claude_code_repo3_plugin_noop_nohook, claude_code_repo3_plugin_tree

## Q1. Have any non-sphinx .rst files been read?

**Yes** — 21 distinct non-sphinx rst files were referenced, 36 total reads. Top 10:

| file_path | n_reads | first_seen_in (agent / run) |
|---|---:|---|
| `/geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst` | 4 | claude_code_repo3_plugin_gmem / gmem_v2_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst` | 4 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst` | 4 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst` | 3 | claude_code_no_plugin / mm_noplug_run1 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/SolidModels.rst` | 2 | claude_code_repo3_plugin_gmem / gmem_v2_run1 |
| `/geos_lib/src/coreComponents/functions/docs/FunctionManager.rst` | 2 | claude_code_no_plugin / noplug_mm_v2 |
| `/geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst` | 2 | claude_code_no_plugin / noplug_mm_v2 |
| `/geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst` | 2 | claude_code_no_plugin / noplug_mm_v2_s2 |
| `/geos_lib/src/coreComponents/constitutive/docs/TemperatureDependentSolidVolumetricHeatCapacity.rst` | 1 | claude_code_no_plugin / ablation_deepseek_v2 |
| `/geos_lib/src/coreComponents/constitutive/docs/BlackOilFluid.rst` | 1 | claude_code_no_plugin / mm_noplug_run1 |

## Q2. Has xmllint ever been invoked?

**Yes.** 91 total invocations across 87 task-runs. Distribution by agent:

| agent | n_xmllint |
|---|---:|
| claude_code_no_plugin | 31 |
| claude_code_repo3_plugin | 13 |
| claude_code_repo3_plugin_m1g | 9 |
| claude_code_repo3_plugin_m4u | 8 |
| claude_code_repo3_plugin_gmem | 5 |
| claude_code_repo3_plugin_m1u | 4 |
| claude_code_repo3_plugin_gmemsilent | 3 |
| claude_code_repo3_plugin_tree | 3 |
| claude_code_repo3_plugin_nohook | 3 |
| claude_code_repo3_plugin_memws | 3 |
| claude_code_repo3_plugin_memshort | 3 |
| claude_code_repo3_plugin_gmemsilent_nohook | 2 |
| claude_code_repo3_plugin_m3g | 2 |
| claude_code_repo3_plugin_mem | 1 |
| claude_code_repo3_plugin_m_placebo | 1 |

## Top 15 most-read sphinx .rst files

| file_path | n_reads |
|---|---:|
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst` | 29 |
| `/geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst` | 26 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst` | 22 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst` | 15 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst` | 14 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst` | 11 |
| `/geos_lib/src/docs/sphinx/basicExamples/poromechanics/Example.rst` | 10 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/thermalLeakyWell/Example.rst` | 10 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalLeakyWell/Example.rst` | 8 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedElasticWellbore/Example.rst` | 8 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedContactElasticWellbore/Example.rst` | 8 |
| `/geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst` | 8 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedThermoElasticWellbore/Example.rst` | 8 |
| `/geos_lib/src/docs/sphinx/advancedExamples/validationStudies/thermoPoromechanics/thermalConsolidation/Example.rst` | 8 |
| `/geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst` | 7 |

## Top 15 most-read .xml example files (under inputFiles/)

| file_path | n_reads |
|---|---:|
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml` | 141 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml` | 103 |
| `/geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml` | 66 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml` | 53 |
| `/geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml` | 49 |
| `/geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml` | 49 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml` | 47 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml` | 45 |
| `/geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml` | 43 |
| `/geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml` | 41 |
| `/geos_lib/inputFiles/triaxialDriver/triaxialDriver_ModifiedCamClay.xml` | 40 |
| `/geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_base.xml` | 39 |
| `/geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_iterative.xml` | 36 |
| `/geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml` | 33 |
| `/geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml` | 33 |

## Per-agent rollup (sums across runs/tasks)

| agent | n_tasks | rst_sphinx | rst_nonsphinx | xml_input | xml_workspace | xmllint | unique_files |
|---|---:|---:|---:|---:|---:|---:|---:|
| claude_code_no_plugin | 205 | 143 | 33 | 1169 | 485 | 31 | 1779 |
| claude_code_repo3_plugin | 117 | 27 | 0 | 281 | 284 | 13 | 563 |
| claude_code_repo3_plugin_gmemsilent | 87 | 18 | 0 | 227 | 202 | 3 | 400 |
| claude_code_repo3_plugin_m1g | 52 | 3 | 0 | 109 | 155 | 9 | 192 |
| claude_code_repo3_plugin_m3g | 52 | 0 | 0 | 2 | 28 | 2 | 26 |
| claude_code_repo3_plugin_m1u | 51 | 1 | 0 | 120 | 114 | 4 | 185 |
| claude_code_repo3_plugin_m4g | 51 | 1 | 0 | 37 | 57 | 0 | 101 |
| claude_code_repo3_plugin_m4u | 51 | 1 | 0 | 82 | 96 | 8 | 150 |
| claude_code_repo3_plugin_m_placebo | 51 | 0 | 0 | 17 | 99 | 1 | 123 |
| claude_code_repo3_plugin_gmemsilent_nohook | 34 | 6 | 0 | 56 | 73 | 2 | 119 |
| claude_code_repo3_plugin_gmem | 34 | 47 | 3 | 203 | 85 | 5 | 322 |
| claude_code_repo3_plugin_nohook | 30 | 0 | 0 | 23 | 79 | 3 | 76 |
| claude_code_repo3_plugin_memshort | 17 | 9 | 0 | 88 | 72 | 3 | 128 |
| claude_code_repo3_plugin_mem | 17 | 12 | 0 | 83 | 30 | 1 | 132 |
| claude_code_repo3_plugin_memws | 17 | 17 | 0 | 96 | 48 | 3 | 154 |
| claude_code_repo3_plugin_tree | 17 | 13 | 0 | 90 | 42 | 3 | 136 |
| claude_code_repo3_plugin_noop_nohook | 13 | 0 | 0 | 23 | 26 | 0 | 44 |
| claude_code_repo3_plugin_noop | 12 | 0 | 0 | 17 | 32 | 0 | 45 |

## Output files

- `/home/matt/sci/repo3/scripts/analysis/out/file_access/file_access_per_run.csv`
- `/home/matt/sci/repo3/scripts/analysis/out/file_access/file_access_per_task.csv`
- `/home/matt/sci/repo3/scripts/analysis/out/file_access/file_access_summary.csv` (per-run rollup)
- `/home/matt/sci/repo3/scripts/analysis/out/file_access/file_access_glob_grep.csv`

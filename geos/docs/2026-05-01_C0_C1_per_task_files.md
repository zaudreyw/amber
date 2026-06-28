# Per-task file lists — C0 vs C1 (companion to 2026-05-01_C0_abs_min_primer_behavior.md)

*2026-05-01 — full per-task list of XML and RST files read in C0
(`abl_c0_true_vanilla`, 3 seeds) vs C1 (`c1redux_test17_s1..s3`,
3 seeds). Counts are total reads across the three seeds; same
file counted once per `Read` tool call.*

## Caveats

- C1 trajectory data comes from **c1redux** (re-run on 2026-05-01),
  not the original C1 (April). Same primer file
  (`GEOS_PRIMER_minimal_vanilla.md`), same model (`deepseek-v4-flash`),
  same anti-leakage blocklist; trajectory should be representative
  but is not the literal trajectory that produced the cited C1
  scores.
- Reads of `/workspace/inputs/...` are the agent reading its own
  output back (verification reads); these are included.
- Sorted within each block by read count desc, then path asc.

---

### ExampleMandel  —  C1: 0.312, C0: 0.953, Δ: +0.641

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=15, total reads=37):**
```
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_sequential.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_prism6_base_hybrid.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_smoke_fim.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_prism6_benchmark.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_prism6_smoke.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_base_direct.xml
  3× /workspace/inputs/PoroElastic_Mandel_base.xml
  3× /workspace/inputs/PoroElastic_Mandel_benchmark_fim.xml
  3× /workspace/inputs/PoroElastic_Mandel_smoke_sequential.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_base_iterative.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_smoke.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_smoke.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_gravity.xml
```

**C0 XMLs read (unique=37, total reads=70):**
```
  6× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_base_direct.xml
  5× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_sequential.xml
  5× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_prism6_base_hybrid.xml
  5× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_smoke_fim.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_prism6_benchmark.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_prism6_smoke.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_base_iterative.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_benchmark.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_smoke.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_deadoil_3ph_baker_2d_base.xml
  2× /geos_lib/inputFiles/poromechanics/nonlinearAcceleration/validationCase/validationCase.xml
  2× /workspace/inputs/PoroElastic_Mandel_base.xml
  2× /workspace/inputs/PoroElastic_Mandel_benchmark_fim.xml
  2× /workspace/inputs/PoroElastic_Mandel_smoke_sequential.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_poroelastic_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/inducedSeismicity/SeismicityRate_poromechanics_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDelftEggWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_CarmanKozenyPermeability_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_gravity.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_hybridHexPrism_co2_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_co2_3d_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_base_stab.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_fim.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_fim_stab.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_sequential.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_sequential_stab.xml
  1× /geos_lib/inputFiles/poromechanics/impermeableFault_benchmark.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_sequential_solvers.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_solvers.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml
```

**C1 RSTs read (unique=1, total reads=1):**
```
  1× /geos_lib/src/docs/sphinx/basicExamples/poromechanics/Example.rst
```

**C0 RSTs read (unique=6, total reads=8):**
```
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/poromechanics/Index.rst
  2× /geos_lib/src/docs/sphinx/basicExamples/poromechanics/Example.rst
  1× /geos_lib/src/docs/sphinx/Publications.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/Index.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/Index.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step04/Tutorial.rst
```

### ExampleDPWellbore  —  C1: 0.487, C0: 0.998, Δ: +0.511

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=53, total reads=96):**
```
  5× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  5× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml
  5× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_smoke.xml
  5× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  3× /geos_lib/inputFiles/solidMechanics/OpenWellbore.xml
  3× /workspace/inputs/DruckerPragerWellbore_base.xml
  3× /workspace/inputs/DruckerPragerWellbore_benchmark.xml
  3× /workspace/inputs/DruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_benchmark.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_smoke.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/KirschProblem_base.xml
  2× /geos_lib/inputFiles/solidMechanics/KirschProblem_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/casedWellbore.xml
  2× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroDruckerPrager_consolidation_smoke.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroExtendedDruckerPrager_consolidation_smoke.xml
  2× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  2× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  1× /geos_lib/inputFiles/phaseField/PhaseFieldPoromechanics_Nucleation_Wellbore.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDelftEggWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDelftEggWellbore_smoke.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/poromechanics/PoroModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroModifiedCamClayWellbore_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/benchmarks/VerticalElasticWellbore.xml
  1× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom01.xml
  1× /geos_lib/inputFiles/wellboreECP/mechanics/ECP_Wellbore_probdef.xml
```

**C0 XMLs read (unique=32, total reads=70):**
```
  6× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  5× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml
  5× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  4× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  4× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_smoke.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  3× /geos_lib/inputFiles/solidMechanics/OpenWellbore.xml
  3× /geos_lib/inputFiles/solidMechanics/benchmarks/VerticalElasticWellbore.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_benchmark.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_base.xml
  2× /geos_lib/inputFiles/solidMechanics/casedWellbore.xml
  2× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroDruckerPrager_consolidation_smoke.xml
  2× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  2× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom01.xml
  1× /geos_lib/inputFiles/poromechanics/PoroVisoDruckerPrager_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_benchmark.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_base.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
```

**C1 RSTs read (unique=5, total reads=5):**
```
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/edpWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/kirschWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/mccWellbore/Example.rst
```

**C0 RSTs read (unique=16, total reads=22):**
```
  3× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  3× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/dpWellbore/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/edpWellbore/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/Plasticity.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/SolidModels.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst
  1× /geos_lib/src/coreComponents/events/docs/EventManager.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/OutputTasks.rst
  1× /geos_lib/src/coreComponents/mesh/docs/Mesh.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/docs/SolidMechanics.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/verticalPoroElastoPlasticWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step01/Tutorial.rst
```

### AdvancedExampleDruckerPrager  —  C1: 0.608, C0: 0.998, Δ: +0.390

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=13, total reads=36):**
```
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ModifiedCamClay.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  4× /workspace/inputs/triaxialDriver_base.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  3× /workspace/inputs/triaxialDriver_DruckerPrager.xml
  2× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  1× /geos_lib/inputFiles/thermalSinglePhaseFlowFractures/fractureMatrixThermalFlow_edfm_base.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClayVolumetric.xml
```

**C0 XMLs read (unique=36, total reads=88):**
```
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ModifiedCamClay.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  3× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  3× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_benchmark.xml
  3× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_smoke.xml
  3× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  3× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  3× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_smoke.xml
  3× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
  2× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_benchmark.xml
  2× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_benchmark.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase1.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropic.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
  2× /workspace/inputs/triaxialDriver_DruckerPrager.xml
  2× /workspace/inputs/triaxialDriver_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_benchmark.xml
  1× /geos_lib/inputFiles/poromechanics/PoroModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoModifiedCamClay_base.xml
  1× /geos_lib/inputFiles/singlePhaseFlow/FieldCaseTutorial3_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/beamBending_base.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase2.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathDryUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathWetUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropicPressureDependent.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClayVolumetric.xml
```

**C1 RSTs read (unique=14, total reads=22):**
```
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/PorousSolids.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/Plasticity.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/SolidModels.rst
  1× /geos_lib/src/coreComponents/constitutiveDrivers/docs/ConstitutiveDrivers.rst
  1× /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
```

**C0 RSTs read (unique=17, total reads=30):**
```
  4× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
  2× /geos_lib/src/coreComponents/constitutiveDrivers/docs/ConstitutiveDrivers.rst
  2× /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
  1× /geos_lib/src/docs/sphinx/developerGuide/Contributing/InputFiles.rst
  1× /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/XML.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step04/Tutorial.rst
```

### AdvancedExampleModifiedCamClay  —  C1: 0.570, C0: 0.941, Δ: +0.370

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=14, total reads=27):**
```
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  3× /workspace/inputs/triaxialDriver_ModifiedCamClay.xml
  3× /workspace/inputs/triaxialDriver_base.xml
  2× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  1× /geos_lib/inputFiles/poromechanics/PoroModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoModifiedCamClay_base.xml
  1× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
```

**C0 XMLs read (unique=37, total reads=87):**
```
  7× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  7× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  5× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  5× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  4× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClayVolumetric.xml
  3× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroModifiedCamClayWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoModifiedCamClay_base.xml
  2× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_benchmark.xml
  2× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_smoke.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroMCC_consolidation_smoke.xml
  2× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggUseLinear.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropic.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropicPressureDependent.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_base.xml
  1× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/plasticCubeReset.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroDruckerPrager_consolidation_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroExtendedDruckerPrager_consolidation_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase1.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase2.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathDryUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathWetUseLinear.xml
  1× /workspace/inputs/triaxialDriver_ModifiedCamClay.xml
  1× /workspace/inputs/triaxialDriver_base.xml
```

**C1 RSTs read (unique=11, total reads=14):**
```
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ExtendedDruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
```

**C0 RSTs read (unique=8, total reads=12):**
```
  2× /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
```

### TutorialPoroelasticity  —  C1: 0.365, C0: 0.636, Δ: +0.271

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=22, total reads=48):**
```
  6× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml
  5× /geos_lib/inputFiles/poromechanics/PoroElastic_gravity.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_CarmanKozenyPermeability_base.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_fim.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_smoke_fim.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_CarmanKozenyPermeability_fim_smoke.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_deadoil_3ph_baker_2d_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_fim.xml
  2× /geos_lib/inputFiles/poromechanics/faultPoroelastic_base.xml
  2× /geos_lib/inputFiles/poromechanics/impermeableFault_benchmark.xml
  2× /geos_lib/inputFiles/poromechanics/permeableFault_benchmark.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_smoke_base.xml
  1× /geos_lib/inputFiles/inducedSeismicity/SeismicityRate_poromechanics_base.xml
  1× /geos_lib/inputFiles/multiscalePreconditioner/singlePhasePoromechanics/cube_amg.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_base.xml
  1× /geos_lib/inputFiles/poromechanics/nonlinearAcceleration/validationCase/validationCase.xml
  1× /geos_lib/inputFiles/poromechanics/permeableFault_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_fim.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_smoke_fim.xml
```

**C0 XMLs read (unique=41, total reads=77):**
```
  7× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml
  5× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  5× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_base.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_CarmanKozenyPermeability_base.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_fim.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_smoke_fim.xml
  4× /geos_lib/inputFiles/poromechanics/PoroElastic_gravity.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_staircase_singlephase_3d_base.xml
  3× /geos_lib/inputFiles/poromechanicsFractures/singlePhasePoromechanics_FaultModel_base.xml
  2× /geos_lib/inputFiles/multiscalePreconditioner/singlePhasePoromechanics/cube_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_deadoil_3ph_baker_2d_base.xml
  2× /geos_lib/inputFiles/poromechanics/faultPoroelastic_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_base.xml
  2× /geos_lib/inputFiles/solidMechanics/sedov_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_fim.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_poroelastic_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEBICrack_base.xml
  1× /geos_lib/inputFiles/multiscalePreconditioner/singlePhasePoromechanics/cube_amg.xml
  1× /geos_lib/inputFiles/multiscalePreconditioner/solidMechanics/cube_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_sequential.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_smoke_sequential.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  1× /geos_lib/inputFiles/poromechanics/nonlinearAcceleration/validationCase/validationCase.xml
  1× /geos_lib/inputFiles/poromechanics/permeableFault_benchmark.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/ALM_singlephasePoromechanics_curvedFrac_smoke.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_solvers.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_base.xml
  1× /geos_lib/inputFiles/simplePDE/Laplace_base.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_base.xml
  1× /geos_lib/inputFiles/solidMechanics/beamBending_base.xml
  1× /geos_lib/inputFiles/solidMechanics/plasticCubeReset.xml
  1× /geos_lib/inputFiles/solidMechanics/solidMechBlock.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_sequential.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_smoke_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_benchmark.xml
  1× /workspace/inputs/PoroElastic_Terzaghi_base_direct.xml
  1× /workspace/inputs/PoroElastic_Terzaghi_benchmark.xml
  1× /workspace/inputs/PoroElastic_Terzaghi_smoke.xml
```

**C1 RSTs read (unique=3, total reads=3):**
```
  1× /geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/poromechanics/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/poromechanics/mandel/Example.rst
```

**C0 RSTs read (unique=1, total reads=1):**
```
  1× /geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst
```

### AdvancedExampleViscoDruckerPrager  —  C1: 0.738, C0: 0.975, Δ: +0.237

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=11, total reads=28):**
```
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  3× /workspace/inputs/triaxialDriver_ViscoDruckerPrager.xml
  3× /workspace/inputs/triaxialDriver_base.xml
  2× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ModifiedCamClay.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
```

**C0 XMLs read (unique=41, total reads=101):**
```
  7× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  7× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  7× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ModifiedCamClay.xml
  7× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  7× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  5× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
  4× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  4× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
  4× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropic.xml
  3× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClayVolumetric.xml
  3× /workspace/inputs/triaxialDriver_ViscoDruckerPrager.xml
  3× /workspace/inputs/triaxialDriver_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  2× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEBICrack_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_Sneddon_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SlippingFault_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_benchmark.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoModifiedCamClay_base.xml
  1× /geos_lib/inputFiles/relpermDriver/testRelpermDriverTableHyst2ph.xml
  1× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/plasticCubeReset.xml
  1× /geos_lib/inputFiles/solidMechanics/solidMechBlock.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_smoke.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase1.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase2.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathDryUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathWetUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropicPressureDependent.xml
```

**C1 RSTs read (unique=8, total reads=14):**
```
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
```

**C0 RSTs read (unique=16, total reads=25):**
```
  3× /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/Index.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
  2× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst
  1× /geos_lib/src/coreComponents/constitutiveDrivers/docs/ConstitutiveDrivers.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step03/Tutorial.rst
```

### TutorialSneddon  —  C1: 0.643, C0: 0.868, Δ: +0.226

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=111, total reads=174):**
```
  5× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  4× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFracShapes_base.xml
  4× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_base.xml
  3× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_CoulombFriction_base.xml
  3× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_Frictionless_base.xml
  3× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFracShapes_smoke.xml
  3× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_staticCondensation_benchmark.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_poroelastic_base.xml
  3× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_Sneddon_benchmark.xml
  3× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PassingCrack_smoke.xml
  3× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SingleFracCompression_benchmark.xml
  3× /geos_lib/inputFiles/lagrangianContactMechanics/SingleFracCompression_base.xml
  3× /geos_lib/inputFiles/lagrangianContactMechanics/Sneddon_smoke.xml
  3× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_pressurizedFrac_smoke.xml
  3× /geos_lib/inputFiles/poromechanicsFractures/SlipPermeability_embeddedFrac.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d_fractured.xml
  2× /geos_lib/inputFiles/efemFractureMechanics/SneddonRotated_benchmark.xml
  2× /geos_lib/inputFiles/efemFractureMechanics/SneddonRotated_smoke.xml
  2× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_staticCondensation_smoke.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_poroelastic_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/walshQuarterNoChombo_base.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_SingleFracCompression_benchmark.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_Sneddon_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEBICrack_base.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEBICrack_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SimpleCubes_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SingleFracCompression_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_TFrac_benchmark.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_TFrac_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_UnstructuredCrack_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_slippingFault_vertical_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/LagrangeContactBubbleStab_singleFracCompression_base.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/PassingCrack_base.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/TFrac_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/ExponentialDecayPermeability_edfm_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/SlipPermeability_pEDFM_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/WillisRichardsPermeability_efem-edfm_base.xml
  2× /geos_lib/inputFiles/singlePhaseFlowFractures/fractureMatrixFlow_edfm_base.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_CoulombFriction_smoke.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_Frictionless_smoke.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/SneddonRotated_benchmark2.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdBase_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdNodeBased_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdSmokeBase_C3D6.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Leakoff_Dominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Leakoff_Dominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Storage_Dominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Storage_Dominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdValidation_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedAnisotropicToughness_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedToughnessDominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedToughnessDominated_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedToughnessDominated_poroelastic_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedToughnessDominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_PassingCrack_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_SimpleCubes_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_SingleFracCompression_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_TFrac_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_TFrac_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_UnstructuredCrack_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_UnstructuredCrack_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_slippingFault_horizontal_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_slippingFault_vertical_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEMICrack/PEMICrack_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_UnstructuredCrack_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_slippingFault_horizontal_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/LagrangeContactBubbleStab_FixedSlip_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SimpleCubes_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SingleFracCompression_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SlippingFault_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/TFrac_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/UnstructuredCrack_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/UnstructuredCrack_benchmark.xml
  1× /geos_lib/inputFiles/multiphaseFlowFractures/deadOil_fractureMatrixFlow_edfm_base.xml
  1× /geos_lib/inputFiles/multiphaseFlowFractures/deadoil_3ph_corey_2d_edfm.xml
  1× /geos_lib/inputFiles/multiphaseFlowFractures/deadoil_3ph_corey_pedfm_impermeableFault_smoke.xml
  1× /geos_lib/inputFiles/phaseField/PhaseFieldPoromechanics_Nucleation_Injection.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/ALM_singlephasePoromechanics_curvedFrac_smoke.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/ExponentialDecayPermeability_conformingFracture_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_eggModel_small.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_pennyCrack_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_pennyCrack_benchmark.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_pennyCrack_smoke.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/singlePhasePoromechanics_FaultModel_base.xml
  1× /geos_lib/inputFiles/singlePhaseFlowFractures/fractureFlow_conforming_2d.xml
  1× /geos_lib/inputFiles/singlePhaseFlowFractures/fractureMatrixFlowWithGravity_edfm_verticalFrac_smoke.xml
  1× /geos_lib/inputFiles/singlePhaseFlowFractures/fractureMatrixFlow_pedfm_impermeableFracture_smoke.xml
  1× /geos_lib/inputFiles/surfaceGeneration/DryFrac_StaticPenny_PrismElem.xml
  1× /geos_lib/inputFiles/surfaceGeneration/DryFrac_ThreeNodesPinched_HorizontalFrac.xml
  1× /geos_lib/inputFiles/surfaceGeneration/SurfaceGenerator.xml
  1× /geos_lib/inputFiles/thermalSinglePhaseFlowFractures/fractureMatrixThermalFlow_edfm_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_efem-edfm_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_ImperfectInterfaces_base.xml
```

**C0 XMLs read (unique=59, total reads=128):**
```
  6× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  6× /geos_lib/inputFiles/lagrangianContactMechanics/Sneddon_smoke.xml
  5× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFracShapes_base.xml
  5× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFracShapes_smoke.xml
  5× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_staticCondensation_benchmark.xml
  5× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SingleFracCompression_smoke.xml
  5× /geos_lib/inputFiles/lagrangianContactMechanics/SingleFracCompression_base.xml
  4× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_Sneddon_benchmark.xml
  4× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEBICrack_base.xml
  3× /geos_lib/inputFiles/efemFractureMechanics/SneddonRotated_benchmark.xml
  3× /geos_lib/inputFiles/efemFractureMechanics/SneddonRotated_smoke.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/kgdValidation_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_smoke.xml
  3× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SingleFracCompression_benchmark.xml
  3× /geos_lib/inputFiles/lagrangianContactMechanics/SingleFracCompression_smoke.xml
  3× /workspace/inputs/Sneddon_base.xml
  2× /geos_lib/inputFiles/efemFractureMechanics/SneddonRotated_benchmark2.xml
  2× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_staticCondensation_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_Sneddon_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_TFrac_benchmark.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_TFrac_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/SingleFracCompression_benchmark.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/TFrac_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_inclinedFrac_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_verticalFrac_smoke.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/SlipPermeability_embeddedFrac.xml
  2× /workspace/inputs/ContactMechanics_Sneddon_benchmark.xml
  2× /workspace/inputs/Sneddon_benchmark.xml
  2× /workspace/inputs/Sneddon_embeddedFrac_base.xml
  2× /workspace/inputs/Sneddon_embeddedFrac_verification.xml
  2× /workspace/inputs/Sneddon_hydroFrac_base.xml
  2× /workspace/inputs/Sneddon_hydroFrac_benchmark.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_CoulombFriction_smoke.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_Frictionless_base.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_Frictionless_smoke.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_base.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_shapes_base.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdBase_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdSmokeBase_C3D6.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdValidation_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEBICrack_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PassingCrack_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SimpleCubes_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SingleFracCompression_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_UnstructuredCrack_benchmark.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/PassingCrack_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/PassingCrack_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SimpleCubes_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SimpleCubes_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SlippingFault_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SlippingFault_horizontal_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/Sneddon_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/TFrac_smoke.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_efem-edfm_verticalFrac_base.xml
```

**C1 RSTs read (unique=0, total reads=0):**

*(none — C1 read no .rst on this task)*

**C0 RSTs read (unique=40, total reads=45):**
```
  2× /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/contact/docs/ContactMechanics.rst
  2× /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/contact/docs/SolidMechanicsEmbeddedFractures.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/Index.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/intersectFrac/Example.rst
  2× /geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/Constitutive.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/Damage.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/ElasticIsotropic.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/Plasticity.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/SolidModels.rst
  1× /geos_lib/src/coreComponents/discretizationMethods/docs/NumericalMethodsManager.rst
  1× /geos_lib/src/coreComponents/events/docs/EventManager.rst
  1× /geos_lib/src/coreComponents/events/docs/TasksManager.rst
  1× /geos_lib/src/coreComponents/fieldSpecification/docs/FieldSpecification.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/Index.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/InputXMLFiles.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/LogCsvOutputs.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/OutputTasks.rst
  1× /geos_lib/src/coreComponents/functions/docs/FunctionManager.rst
  1× /geos_lib/src/coreComponents/linearAlgebra/docs/LinearSolvers.rst
  1× /geos_lib/src/coreComponents/mesh/docs/Mesh.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/PhysicsSolvers.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/SolutionStrategy.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/ProppantTransport.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/SinglePhaseFlow.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/contact/docs/SolidMechanicsConformingFractures.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/docs/SolidMechanics.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/faultVerification/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/singleFracCompression/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/pennyFracViscosityDominated/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/poromechanics/Example.rst
  1× /geos_lib/src/docs/sphinx/developerGuide/Contributing/InputFiles.rst
  1× /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/XML.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step02/Tutorial.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step03/Tutorial.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step04/Tutorial.rst
  1× /geos_lib/src/docs/sphinx/userGuide/Index.rst
```

### AdvancedExampleDeviatedElasticWellbore  —  C1: 0.766, C0: 0.939, Δ: +0.172

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=52, total reads=112):**
```
  6× /geos_lib/inputFiles/solidMechanics/OpenWellbore.xml
  6× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
  5× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_base.xml
  5× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  5× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_benchmark.xml
  4× /geos_lib/inputFiles/solidMechanics/KirschProblem_base.xml
  4× /geos_lib/inputFiles/solidMechanics/benchmarks/VerticalElasticWellbore.xml
  4× /geos_lib/inputFiles/solidMechanics/casedWellbore.xml
  4× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_smoke.xml
  4× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_benchmark.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  3× /geos_lib/inputFiles/solidMechanics/KirschProblem_smoke.xml
  3× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml
  3× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  3× /workspace/inputs/DeviatedElasticWellbore_base.xml
  3× /workspace/inputs/DeviatedElasticWellbore_benchmark.xml
  3× /workspace/inputs/DeviatedElasticWellbore_smoke.xml
  2× /geos_lib/inputFiles/phaseField/PhaseFieldPoromechanics_Nucleation_Wellbore.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroModifiedCamClayWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/KirschProblem_benchmark.xml
  2× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_isotropic_smoke.xml
  2× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_base.xml
  2× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_base.xml
  2× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom01.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDelftEggWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_fim.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_orthotropic_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/sedov_ssle_base.xml
  1× /geos_lib/inputFiles/solidMechanics/solidMechBlock.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_smoke.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_ImperfectInterfaces_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_ImperfectInterfaces_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_smoke.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom02.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom03.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom04.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom05.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_probdef.xml
  1× /geos_lib/inputFiles/wellboreECP/mechanics/ECP_Wellbore_probdef.xml
  1× /geos_lib/inputFiles/wellboreECP/mechanics/level01/ECP_Wellbore_cpu.xml
  1× /geos_lib/inputFiles/wellboreECP/mechanics/level02/ECP_Wellbore_cpu.xml
```

**C0 XMLs read (unique=38, total reads=72):**
```
  5× /geos_lib/inputFiles/solidMechanics/OpenWellbore.xml
  5× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
  5× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_benchmark.xml
  4× /geos_lib/inputFiles/solidMechanics/KirschProblem_base.xml
  4× /geos_lib/inputFiles/solidMechanics/KirschProblem_smoke.xml
  3× /geos_lib/inputFiles/solidMechanics/benchmarks/VerticalElasticWellbore.xml
  3× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_base.xml
  3× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  3× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/KirschProblem_benchmark.xml
  2× /geos_lib/inputFiles/solidMechanics/casedWellbore.xml
  2× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_isotropic_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/solidMechBlock.xml
  2× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_benchmark.xml
  2× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_base.xml
  2× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_benchmark.xml
  1× /geos_lib/inputFiles/initialization/gravityInducedStress_initialization_base.xml
  1× /geos_lib/inputFiles/initialization/userdefinedStress_initialization_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/VerticalElasticWellbore.xml
  1× /geos_lib/inputFiles/solidMechanics/benchmarks/SSLE-QS-small.xml
  1× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_orthotropic_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_transverseIsotropic_smoke.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_base.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom01.xml
  1× /workspace/inputs/DeviatedElasticWellbore_base.xml
  1× /workspace/inputs/DeviatedElasticWellbore_benchmark.xml
  1× /workspace/inputs/DeviatedElasticWellbore_smoke.xml
```

**C1 RSTs read (unique=4, total reads=4):**
```
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/deviatedPoroElasticWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/kirschWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/verticalPoroElastoPlasticWellbore/Example.rst
```

**C0 RSTs read (unique=7, total reads=10):**
```
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedElasticWellbore/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/deviatedPoroElasticWellbore/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/kirschWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/deviatedPoroElasticWellbore/Example2.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/dpWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/edpWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/verticalPoroElastoPlasticWellbore/Example.rst
```

### buckleyLeverettProblem  —  C1: 0.726, C0: 0.875, Δ: +0.149

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=28, total reads=55):**
```
  7× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/buckleyLeverett_1d/buckleyLeverett_1d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/buckleyLeverett_1d/buckleyLeverett_1d_DBC.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d.xml
  4× /workspace/inputs/buckleyLeverett_benchmark.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/c1-ppu/grav_seg_c1ppu_base.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/c1-ppu/grav_seg_c1ppu_drain.xml
  3× /workspace/inputs/buckleyLeverett_base.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/2ph_cap_1d_ihu.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/4comp_2ph_1d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_baker_1d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_stone2_1d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/gravitySegregation/grav_seg_drain_Z.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_deadoil_3ph_baker_2d_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/4comp_2ph_cap_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE10/deadOilSpe10Layers84_85_base_iterative.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE10/deadOilSpe10Layers84_85_benchmark.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/kr.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_direct.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_benchmark.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/c1-ppu/grav_seg_c1ppu_hyst.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_hybrid_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d_fractured.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/gravitySegregation/grav_seg_base.xml
  1× /geos_lib/inputFiles/immiscibleMultiphaseFlow/immiscible_2phaseFlow_1d.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_deadoil_3ph_baker_2d_fim.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/multiphasePoromechanics_FaultModel_base.xml
  1× /geos_lib/inputFiles/relpermDriver/testRelpermDriverBCBaker.xml
  1× /geos_lib/inputFiles/relpermDriver/testRelpermDriverBCStoneII.xml
```

**C0 XMLs read (unique=39, total reads=80):**
```
  8× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/buckleyLeverett_1d/buckleyLeverett_1d.xml
  5× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/buckleyLeverett_1d/buckleyLeverett_1d_DBC.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE10/deadOilSpe10Layers84_85_base_iterative.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE10/deadOilSpe10Layers84_85_benchmark.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/gravitySegregation/grav_seg_base.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/gravitySegregation/grav_seg_drain_Z.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/4comp_2ph_1d.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_direct.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_staircase_3d.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_staircase_3d_transmi_output.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_base.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_3d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_dirichlet.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_hybrid_1d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_2ph_staircase_gravity_segregation_3d.xml
  2× /workspace/inputs/buckleyLeverett_base.xml
  2× /workspace/inputs/buckleyLeverett_benchmark.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/2ph_cap_1d_ihu.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/4comp_2ph_cap_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/buckleyLeverettProblem/buckleyLeverett_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/buckleyLeverettProblem/buckleyLeverett_benchmark.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/c1-ppu/grav_seg_c1ppu_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/c1-ppu/grav_seg_c1ppu_drain.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/c1-ppu/grav_seg_c1ppu_hyst.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/bottom_layer_SPE10/bottom_layer_SPE10.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/bottom_layer_SPE10/bottom_layer_SPE10_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_baker_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d_fractured.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_staircase_hybrid_3d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_stone2_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/initialization_2phase.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/soreideWhitson/lockExchange/lockExchange_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Egg/deadOilEgg_base_iterative.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_base.xml
  1× /geos_lib/inputFiles/immiscibleMultiphaseFlow/immiscible_2phaseFlow_1d.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_deadoil_3ph_baker_2d_base.xml
  1× /geos_lib/inputFiles/relpermDriver/testRelpermDriverBCBaker.xml
  1× /geos_lib/inputFiles/singlePhaseFlow/vtk/3D_10x10x10_compressible_hex_gravity_base.xml
```

**C1 RSTs read (unique=0, total reads=0):**

*(none — C1 read no .rst on this task)*

**C0 RSTs read (unique=15, total reads=23):**
```
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/Index.rst
  3× /geos_lib/src/docs/sphinx/basicExamples/co2Injection/Example.rst
  3× /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst
  2× /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/CompositionalMultiphaseFlow.rst
  2× /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/XML.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/LogCsvOutputs.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/PhysicsSolvers.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/SolutionStrategy.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalHystInjection/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalLeakyWell/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlowWithWells/Example.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step01/Tutorial.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step03/Tutorial.rst
  1× /geos_lib/src/docs/sphinx/userGuide/Index.rst
```

### ExampleEDPWellbore  —  C1: 0.841, C0: 0.979, Δ: +0.138

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=46, total reads=102):**
```
  6× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  5× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  5× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_benchmark.xml
  5× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_benchmark.xml
  4× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  3× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  3× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_base.xml
  3× /geos_lib/inputFiles/solidMechanics/OpenWellbore.xml
  3× /geos_lib/inputFiles/solidMechanics/benchmarks/VerticalElasticWellbore.xml
  3× /geos_lib/inputFiles/solidMechanics/casedWellbore.xml
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroExtendedDruckerPrager_consolidation_smoke.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  3× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  3× /workspace/inputs/ExtendedDruckerPragerWellbore_base.xml
  3× /workspace/inputs/ExtendedDruckerPragerWellbore_benchmark.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroDruckerPrager_consolidation_smoke.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml
  2× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  2× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_base.xml
  2× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
  1× /geos_lib/inputFiles/phaseField/PhaseFieldPoromechanics_Nucleation_Wellbore.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_base.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/plasticCubeReset.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Injection_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_benchmark.xml
```

**C0 XMLs read (unique=54, total reads=104):**
```
  6× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
  6× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  5× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_benchmark.xml
  4× /geos_lib/inputFiles/solidMechanics/OpenWellbore.xml
  4× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  3× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_base.xml
  3× /geos_lib/inputFiles/solidMechanics/benchmarks/VerticalElasticWellbore.xml
  3× /geos_lib/inputFiles/solidMechanics/casedWellbore.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  3× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  3× /workspace/inputs/ExtendedDruckerPragerWellbore_base.xml
  3× /workspace/inputs/ExtendedDruckerPragerWellbore_benchmark.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_benchmark.xml
  2× /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  2× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_smoke.xml
  2× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/benchmarks/SSLE-QS-small.xml
  2× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_base.xml
  2× /geos_lib/inputFiles/solidMechanics/sedov_ssle_smoke.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroExtendedDruckerPrager_consolidation_smoke.xml
  2× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  2× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_base.xml
  2× /geos_lib/inputFiles/wellboreECP/mechanics/ECP_Wellbore_probdef.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_base.xml
  1× /geos_lib/inputFiles/phaseField/PhaseFieldPoromechanics_Nucleation_Wellbore.xml
  1× /geos_lib/inputFiles/poromechanics/PoroDelftEggWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_smoke.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_smoke.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_base.xml
  1× /geos_lib/inputFiles/solidMechanics/KirschProblem_benchmark.xml
  1× /geos_lib/inputFiles/solidMechanics/SSLE-QS-small.xml
  1× /geos_lib/inputFiles/solidMechanics/mechanicsWithHeterogeneousMaterials.xml
  1× /geos_lib/inputFiles/solidMechanics/plasticCubeReset.xml
  1× /geos_lib/inputFiles/solidMechanics/sedov_base.xml
  1× /geos_lib/inputFiles/solidMechanics/sedov_ssle_base.xml
  1× /geos_lib/inputFiles/solidMechanics/sedov_ssle_benchmark1.xml
  1× /geos_lib/inputFiles/solidMechanics/sedov_with_bias.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_benchmark.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroDruckerPrager_consolidation_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
  1× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom01.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom02.xml
  1× /geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom06.xml
  1× /geos_lib/inputFiles/wellboreECP/compositionalMultiphaseFlow/ECP_Wellbore_probdef.xml
  1× /geos_lib/inputFiles/wellboreECP/singlePhaseFlow/ECP_Wellbore_probdef.xml
```

**C1 RSTs read (unique=5, total reads=5):**
```
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/verticalPoroElastoPlasticWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
```

**C0 RSTs read (unique=9, total reads=10):**
```
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/verticalPoroElastoPlasticWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/dpWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/kirschWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/mccWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/WorkingWithData.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step01/Tutorial.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step04/Tutorial.rst
```

### kgdExperimentValidation  —  C1: 0.773, C0: 0.910, Δ: +0.137

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=36, total reads=68):**
```
  5× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_base.xml
  5× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_benchmark.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_base.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_benchmark.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/kgdBase_C3D6_base.xml
  3× /workspace/inputs/kgdValidation_base.xml
  3× /workspace/inputs/kgdValidation_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_smoke.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdSmokeBase_C3D6.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_poroelastic_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Leakoff_Dominated_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Storage_Dominated_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_smoke.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdNodeBased_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdNodeBased_C3D6_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_poroelastic_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Leakoff_Dominated_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Leakoff_Dominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Storage_Dominated_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Storage_Dominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/walshQuarterNoChombo_base.xml
```

**C0 XMLs read (unique=24, total reads=78):**
```
  6× /geos_lib/inputFiles/hydraulicFracturing/kgdBase_C3D6_base.xml
  6× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_base.xml
  6× /geos_lib/inputFiles/hydraulicFracturing/kgdSmokeBase_C3D6.xml
  5× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml
  5× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_base.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_smoke.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_benchmark.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_poroelastic_base.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Leakoff_Dominated_base.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_benchmark.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/kgdNodeBased_C3D6_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Storage_Dominated_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_base.xml
  3× /workspace/inputs/kgdValidation_base.xml
  3× /workspace/inputs/kgdValidation_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Leakoff_Dominated_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughness_Storage_Dominated_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_smoke.xml
```

**C1 RSTs read (unique=0, total reads=0):**

*(none — C1 read no .rst on this task)*

**C0 RSTs read (unique=5, total reads=14):**
```
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/Index.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdToughnessDominated/Example.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdValidation/Example.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdViscosityDominated/Example.rst
  2× /geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst
```

### AdvancedExampleCasedContactThermoElasticWellbore  —  C1: 0.699, C0: 0.813, Δ: +0.114

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=36, total reads=76):**
```
  5× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_conforming_base.xml
  5× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml
  5× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_base.xml
  4× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_base.xml
  4× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_benchmark.xml
  4× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_benchmark.xml
  3× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_smoke.xml
  3× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  3× /workspace/inputs/CasedThermoElasticWellbore_ImperfectInterfaces_base.xml
  3× /workspace/inputs/CasedThermoElasticWellbore_ImperfectInterfaces_benchmark.xml
  3× /workspace/inputs/CasedThermoElasticWellbore_ImperfectInterfaces_smoke.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/SingleFracCompression_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_base.xml
  2× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_efem-edfm_base.xml
  2× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_smoke.xml
  2× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  2× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_benchmark.xml
  2× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_slippingFault_horizontal_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SimpleCubes_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SlippingFault_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/Sneddon_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/singlePhasePoromechanics_FaultModel_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/singlePhasePoromechanics_FaultModel_well_base.xml
  1× /geos_lib/inputFiles/solidMechanics/casedWellbore.xml
  1× /geos_lib/inputFiles/solidMechanics/elasticHollowCylinder_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_conforming_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
```

**C0 XMLs read (unique=52, total reads=88):**
```
  5× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_conforming_base.xml
  5× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml
  5× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_benchmark.xml
  5× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_smoke.xml
  4× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_base.xml
  4× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_base.xml
  4× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  3× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_benchmark.xml
  3× /geos_lib/inputFiles/wellbore/CasedThermoElasticWellbore_smoke.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SingleFracCompression_benchmark.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/SingleFracCompression_base.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/SlippingFault_base.xml
  2× /geos_lib/inputFiles/lagrangianContactMechanics/Sneddon_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_base.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_solvers.xml
  2× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_solvers.xml
  1× /geos_lib/inputFiles/efemFractureMechanics/EmbFrac_Compression_CoulombFriction_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdBase_C3D6_base.xml
  1× /geos_lib/inputFiles/inducedSeismicity/SCEC_BP6_QD_S_base.xml
  1× /geos_lib/inputFiles/inducedSeismicity/SpringSlider_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ALM_SimpleCubes_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_PEBICrack_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_SingleFracCompression_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_slippingFault_horizontal_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_slippingFault_vertical_smoke.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/PassingCrack_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/SimpleCubes_base.xml
  1× /geos_lib/inputFiles/lagrangianContactMechanics/TFrac_base.xml
  1× /geos_lib/inputFiles/phaseField/PhaseFieldFracture_CohesiveModel.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/ExponentialDecayPermeability_conformingFracture_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_ALM_conformingFracture_2d_openingFrac_sequential_solvers.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_BartonBandis_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_faultSlip_sequential_solvers.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/SlipPermeability_embeddedFrac.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/WillisRichardsPermeability_efem-edfm_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/singlePhasePoromechanics_FaultModel_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/singlePhasePoromechanics_FaultModel_well_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/yieldAcceleration/validation_case_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_smoke_fim.xml
  1× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_conforming_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedElasticWellbore_smoke.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_base.xml
  1× /geos_lib/inputFiles/wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml
  1× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_benchmark.xml
```

**C1 RSTs read (unique=5, total reads=5):**
```
  1× /geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedContactElasticWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedElasticWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedThermoElasticWellbore/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/thermoPoroElasticWellbore/Example.rst
```

**C0 RSTs read (unique=0, total reads=0):**

*(none — C0 read no .rst on this task)*

### ExampleIsothermalLeakyWell  —  C1: 0.791, C0: 0.878, Δ: +0.087

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=46, total reads=71):**
```
  5× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_smoke_3d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_benchmark.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE10/deadOilSpe10Layers84_85_base_iterative.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_base.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_benchmark.xml
  3× /workspace/inputs/isothermalLeakyWell_base_iterative.xml
  3× /workspace/inputs/isothermalLeakyWell_benchmark.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_base_iterative.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_smoke_3d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_2ph_staircase_gravity_segregation_3d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_drainageOnly_iterative_base.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_smoke_3d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_base.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_smoke.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/staged_perf_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE10/deadOilSpe10Layers84_85_benchmark.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/dirichlet_boundary_vti.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/kr.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/properties_vti.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_00840x00120.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/buckleyLeverettProblem/buckleyLeverett_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_3d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_hybrid_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/bottom_layer_SPE10/bottom_layer_SPE10_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/buckleyLeverett_1d/buckleyLeverett_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/buckleyLeverett_1d/buckleyLeverett_1d_DBC.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/grav_seg_1d/grav_seg_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/grav_seg_1d/grav_seg_1d_DBC.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d_fractured.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_staircase_3d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/co2_2d_plume/co2_2d_plume_Z.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_hystRelperm_direct_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Egg/deadOilEgg_benchmark.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/compositional_multiphase_wells_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/compositional_multiphase_wells_2d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_kvalue_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_kvalue_smoke.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_soreide_whitson_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/staircase_co2_wells_3d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/staircase_co2_wells_hybrid_3d.xml
  1× /geos_lib/inputFiles/immiscibleMultiphaseFlow/immiscibleTwoPhase_BuckleyLeverett/buckleyLeverett_base.xml
  1× /geos_lib/inputFiles/immiscibleMultiphaseFlow/immiscibleTwoPhase_SPE10_layer84/immiscibleTwoPhase_SPE10_layer84_base_iterative.xml
  1× /geos_lib/inputFiles/relpermDriver/testRelpermDriverBCBaker.xml
  1× /geos_lib/inputFiles/thermalMultiphaseFlow/co2_thermal_2d.xml
```

**C0 XMLs read (unique=55, total reads=110):**
```
  7× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_base.xml
  6× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_smoke_3d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_base_iterative.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_benchmark.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_smoke_3d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_2ph_staircase_gravity_segregation_3d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_staircase_3d.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_00840x00120.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_base.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_3d.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_base.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseWell/staircase_co2_wells_3d.xml
  3× /workspace/inputs/isothermalLeakyWell_base_iterative.xml
  3× /workspace/inputs/isothermalLeakyWell_benchmark.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE10/deadOilSpe10Layers84_85_base_iterative.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/dirichlet_boundary_vti.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/kr.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/properties_vti.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_dirichlet.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_hybrid_1d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_corey_1d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/initialization_2phase.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/co2_2d_plume/co2_2d_plume_Z.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_benchmark.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_drainageOnly_iterative_base.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/black_oil_wells_unsaturated_3d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/dead_oil_wells_2d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_kvalue_base.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/staged_perf_base.xml
  1× /geos_lib/examples/compositionalFlow/deadoilStaircase.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/2ph_cap_1d_ihu.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_direct.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_iterative.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalleakyWell/thermalLeakyWell_base_iterative.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/bottom_layer_SPE10/bottom_layer_SPE10_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/dbc/buckleyLeverett_1d/buckleyLeverett_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_2ph_compressible_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_3ph_staircase_3d_transmi_output.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/initialization_2phase_no_cappres.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/initialization_3phase.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/sourceFlux_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_drainageOnly_direct_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Egg/deadOilEgg_base_direct.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Egg/deadOilEgg_base_iterative.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/black_oil_wells_saturated_3d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/compositional_multiphase_wells_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_initialisation.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_properties.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_soreide_whitson_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_smoke.xml
  1× /geos_lib/inputFiles/immiscibleMultiphaseFlow/immiscibleTwoPhase_BuckleyLeverett/buckleyLeverett_base.xml
  1× /geos_lib/inputFiles/immiscibleMultiphaseFlow/immiscible_2phaseFlow_1d.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_deadoil_3ph_baker_2d_base.xml
  1× /geos_lib/inputFiles/singlePhaseFlow/sourceFlux_1d.xml
  1× /geos_lib/inputFiles/thermalMultiphaseFlow/co2_thermal_2d.xml
```

**C1 RSTs read (unique=4, total reads=6):**
```
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/buckleyLeverett/Example.rst
  2× /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/co2Injection/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlowWithWells/Example.rst
```

**C0 RSTs read (unique=12, total reads=14):**
```
  2× /geos_lib/src/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/Index.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/BlackOilFluid.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/CO2BrineFluid.rst
  1× /geos_lib/src/coreComponents/fieldSpecification/docs/EquilibriumInitialCondition.rst
  1× /geos_lib/src/coreComponents/mesh/docs/Mesh.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/CompositionalMultiphaseFlow.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/ImmiscibleMultiphaseFlow.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/wells/docs/CompositionalMultiphaseWell.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalLeakyWell/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/spe11b/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/thermalLeakyWell/Example.rst
```

### pknViscosityDominated  —  C1: 0.899, C0: 0.986, Δ: +0.087

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=22, total reads=55):**
```
  6× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_base.xml
  6× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_benchmark.xml
  5× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_base.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_benchmark.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_smoke.xml
  3× /workspace/inputs/pknViscosityDominated_base.xml
  3× /workspace/inputs/pknViscosityDominated_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdValidation_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdValidation_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_smoke.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_poroelastic_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_poroelastic_benchmark.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/PoroElastic_conformingFracture_2d_openingFrac_solvers.xml
```

**C0 XMLs read (unique=19, total reads=44):**
```
  6× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_base.xml
  6× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_benchmark.xml
  4× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_base.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
  3× /geos_lib/inputFiles/hydraulicFracturing/pknViscosityDominated_poroelastic_smoke.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/heterogeneousInSitu_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/kgdViscosityDominated_benchmark.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_base.xml
  2× /geos_lib/inputFiles/hydraulicFracturing/pennyShapedViscosityDominated_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/Sneddon_hydroFrac_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdEdgeBased_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdNodeBased_C3D6_base.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdToughnessDominated_benchmark.xml
  1× /geos_lib/inputFiles/hydraulicFracturing/kgdValidation_base.xml
  1× /workspace/inputs/pknViscosityDominated_base.xml
  1× /workspace/inputs/pknViscosityDominated_benchmark.xml
```

**C1 RSTs read (unique=0, total reads=0):**

*(none — C1 read no .rst on this task)*

**C0 RSTs read (unique=5, total reads=8):**
```
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/Index.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdViscosityDominated/Example.rst
  2× /geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdToughnessDominated/Example.rst
  1× /geos_lib/src/docs/sphinx/developerGuide/Contributing/IntegratedTests.rst
```

### ExampleThermoporoelasticConsolidation  —  C1: 0.769, C0: 0.819, Δ: +0.050

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=14, total reads=33):**
```
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_base.xml
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_benchmark_fim.xml
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_smoke_fim.xml
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_sequential.xml
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_smoke_sequential.xml
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml
  3× /workspace/inputs/ThermoPoroElastic_consolidation_base.xml
  3× /workspace/inputs/ThermoPoroElastic_consolidation_benchmark_fim.xml
  3× /workspace/inputs/ThermoPoroElastic_consolidation_smoke_fim.xml
  2× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_fim.xml
  1× /geos_lib/inputFiles/singlePhaseFlow/thermalCompressible_2d_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_benchmark_sequential.xml
```

**C0 XMLs read (unique=36, total reads=63):**
```
  6× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_base.xml
  5× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_sequential.xml
  4× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_benchmark_fim.xml
  4× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_smoke_fim.xml
  4× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_smoke_sequential.xml
  3× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_base_direct.xml
  3× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml
  2× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_base.xml
  2× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml
  2× /workspace/inputs/ThermoPoroElastic_consolidation_base.xml
  2× /workspace/inputs/ThermoPoroElastic_consolidation_benchmark_fim.xml
  2× /workspace/inputs/ThermoPoroElastic_consolidation_smoke_fim.xml
  1× /geos_lib/inputFiles/multiscalePreconditioner/singlePhasePoromechanics/cube_amg.xml
  1× /geos_lib/inputFiles/multiscalePreconditioner/singlePhasePoromechanics/cube_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Mandel_benchmark_fim.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_base_iterative.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_benchmark.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_Terzaghi_smoke.xml
  1× /geos_lib/inputFiles/poromechanics/PoroElastic_gravity.xml
  1× /geos_lib/inputFiles/poromechanics/faultPoroelastic_base.xml
  1× /geos_lib/inputFiles/poromechanicsFractures/singlePhasePoromechanics_FaultModel_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroDruckerPrager_consolidation_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_benchmark_sequential.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_smoke_sequential.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_consolidation_benchmark_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_staircase_co2_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroExtendedDruckerPrager_consolidation_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroMCC_consolidation_smoke.xml
  1× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_conforming_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_efem-edfm_base.xml
  1× /geos_lib/inputFiles/thermoPoromechanicsFractures/ThermoPoroElastic_efem-edfm_eggModel_small.xml
  1× /geos_lib/inputFiles/wellbore/CasedElasticWellbore_ImperfectInterfaces_base.xml
  1× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_benchmark.xml
  1× /geos_lib/inputFiles/wellbore/ThermoPoroElasticWellbore_smoke.xml
```

**C1 RSTs read (unique=6, total reads=6):**
```
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/thermoPoromechanics/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/linearThermalDiffusion/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/nonLinearThermalDiffusion_TemperatureDependentSinglePhaseThermalConductivity/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/nonLinearThermalDiffusion_TemperatureDependentVolumetricHeatCapacity/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/thermoPoroElasticWellbore/Example.rst
```

**C0 RSTs read (unique=5, total reads=7):**
```
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/thermoPoromechanics/Index.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/thermoPoroElasticWellbore/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/BiotPorosity.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/Index.rst
```

### AdvancedExampleExtendedDruckerPrager  —  C1: 0.769, C0: 0.705, Δ: -0.064

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=17, total reads=51):**
```
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ModifiedCamClay.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  5× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  5× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  3× /workspace/inputs/triaxialDriver_ExtendedDruckerPrager.xml
  3× /workspace/inputs/triaxialDriver_base.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoModifiedCamClay_base.xml
  1× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  1× /geos_lib/inputFiles/solidMechanics/plasticCubeReset.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClayVolumetric.xml
```

**C0 XMLs read (unique=26, total reads=67):**
```
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml
  6× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
  5× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ModifiedCamClay.xml
  5× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
  3× /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
  3× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
  2× /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml
  2× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropic.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_elasticIsotropicPressureDependent.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
  2× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClayVolumetric.xml
  2× /workspace/inputs/triaxialDriver_ExtendedDruckerPrager.xml
  2× /workspace/inputs/triaxialDriver_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml
  1× /geos_lib/inputFiles/poromechanics/PoroViscoExtendedDruckerPrager_base.xml
  1× /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_benchmark.xml
  1× /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase1.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggCase2.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathDryUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggLoadPathWetUseLinear.xml
  1× /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_delftEggUseLinear.xml
```

**C1 RSTs read (unique=11, total reads=17):**
```
  4× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  1× /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
  1× /geos_lib/src/coreComponents/functions/docs/FunctionManager.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
```

**C0 RSTs read (unique=15, total reads=30):**
```
  3× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
  3× /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
  3× /geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst
  3× /geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst
  3× /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
  3× /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
  2× /geos_lib/src/coreComponents/constitutive/docs/solid/ElasticIsotropic.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/Plasticity.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/solid/SolidModels.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/Index.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
```

### ExampleThermalLeakyWell  —  C1: 0.656, C0: 0.428, Δ: -0.227

*C1 trajectories: 3/3 seeds; C0 trajectories: 3/3 seeds*

**C1 XMLs read (unique=25, total reads=49):**
```
  5× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_smoke_3d.xml
  5× /geos_lib/inputFiles/thermalMultiphaseFlow/co2_thermal_2d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_benchmark.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_dirichlet.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_direct.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_3d.xml
  3× /workspace/inputs/thermalLeakyWell_benchmark.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_base.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_iterative.xml
  2× /geos_lib/inputFiles/thermalMultiphaseFlow/co2_thermal_obl_3d.xml
  2× /workspace/inputs/thermalLeakyWell_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/4comp_2ph_1d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/dirichlet_boundary_vti.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/kr.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/properties_vti.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/tables/pvtdriver.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_smoke_3d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/c1-ppu/grav_seg_c1ppu_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/deadoil_2ph_staircase_gravity_segregation_3d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/co2_2d_plume/co2_2d_plume_Z.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_drainageOnly_direct_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/dome_kvalue_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/isothm_mass_inj_table.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/isothm_vol_inj_table.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_base.xml
```

**C0 XMLs read (unique=32, total reads=86):**
```
  8× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_smoke_3d.xml
  6× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_direct.xml
  5× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/kr.xml
  5× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_base.xml
  5× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_3d.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/dirichlet_boundary_vti.xml
  4× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_flux_dirichlet.xml
  4× /geos_lib/inputFiles/thermalMultiphaseFlow/co2_thermal_2d.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/properties_vti.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_00840x00120.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_benchmark.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseWell/isothm_mass_inj_table.xml
  3× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_base.xml
  3× /geos_lib/inputFiles/thermalMultiphaseFlow/co2_thermal_obl_3d.xml
  3× /workspace/inputs/thermalLeakyWell_base.xml
  3× /workspace/inputs/thermalLeakyWell_benchmark.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/tables/pvtdriver.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_smoke_3d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_hybrid_1d.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/co2_2d_plume/co2_2d_plume_Z.xml
  2× /geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_smoke.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_base_iterative.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/co2_thermal_2d.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/initialization_2phase.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/overallCompositionFormulation/gravitySegregation/grav_seg_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/soreideWhitson/gravSeg/gravSeg.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/benchmarks/Class09Pb3/class09_pb3_drainageOnly_direct_base.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/isothm_vol_inj_table.xml
  1× /geos_lib/inputFiles/compositionalMultiphaseWell/staircase_co2_wells_3d.xml
  1× /geos_lib/inputFiles/relpermDriver/testRelpermDriverTableHyst2ph.xml
  1× /geos_lib/inputFiles/thermoPoromechanics/ThermoPoroElastic_staircase_co2_smoke.xml
```

**C1 RSTs read (unique=0, total reads=0):**

*(none — C1 read no .rst on this task)*

**C0 RSTs read (unique=30, total reads=54):**
```
  4× /geos_lib/src/docs/sphinx/basicExamples/co2Injection/Example.rst
  4× /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst
  3× /geos_lib/src/coreComponents/fieldSpecification/docs/FieldSpecification.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/buckleyLeverett/Example.rst
  3× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalLeakyWell/Example.rst
  2× /geos_lib/src/coreComponents/constitutive/docs/CO2BrineFluid.rst
  2× /geos_lib/src/coreComponents/constitutive/docs/RelativePermeabilityModels.rst
  2× /geos_lib/src/coreComponents/constitutive/docs/TableRelativePermeability.rst
  2× /geos_lib/src/coreComponents/events/docs/EventManager.rst
  2× /geos_lib/src/coreComponents/events/docs/TasksManager.rst
  2× /geos_lib/src/coreComponents/fileIO/doc/OutputTasks.rst
  2× /geos_lib/src/coreComponents/mesh/docs/Mesh.rst
  2× /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/CompositionalMultiphaseFlow.rst
  2× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/spe11b/Example.rst
  2× /geos_lib/src/docs/sphinx/tutorials/step02/Tutorial.rst
  2× /geos_lib/src/docs/sphinx/tutorials/step03/Tutorial.rst
  2× /geos_lib/src/docs/sphinx/userGuide/Index.rst
  1× /geos_lib/inputFiles/compositionalMultiphaseFlow/rstFile/co2_flux_3d_restart.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/CompositionalMultiphaseFluid.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/FluidModels.rst
  1× /geos_lib/src/coreComponents/constitutive/docs/TableCapillaryPressure.rst
  1× /geos_lib/src/coreComponents/fieldSpecification/docs/AquiferBoundaryCondition.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/Index.rst
  1× /geos_lib/src/coreComponents/fileIO/doc/InputXMLFiles.rst
  1× /geos_lib/src/coreComponents/linearAlgebra/docs/LinearSolvers.rst
  1× /geos_lib/src/coreComponents/physicsSolvers/PhysicsSolvers.rst
  1× /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalHystInjection/Example.rst
  1× /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlowWithWells/Example.rst
  1× /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/XML.rst
  1× /geos_lib/src/docs/sphinx/tutorials/step01/Tutorial.rst
```
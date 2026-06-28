# GEOS authoring cheatsheet (v4)

## Task → canonical XML lookup

**Read the listed file(s) FIRST. Do not Grep/Glob to find them — they are already verified.**

| Task name keyword | Canonical XML(s) under `/geos_lib/inputFiles/` |
|---|---|
| AdvancedExampleCasedContactThermoElasticWellbore | `wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml`, `solidMechanics/KirschProblem_smoke.xml` |
| AdvancedExampleDeviatedElasticWellbore | `wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml`, `solidMechanics/KirschProblem_smoke.xml` |
| AdvancedExampleDruckerPrager | `triaxialDriver/triaxialDriver_base.xml`, `triaxialDriver/tables/time.geos` |
| AdvancedExampleExtendedDruckerPrager | `triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml`, `triaxialDriver/tables/time.geos` |
| AdvancedExampleModifiedCamClay | `poromechanics/PoroViscoModifiedCamClay_base.xml` |
| AdvancedExampleViscoDruckerPrager | `triaxialDriver/triaxialDriver_base.xml`, `triaxialDriver/tables/time.geos` |
| buckleyLeverettProblem | `compositionalMultiphaseFlow/benchmarks/buckleyLeverettProblem/buckleyLeverett_base.xml` |
| ExampleDPWellbore | `solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml`, `solidMechanics/ExtendedDruckerPragerWellbore_base.xml` |
| ExampleEDPWellbore | `solidMechanics/DruckerPragerWellbore_benchmark.xml`, `solidMechanics/DruckerPragerWellbore_base.xml` |
| ExampleIsothermalLeakyWell | `compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_benchmark.xml` |
| ExampleMandel | `poromechanics/PoroElastic_Mandel_prism6_base_hybrid.xml`, `poromechanics/PoroElastic_Mandel_smoke_fim.xml` |
| ExampleThermalLeakyWell | `compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_base.xml` |
| ExampleThermoporoelasticConsolidation | `thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml`, `thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_base.xml` |
| kgdExperimentValidation | `hydraulicFracturing/kgdBase_C3D6_base.xml`, `hydraulicFracturing/kgdEdgeBased_C3D6_base.xml` |
| pknViscosityDominated | `hydraulicFracturing/pknViscosityDominated_poroelastic_benchmark.xml`, `hydraulicFracturing/pknViscosityDominated_poroelastic_base.xml` |
| TutorialPoroelasticity | `poromechanics/PoroElastic_Terzaghi_base_direct.xml`, `poromechanics/PoroElastic_Mandel_smoke_fim.xml` |
| TutorialSneddon | `hydraulicFracturing/hydrofractureSinglePhase2d.xml`, `lagrangianContactMechanics/TFrac_base.xml` |

## Constitutive class → header file (skip the Grep)

| Class | Header path under `/geos_lib/src/coreComponents/` |
|---|---|
| TriaxialDriver | `constitutiveDrivers/solid/TriaxialDriver.hpp` |
| DruckerPrager | `constitutive/solid/DruckerPrager.hpp` |
| ExtendedDruckerPrager | `constitutive/solid/DruckerPragerExtended.hpp` |
| ModifiedCamClay | `constitutive/solid/ModifiedCamClay.hpp` |
| ElasticIsotropic | `constitutive/solid/ElasticIsotropic.hpp` |
| ElasticIsotropicPressureDependent | `constitutive/solid/ElasticIsotropicPressureDependent.hpp` |
| DuvautLionsSolid | `constitutive/solid/DuvautLionsSolid.hpp` |
| BiotPorosity | `constitutive/solid/porosity/BiotPorosity.hpp` |
| TableFunction | `functions/TableFunction.hpp` |
| InternalWellboreGenerator | `mesh/generators/InternalWellboreGenerator.hpp` |

## Common solver names (use these directly)

| Solver name | Physics |
|---|---|
| `SinglePhasePoromechanics` | Coupled poroelasticity |
| `SolidMechanicsLagrangianFEM` | Solid mechanics |
| `SolidMechanicsLagrangianSSLE` | Solid mechanics, small strain |
| `HydrofractureSolver` | Hydraulic fracturing (coupled) |
| `SurfaceGenerator` | Fracture propagation |
| `CompositionalMultiphaseFVM` | Multiphase flow |
| `ThermoPoromechanics` | Thermal poroelasticity |
| `MultiphasePoromechanics` | Multiphase poroelasticity |
| `TriaxialDriver` | Triaxial test driver |
| `InternalWellbore` | Wellbore mesh generator |

## Don't Grep for these (empirically wasted in F0 trajectories)

- `class`, `public:` — too vague, matches everything
- `catalogName` — use specific class names instead
- `Coulomb` — use `DruckerPrager`
- `StructuredMesh` — use `InternalMesh`
- `SurfaceElementRegion` — use `SurfaceGenerator`
- `NewtonRaphson` — use solver-specific names
- `lineSearchMaxCuts`, `lineSearchAction` — rarely productive
- `viewKeyStruct` — implementation detail, not authoring info

## Workflow shortcuts

- **Task in the table above** → skip search, Read the canonical XML(s) directly.
- **Constitutive class in the table above** → skip Grep, Read the header.
- **Solver in the table above** → search `inputFiles/` for `<SolverName` to find usage examples.

---

## Inherited problem-class hints (from v3)

### Thermal Poromechanics (ThermoPoroElastic Consolidation)

- **Solver**: `<SinglePhasePoromechanics>` with `thermalFluxFlag="1"` and `discretization="fe1"` (or `sequential` for benchmarking). Also need `maxTime`, `timeStep` parameters.
- **Mesh**: `InternalMesh` – often a simple block `{1,1,1}` with `xCoords{0,1000}`, `yCoords{0,200}`, `zCoords{0,200}` for 2D plane strain.
- **Constitutive**: `<ElasticIsotropic>` with `defaultBulkModulus`, `defaultShearModulus`, `defaultThermalExpansionCoefficient`. Plus `<BiotPorosity>` and `<ConstantPermeability>`.
- **Fluid**: `<CompressibleSinglePhaseFluid>` with reference pressure, density, viscosity, and thermal expansion.
- **Initial conditions**: `pressure`, `temperature`, `totalDisplacement` fields via `<FieldSpecifications>`. Often linear temperature gradient.
- **Boundary conditions**: `Dirichlet` for temperature on top/bottom, `Dirichlet` for displacement on sides, `Traction` for mechanical load.
- **Output**: `<HistoryCollection>` for displacement at nodes, pressure/temperature at cell centers. `<VTKCollection>` for field outputs.
- **Base files**: Look for `ThermoPoroElastic_*<file>` or `<file>` in `thermoPoromechanics/`. They include the solver, output, and sometimes tables.

### Poroelastic Consolidation (Terzaghi / Mandel)

- **Solver**: `<SinglePhasePoromechanics>` – coupling `fullyImplicit` (preferred) or `sequential`.
- **Base files**: `PoroElastic_Terzaghi_*` and `PoroElastic_Mandel_*` in `poromechanics/`.
- **Mesh**: `InternalMesh` – 1D (Terzaghi) or 2D plane strain (Mandel).
- **Constitutive**: `<ElasticIsotropic>`, `<BiotPorosity>`, `<CompressibleSinglePhaseFluid>`.
- **BCs**: Typical consolidation BCs (drained top, impermeable sides, mechanical load).
- **Tables**: Some base files reference external table files for loading curves – copy them.

### Hydraulic Fracturing – Sneddon (EFEM)

- **Solvers**: Use `<ContactMechanics>` or `<SolidMechanicsLagrangianFEM>` with `<SurfaceGenerator>` or `<EmbeddedSurfaceGenerator>` for fracture.
- **Base files**: Look in `efemFractureMechanics/`, `lagrangianContactMechanics/`, `hydraulicFracturing/` for files containing `Sneddon`, `kgd`, `pkn`.
- **Mesh**: `InternalMesh` – often a simple domain with a predefined fracture plane (e.g., `xCoords{0,1000}`, `yCoords{0,1000}`, `zCoords{-250,250}`).
- **Fracture initialization**: `<SurfaceElementRegion>` with `faceBlock` and `subRegion`. Or use `<EmbeddedSurfaceGenerator>` with `nodeBasedSIF`.
- **BCs**: `Dirichlet` for far-field stresses (sigma_xx, sigma_yy, sigma_zz) via `initialStress`. Traction on fracture faces if fluid-driven.

### Hydraulic Fracturing – KGD / PKN (HydrofractureSolver)

- **Solver**: `<HydrofractureSolver>` (coupled solid mechanics + fluid flow in fracture). Uses `<SinglePhasePoromechanics>` + `<SurfaceGenerator>` under the hood.
- **Mesh**: `InternalMesh` – often 3D block with small thickness for 2D plane strain.
- **Fluid**: `<CompressibleSinglePhaseFluid>` or incompressible; fracture fluid viscosity set via `<FractureFluid>`.
- **Injection**: `<WellElement>` or `<FluxBoundaryCondition>` at injection point.
- **Fracture toughness**: Set via `rockToughness` in `SurfaceGenerator` or `initialRockToughness`.
- **Dependencies**: Copy all files from `hydraulicFracturing/` directory that are referenced (e.g., `*.csv`, `*.geos`).

## General pitfalls

- **Missing table files**: After copying a base file, always run `grep -r 'tables/\|\.geos\|\.txt\|\.csv' /workspace/inputs/` to list external references, then ensure each file exists.
- **Base file `<Included>` chains**: If `<Included>` is used in the base file, copy those included files as well. Usually in the same directory.
- **Solver name mismatch**: The solver `name` attribute must match the `objectPath` in `HistoryCollection`.
- **Always verify**: Run `ls -R /workspace/inputs/` before declaring done.

# v4 plugin design proposal — derived from trajectory patterns

*Generated 2026-05-02 from `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/patterns.json` via DeepSeek synthesis.
Empirical patterns mined from 17 tasks × 5 cells × 3 seeds = 255 trajectories.*

## How this was generated

`scripts/trajectory_patterns.py` mines the trajectories for:
- Per-task canonical files (read in the last 10 calls before first Write, in ≥3 successful runs)
- Constitutive C++ headers and the Grep patterns that lead to them
- Cross-task recurring Grep patterns
- Dead patterns (Grep with no follow-up Read)

`scripts/trajectory_patterns_synthesize.py` (this script) feeds the
mining results to DeepSeek with a focused design prompt. Output below.

---

### 1. cheatsheet.md

#### Task → Canonical Example Mapping
| Task | Canonical XMLs (under /geos_lib/inputFiles/) |
|------|----------------------------------------------|
| AdvancedExampleCasedContactThermoElasticWellbore | wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml, solidMechanics/KirschProblem_smoke.xml |
| AdvancedExampleDeviatedElasticWellbore | wellbore/DeviatedPoroElasticWellbore_Drilling_smoke.xml, solidMechanics/KirschProblem_smoke.xml |
| AdvancedExampleDruckerPrager | triaxialDriver/triaxialDriver_base.xml, triaxialDriver/tables/time.geos |
| AdvancedExampleExtendedDruckerPrager | triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml, triaxialDriver/tables/time.geos |
| AdvancedExampleModifiedCamClay | poromechanics/PoroViscoModifiedCamClay_base.xml, /geos_lib/src/coreComponents/schema/schema.xsd |
| AdvancedExampleViscoDruckerPrager | triaxialDriver/triaxialDriver_base.xml, triaxialDriver/tables/time.geos |
| buckleyLeverettProblem | compositionalMultiphaseFlow/benchmarks/isothermalLeakyWell/isothermalLeakyWell_benchmark.xml |
| ExampleDPWellbore | solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml, solidMechanics/ExtendedDruckerPragerWellbore_base.xml |
| ExampleEDPWellbore | solidMechanics/DruckerPragerWellbore_benchmark.xml, solidMechanics/DruckerPragerWellbore_base.xml |
| ExampleIsothermalLeakyWell | compositionalMultiphaseFlow/benchmarks/buckleyLeverettProblem/buckleyLeverett_base.xml |
| ExampleMandel | poromechanics/PoroElastic_Mandel_prism6_base_hybrid.xml, poromechanics/PoroElastic_Mandel_smoke_fim.xml |
| ExampleThermalLeakyWell | compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_base.xml |
| ExampleThermoporoelasticConsolidation | thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml, thermoPoromechanics/ThermoPoroElastic_SinglePhase_ThermalGradient_base.xml |
| kgdExperimentValidation | hydraulicFracturing/kgdBase_C3D6_base.xml, hydraulicFracturing/kgdEdgeBased_C3D6_base.xml |
| pknViscosityDominated | hydraulicFracturing/pknViscosityDominated_poroelastic_benchmark.xml, hydraulicFracturing/pknViscosityDominated_poroelastic_base.xml |
| TutorialPoroelasticity | poromechanics/PoroElastic_Terzaghi_base_direct.xml, poromechanics/PoroElastic_Mandel_smoke_fim.xml |
| TutorialSneddon | hydraulicFracturing/hydrofractureSinglePhase2d.xml, lagrangianContactMechanics/TFrac_base.xml |

#### Constitutive Class → Header File Mapping
| Class | Header |
|-------|--------|
| TriaxialDriver | constitutiveDrivers/solid/TriaxialDriver.hpp |
| DruckerPrager | constitutive/solid/DruckerPrager.hpp |
| ExtendedDruckerPrager | constitutive/solid/DruckerPragerExtended.hpp |
| ModifiedCamClay | constitutive/solid/ModifiedCamClay.hpp |
| ElasticIsotropic | constitutive/solid/ElasticIsotropic.hpp |
| ElasticIsotropicPressureDependent | constitutive/solid/ElasticIsotropicPressureDependent.hpp |
| DuvautLionsSolid | constitutive/solid/DuvautLionsSolid.hpp |
| BiotPorosity | constitutive/solid/porosity/BiotPorosity.hpp |
| TableFunction | functions/TableFunction.hpp |
| InternalWellboreGenerator | mesh/generators/InternalWellboreGenerator.hpp |

#### Common Solver Names
| Grep Pattern | Physics Meaning |
|--------------|-----------------|
| SinglePhasePoromechanics | Coupled poroelasticity solver |
| SolidMechanicsLagrangianFEM | Solid mechanics solver |
| SolidMechanicsLagrangianSSLE | Solid mechanics solver (small strain) |
| HydrofractureSolver | Hydraulic fracturing solver |
| SurfaceGenerator | Fracture propagation solver |
| CompositionalMultiphaseFVM | Multiphase flow solver |
| ThermoPoromechanics | Thermal poroelasticity solver |
| MultiphasePoromechanics | Multiphase poroelasticity solver |
| TriaxialDriver | Triaxial test driver |
| InternalWellbore | Wellbore mesh generator |

#### Don't Grep For These
- `class` (too vague)
- `public:` (too vague)
- `catalogName` (use specific class names instead)
- `viewKeyStruct` (rarely productive)
- `Coulomb` (use DruckerPrager instead)
- `StructuredMesh` (use InternalMesh instead)
- `SurfaceElementRegion` (use SurfaceGenerator instead)
- `NewtonRaphson` (use solver-specific names)
- `lineSearchMaxCuts|lineSearchAction` (rarely productive)

### 2. skills/

#### skill-1: drucker-prager-wellbore.md
**When to invoke:** Tasks with "Wellbore" in name (ExampleDPWellbore, ExampleEDPWellbore, AdvancedExampleDeviatedElasticWellbore, AdvancedExampleCasedContactThermoElasticWellbore)

**Canonical XMLs to Read:**
- solidMechanics/ExtendedDruckerPragerWellbore_benchmark.xml
- solidMechanics/ExtendedDruckerPragerWellbore_base.xml
- solidMechanics/DruckerPragerWellbore_benchmark.xml
- solidMechanics/DruckerPragerWellbore_base.xml

**What to copy verbatim:**
- `<InternalWellbore>` section (mesh generation parameters)
- `<SolidMechanicsLagrangianSSLE>` solver section
- `<DruckerPrager>` or `<ExtendedDruckerPrager>` constitutive section
- Boundary conditions (stress, pore pressure)

**What to adapt:**
- Wellbore geometry (radius, length, mesh grading)
- Material properties (bulk modulus, shear modulus, friction angle)
- Loading conditions (far-field stress, mud pressure)
- Output timesteps

#### skill-2: triaxial-driver.md
**When to invoke:** Tasks with "DruckerPrager", "ModifiedCamClay", or "Triaxial" in name (AdvancedExampleDruckerPrager, AdvancedExampleExtendedDruckerPrager, AdvancedExampleModifiedCamClay, AdvancedExampleViscoDruckerPrager)

**Canonical XMLs to Read:**
- triaxialDriver/triaxialDriver_base.xml
- triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
- triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml

**What to copy verbatim:**
- `<TriaxialDriver>` section structure
- `<TableFunction>` definitions for time, axialStrain, radialStress
- `<DruckerPrager>` or `<ModifiedCamClay>` constitutive section

**What to adapt:**
- Table data (time, strain, stress values)
- Material parameters (cohesion, friction angle, hardening)
- Output file names

#### skill-3: hydraulic-fracture.md
**When to invoke:** Tasks with "kgd", "pkn", or "Sneddon" in name (kgdExperimentValidation, pknViscosityDominated, TutorialSneddon)

**Canonical XMLs to Read:**
- hydraulicFracturing/kgdBase_C3D6_base.xml
- hydraulicFracturing/kgdEdgeBased_C3D6_base.xml
- hydraulicFracturing/pknViscosityDominated_poroelastic_benchmark.xml
- hydraulicFracturing/hydrofractureSinglePhase2d.xml

**What to copy verbatim:**
- `<SurfaceGenerator>` section
- `<HydrofractureSolver>` section
- `<FractureManager>` section
- Mesh generation parameters (C3D6 elements)

**What to adapt:**
- Fracture geometry (length, height, spacing)
- Injection rate and fluid properties
- In-situ stress state
- Output frequency

#### skill-4: poroelasticity.md
**When to invoke:** Tasks with "Mandel", "Terzaghi", "Poroelasticity", or "Consolidation" in name (ExampleMandel, ExampleThermoporoelasticConsolidation, TutorialPoroelasticity)

**Canonical XMLs to Read:**
- poromechanics/PoroElastic_Mandel_prism6_base_hybrid.xml
- poromechanics/PoroElastic_Mandel_smoke_fim.xml
- poromechanics/PoroElastic_Terzaghi_base_direct.xml
- thermoPoromechanics/ThermoPoroPlastic_consolidation_base.xml

**What to copy verbatim:**
- `<SinglePhasePoromechanics>` solver section
- `<BiotPorosity>` constitutive section
- Boundary conditions (drainage, stress)
- Mesh structure (prism6 elements)

**What to adapt:**
- Material properties (porosity, permeability, Biot coefficient)
- Loading conditions (confining stress, pore pressure)
- Time stepping parameters
- Output variables

### 3. memory/anti-patterns.md

- Don't grep for `class`; instead grep for specific class names like `DruckerPrager`
- Don't grep for `catalogName`; instead grep for the class name directly
- Don't read schema.xsd for attribute names; instead read the specific header file
- Don't grep for `StructuredMesh`; instead use `InternalMesh` for structured meshes
- Don't grep for `Coulomb`; instead use `DruckerPrager` for plasticity
- Don't grep for `SurfaceElementRegion`; instead use `SurfaceGenerator`
- Don't grep for `NewtonRaphson`; instead use solver-specific names like `SolidMechanicsLagrangianFEM`
- Don't grep for `lineSearchMaxCuts|lineSearchAction`; rarely productive
- Don't read full header files for simple attribute names; use the cheatsheet mapping
- Don't start from scratch; always read the canonical XML first

### 4. Estimated Savings

| Component | Estimated Tool Savings vs F0 | Notes |
|-----------|------------------------------|-------|
| Task→Canonical Mapping | ~15 tools/task | Eliminates searching for correct example files |
| Constitutive→Header Mapping | ~8 tools/task | Eliminates grep-then-read cycle for attribute names |
| Anti-patterns | ~5 tools/task | Eliminates dead-end grep patterns |
| Skill files | ~10 tools/task | Provides structured recipe for common families |
| **Total** | **~38 tools/task** | **Target: 73→35 tools before first Write** |

**Which v3 cells benefit most:**
- F0 (no-plugin): Most benefit, ~50% reduction
- F2 (SR+memory): Moderate benefit, ~30% reduction
- F4 (xmllint+memory): Moderate benefit, ~25% reduction
- F6 (SR+xmllint): Least benefit, ~15% reduction (already efficient)
- SE v3: Minimal benefit, ~10% reduction (already optimized)

**Honest assessment:** The task→canonical mapping and skill files provide the most value. The anti-patterns list is small but helps avoid common traps. The constitutive→header mapping saves ~2-3 grep calls per task. Overall, expect ~35-40 tools saved per task, bringing F0 from 73 to ~33-38 tools before first Write.

---

## Source

- Patterns JSON: `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/patterns.json`
- Mining script: `scripts/trajectory_patterns.py`
- Synthesis script: `scripts/trajectory_patterns_synthesize.py`
- Trajectory diff (sibling analysis): `docs/2026-05-02_F0_vs_SE_trajectory_diff.md`
- Main campaign writeup: `docs/2026-05-02_autonomous-campaign-results.md`

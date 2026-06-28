# Reasoning-Memory Items (distilled from past trajectories)

*Each item is a cross-task rule or anti-pattern. Use these to guide solver selection, schema choices, and attribute usage.*


## 1. Hydrofracture Solver and Permeability Mapping

- **Solver family:** hydrofracture
- **Kind:** structural_pattern (medium abstraction)
- **Description:** Correct solver and constitutive mapping for hydraulic fracturing simulations.
- **Applies when:** Simulating hydraulic fracture propagation, KGD, or radial penny-shaped benchmarks.

Use Hydrofracture as the primary solver. For fracture flow, pair with ParallelPlatesPermeability or CompressibleSolidParallelPlatesPermeability constitutive models. Ensure the fracture surface is defined within a SurfaceGenerator or EmbeddedSurface to manage the discontinuity.

## 2. Poromechanics Solver Coupling

- **Solver family:** poromechanics
- **Kind:** structural_pattern (medium abstraction)
- **Description:** Coupling logic for single-phase flow and solid mechanics.
- **Applies when:** Task requires coupled fluid-solid interaction in porous media.

Use the SinglePhasePoromechanics solver. This solver acts as a wrapper; it requires explicit attributes flowSolverName and solidSolverName that point to a SinglePhaseFVM and SolidMechanicsLagrangianFEM solver respectively.

## 3. Triaxial and Oedometric Driver Setup

- **Solver family:** triaxial
- **Kind:** structural_pattern (medium abstraction)
- **Description:** Configuration for single-element or laboratory-scale geomechanics tests.
- **Applies when:** Simulating strain-controlled or stress-controlled triaxial tests.

Use the TriaxialDriver element. It is compatible with advanced constitutive models like ViscoplasticModifiedCamClay, DruckerPrager, and ViscoExtendedDruckerPrager. It bypasses standard mesh-based boundary conditions for simplified element-level testing.

## 4. Wellbore and Radial Mesh Generation

- **Solver family:** wellbore
- **Kind:** structural_pattern (medium abstraction)
- **Description:** Defining geometry for wellbore casing and cement interfaces.
- **Applies when:** Simulating wellbore integrity, casing, or cement rock interfaces.

Use InternalWellbore for radial mesh generation. Reference cellBlockNames to distinguish between casing, cement, and rock regions. For contact between these interfaces, use SolidMechanicsLagrangeContact.

## 5. Anti-Pattern: Invented Fracture Elements

- **Solver family:** hydrofracture
- **Kind:** anti_pattern (high abstraction)
- **Description:** Avoid hallucinating non-existent fracture control elements.
- **Applies when:** Defining fracture physics or propagation logic.

Do NOT use <FractureModel>, <HydraulicFractureSolver>, or <FracturePropagation>. These are not valid GEOS elements. Use Hydrofracture for the solver and SurfaceGenerator or EmbeddedSurface for the geometry.

## 6. Anti-Pattern: Fluid-Solid Coupling Hallucinations

- **Solver family:** poromechanics
- **Kind:** anti_pattern (high abstraction)
- **Description:** Avoid incorrect coupling element names.
- **Applies when:** Setting up coupled simulations.

Do NOT use <CoupledSolver> or <BiotSolver>. GEOS uses specific coupling wrappers like SinglePhasePoromechanics. Do NOT use <FluidSolidInterface>; use the solver's internal coupling attributes to link flow and solid solvers.

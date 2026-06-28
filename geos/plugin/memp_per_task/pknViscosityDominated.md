## Procedural memory (retrieved by similarity)

Below are workflow notes from past similar GEOS XML authoring tasks. They are *guidance*, not commands — adapt to the current task. Top 3 most similar past tasks (cosine similarity in parentheses):

### Past task: pennyFracViscosityDominated (sim 0.881)

To author a GEOS XML for a viscosity-storage-dominated radial hydraulic fracture, begin by identifying reference files for "penny-shaped toughness-dominated" or "viscosity-dominated poroelastic" benchmarks. These provide the necessary structure for the `Hydrofracture` solver, which couples solid mechanics with fluid flow. Use a `CartesianMesh` with local refinement near the fracture plane and define the fracture geometry using a `SurfaceGenerator` to specify the potential yielding area and the initial seed. For the physics, select the `Hydrofracture` solver and configure the rock as `ElasticIsotropic`. A critical component for this task class is the `ParallelPlatePermeability` model, where the `meanPermCoefficient` must be set (typically 0.8 for finite-volume) to govern fluid conductance.

Common pitfalls include neglecting the `Contact` solver with appropriate penalty stiffness, which prevents element interpenetration, and failing to define a `SourceTerm` for fluid injection. Ensure the `Fracture` constitutive model uses a `Table` for hydraulic aperture to handle sub-resolution flow. When creating multi-file variants (base and benchmark), ensure the benchmark file correctly includes the base file and overrides parameters like `maxStep` or `stopTime` without duplicating the entire mesh or solver definitions. Always verify that the `targetRegions` in the solver match the `ElementRegions` defined in the mesh.


### Past task: pennyFracToughnessDominated (sim 0.836)

To simulate a radial hydraulic fracture in the toughness-dominated regime, begin by identifying reference XMLs for penny-shaped fracture benchmarks or KGD toughness-dominated problems. The workflow requires a two-file structure: a base XML defining materials, constitutive laws, and numerical methods, and a benchmark XML defining the mesh, solvers, and boundary conditions. For the mesh, utilize the `InternalMesh` generator with a structured hexahedral grid, applying refinement near the origin and fracture plane. Use `Box` regions to define the initial fracture area and injection source. 

The physics should employ a `SolidMechanicsLagrangianSSLE` solver coupled with a `Hydrofracture` solver. Crucially, if the rock is impermeable, omit poroelastic coupling and use a standard `ElasticIsotropic` material for the rock and `CompressibleSinglePhaseFluid` for the fracturing fluid. To handle fracture propagation, implement a `SurfaceGenerator` using a node-based `StressIntensityFactor` criterion. A common pitfall is hallucinating schema names for aperture relations; ensure the `TabularFunction` correctly maps mechanical to hydraulic aperture. Additionally, ensure the `SurfaceRegion` includes a `Contact` model with appropriate penalty stiffness and a `ParallelPlatePermeability` model to govern fluid flow within the fracture. Always verify that the benchmark file correctly references the base file to avoid missing variant errors.


### Past task: kgdToughnessDominated (sim 0.830)

To author a GEOS XML for a toughness-dominated KGD hydraulic fracture, begin by referencing existing tutorials for toughness-dominated or viscosity-dominated KGD problems. These provide the necessary structure for coupling solid mechanics with fracture flow. Use a modular approach by splitting the simulation into a base file—containing reusable material properties, solvers, and constitutive models—and a benchmark file for mesh and execution schedules. For the physics, employ a single-phase hydrofracture solver that couples a Lagrangian mechanics solver with a fracture flow solver. Key constitutive elements include an isotropic elastic model for the rock, a compressible single-phase fluid model, and a frictionless contact model to manage fracture face interactions.

To handle the specific requirements of hydraulic fracturing, use a `SurfaceGenerator` to define the separable face blocks along the symmetry plane and initialize the fracture using a `ruptureState` condition within a targeted bounding box. Apply fluid injection via a `SourceFlux` on the same initial fracture region, ensuring mass rates are halved if modeling a half-wing symmetry. A common pitfall is failing to align the `InternalWellbore` or source terms with the refined mesh coordinates. Avoid schema hallucinations by ensuring that propagation criteria, such as stress intensity factors, are correctly nested within the fracture solver settings and that all referenced property names match the constitutive definitions exactly.


---

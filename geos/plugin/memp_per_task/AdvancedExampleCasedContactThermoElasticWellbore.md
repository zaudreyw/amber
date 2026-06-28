## Procedural memory (retrieved by similarity)

Below are workflow notes from past similar GEOS XML authoring tasks. They are *guidance*, not commands — adapt to the current task. Top 3 most similar past tasks (cosine similarity in parentheses):

### Past task: AdvancedExampleCasedElasticWellboreImperfectInterfaces (sim 0.830)

To simulate a cased wellbore with imperfect interfaces, the most effective starting point is the base XML for a cased elastic wellbore, supplemented by Lagrangian contact mechanics examples for single-fracture compression. The core of this workflow involves using a **SolidMechanicsLagrangianSSLE** solver paired with a **SurfaceGenerator** to define the interfaces. You must explicitly define the casing-cement and cement-rock boundaries using hollow cylinder geometries within the **SurfaceGenerator** to identify the correct nodes. To model debonding and frictional behavior, use a **CoulombFriction** constitutive model and initialize the **ruptureState** and **isFaceSeparable** parameters to 1 within the **FieldSpecifications**. 

A common pitfall is failing to include the **SurfaceElementRegion** required for contact mechanics or neglecting to set a placeholder aperture for non-hydraulic simulations. Ensure that the mesh is generated using an **InternalWellbore** mesh generator to correctly capture the radial layers. When creating the multi-variant suite, the benchmark and smoke test files should use the **Included** tag to reference the base XML, overriding only the time-history tables or mesh refinement levels to ensure consistency across the test suite. Avoid schema hallucinations by verifying that contact-specific attributes like **isFaceSeparable** are placed within the correct field specification blocks.


### Past task: AdvancedExampleCasedElasticWellbore (sim 0.751)

To solve wellbore stress problems in GEOS, the most effective workflow begins by identifying reference XMLs for wellbore completion or solid mechanics benchmarks, specifically those utilizing the InternalWellbore mesh generator. This generator is critical for creating concentric cylindrical regions (casing, cement, and rock) and supports the `useCartesianOuterBoundary` attribute to transform the far-field boundary into a square for easier constraint application. For the physics, the `SolidMechanicsLagrangianSSLE` solver is the standard choice for quasi-static linear elastic responses. 

When authoring multi-variant tutorials, structure the files into a base XML containing shared material properties, boundary conditions, and geometry definitions, while using variant files to specify discretization density and solver tolerances. Use a direct solver for coarse "smoke-test" variants to ensure stability, and an iterative GMRES solver for high-resolution benchmarks to manage computational cost. A common pitfall is neglecting the `autoSpaceRadialElems` flag, which is essential for smooth mesh transitions in the rock formation. Ensure that face sets for boundary conditions (e.g., `xneg`, `ypos`, `zneg`) align with the chosen outer boundary geometry to avoid schema errors or unconstrained degrees of freedom.


### Past task: AdvancedExampleWellboreNonLinearThermalDiffusionTemperatureDependentSinglePhaseThermalConductivity (sim 0.710)

To simulate wellbore cooling with non-linear thermal diffusion, begin by referencing the base XML for a **single-phase thermal compressible flow problem** and the specific benchmark for **temperature-dependent single-phase thermal conductivity**. For the domain, use the `InternalWellbore` mesh generator to create a quarter-symmetry cylindrical mesh, carefully defining radial intervals and using the `autoSpacing` attribute for the outermost region to ensure proper resolution. 

The core physics should be handled by the `SinglePhaseThermal` solver coupled with a `SinglePhaseThermalConductivity` constitutive model. To capture the non-linear diffusion, specify the `defaultThermalConductivityComponent` and the `thermalConductivityGradient` within the conductivity model. Ensure the fluid is defined with a `CompressibleFluid` model and the rock uses a `ConstantVolumetricHeatCapacity` model for its internal energy. Use the `TwoPointFluxApproximation` (TPFA) for spatial discretization within the numerical methods section. 

**Common pitfalls** include hallucinating temperature-dependent attribute names; always verify the schema for the exact gradient parameter names. Additionally, ensure that the `InternalWellbore` mesh parameters (azimuthal sweep and radial intervals) align with the symmetry requirements and that boundary conditions are correctly mapped to the generated face sets (e.g., `xNeg` for the inner wellbore face).


---

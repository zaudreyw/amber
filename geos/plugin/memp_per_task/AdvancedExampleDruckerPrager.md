## Procedural memory (retrieved by similarity)

Below are workflow notes from past similar GEOS XML authoring tasks. They are *guidance*, not commands — adapt to the current task. Top 3 most similar past tasks (cosine similarity in parentheses):

### Past task: AdvancedExampleViscoModifiedCamClay (sim 0.833)

To author a GEOS XML for an oedometric compression test using a single-element driver, begin by referencing existing triaxial driver validation studies, specifically those for viscoplasticity or Modified Cam-Clay. The workflow involves a two-file structure: a base XML containing the material library and a driver XML for the specific test. In the base file, define a comprehensive material library using `Constitutive` blocks for Drucker-Prager, Extended Drucker-Prager, and Modified Cam-Clay, along with their viscoplastic counterparts by adding a `relaxationTime` parameter. Use a `TriaxialDriver` solver, which is ideal for single-element constitutive verification as it bypasses complex mesh generation in favor of a single hexahedral element. 

For the benchmark file, use the `Included` tag to pull in the base setup. Configure the `TriaxialDriver` in strain-control mode for oedometric conditions, driving the axial strain via a `TableFunction` while holding radial strains at zero. A common pitfall is schema-hallucinating material parameters; ensure Modified Cam-Clay uses `virginCompressionIndex` and `recompressionIndex` rather than standard elastic moduli. Additionally, ensure the `Events` block correctly triggers the driver and that the `TableFunction` files for time and strain are correctly pathed relative to the execution directory.


### Past task: triaxialDriverExample (sim 0.794)

To author a GEOS XML for a triaxial rock mechanics laboratory experiment, begin by identifying reference files for the **TriaxialDriver** task and the **ExtendedDruckerPrager** constitutive model. The most useful starting points are integration tests for constitutive behavior and validation studies for viscoplasticity or elastoplasticity. Use the `TriaxialDriver` task with `mode="mixedControl"` to simultaneously handle axial strain control and radial stress control. For the material definition, select the `ExtendedDruckerPrager` constitutive element, ensuring you specify the `flowRule="associated"` and define hardening parameters like `hardeningRate` and `frictionAngle` (initial and residual) to capture the elastoplastic response.

When handling loading histories, use `TableFunction` elements with `coordinateFiles` for the time axis and `voxelFile` for the data values (strains or stresses). A common pitfall is schema-hallucinating attribute names; always verify the exact parameter names for the Drucker-Prager model (e.g., `dilationRatio`, `cohesion`) against the GEOS schema or documentation. Ensure the `Solvers` block includes a `SolidMechanicsLagrangianSS` solver to handle the mechanical deformation. Finally, verify that the `Events` block correctly references the `TriaxialDriver` task and that the `Outputs` block is configured to produce the requested ASCII text file.


### Past task: relaxationTest (sim 0.640)

To simulate a stress relaxation test on a viscoplastic rock slab, the most effective starting point is a combination of a **solid mechanics triaxial driver** for the constitutive setup and a **poromechanics or solid mechanics validation test** for the base/benchmark file structure. The `SolidMechanicsLagrangianFEM` solver is the appropriate choice for this displacement-controlled uniaxial loading problem, paired with the `ViscoExtendedDruckerPrager` constitutive model to capture time-dependent relaxation. For the spatial discretization, use the `InternalMesh` generator with `MeshElementGroup` and `MeshBlock` definitions to create the segmented hexahedral grid and element blocks. To handle the specific nodal displacement tracking, define a `Box` geometry to create a named node set (`topPoint`). 

A common pitfall is hallucinating attribute names for the viscoplastic model; ensure parameters like `relaxationTime`, `hardeningRate`, and `dilationRatio` match the schema exactly. Additionally, when splitting into two files, ensure the benchmark file uses the `Included` tag to pull in the base physics and that the `TimeHistory` table for displacement is correctly referenced in the `BoundaryCondition` task. Always verify that the `PackCollection` tasks for stress and displacement correctly target the specific element blocks and node sets defined in the mesh.


---

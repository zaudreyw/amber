### Reasoning Summary
To develop this cheatsheet, I analyzed the provided training trajectories to identify recurring solver configurations and common pitfalls in GEOS XML generation. I synthesized these observations into conditional logic rules that map specific physics requirements (e.g., hydrofracture, poromechanics) to the correct solver hierarchies and element structures. Finally, I identified common hallucinated element names and formulated explicit "do NOT" instructions to prevent the agent from using non-existent vocabulary.

***

# GEOS XML Configuration Cheatsheet

## Solver Routing & Physics Mapping

*   **`hydrofracture`**: When simulating hydraulic fracturing, use the `SolidMechanicsLagrangianSSLE` solver coupled with a `FlowSolver`. Fracture propagation must be managed via the `SurfaceGenerator` and `FractureManager` elements rather than standalone fracture solvers.
*   **`poromechanics` / `multiphase`**: For coupled fluid-solid tasks, utilize the `BiotLinearPoromechanics` or `Poromechanics` solver families. Ensure the `Solvers` block contains a `CompositionalMultiphaseFVM` or `SinglePhaseFVM` child depending on the fluid complexity.
*   **`thermal`**: When temperature effects are specified, the `SolidMechanics` solver must be coupled with a `HeatConduction` solver within a `Group` or `Sequence` solver block.
*   **`contact`**: For tasks involving sliding or non-penetration interfaces, use the `Contact` solver within the `SolidMechanics` hierarchy. Define contact properties in the `ContactManager`.
*   **`triaxial` / `wellbore`**: For geomechanical stability tests, use `SolidMechanicsQuasiStatic` or `SolidMechanicsLagrangianSSLE`. Boundary conditions must be applied via `DirichletBC` and `BoundaryCondition` elements targeting specific `FaceSets`.

## Structural Patterns

*   **Solver Coupling**: Always wrap multiple physics in a `CoupledSolver` or `Group` solver. Use the `timeStepSize` attribute at the top-level solver to control global stepping.
*   **Mesh & Geometry**: Reference `InternalMesh` for simple geometries and `ExternalMesh` for complex imported grids. Ensure `Nodesets` and `Facesets` are explicitly defined for boundary condition application.
*   **Constitutive Models**: Define material behaviors (e.g., `LinearElastic`, `DruckerPrager`) within the `Constitutive` block and reference them by name in the `Region` elements.

## Common Anti-Patterns (Do NOT Use)

*   **DO NOT** use `FractureModel` or `HydraulicFractureSolver`. These are hallucinated. Use `SurfaceGenerator` and `FractureManager` within a coupled mechanics-flow framework.
*   **DO NOT** use `FluidProperties` as a top-level element. Fluid behavior is defined within `Constitutive` or specific `FlowSolver` parameters.
*   **DO NOT** use `GlobalSettings` for physics parameters. Use the specific attributes within the relevant `Solver` or `Material` blocks.
*   **DO NOT** use `BoundaryConditionGroup`. Apply multiple conditions as individual `BoundaryCondition` or `DirichletBC` elements within the `BoundaryConditions` block.
*   **DO NOT** invent element names like `TimeStepper` or `MeshRefiner`. Use the standard `Events` and `Solver` attributes to manage simulation progression.

## Actionable Reminders
*   Verify that every `Region` references a valid `Material` name defined in the `Constitutive` section.
*   Ensure the `Events` block contains a `PeriodicEvent` for `Restart` and `Output` to ensure data persistence.
*   Check that all `FieldSpecification` elements target valid `Object` types (e.g., `Node`, `Element`, `Face`).
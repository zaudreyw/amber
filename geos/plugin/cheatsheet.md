# GEOS XML Authoring Cheatsheet

*Generated 2026-04-20 from 18 train-split trajectories of repo3_eval_run4 (plugin + deepseek-v3.2).*

This cheatsheet distills patterns that helped past CC+plugin runs on GEOS XML tasks. Apply these when relevant; ignore when they conflict with the user's task-specific requirements.

## RAG Usage
*   Use RAG early to read a complete, relevant example file to understand required XML structure and naming conventions for a given physics module.
*   Use RAG to search for specific schema definitions of constitutive models and solvers to confirm required and optional attributes before writing the XML block.
*   Use RAG to locate and examine existing benchmark XML files for similar physics to understand required structures and attribute patterns.

## XML Structure & File Organization
*   When splitting a simulation into reusable files, follow the pattern of a base file for physics, a benchmark file for mesh/geometry, and a main file for solvers/events.
*   When creating a base/variant file pattern, ensure solver definitions that differ between variants are omitted from the base file and placed only in the variant files.
*   When adapting an example that uses XML file inclusion, prefer merging the included content into a single standalone file to avoid hidden dependencies.
*   Structure the benchmark file to include the base file first, then define the mesh, geometry sets, and any case-specific field specifications, maintaining a clear separation of reusable and case-specific parameters.
*   When including a base XML file that defines solvers, augment it in the benchmark file by adding case-specific elements like `Mesh` and `Events` rather than modifying the base.
*   When creating a benchmark file that includes a base XML, avoid duplicating output definitions by overriding specific attributes in the benchmark rather than redefining the entire block.

## Mesh & Geometry
*   When defining a multi-region cylindrical mesh, use the `InternalWellbore` generator with arrays for `radius`, `nr`, and `cellBlockNames` to specify concentric layers.
*   Use the `autoSpaceRadialElems` attribute array (e.g., `"{0,0,1}"`) to enable automatic radial sizing only for specific outer blocks.
*   When the mesh uses `InternalMesh`, rely on its automatic generation of side sets (e.g., "xneg", "xpos") for boundary conditions instead of manually defining them in Geometry.
*   For boundary conditions derived from a mesh generator (like `InternalWellbore`), use the automatically generated node/face set names (e.g., "rneg", "rpos") in `FieldSpecifications` instead of defining custom geometry sets.
*   When using the `InternalWellbore` mesh generator, explicitly set `useCartesianOuterBoundary="0"` if a radial outer boundary is required.
*   For defining a non-uniform mesh with multiple segments, ensure the number of entries in the `bias` attribute matches the number of segments defined in the element count attribute.
*   When defining a multi-block `InternalMesh`, ensure the order of `cellBlockNames` follows the documented k-j-i mapping (fastest to slowest index).
*   When importing a mesh and field data from a VTK file, explicitly specify both `fieldNamesInGEOS` and `fieldsToImport` attributes in the `VTKMesh` block.
*   When mapping external VTK mesh cell blocks to element regions, explicitly define each cell block by its `regionAttribute_elementType` qualifier in the `CellElementRegion`'s `cellBlocks` attribute.

## Solver Configuration
*   When adapting a coupled-physics example for a single-physics simulation, directly use the dedicated single-physics solver instead of trying to strip components from a coupled solver.
*   Before implementing a solver, verify its applicability by cross-referencing the problem description with example use cases.
*   When adapting a solver from a reference example, cross-check the full set of required and optional attributes in the schema, not just the example, to avoid missing defaults that affect convergence.
*   If a user advises against direct parallel solving, configure the `LinearSolverParameters` to use an iterative method like `fgmres` or `gmres` with appropriate tolerance and iteration limits instead of `direct`.
*   When a solver specification requires an adaptive Krylov tolerance, set both `krylovAdaptiveTol="1"` and an appropriate `krylovTol` value in the `LinearSolverParameters`.
*   For time-stepping control, set the `timeStepIncreaseIterLimit` and `timeStepDecreaseIterLimit` attributes in `NonlinearSolverParameters` based on iteration percentages.

## Constitutive Models & Materials
*   When creating a base XML file for multiple constitutive models, define a dummy `ElasticIsotropic` material for the element region's `materialList` to satisfy the solver's requirement for a valid material reference.
*   When a user specifies a temperature-dependent property, verify the schema for the corresponding constitutive model to find the correct derivative attribute and include it.
*   When constitutive models share common parameters (like porosity and permeability), define them once in the base file and reference them in multiple composite models to avoid duplication.
*   When defining a constitutive model that uses external property tables, explicitly create and reference the required `TableFunction` elements in the `Functions` block.
*   Always compute derived material properties (like Young's modulus) from given parameters using standard constitutive relationships to ensure consistency.
*   For temperature-dependent constitutive models, always verify the sign and units of gradient parameters against the reference example to ensure the physical direction of property change is correct.

## Field Specifications & Initial Conditions
*   When defining initial conditions for a constitutive field, set the `objectPath` to the `ElementRegion` (e.g., `"ElementRegions/Omega"`) rather than a specific cell block.
*   When a mesh generator already produces node/face sets (e.g., `"xneg"`, `"rpos"`), use those names directly in `FieldSpecifications` instead of defining custom `Box` geometry sets.

## Common Mistakes to Avoid
*   Do NOT leave an `ElementRegion`'s `materialList` empty; at minimum, reference a placeholder constitutive model.
*   Do NOT redefine entire `<Outputs>` blocks in a benchmark file when the base already defines them — override individual attributes instead.
*   Do NOT infer solver attributes from the example alone; always verify against the schema for required + default values.
*   Do NOT rely on `<Included>` relative paths that cross between the task workspace and `/geos_lib`; prefer self-contained files or merge included content.

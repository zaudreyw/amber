### AdvancedExampleViscoModifiedCamClay  (treesim=0.998)
LESSON 1: When creating a base XML file for multiple constitutive models, define a dummy ElasticIsotropic material for the element region's materialList to satisfy the solver's requirement for a valid material reference.
LESSON 2: Before writing a new XML block, search the schema for the exact element name and its required attributes to ensure correct parameter names and avoid typos.
LESSON 3: When a required file (like a base XML) is referenced in documentation but missing, locate and examine a similar, self-contained example file to infer the correct structure.
LESSON 4: After copying external data files (like table functions), verify they are placed in the correct relative path from the main XML file to ensure the simulation can find them.

### kgdToughnessDominated  (treesim=0.970)
LESSON 1: When adapting an existing example file, systematically compare and modify all parameter values (like viscosity and toughness) and output names (like plotFileRoot) as specified, rather than only checking structural elements.
LESSON 2: After writing a file, immediately read it back to verify the changes were applied correctly and to catch any syntax errors before final submission.
LESSON 3: Use the RAG tool to read a complete, relevant example file early in the process to understand the required XML structure and naming conventions for a given physics module.
LESSON 4: When the task requires a specific numerical method (like Quasi-Newton), confirm its required XML attribute name and value by checking the schema, even if a similar example omits it.

### triaxialDriverExample  (treesim=0.957)
LESSON 1: When adapting an example that uses XML file inclusion, prefer merging the included content into a single standalone file to avoid hidden dependencies and ensure all required blocks are present.
LESSON 2: When a required attribute like `materialList` references a placeholder name (e.g., "dummy"), verify if a corresponding constitutive model exists and explicitly replace the placeholder with the actual model name to ensure consistency.
LESSON 3: After writing a configuration file, immediately read it back to verify its content matches your intended structure and parameter values before finalizing.
LESSON 4: Use schema searches to confirm the purpose and requirements of ambiguous XML elements (like `materialList`) rather than inferring behavior from incomplete examples.

### kgdViscosityDominated  (treesim=0.932)
LESSON 1: When adapting an existing simulation template, systematically compare each required parameter from the specification against the template's values and update them directly, as the agent did by changing gravity, toughness, and mesh biasing.

LESSON 2: For defining a non-uniform mesh with multiple segments, ensure the number of entries in the bias attribute matches the number of segments defined in the element count attribute, as the agent correctly did for the smoke test's yBias.

LESSON 3: When a specification calls for a maximum solver timestep, use the `maxEventDt` attribute within the solver's PeriodicEvent definition, as the agent identified, rather than only setting the initial timestep.

LESSON 4: To output data at every simulation step, define a PeriodicEvent for the output collection with `cycleFrequency="1"` and omit the `timeFrequency` attribute, which the agent deduced from example files.

LESSON 5: Use the RAG tools to search for specific schema definitions of constitutive models and solvers to confirm required and optional attributes, as the agent did for CompressibleSinglePhaseFluid and Hydrofracture, before writing the XML block.

### pennyFracViscosityDominated  (treesim=0.898)
LESSON 1: When adapting an example XML, systematically verify that all constitutive model parameters (like compressibility) are updated to match the new problem's specifications, as the agent correctly did by changing the compressibility value from the example.

LESSON 2: Always cross-reference the schema for solver configurations (like LinearSolverParameters) to set attributes (e.g., solverType, preconditionerType) explicitly when the specification requires a particular iterative method, rather than relying on example defaults.

LESSON 3: Ensure geometry boxes (e.g., for sets like "core" or "source") are defined with extents that align precisely with the generated mesh dimensions and symmetry assumptions, as the agent carefully adjusted box coordinates for a quarter-symmetry domain.

LESSON 4: When a specification provides a non-default coefficient (like meanPermCoefficient), search the schema for the relevant attribute in the appropriate XML block (e.g., TwoPointFluxApproximation) and set it explicitly, instead of omitting it.

LESSON 5: After writing the main XML structure, review the Events block to confirm all required periodic outputs (like restart files) are included, as the agent added a missing restart output event by editing the file.

### AdvancedExampleCasedElasticWellboreImperfectInterfaces  (treesim=0.880)
LESSON 1: When adapting a coupled-physics example for a single-physics simulation, directly use the dedicated single-physics solver (e.g., `SolidMechanicsLagrangeContact`) instead of trying to strip components from a coupled solver (e.g., `SinglePhasePoromechanicsConformingFractures`), as this avoids unnecessary complexity and potential errors.

LESSON 2: When defining a `SurfaceElementRegion` for contact, ensure its `materialList` references the friction law constitutive model (e.g., `"{ frictionLaw }"`) and not the solid material models, as this is required for the contact physics.

LESSON 3: When applying a global parameter like `gravityVector`, define it directly within the `<Solvers>` tag in the base XML to ensure it is consistently applied, rather than relying on benchmark file overrides or omissions.

LESSON 4: For simulations using `SurfaceGenerator`, verify that the `targetRegions` attribute lists the solid cell regions (e.g., `"{ casing, cement, rock }"`) and not the fracture surface region, as the tool generates surfaces at the interfaces between these solid bodies.

### ExampleKirschWellbore  (treesim=0.867)
LESSON 1: When defining initial conditions for a constitutive field, set the `objectPath` to the ElementRegion (e.g., `"ElementRegions/Omega"`) rather than a specific cell block, as the constitutive model is attached at the region level.
LESSON 2: For single-shot data collection outputs, use a `SoloEvent` targeting the output's path (e.g., `"/Outputs/displacementHistory"`) to trigger it exactly once at the desired time.
LESSON 3: When using the `InternalWellbore` mesh generator, explicitly set `useCartesianOuterBoundary="0"` if a radial outer boundary is required, as the default may not match the intended geometry.
LESSON 4: To output solver-calculated fields like stress, use the dedicated solver field name (e.g., `"averageStress"`) in a `PackCollection` task instead of the constitutive model's internal stress field.
LESSON 5: Before finalizing an XML, cross-reference the field names used in `FieldSpecifications` and `PackCollection` against example files to ensure they match the solver's expected field naming convention.

### pennyFracToughnessDominated  (treesim=0.866)
LESSON 1: When adapting an example XML, search for and read the exact benchmark file from the library to copy the correct structure for mesh, geometry, and event scheduling, as the agent did with the KGD toughness example.
LESSON 2: Always compute derived material properties (like Young's modulus) from given parameters using standard constitutive relationships to ensure consistency, as the agent did for the rock model.
LESSON 3: Verify that set names in FieldSpecification blocks (e.g., `{ fracture }`) exactly match the names defined in the Geometry section, as the agent carefully aligned "fracture", "source", and "core".
LESSON 4: Use the schema search tool to confirm attribute names and valid values for key solvers (like `Hydrofracture` and `SolidMechanicsLagrangianFEM`) to avoid syntax errors, as the agent did for `maxNumResolves` and `contactPenaltyStiffness`.
LESSON 5: When the mesh uses `InternalMesh`, rely on its automatic generation of side sets (e.g., "xneg", "xpos") for boundary conditions instead of manually defining them in Geometry, as inferred from the example.

### AdvancedExampleCasedElasticWellbore  (treesim=0.857)
LESSON 1: When defining a multi-region cylindrical mesh, use the `InternalWellbore` generator with arrays for `radius`, `nr`, and `cellBlockNames` to correctly specify concentric layers, as the agent did by referencing a similar cased wellbore example.

LESSON 2: For boundary conditions on a full 360-degree cylindrical mesh, explicitly check for and apply constraints to prevent rigid body rotation, since the agent noted that quarter-symmetry examples used azimuthal plane constraints which may not be sufficient for a full circle.

LESSON 3: When creating a base/variant file pattern, ensure solver definitions (like `LinearSolverParameters`) that differ between variants are omitted from the base file and placed only in the variant files, as the agent correctly removed the Solvers block from the base.

LESSON 4: Use the `autoSpaceRadialElems` attribute array to enable automatic radial sizing only for specific outer blocks, matching the agent's approach of setting it to `{0,0,1}` for the rock formation to smoothly transition to the far-field boundary.

LESSON 5: Validate that field specification object paths (e.g., `objectPath="faceManager"` for traction) and set names (e.g., `rpos`, `zneg`) align with those automatically generated by the mesh generator, as the agent cross-referenced example files to confirm.

### AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity  (treesim=0.851)
LESSON 1: When defining a thermal solver, always set the `temperature` attribute in the solver block to match the initial temperature scale specified in the `FieldSpecifications` to ensure consistent initialization.
LESSON 2: When a user specifies a temperature-dependent property (like volumetric heat capacity), verify the schema for the corresponding constitutive model (e.g., `SolidInternalEnergy`) to find the correct derivative attribute (e.g., `dVolumetricHeatCapacity_dTemperature`) and include it.
LESSON 3: If a user advises against direct parallel solving, configure the `LinearSolverParameters` to use an iterative method like `fgmres` or `gmres` with appropriate tolerance and iteration limits instead of `direct`.
LESSON 4: When constitutive models share common parameters (like porosity and permeability), define them once in the base file and reference them in multiple composite models (e.g., different `CompressibleSolidConstantPermeability` rocks) to avoid duplication.
LESSON 5: For boundary conditions derived from a mesh generator (like `InternalWellbore`), use the automatically generated node/face set names (e.g., "rneg", "rpos") in `FieldSpecifications` instead of defining custom geometry sets.

### TutorialDeadOilBottomLayersSPE10  (treesim=0.844)
LESSON 1: When defining a constitutive model that uses external property tables, explicitly create and reference the required TableFunction elements in the Functions block, as the agent did correctly for oil PVT properties.
LESSON 2: For case-specific boundary conditions like source fluxes or pressure sinks, define them in the benchmark file with specific geometry sets rather than in the base file, to avoid unintended global application.
LESSON 3: When using heterogeneous field data from external files, ensure the TableFunction scaling factor matches the required unit conversion, as the agent verified for permeability (milliDarcy to m²).
LESSON 4: After editing an XML block, verify that all required attributes for the model are present, especially optional attributes that become mandatory when certain features are used, like hydrocarbon PVT table names in DeadOilFluid.
LESSON 5: Structure the benchmark file to include the base file first, then define the mesh, geometry sets, and any case-specific field specifications that reference those sets, maintaining a clear separation of reusable and case-specific parameters.

### TutorialDeadOilEgg  (treesim=0.804)
LESSON 1: When importing a mesh and field data from a VTK file, explicitly specify both `fieldNamesInGEOS` and `fieldsToImport` attributes in the `VTKMesh` block to ensure proper mapping, as the agent correctly did for permeability.

LESSON 2: For well definitions, always match the `wellRegionName` and `wellControlsName` attributes exactly between the `WellElementRegion` and `WellControls` blocks to ensure proper linkage, as the agent ensured when configuring multiple wells.

LESSON 3: When including a base XML file that defines solvers, augment it in the benchmark file by adding case-specific elements like `Mesh` and `Events` rather than modifying the base, following the modular pattern the agent observed in examples.

LESSON 4: For time-stepping control, set the `timeStepIncreaseIterLimit` and `timeStepDecreaseIterLimit` attributes in `NonlinearSolverParameters` based on iteration percentages, as the agent did to implement convergence-based step adjustments.

LESSON 5: Use RAG searches to locate and examine existing benchmark XML files for similar physics to understand required structures and attribute patterns, as the agent did by reading the CO2 injection and Egg example files.

### relaxationTest  (treesim=0.802)
LESSON 1: When defining a multi-block InternalMesh, ensure the order of `cellBlockNames` follows the documented k-j-i mapping (fastest to slowest index) by verifying the pattern in a technical example, as incorrect ordering will misalign regions and constitutive assignments.

LESSON 2: When referencing a specific element subregion in a Task or FieldSpecification, use the full hierarchical path (e.g., `ElementRegions/RegionName/BlockName`) instead of just the region name, because GEOS requires the exact subregion path for correct targeting.

LESSON 3: For traction boundary conditions, prefer the simpler `tractionType="normal"` attribute over manually specifying a direction vector, as it automatically applies the traction in the outward normal direction, reducing the risk of vector orientation errors.

LESSON 4: When configuring XML outputs (VTK, TimeHistory, Restart), explicitly set the `childDirectory` attribute to ensure all output files are written to a consistent, organized location, preventing them from being scattered in the working directory.

LESSON 5: After writing a complex XML structure, systematically review each Event's target paths against the actual names defined in the Outputs and Tasks sections, as mismatches here are a common cause of missing or mis-triggered outputs.

### AdvancedExampleDeviatedPoroElasticWellbore  (treesim=0.756)
LESSON 1: When referencing mesh-generated cell blocks in field specifications, explicitly set the `cellBlockNames` attribute in the mesh generator and use the exact same block name (e.g., "cb1") in the `objectPath` to ensure consistent targeting, as the agent corrected mismatched default and explicit references.

LESSON 2: For boundary conditions on curved surfaces like cylindrical outer boundaries, use the `direction` attribute with a vector (e.g., radial normal) in FieldSpecifications instead of Cartesian component constraints, as the agent initially struggled with applying normal displacement on "rpos".

LESSON 3: When creating a benchmark file that includes a base XML, avoid duplicating output definitions (e.g., Silo) by overriding specific attributes like `parallelThreads` in the benchmark rather than redefining the entire block, which the agent corrected by removing the Silo block from the base file.

LESSON 4: To enforce a constant timestep for a coupled solver, apply the `forceDt` attribute directly on the PeriodicEvent targeting that solver, as the agent identified from example files instead of relying on solver-internal settings.

LESSON 5: Always verify that material property units in constitutive models match the expected SI base units (e.g., converting GPa to Pa) by cross-referencing example files, as the agent did for bulk and shear moduli.

### TutorialCO2FieldCase  (treesim=0.735)
LESSON 1: When defining a data collection for output, place the `PackCollection` element within the `Tasks` block and reference it with an absolute path (e.g., `/Tasks/collectionName`) in the `TimeHistory` output, as the agent corrected after finding examples showing this structure.

LESSON 2: When adapting an example XML, verify that all referenced file paths (e.g., for `TableFunction` external data) match the expected directory structure and naming conventions used in the task specification to avoid runtime file-not-found errors.

LESSON 3: For solver parameters like maximum time step size, explicitly add attributes such as `maxDt` to the solver element when specified, as the agent did after noting the requirement, rather than relying on defaults.

LESSON 4: When constructing a mesh with multiple regions (e.g., reservoir and well), ensure the region names and block references (like `cellBlockNames`) are consistent across the `Mesh` and `ElementRegions` sections, as the agent checked for alignment.

LESSON 5: Use schema searches (e.g., `search_schema`) to confirm attribute names and allowed values for elements like `TableFunction` (e.g., `voxelFile`, `coordinateFiles`) before writing them, reducing syntax errors.

### faultVerification  (treesim=0.712)
LESSON 1: When mapping external VTK mesh cell blocks to element regions, explicitly define each cell block by its regionAttribute_elementType qualifier in the CellElementRegion's cellBlocks attribute, as the agent correctly did for "97_hexahedra" and "96_hexahedra", to ensure precise material assignment and field application.

LESSON 2: For applying initial conditions or constraints to specific mesh cell blocks, set the FieldSpecification's objectPath to "ElementRegions/<RegionName>/<CellBlockName>" (e.g., "ElementRegions/LeftCompartment/97_hexahedra") instead of using generic names like "cb", as the agent corrected after initial uncertainty.

LESSON 3: When a solver specification requires an adaptive Krylov tolerance, set both `krylovAdaptiveTol="1"` and an appropriate `krylovTol` value in the LinearSolverParameters, as the agent did after consulting the schema, rather than interpreting "adaptive Krylov tolerance of 1" as only the tolerance value.

LESSON 4: To define a compressive traction boundary condition, use a negative scale value in the FieldSpecification (e.g., scale="-7e7") with fieldName="traction" and component="0", mirroring the agent's correct implementation for the upper boundary.

LESSON 5: Before writing the final XML, verify that all required sections (Parameters, Mesh, Constitutive, ElementRegions, NumericalMethods, Solvers, FieldSpecifications, Events, Outputs) are present, as the agent's high scores in Solvers and NumericalMethods indicate thorough structural compliance.

### ExampleTFrac  (treesim=0.596)
LESSON 1: When splitting a simulation into reusable files, follow the established pattern of a base file for physics, a benchmark file for mesh/geometry, and a main file for solvers/events, as the agent correctly deduced from the example structure.

LESSON 2: Before implementing a solver, verify its applicability by cross-referencing the problem description with example use cases, as the agent did by comparing "Lagrangian contact solver" against both `SolidMechanicsLagrangeContact` and `SolidMechanicsEmbeddedFractures` examples.

LESSON 3: When defining field specifications for tensor components, confirm the component indexing convention by checking example files, as the agent did for the `rock_stress` field to ensure correct directional stress application.

LESSON 4: Use the RAG tools to search for exact attribute names and usage in examples before writing XML blocks, as the agent did for `initialRockToughness` and `isFaceSeparable` to avoid schema errors.

LESSON 5: For time-dependent functions, create the supporting CSV files (coordinates and values) in the same directory as the XML and ensure the file paths are correctly referenced, as the agent did for the pressure ramp TableFunction.

### AdvancedExampleWellboreNonLinearThermalDiffusionTemperatureDependentSinglePhaseThermalConductivity  (treesim=0.537)
LESSON 1: When defining a multi-block radial mesh with `InternalWellbore`, explicitly set `cellBlockNames` to unique identifiers for each block and reference them in the region's `cellBlocks` list, rather than relying on `"{ * }"`, to ensure correct material assignment across all intervals.

LESSON 2: For temperature-dependent constitutive models like `SinglePhaseThermalConductivity`, always verify the sign and units of gradient parameters (e.g., `thermalConductivityGradientComponents`) against the reference example to ensure the physical direction of property change is correct.

LESSON 3: When adapting a solver from a reference example (e.g., adding `isThermal="1"` to `SinglePhaseFVM`), cross-check the full set of required and optional attributes in the schema, not just the example, to avoid missing defaults that affect convergence.

LESSON 4: Use the `autoSpaceRadialElems` attribute in `InternalWellbore` with explicit per-block values (like `"{ 0, 0, 1 }"`) as seen in benchmark files, rather than a single global value, to control radial spacing independently for manual and auto-spaced intervals.


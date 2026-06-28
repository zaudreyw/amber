## Thermal Poromechanics (ThermoPoroElastic Consolidation)

- **Solver**: `<SinglePhasePoromechanics>` with `thermalFluxFlag="1"` and `discretization="fe1"` (or `sequential` for benchmarking). Also need `maxTime`, `timeStep` parameters.
- **Mesh**: `InternalMesh` – often a simple block `{1,1,1}` with `xCoords{0,1000}`, `yCoords{0,200}`, `zCoords{0,200}` for 2D plane strain.
- **Constitutive**: `<ElasticIsotropic>` with `defaultBulkModulus`, `defaultShearModulus`, `defaultThermalExpansionCoefficient`. Plus `<BiotPorosity>` and `<ConstantPermeability>`.
- **Fluid**: `<CompressibleSinglePhaseFluid>` with reference pressure, density, viscosity, and thermal expansion.
- **Initial conditions**: `pressure`, `temperature`, `totalDisplacement` fields via `<FieldSpecifications>`. Often linear temperature gradient.
- **Boundary conditions**: `Dirichlet` for temperature on top/bottom, `Dirichlet` for displacement on sides, `Traction` for mechanical load.
- **Output**: `<HistoryCollection>` for displacement at nodes, pressure/temperature at cell centers. `<VTKCollection>` for field outputs.
- **Base files**: Look for `ThermoPoroElastic_*<file>` or `<file>` in `thermoPoromechanics/`. They include the solver, output, and sometimes tables.

## Poroelastic Consolidation (Terzaghi / Mandel)

- **Solver**: `<SinglePhasePoromechanics>` – coupling `fullyImplicit` (preferred) or `sequential`.
- **Base files**: `PoroElastic_Terzaghi_*` and `PoroElastic_Mandel_*` in `poromechanics/`. The `*<file>` files are good starting points.
- **Mesh**: `InternalMesh` – 1D (Terzaghi) or 2D plane strain (Mandel).
- **Constitutive**: `<ElasticIsotropic>`, `<BiotPorosity>`, `<CompressibleSinglePhaseFluid>`.
- **BCs**: Typical consolidation BCs (drained top, impermeable sides, mechanical load).
- **Tables**: Some base files reference external table files for loading curves – copy them.

## Hydraulic Fracturing – Sneddon (EFEM)

- **Solvers**: Use `<ContactMechanics>` or `<SolidMechanicsLagrangianFEM>` with `<SurfaceGenerator>` or `<EmbeddedSurfaceGenerator>` for fracture.
- **Base files**: Look in `efemFractureMechanics/`, `lagrangianContactMechanics/`, `hydraulicFracturing/` for files containing `Sneddon`, `kgd`, `pkn`.
- **Mesh**: `InternalMesh` – often a simple domain with a predefined fracture plane (e.g., `xCoords{0,1000}`, `yCoords{0,1000}`, `zCoords{-250,250}`).
- **Fracture initialization**: `<SurfaceElementRegion>` with `faceBlock` and `subRegion`. Or use `<EmbeddedSurfaceGenerator>` with `nodeBasedSIF`.
- **BCs**: `Dirichlet` for far-field stresses (sigma_xx, sigma_yy, sigma_zz) via `initialStress`. Traction on fracture faces if fluid-driven.
- **Output**: `<HistoryCollection>` for `displacementJump`, `traction`. `<VTKCollection>` for whole domain.
- **Dependencies**: Copy any `.geos` table files (e.g., loading curves) from the base file directory.

## Hydraulic Fracturing – KGD / PKN (HydrofractureSolver)

- **Solver**: `<HydrofractureSolver>` (coupled solid mechanics + fluid flow in fracture). Uses `<SinglePhasePoromechanics>` + `<SurfaceGenerator>` under the hood.
- **Base files**: `<file>`, `<file>`, `<file>`, etc.
- **Mesh**: `InternalMesh` – often 3D block with small thickness for 2D plane strain.
- **Fluid**: `<CompressibleSinglePhaseFluid>` or incompressible; fracture fluid viscosity set via `<FractureFluid>`.
- **Injection**: `<WellElement>` or `<FluxBoundaryCondition>` at injection point.
- **Fracture toughness**: Set via `rockToughness` in `SurfaceGenerator` or `initialRockToughness`.
- **Dependencies**: Copy all files from `hydraulicFracturing/` directory that are referenced (e.g., `*.csv`, `*.geos`). Many base files include other XMLs – copy them too.

## General Pitfalls (expanded)

- **Missing table files**: After copying a base file, always run `grep -r 'tables/\|\.geos\|\.txt\|\.csv' /workspace/inputs/` to list all external references, then ensure each file exists.
- **Base file includes other files**: If `<Included>` is used in the base file, you must copy those included files as well. They are usually in the same directory.
- **Wrong solver name**: The solver `name` attribute must match the `objectPath` in `HistoryCollection`. Check the base file.
- **Unaltered constitutive parameters**: Some base files have placeholder values. Override them by redefining the `<Constitutive>` block after the `<Included>` line.
- **Not verifying final file list**: Run `ls -R /workspace/inputs/` after copying and writing to confirm all files are present.

## Leaky Well – Compositional Multiphase Flow

- **Solver**: `<CompositionalMultiphaseFlow>` with `discretization="fe1"` or `"tpfa"`.
- **Fluid model**: Often `<CO2BrinePhillipsFluid>` with parameters like `phasePermeabilityThreshold`, `inputTemperature`, `salinity`.
- **Relative permeability**: Use `<TableRelativePermeability>` with tables from `relPerm_water.txt`, `relPerm_gas.txt` (single column of floats).
- **Capillary pressure**: Use `<TableCapillaryPressure>` with `capPres_water.txt` (or skip if zero).
- **Mesh**: `InternalMesh` is common – create a block `{1,100,100}` with `xCoords{0,1}`, `yCoords{0,200,400}`, `zCoords{0,200,400}`.
- **Initial conditions**: Set `pressure` and `globalCompFraction` fields via `FieldSpecifications` – often a hydrostatic gradient.
- **Boundary conditions**: Use `Dirichlet` for pressure at far‑field boundaries, `FluxBoundaryCondition` (e.g., `SourceFlux`) for injection well.
- **Output**: `<VTKCollection>` every N timesteps, `<TimeHistoryCollection>` for specific field points.

## Mandel / Consolidation – Single‑Phase Poromechanics

- **Solver**: `<SinglePhasePoromechanics>` – choose coupling `fullyImplicit` (preferred) or `sequential`.
- **Mesh**: `InternalMesh` – a rectangle `{1,1,1}` elements with `xCoords{0,1000}, yCoords{0,200}` for 2D plane strain.
- **Constitutive**: `<ElasticIsotropic>` with `defaultBulkModulus`, `defaultShearModulus`, plus `<BiotPorosity>` for poroelasticity.
- **Permeability**: `<ConstantPermeability>` with `permeabilityComponents`.
- **BCs**: Apply `totalDisplacement` on edges (e.g., roller constraints), `pressure` on top/bottom, `Traction` for external load.
- **Initial**: Hydrostatic pressure gradient, zero displacement.
- **Output**: `<HistoryCollection>` on specific nodes for displacement, on cell elements for pressure.

## Buckley‑Leverett – Immiscible Two‑Phase Flow

- **Solver**: `<ImmiscibleTwoPhase>` with `discretization="tpfa"`.
- **Fluid models**: `<CO2BrinePhillipsFluid>` or `PVDG`/`PVTW` tables. Often use `<BrooksCoreyRelativePermeability>` with `phaseMinVolFraction`, `phaseRelPermExp`, `phaseRelPermMax`, `phaseCapPressureExponentInv`.
- **Mesh**: `InternalMesh` – 1D with many elements along x (`{1,1000,1}`).
- **BCs**: `Dirichlet` on left face for saturation (e.g., `globalCompFraction = {1,0}` for CO2 injection) and pressure; `Dirichlet` on right face for pressure.
- **Initial**: Uniform pressure and saturation (`globalCompFraction = {0,1}`).
- **Tables**: If using PVDG/PVTW, copy `pvdg.txt` and `pvtw.txt` from the benchmark directory.

## Wellbore with Plasticity – InternalWellbore Mesh

- **Mesh node**: `<InternalWellbore>` parameters: `radius`, `thickness`, `length`, `nr`, `nt`, `nz`, `rockRadius`, `cementThickness`, `casingThickness`.
- **Regions**: Auto‑named `rock`, `cement`, `casing`. Assign materials via `<ElementRegions>` referencing those region names.
- **Constitutive model**: For rock, use a plastic model like `<DruckerPrager>` or `<ExtendedDruckerPrager>` with all required parameters (`defaultFrictionAngle`, `defaultDilationAngle`, `hardeningRate`). Also define elastic material for casing.
- **BCs**: `Traction` on the inner wellbore wall (e.g., mud pressure). `FieldSpecifications` for far‑field stresses (e.g., `initialStress` with components).
- **Output**: `HistoryCollection` for `totalDisplacement` on inner wall, `VTKCollection` for domain.

## General Pitfalls

- **Missing table files**: Always copy `.geos`, `.txt`, `.csv` files referenced by `<TableFunction>` or `<Included>` – place them in the same relative subdirectory.
- **Wrong solver name**: The solver `name` attribute must match the `objectPath` in `HistoryCollection`. Check base file for exact names.
- **Unset required parameters**: For DruckerPrager, provide `hardeningRate`; for ModifiedCamClay, `cslSlope` and `recompressionIndex`. Use schema or base files to check.
- **Viscoplasticity**: Non‑viscous models (DruckerPrager) do not have `relaxationTime`. Use `ViscoExtendedDruckerPrager` or wrap with `<DuvautLions>`.
- **Overwriting base includes**: If you include a base file that itself includes other files, you must also include those files – copy them into your workspace.
- **Not running final check**: After writing all files, run `ls /workspace/inputs -R` and verify no missing includes.

## How to Find Base Files Efficiently

- For solid mechanics: `/geos_lib/inputFiles/solidMechanics/`
- For poromechanics: `/geos_lib/inputFiles/poromechanics/`
- For compositional multiphase flow: `/geos_lib/inputFiles/compositionalMultiphaseFlow/`
- For immiscible: `/geos_lib/inputFiles/immiscibleMultiphaseFlow/`
- Look for `*<file>`, `*<file>`, or `*<file>` – these are complete templates.
- Use `Grep` to find files containing the solver name (e.g., `SinglePhasePoromechanics`).

# GEOS XML Configuration Cheatsheet

## Solver Selection & Physics Routing

| Physics Family | Primary Solver | Key Supporting Elements |
| :--- | :--- | :--- |
| **Hydrofracture** | `Hydrofracture` | `SurfaceGenerator`, `ParallelPlatesPermeability`, `CompressibleSolidParallelPlatesPermeability` |
| **Solid Mechanics** | `SolidMechanicsLagrangianFEM` | `ElasticIsotropic`, `DruckerPrager`, `ViscoExtendedDruckerPrager` |
| **Poromechanics** | `SinglePhasePoromechanics` | Requires `flowSolverName` and `solidSolverName` attributes. |
| **Thermal Flow** | `SinglePhaseThermalFVM` | `SinglePhaseThermalConductivity`, `SolidInternalEnergy` |
| **Multiphase Flow** | `CompositionalMultiphaseFVM` | `DeadOilFluid`, `CompositionalMultiphaseWell`, `SourceFlux` |
| **Contact/Interfaces**| `SolidMechanicsLagrangeContact`| `SurfaceGenerator`, `EmbeddedSurface` |
| **Single Element** | `TriaxialDriver` | Used for constitutive model validation (e.g., `ViscoplasticModifiedCamClay`). |

## Mesh & Geometry Patterns
- **Internal Generation**: Use `InternalMesh` for Cartesian grids (attributes: `xCoords`, `yCoords`, `zCoords`, `nx`, `ny`, `nz`).
- **Wellbore Geometry**: Use `InternalWellbore` for radial/cylindrical meshes; specify `cellBlockNames` to map regions.
- **External Meshes**: Use `VTKMesh` for complex geometries.
- **Fracture Surfaces**: Define regions using `SurfaceGenerator` or `EmbeddedSurface` rather than manual element lists.

## Constitutive Model Mapping
- **Rock Mechanics**: `ExtendedDruckerPrager` or `ViscoDruckerPrager` for pressure-dependent plasticity.
- **Fluid Flow**: `CompressibleSinglePhaseFluid` for basic hydro; `DeadOilFluid` for black-oil reservoir tasks.
- **Permeability**: Use `ParallelPlatesPermeability` for fracture flow; use `TableFunction` with `voxelFile` for heterogeneous spatial permeability.

## Common Anti-Patterns (Do NOT Use)
- **DO NOT** use `<FractureModel>` or `<HydraulicFractureSolver>` — these are hallucinated. Use `Hydrofracture` and `SurfaceGenerator`.
- **DO NOT** use `<ContactSolver>` — use `SolidMechanicsLagrangeContact`.
- **DO NOT** use `<FluidProperties>` as a wrapper — fluid models like `DeadOilFluid` or `CompressibleSinglePhaseFluid` are defined directly within the constitutive section.
- **DO NOT** use `<BoundaryCondition>` as a generic tag — use specific types like `FieldSpecification` with a `traction` or `displacement` component.
- **DO NOT** invent attribute names like `toughness` directly on the solver; verify specific benchmark attributes like `kgdToughnessDominated` via RAG.

## Actionable Tips
- **Coupling**: When using `SinglePhasePoromechanics`, ensure both a flow solver and a solid solver are defined and referenced by name.
- **Interpolation**: For voxel-based data, `TableFunction` requires both `voxelFile` and `coordinateFile`.
- **Boundary Conditions**: Always verify if a `SourceFlux` requires a `scale` attribute or a `TableFunction` for time-dependent injection.
## TriaxialDriver Patterns

- **Base file**: starts with `<file>` – defines solver, output, table functions. Override `<Constitutive>` with desired model.
- **Table files**: three `.geos` files: `time.geos`, `axialStrain.geos`, `radialStress.geos`. Each is one column of floats. Place in `tables/` subdirectory. Include them with `<Included>`. Write them to workspace exactly as in source.
- **Viscoplasticity**: Append `<DuvautLions>` wrapper inside the solid model, with parameters: `relaxationTime`, `solidModelName` etc. Or use visco‑specific model (e.g., `ViscoDruckerPrager`). The `relaxationTime` must be provided (default may not exist). See source header for defaults.
- **Output**: Must define `<HistoryCollection>` with `objectPath="TriaxialDriver"` and `fieldName` like `stress`, `strain`. Use `setNames` to select specific components.
- **Common mistakes**: Forgetting to set `defaultFrictionAngle`, `defaultDilationAngle`, `hardeningRate` for DruckerPrager. For ModifiedCamClay, provide `cslSlope`, `recompressionIndex`, `criticalStateLine`.

## Wellbore / InternalWellbore

- Mesh node: `<InternalWellbore name="mesh" ...>`
  - Parameters: `radius`, `thickness`, `length`, `nr`, `nt`, `nz`, `rockRadius`, `cementThickness`, `casingThickness`.
  - Regions are auto‑named `rock`, `cement`, `casing`. Assign materials in `<ElementRegions>`.
- For cased wellbore with imperfect interfaces: need `SurfaceGenerator` and contact mechanics. Search for `<file>` as starting point.
- Loading: often apply internal pressure and far‑field stresses via `FieldSpecifications`. Use `Traction` boundary condition for pressure on wellbore wall.

## HistoryCollection Output

- Use `<HistoryCollection>` block with `objectPath` set to the solver name or a mesh object.
- Common fields: `totalDisplacement`, `totalMeanStress`, `porosity`, `pressure`, `temperature`.
- For TriaxialDriver, `objectPath="TriaxialDriver"` and `fieldName` must match available internal fields (see source or base file).

## Viscoplastic Pitfalls

- Non‑viscous models (DruckerPrager, ExtendedDruckerPrager) do not have `relaxationTime` by default. Use `ViscoExtendedDruckerPrager` or wrap with `<DuvautLions>`.
- Check base files in `inputFiles/solidMechanics/<file>` for reference.
- Table time steps must match relaxation time scale to see viscoplastic effects.

## General Tips

- Always include base file (`<Included>`) and override only necessary sections to avoid missing required defaults.
- When copying table files, ensure exact format (single column, no header). Use `Bash` to `cp` from source to workspace.
- After writing XML, run `find /workspace/inputs -type f | sort` to verify all files present.
- If task asks for specific output format (e.g., `.dat` file), check for post‑processing scripts in `/geos_lib/src/docs/sphinx/` rst files.

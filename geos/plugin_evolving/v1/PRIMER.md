# GEOS – XML Authoring Guide

GEOS is an open-source multiphysics simulator. Input files are XML. The source repository is at `/geos_lib/`. Write final XML to `/workspace/inputs/`.

## Two Major Simulation Styles

1. **Full mesh-based simulations** (most problems)
   - Mesh defined under `<Mesh>` – InternalMesh, InternalWellbore, read from file, etc.
   - Solvers like `SolidMechanicsLagrangianFEM`, `SinglePhasePoromechanics`, `ThermalPoromechanics`, etc.
   - Output via `HistoryCollection` or `VTKCollection`.

2. **Constitutive driver simulations** (e.g., TriaxialDriver)
   - No mesh – single material point under user‑defined loading paths.
   - Use `<TriaxialDriver>` solver, `<TableFunction>` for loading curves (time, axialStrain, radialStress).
   - Table data files (`.geos` plain text) must be included via `<Included>`. Output via `<HistoryCollection>`.

## Common Problem Classes

- **Triaxial tests**: DruckerPrager, ModifiedCamClay, ExtendedDruckerPrager, viscoplastic variants. Include `relaxationTime` for Duvaut‑Lions viscoplasticity.
- **Wellbore problems**: Use `InternalWellbore` mesh generator to create concentric cylinders (rock, cement, casing). Assign different constitutive models per region. For imperfect interfaces, add `SurfaceGenerator` with contact mechanics.
- **Contact / fracture**: Use `SurfaceGenerator` to create discrete fracture representation; specify contact law (Coulomb, etc.) under `<Contact>`.
- **Poromechanics / thermal**: Use appropriate solver (single‑phase, multiphase, thermal) and couple with constitutive models.

## XML Structure Hint

Near the top, include `<Included>` for base files (from `/geos_lib/inputFiles/`). Then override or add:
- `<Mesh>`
- `<Solvers>` (list of solver objects)
- `<Constitutive>` (material definitions)
- `<FieldSpecifications>` (BCs, initial conditions)
- `<Outputs>` (collections)

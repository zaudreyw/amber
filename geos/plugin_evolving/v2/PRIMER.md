# GEOS – XML Authoring Guide

GEOS is an open‑source multiphysics simulator. Input files are XML. The source repository is at `/geos_lib/`. Write final XML to `/workspace/inputs/`.

## Two Major Simulation Styles

1. **Full mesh‑based simulations** — most problems (wellbore, consolidation, multiphase flow)
   - Mesh defined under `<Mesh>` – InternalMesh, InternalWellbore, read from file, etc.
   - Solvers: `SolidMechanicsLagrangianFEM`, `SinglePhasePoromechanics`, `CompositionalMultiphaseFlow`, `ImmiscibleTwoPhase`, etc.
   - Output via `HistoryCollection` or `VTKCollection`.

2. **Constitutive driver simulations** (e.g., TriaxialDriver)
   - No mesh – single material point under user‑defined loading paths.
   - Use `<TriaxialDriver>` solver, `<TableFunction>` for loading curves (time, axialStrain, radialStress).

## Workflow for Every New Input File

1. **Identify problem class** — Is it solid mechanics? Poromechanics? Compositional multiphase flow? Immiscible two‑phase? Check the task description for keywords.
2. **Locate the right base file** — Always look in `/geos_lib/inputFiles/` under the relevant subdirectory (e.g., `solidMechanics/`, `poromechanics/`, `compositionalMultiphaseFlow/benchmarks/`). Prefer files named `*<file>` or `*<file>`; these contain complete solver/output/table skeletons.
3. **Copy all dependencies** — Base files often include table data (`.geos`, `.txt`), other XML includes, or fluid property files. Copy them verbatim to the same relative path in `/workspace/inputs/`.
4. **Override only what is needed** — The main XML should `<Included>` the base file, then override the `<Constitutive>`, `<Mesh>`, `<FieldSpecifications>`, or solver parameters as required.
5. **Verify completeness** — Run `find /workspace/inputs -type f | sort` to ensure all referenced files exist.

## Common Problem Classes and Base File Hints

- **Wellbore with plasticity** – See `<file>` or `<file>` under `solidMechanics/`. They use `InternalWellbore` mesh and include traction BCs.
- **Leaky well (isothermal/thermal)** – Look in `compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/` or `isothermalLeakyWell/`. They include fluid tables and relative permeability files.
- **Mandel consolidation** – See `PoroElastic_*` files under `poromechanics/`. Use `SinglePhasePoromechanics` solver.
- **Buckley‑Leverett** – See `immiscibleMultiphaseFlow/` or `immiscibleTwoPhase_BuckleyLeverett/`. PVDG/PVTW tables are needed.

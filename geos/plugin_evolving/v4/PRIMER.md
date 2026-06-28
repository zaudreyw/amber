# GEOS – XML Authoring Guide

GEOS is an open‑source multiphysics simulator. Input files are XML. The source repository is at `/geos_lib/`. Write final XML to `/workspace/inputs/`.

## Two Major Simulation Styles

1. **Full mesh‑based simulations** — most problems (wellbore, consolidation, multiphase flow, hydraulic fracturing)
   - Mesh defined under `<Mesh>` – InternalMesh, InternalWellbore, read from file, etc.
   - Solvers: `SolidMechanicsLagrangianFEM`, `SinglePhasePoromechanics`, `CompositionalMultiphaseFlow`, `ImmiscibleTwoPhase`, `HydrofractureSolver`, etc.
   - Output via `HistoryCollection` or `VTKCollection`.

2. **Constitutive driver simulations** (e.g., TriaxialDriver)
   - No mesh – single material point under user‑defined loading paths.
   - Use `<TriaxialDriver>` solver, `<TableFunction>` for loading curves.

## Workflow for Every New Input File

1. **Identify problem class** – Solid mechanics? Poromechanics? Compositional multiphase flow? Hydraulic fracturing? Check task keywords.
2. **Locate the right base file** – Always look in `/geos_lib/inputFiles/` under the relevant subdirectory. Search for `*<file>` or `*_smoke*.xml` files that contain the target solver.
3. **Copy ALL files from the base file's directory** – Base files often include table files (`.geos`, `.txt`, `.csv`) and other XMLs. Use `ls` to list the directory, then copy every file to the same relative path in `/workspace/inputs/`. Preserve subdirectory structure (e.g., `tables/`).
4. **Use `<Included>` to reference the base file** – Your main XML should `<Included>` the base file, then override blocks like `<Constitutive>`, `<Mesh>`, `<FieldSpecifications>` as needed. Do NOT duplicate the entire base content.
5. **Verify completeness** – Run `find /workspace/inputs -type f | sort` to ensure all referenced files exist. Also check that `<Included>` paths match exactly.

## Common Problem Classes and Base File Hints

- **Thermal poromechanics** – Look in `thermoPoromechanics/` for `ThermoPoroElastic_*<file>`. Use `<SinglePhasePoromechanics>` with `thermalFluxFlag="1"`.
- **Poroelastic consolidation (Terzaghi, Mandel)** – Files in `poromechanics/` named `PoroElastic_Terzaghi_*` and `PoroElastic_Mandel_*`.
- **Sneddon fracture (EFEM)** – Files in `efemFractureMechanics/` or `lagrangianContactMechanics/` with `Sneddon_*<file>`.
- **KGD / PKN hydraulic fracturing** – Files in `hydraulicFracturing/` named `kgd*<file>` or `pkn*<file>`. Often use `<SurfaceGenerator>` or `<HydrofractureSolver>`.
- **Wellbore with plasticity** – See `solidMechanics/` or `wellbore/` with `InternalWellbore` mesh.
- **Leaky well (isothermal/thermal)** – Files in `compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/` or `isothermalLeakyWell/`.

## Critical: Copy Dependencies Immediately

After selecting a base file, ALWAYS run:
```
ls <base_file_directory>
```
Then copy every file that is not a `.xml` that also has a corresponding include (e.g., `.geos`, `.txt`, `.csv`) OR if the base file `<Include>`s other XMLs, copy those too. Place all copied files in the same relative subdirectory under `/workspace/inputs/`.

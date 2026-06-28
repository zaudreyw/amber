# GEOS Primer (minimal, vanilla-CC-compatible)

GEOS (Geomechanics and EOS Simulator) is an open-source multiphysics simulator. Tasks require authoring an XML input file (or a small set, sometimes with `<Included>` cross-file references) that specifies the simulation. All values are in SI units.

## Where things live (inside the container)

- `/geos_lib/inputFiles/` — validated example XML files, organized by physics family (e.g., `wellbore/`, `hydraulicFracturing/`, `triaxialDriver/`, `compositionalMultiphaseFlow/`, `thermoPoromechanics/`). Treat these as the authoritative reference.
- `/geos_lib/src/docs/` — GEOS documentation (Sphinx RSTs). Includes tutorials, schema definitions, and the Datastructure Index.
- `/workspace/inputs/` — where you must write the final XML(s). Your output goes here.

## Top-level XML skeleton
```
<Problem>
  <Solvers>...</Solvers>
  <Mesh>...</Mesh>              <!-- or VTKMesh, InternalWellbore, InternalMesh -->
  <Geometry>...</Geometry>      <!-- Box, Cylinder, etc. for fieldspec regions -->
  <Events>...</Events>
  <NumericalMethods>...</NumericalMethods>
  <ElementRegions>...</ElementRegions>
  <Constitutive>...</Constitutive>
  <FieldSpecifications>...</FieldSpecifications>
  <Functions>...</Functions>    <!-- optional: TableFunction for time/space-varying data -->
  <Outputs>...</Outputs>
  <Tasks>...</Tasks>            <!-- optional -->
</Problem>
```

## Recommended workflow
1. Find a similar existing example using `Glob` / `Grep` / `Read` against `/geos_lib/inputFiles/`. Search by physics keyword (e.g. `Glob` for `*Wellbore*.xml`; `Grep` for `<SinglePhasePoromechanics`); use `Read` on the full example XMLs.
2. `Read` the full example XML from `/geos_lib/inputFiles/...` and adapt it to the task's spec.
3. Write the adapted XML to `/workspace/inputs/<name>.xml`.
4. Read each file back to verify structure matches the spec before finishing.

That's it.

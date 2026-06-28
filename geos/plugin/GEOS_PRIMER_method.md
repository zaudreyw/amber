# GEOS authoring methodology

GEOS is an open-source multiphysics simulator. Tasks require authoring
XML input files (sometimes a small set with `<Included>` cross-file
references). All values are SI units.

## Where to find references

- **Validated example XMLs**: `/geos_lib/inputFiles/`, organized by
  physics family (e.g. `wellbore/`, `hydraulicFracturing/`,
  `triaxialDriver/`, `compositionalMultiphaseFlow/`,
  `thermoPoromechanics/`, `poromechanics/`). Treat these as the
  authoritative structural reference.
- **Sphinx documentation**: `/geos_lib/src/docs/sphinx/` — tutorials,
  basic and advanced example pages, schema definitions, datastructure
  index.
- **Constitutive model attribute names** are defined in C++ headers
  under `/geos_lib/src/coreComponents/constitutive/.../*.hpp`. Look for
  `static constexpr char const *` lines if examples don't disambiguate
  a parameter name.

## Use examples as references, not templates to copy verbatim

When you find a relevant example:
- Use it to understand the XML structure, required tags, and solver
  configuration.
- Do NOT copy parameter values wholesale — the spec dictates the
  parameters.
- Build the input deck around the spec's actual requirements, with
  the example providing structural guidance.

## Recommended workflow

1. **Find similar example**: `Glob`/`Grep`/`Read` against
   `/geos_lib/inputFiles/`. Search by physics keyword
   (e.g. `Glob` for `**/*Wellbore*.xml`; `Grep` for
   `<SinglePhasePoromechanics`); use `Read` on the full example XMLs.
2. **Adapt to spec**: Read the example XMLs carefully and adapt to the
   task spec. Keep the example's structural choices (section ordering,
   naming conventions, attribute spellings) unless the spec demands
   otherwise.
3. **Write output**: Write to `/workspace/inputs/<name>.xml`.
4. **Verify**: Read each file back and check structure matches the
   spec before finishing.

## Input file organization (base/benchmark pattern)

When the spec calls for a reusable physics setup with multiple runner
configurations (e.g. fully-implicit vs sequential coupling, smoke vs
benchmark), prefer the two-file pattern:
- `*_base.xml` — physics, mesh, constitutive laws, BC types — reusable
- `*_benchmark.xml` / `*_smoke.xml` / `*_run.xml` — scenario specifics,
  pulls in base via `<Included>`

## Top-level XML skeleton

```
<Problem>
  <Solvers>...</Solvers>
  <Mesh>...</Mesh>              <!-- or VTKMesh, InternalWellbore, InternalMesh -->
  <Geometry>...</Geometry>      <!-- Box, Cylinder, etc. for fieldspec sets -->
  <Events>...</Events>
  <NumericalMethods>...</NumericalMethods>
  <ElementRegions>...</ElementRegions>
  <Constitutive>...</Constitutive>
  <FieldSpecifications>...</FieldSpecifications>
  <Functions>...</Functions>    <!-- TableFunction for time/space-varying data -->
  <Outputs>...</Outputs>
  <Tasks>...</Tasks>            <!-- output collection, optional -->
</Problem>
```

## Safety

- Never invent GEOS XML schema details — verify against
  `/geos_lib/inputFiles/` examples or the constitutive C++ headers
  when unsure.
- Match cross-referenced names exactly (cell blocks → element regions
  → target regions on solvers; field set names → geometry sets).

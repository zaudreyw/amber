# GEOS XML Authoring — Quick Cheatsheet

*Pitfalls to avoid and shortcuts to save time.*

## Shortcuts (do these first)

- **One example ≈ a solved task.** Before writing anything, use RAG to find the most similar validated example in `/geos_lib/inputFiles/...`, then `Read` it. Adapting a working example is 5× faster than composing from the schema.
- **Query the schema once, not repeatedly.** Call `mcp__geos-rag__search_schema` for each major XML element ONCE (solver, constitutive model, mesh), not every attribute. The schema reply covers the full tag.
- **Copy-don't-compose for `<Events>`, `<Outputs>`, `<NumericalMethods>`.** These blocks are nearly identical across tasks in the same physics family. Copy from your chosen example unless the task spec explicitly overrides.

## Pitfalls (high-cost mistakes)

- **Empty `materialList`**. Never leave an `ElementRegion`'s `materialList=""`. Even a placeholder `ElasticIsotropic` is acceptable; empty is not.
- **Wrong path in `<Included>`**. Paths must be relative to the including file and resolvable inside `/workspace/inputs/`. Cross-file references into `/geos_lib` will not resolve at runtime.
- **Missing `<TableFunction>` data**. If you reference an external table, the table file (or inline values) must be declared in `<Functions>`.
- **Inconsistent mesh/region/material names**. A `CellElementRegion.cellBlocks` entry must match an actual cell block produced by your mesh generator (`InternalMesh`, `InternalWellbore`, or `VTKMesh`'s `regionAttribute`).
- **Wrong units**. GEOS is strictly SI (meters, seconds, Pascal, kg/m³). Common wrong-unit mistakes: permeability in mD (should be m²), viscosity in cP (should be Pa·s), pressure in psi (should be Pa).
- **Exiting without verification**. After writing, `Read` your XML and check every block named in the task spec is present. Do not end without this.

## Meta-strategy

- The task spec names a physics family. Find the matching subdir in `/geos_lib/inputFiles/`. Scan its files. Pick the closest one. Adapt it. Verify.
- Prefer iterative refinement over big-bang authoring. First pass: rough skeleton. Second pass: fill values. Third pass: verify.

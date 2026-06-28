# GEOS Mesh primer (segment-focused)

The `<Mesh>` block defines the discretized geometry. The `<Geometry>` block defines named regions of space (boxes, cylinders, planes) used by `<FieldSpecifications>` to apply BCs/ICs to subsets.

## When to use which mesh type

- **`<InternalMesh>`** — Cartesian or stretched-Cartesian box. Most tutorials use this. Defined by `xCoords`, `yCoords`, `zCoords` (corner positions) and `nx`, `ny`, `nz` (element counts per segment). Element types: `C3D8` (hex), `C3D4` (tet), etc.
- **`<VTKMesh>`** — import an external `.vtu` / `.vtm` mesh. `file="mesh.vtu"` (relative to the simulation working directory). For irregular geometry, contact problems with pre-existing fractures, real-world models.
- **`<InternalWellbore>`** — radial mesh for wellbore problems. Defined by radial coordinates (`radius`), azimuthal counts (`theta`), and vertical (`zCoords`). Has special attributes for wellbore-specific behavior (cement, casing).

## cellBlocks

Every mesh produces named cellBlocks that downstream blocks reference:
- InternalMesh: cellBlock names default to a name based on element index/type (e.g., `cb1`, `0_DEFAULT_HEX`). Use the `cellBlockNames` attribute to set explicit names.
- VTKMesh: cellBlocks are read from the VTU file's `region` (or `attribute`) array. `regionAttribute` chooses the array name to use. Often the attribute is just numeric (1, 2, 3) and the cellBlocks are named after those numbers.
- ElementRegions then reference these cellBlocks by name in `cellBlocks="{ Domain, …}"`.

## Common patterns

- **Single-block Cartesian box**: `xCoords="{0,1}"`, `yCoords="{0,1}"`, `zCoords="{0,1}"`, `nx="{10}"`, `ny="{10}"`, `nz="{10}"`, `cellBlockNames="{Domain}"`.
- **Wellbore**: `<InternalWellbore radius="{0.1, 1, 10}" theta="{0,180,360}" zCoords="{0,5}" nr="{10,20}" nt="{60}" nz="{20}" cellBlockNames="{cb1}" wellboreNames="{wb}"/>`.
- **VTK from file**: `<VTKMesh name="myMesh" file="mesh.vtu" regionAttribute="region"/>`.

## Geometry block (named regions of space)

Used to define which mesh elements/nodes a FieldSpecification applies to. Common shapes:
- `<Box name="leftFace" xMin="{-0.001, -1, -1}" xMax="{0.001, 1, 1}"/>`
- `<Cylinder name="injectionWell" point1="{0,0,0}" point2="{0,0,5}" radius="0.5"/>`
- `<ThickPlane name="fault" normal="{1,0,0}" origin="{0,0,0}" thickness="0.01"/>`

A node or element is "in" a Box/Cylinder/ThickPlane if its centroid is inside. FieldSpecifications then reference these by `setNames="{leftFace}"`.

## Pitfalls

- **Wrong cellBlockNames**: typo here = ElementRegions can't find cellBlocks → empty regions → solver does nothing.
- **VTKMesh with relative path**: files are looked up relative to the directory the XML file lives in. If the example used a path like `mesh.vtu`, the new XML needs the same file present, or a different mesh.
- **Internal mesh `xCoords` length**: `xCoords` has `len(nx)+1` entries (corner coords for N segments). Off-by-one is a common bug.
- **Wellbore mesh axis**: the wellbore axis is along Z. Adjust orientation in the geometry block, not by reordering coordinates.
- **Surface generation**: for fracture problems, the mesh may include faces that get fractured at runtime. Look for `<SurfaceGenerator>` solver — it consumes `faceBlocks` named in the mesh.

## Tools

- `mcp__geos-rag__search_schema` — for exact attribute names of InternalMesh / VTKMesh / InternalWellbore.
- `mcp__geos-rag__search_technical` — for example Mesh blocks matching a specific physics family (wellbore, fracture, leakage well, etc.).

## Authoritative source

- Schema: `/plugins/orchestrator/schema_slices/mesh.xsd`.
- Full doc: `/geos_lib/src/coreComponents/mesh/docs/Mesh.rst`.

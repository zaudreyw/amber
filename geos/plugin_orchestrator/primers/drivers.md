# GEOS Drivers primer (segment-focused)

Combined coverage of `<Functions>`, `<FieldSpecifications>`, `<Tasks>`, `<Outputs>`. Each is small individually but they share dependencies on mesh/region naming.

## Functions

Three types:

- **`<TableFunction>`** — interpolated lookup. Most common.
  ```xml
  <TableFunction name="loadFunc"
                 inputVarNames="{time}"
                 coordinates="{0, 1, 100}"
                 values="{0, -1e6, -1e6}"
                 interpolation="linear"/>
  ```
  - For 1D: `coordinates` is a flat list, `values` matches.
  - For 2D+: use `coordinateFiles="{xs.geos, ys.geos}"` and `voxelFile="z.geos"`. Files contain whitespace-separated numbers.
  - `interpolation`: `linear`, `nearest`, `upper`, `lower`.
- **`<SymbolicFunction>`** — analytic expression.
  ```xml
  <SymbolicFunction name="initialUx"
                    inputVarNames="{ReferencePosition}"
                    variableNames="{x,y,z}"
                    expression="0.001 * x"/>
  ```
- **`<CompositeFunction>`** — combines other functions arithmetically.

`inputVarNames`:
- `time` — function of simulation time only.
- `ReferencePosition` — function of nodal coordinates (for spatially-varying ICs).
- `elementCenter` — for element-centered fields.

## FieldSpecifications

Two main element types: `<FieldSpecification>` (the generic) and `<Dirichlet>` (a constraint with `bcApplicationTableName`).

```xml
<FieldSpecification
    name="xConstraint"
    objectPath="nodeManager"
    fieldName="totalDisplacement"
    component="0"
    setNames="{xneg}"
    scale="0.0"/>
```

Critical attributes:
- **`objectPath`** — where the field lives. Common values:
  - `nodeManager` — nodal fields (displacement, velocity).
  - `faceManager` — face-centered fields.
  - `ElementRegions/<region>/<cellBlock>` — element-centered fields (pressure, temperature).
  - `ElementRegions/<region>/<cellBlock>/<material>` — material-internal fields (stress, plasticState).
- **`fieldName`** — the field's internal name. Examples:
  - `totalDisplacement`, `velocity`, `acceleration` — solid mechanics nodal.
  - `pressure`, `temperature` — flow element-centered.
  - `globalCompFraction` — multiphase composition (use `component=` to pick the species).
  - `<materialName>_stress`, `<materialName>_density` — material-internal.
- **`component`** — for vector fields. 0=x, 1=y, 2=z. Omitting applies to all components — almost never what you want.
- **`setNames`** — list of named sets the spec applies to. Sets come from Mesh's nodeSets, ElementRegions' cellBlocks, or Geometry's named regions.
- **`scale`** — scalar factor. Applied to the (constant 1) field, or to the function value if `functionName` is set.
- **`functionName`** — references a `<TableFunction>` or `<SymbolicFunction>`. Output of the function is multiplied by `scale`.
- **`initialCondition`** — set to "1" if this is an IC (applied at simulation start) rather than a BC (applied throughout).

For an applied traction:
```xml
<Traction
    name="topBoundary"
    objectPath="faceManager"
    tractionType="vector"
    direction="{0,0,-1}"
    scale="1e6"
    setNames="{ztop}"/>
```

For a source/sink:
```xml
<SourceFlux
    name="injection"
    objectPath="ElementRegions/Domain/cb1"
    scale="-0.07"
    setNames="{source}"/>
```

For wellbore aquifers (multiphase flow):
```xml
<Aquifier name="aquifer1" .../>
```

## Tasks

Mostly used for `<PackCollection>` to record time-history of a field at named locations:

```xml
<Tasks>
  <PackCollection
    name="pressureCollection"
    objectPath="ElementRegions/Domain/cb1"
    fieldName="pressure"
    setNames="{outletSet}"/>
</Tasks>
```

The PackCollection is later referenced by an `<Outputs>` element (`sources="{/Tasks/pressureCollection}"`) and triggered by an `<Events>` PeriodicEvent.

Other Task types include `<EmbeddedSurfaceGenerator>` (for fracture problems — generates the embedded surface set at simulation start).

## Outputs

```xml
<Outputs>
  <VTK name="vtkOutput"/>
  <Restart name="restartOutput"/>
  <TimeHistory name="pressureHistoryOutput"
               sources="{/Tasks/pressureCollection}"
               filename="pressure_history"/>
</Outputs>
```

Common types:
- **`<VTK>`** — Paraview-readable .vtu files. Default for visualization.
- **`<Silo>`** — only if Silo is explicitly required (rare for tutorials).
- **`<Restart>`** — checkpoint / restart support.
- **`<TimeHistory>`** — dumps a Task's collected data to an HDF5 file. `sources` references PackCollection paths.
- **`<ChomboIO>`** — for Chombo coupling (rare).

The Output is *defined* here but the *cadence* is set by an `<Events>` PeriodicEvent that targets it.

## Cross-segment naming dependencies (read carefully)

- Every `functionName=` in a FieldSpecification → must match a Function `name=`.
- Every `setNames=` entry → must match a name in Mesh's nodeSets / ElementRegions' cellBlocks / Geometry boxes.
- Every `objectPath="ElementRegions/X/Y"` → X must match a region name; Y must match a cellBlock in that region.
- Every `sources="{/Tasks/X}"` → X must match a Task name.

## Pitfalls

- **Wrong objectPath.** Element-centered fields under `nodeManager` is the most common bug — silent no-op.
- **Missing `component=` on vector fields** — applies to all components, blowing up your BC.
- **Function with mismatched inputVarNames** — `time`-input function can't be used as an IC (`time` is 0 at IC). Use ReferencePosition for spatial ICs.
- **TableFunction with `interpolation="linear"` and only 2 coordinates that are equal** — division-by-zero at runtime.
- **TimeHistory with non-existent sources path** — silent no-op; nothing gets dumped.

## Tools

- `mcp__geos-rag__search_schema` — for FieldSpec attribute names. Especially `fieldName` for material-internal fields.
- `mcp__geos-rag__search_technical` — for example FieldSpecifications blocks matching specific BC patterns (Dirichlet, traction, sourceFlux, aquifer).
- `mcp__geos-rag__search_navigator` — for "how do I impose initial stress" type questions.

## Authoritative sources

- Schema slice: `/plugins/orchestrator/schema_slices/drivers.xsd`.
- Full docs:
  - `/geos_lib/src/coreComponents/fieldSpecification/docs/FieldSpecification.rst`
  - `/geos_lib/src/coreComponents/functions/docs/FunctionManager.rst`
  - `/geos_lib/src/coreComponents/events/docs/TasksManager.rst`
  - `/geos_lib/src/coreComponents/fileIO/doc/OutputTasks.rst`

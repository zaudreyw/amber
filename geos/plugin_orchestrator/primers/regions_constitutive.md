# GEOS ElementRegions + Constitutive primer (segment-focused)

These two segments are tightly coupled: each region's `materialList` is a list of names defined under `<Constitutive>`. Authoring them together prevents naming drift.

## ElementRegions

```xml
<ElementRegions>
  <CellElementRegion name="Domain" cellBlocks="{ * }" materialList="{ shale, water }"/>
</ElementRegions>
```

- `name` — used by Solvers (`targetRegions="{Domain}"`) and FieldSpecifications (`objectPath="ElementRegions/Domain/<cellBlock>"`).
- `cellBlocks` — list of cellBlock names from the Mesh segment. `{ * }` matches all.
- `materialList` — list of constitutive model names (defined below). Order doesn't matter.

Other region types:
- `<WellElementRegion>` — for wellbore segments. Has `materialList` for the wellbore (cement, casing).
- `<SurfaceElementRegion>` — for fracture surfaces. Has `subRegionType="faceElement"` typically. Used by hydraulic fracture solvers.

## Constitutive

The Constitutive block contains many types. Pattern: each material has `name`, plus its own physical parameters.

### Solid mechanics models (rock-like)

- `<ElasticIsotropic name="rock" defaultDensity="2700" defaultBulkModulus="…" defaultShearModulus="…"/>` — linear elastic, simplest.
- `<DruckerPrager name="rock" …/>` — pressure-dependent yield. Adds `defaultCohesion`, `defaultFrictionAngle`, `defaultDilationAngle`.
- `<ExtendedDruckerPrager>` — DP with cap. Adds `initialCriticalFractureEnergy`, hardening params.
- `<DelftEgg>` — modified Cam-Clay variant.
- `<ModifiedCamClay>` — for clay-like soils. Adds `defaultPreConsolidationPressure`, `defaultRecompressionIndex`, `defaultVirginCompressionIndex`.

### Fluid models

- `<CompressibleSinglePhaseFluid name="water" defaultDensity="1000" defaultViscosity="0.001" referencePressure="1e5" compressibility="1e-9"/>` — single-phase, simplest.
- `<DeadOilFluid>` — multiphase oil-water. Has `phaseNames`, table file paths.
- `<CompositionalMultiphaseFluid>` — full compositional EOS (CO2, CH4, etc.). Many components, many tables.

### Porosity / permeability (for poromechanics, flow)

- `<BiotPorosity name="rockPorosity" defaultReferencePorosity="0.1" defaultGrainBulkModulus="..."/>` — pressure-dependent porosity for poromechanics.
- `<PressurePorosity name="rockPorosity" defaultReferencePorosity="0.1" referencePressure="1e5" compressibility="1e-9"/>` — simpler pressure-only model.
- `<ConstantPermeability name="rockPerm" permeabilityComponents="{1e-15, 1e-15, 1e-15}"/>` — fixed permeability tensor.
- `<CarmanKozenyPermeability>` — porosity-dependent.

### Composite materials (poromechanics / fracture)

GEOS exposes pre-bundled "porous solid" composites that wrap a solid model + porosity model + permeability model under one name. Use these when a Solvers block expects a single `solidNames` reference but the underlying solver is poromechanics:

- `<PorousElasticIsotropic name="rock" solidModelName="rockSolid" porosityModelName="rockPorosity" permeabilityModelName="rockPerm"/>` — references the constituent models; the constituents are also defined under Constitutive.
- `<PorousDruckerPrager>` — same pattern with DP plasticity.

### Fracture-aperture composites

- `<CompressibleSolidParallelPlatesPermeability>` — fracture-aperture model coupling permeability to fracture aperture. Used by hydraulic fracture problems.
- `<CompressibleSolidConstantPermeability>` — closed-fracture proxy.
- `<CompressibleSolidExponentialDecayPermeability>` — exponential aperture-permeability law.

## Common pitfalls (from prior agent failures)

- **Vocabulary hallucination is the #1 failure mode.** "PorousSolidType" doesn't exist. "CompressibleSolidCappedPlatesPorosity" doesn't exist (it's `CompressibleSolidParallelPlatesPermeability`). Search the schema before using a name.
- **Coupling pattern mixing.** Either you use the composite (`<PorousElasticIsotropic>`) and reference its constituent model names from inside it, OR you reference the standalone solid/porosity/permeability models from the solver. Don't mix. The composite IS the canonical pattern for poromechanics.
- **Name collisions.** Two materials with the same `name` in Constitutive = error. The solid model used by a `<PorousElasticIsotropic>` composite must have a DIFFERENT name from the composite itself (often suffix with `Solid`, e.g., composite "rock" wraps `rockSolid` + `rockPorosity` + `rockPerm`).
- **defaultDensity must be on the solid model, not the composite.**
- **referencePressure** for fluid is the pressure at which the reference density is measured. Often 1e5 (1 atm) for water, or in-situ pressure for reservoir fluids.

## Tools

- `mcp__geos-rag__search_schema` — for any constitutive type. ALWAYS use this before writing a name you're unsure about.
- `mcp__geos-rag__search_technical` — for example Constitutive blocks for specific physics families.
- `mcp__geos-rag__search_navigator` — for "what porosity model should I use with X" questions.

## Authoritative sources

- Schema slices: `/plugins/orchestrator/schema_slices/regions_constitutive_top.xsd`, `/plugins/orchestrator/schema_slices/constitutive_models.xsd`.
- Full docs:
  - `/geos_lib/src/coreComponents/constitutive/docs/Constitutive.rst` (top-level)
  - `/geos_lib/src/coreComponents/constitutive/docs/SolidModels.rst`
  - `/geos_lib/src/coreComponents/constitutive/docs/FluidModels.rst`
  - `/geos_lib/src/coreComponents/constitutive/docs/Porosity.rst`
  - `/geos_lib/src/coreComponents/constitutive/docs/Permeability.rst`
  - `/geos_lib/src/coreComponents/constitutive/docs/PorousSolids.rst`

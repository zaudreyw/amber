# GEOS Solvers + NumericalMethods primer (segment-focused)

## Solver families

- **Solid mechanics**: deformation, stress, strain.
  - `SolidMechanicsLagrangianFEM` — quasi-static or dynamic continuum mechanics.
  - `SolidMechanicsAugmentedLagrangianContact` / `SolidMechanicsLagrangeContact` / `SolidMechanicsLagrangeContactBubbleStab` — frictional contact between two surfaces.
  - `SolidMechanicsEmbeddedFractures` — embedded fracture continuum (vs. mesh-conforming contact).
  - `SurfaceGenerator` — propagates fracture surfaces (consumed by HydroFracture-style coupled solvers).
- **Single-phase flow**: pressure-driven incompressible/compressible flow.
  - `SinglePhaseFVM` — finite volume, two-point flux. The default.
  - `SinglePhaseHybridFVM` — face-centered hybrid for high-anisotropy or non-K-orthogonal grids.
- **Multiphase flow**:
  - `CompositionalMultiphaseFVM` — full EOS-based compositional flow (CO2, oil, gas, water).
  - `CompositionalMultiphaseHybridFVM` — hybrid variant.
  - `ImmiscibleMultiphaseFlow` — Buckley-Leverett style; faster, no compositional thermodynamics.
- **Coupled poromechanics** (a flow + a mechanics solver coupled):
  - `SinglePhasePoromechanics` — single-phase fluid + solid mechanics. Has `flowSolverName` and `solidSolverName` referring to standalone Solvers in the same `<Solvers>` block.
  - `MultiphasePoromechanics` — multiphase variant.
  - `MultiphasePoromechanicsConformingFractures`, `MultiphasePoromechanicsEmbeddedFractures` — for fractured reservoir poromechanics.
- **Other coupled**:
  - `ProppantTransport` — proppant moving with fluid.
  - `Hydrofracture` (conforming or embedded variants) — coupled propagation of fractures with fluid.

## Discretizations (NumericalMethods)

A solver has a `discretization="<name>"` attribute referencing an entry in `<NumericalMethods>`:

```xml
<NumericalMethods>
  <FiniteElements>
    <FiniteElementSpace name="FE1" order="1"/>
  </FiniteElements>
  <FiniteVolume>
    <TwoPointFluxApproximation name="singlePhaseTPFA"/>
  </FiniteVolume>
</NumericalMethods>
```

Rules:
- SolidMechanics solvers reference a `FiniteElementSpace` (`discretization="FE1"`).
- SinglePhase/Multiphase FVM solvers reference a `TwoPointFluxApproximation` (`discretization="singlePhaseTPFA"` etc.).
- HybridFVM solvers reference a `HybridMimeticDiscretization`.
- A Poromechanics composite solver typically references a `FiniteElementSpace` (it uses the FE backbone for the mechanics part, and inherits the flow discretization through the wrapped flow solver — DO check the example for the exact pattern).

## Composite solver pattern (poromechanics)

```xml
<Solvers>
  <SinglePhasePoromechanics
      name="poroSolver"
      flowSolverName="flowSolver"
      solidSolverName="solidSolver"
      logLevel="1"
      targetRegions="{ Domain }"
      discretization="FE1">
    <NonlinearSolverParameters newtonMaxIter="40"/>
    <LinearSolverParameters directParallel="0"/>
  </SinglePhasePoromechanics>

  <SolidMechanicsLagrangianFEM name="solidSolver" discretization="FE1" targetRegions="{Domain}"/>
  <SinglePhaseFVM name="flowSolver" discretization="singlePhaseTPFA" targetRegions="{Domain}"/>
</Solvers>
```

Critical:
- The composite solver (`SinglePhasePoromechanics`) is what `<Events>` triggers; the standalone solvers it references are not driven directly by Events.
- `flowSolverName` and `solidSolverName` MUST match the names of the standalone solvers in the same block.
- `targetRegions` should match across the composite and the standalone solvers.

## Per-solver knobs

- `newmarkBeta`, `newmarkGamma` — only for `SolidMechanicsLagrangianFEM` with implicit dynamic time integration. For quasi-static, omit.
- `cflFactor` — only for explicit dynamics.
- `temperatureLowerLimit`, `temperatureUpperLimit` — only for thermal-coupled flow.
- `LinearSolverParameters` (nested):
  - `solverType="direct"` for small problems; `solverType="krylov"` for large.
  - `directParallel="0"` enables a serial direct solver (most reliable for tutorials).
  - `preconditionerType="amg"` for iterative.
- `NonlinearSolverParameters`:
  - `newtonMaxIter` — Newton iteration cap.
  - `lineSearchAction` — line-search behavior on Newton failure.
  - `couplingType="FullyImplicit"` for poromechanics that requires it.

## Choosing solver for fracture/contact problems

Three families exist; they are NOT interchangeable:

1. **Mesh-conforming contact**: the mesh contains pre-existing surfaces (faceManager surfaces). Use `SolidMechanicsLagrangeContact` or `SolidMechanicsAugmentedLagrangianContact` (the augmented variant is generally more robust).
2. **Embedded fractures**: fractures are embedded planes inside elements (XFEM-like). Use `SolidMechanicsEmbeddedFractures`. Requires `<EmbeddedSurfaceGenerator>` to define the fracture surfaces in `<Tasks>`.
3. **Hydraulic fracture propagation**: combines a SurfaceGenerator (for propagation) with a coupled poromechanics solver. Look up `Hydrofracture`-family solvers via RAG.

When the task is "compute Sneddon's solution for a pre-existing crack", search RAG for "embedded fracture surface generation" — the right solver may not be the obvious LagrangianContact.

## Pitfalls

- **discretization name mismatch** — the most-common silent failure. The string in Solver matches a name in NumericalMethods exactly or your solver does nothing.
- **targetRegions mismatch** — the solver runs on no elements if names disagree.
- **Composite solver missing sub-solvers** — `SinglePhasePoromechanics` referencing `flowSolverName="flowSolver"` requires a `<SinglePhaseFVM name="flowSolver">` to ALSO exist in `<Solvers>`.
- **HybridFVM with TwoPointFluxApproximation** — schema-incompatible. HybridFVM needs HybridMimeticDiscretization.

## Tools

- `mcp__geos-rag__search_schema` — for solver type names and attribute lists. The single biggest risk-mitigation tool for this segment.
- `mcp__geos-rag__search_technical` — for example Solvers blocks for the specific physics. Especially useful for fracture/contact, which has many variants.
- `mcp__geos-rag__search_navigator` — to discover solver families you might not have considered.

## Authoritative sources

- Schema slice: `/plugins/orchestrator/schema_slices/solvers.xsd`.
- Full docs:
  - `/geos_lib/src/coreComponents/physicsSolvers/PhysicsSolvers.rst`
  - per-solver RSTs under `/geos_lib/src/coreComponents/physicsSolvers/<family>/docs/`.

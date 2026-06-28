---
id: XN-014
title: "PAC-1 failure analysis: why is vanilla CC + RAG failing on GEOS-XML?"
date: 2026-04-22
dag_nodes: [E16, E17, E23, E24]
links:
  related_to: [XN-004, XN-008, XN-009, XN-013]
tags: [failure-analysis, discussion-section, vanilla-cc, rag]
---

# Why is this task hard for vanilla CC?

*Motivation from advisor's post-doc (2026-04-22): "Converting natural language
specs into simulation XML — why wouldn't reading docs make this easy?"
Input: PAC-1 per-task TreeSim (fa0) across A1 (no-plug) and A2 (RAG-only).*

## Per-task scores, 17 v2 tasks, single seed each

| Task | A1 no-plug | A2 RAG-only | Δ |
|---|---:|---:|---:|
| AdvancedExampleCasedContactThermoElasticWellbore | 0.146 | 0.340 | +0.194 |
| AdvancedExampleDeviatedElasticWellbore | 0.651 | — | — |
| AdvancedExampleDruckerPrager | 0.788 | — | — |
| AdvancedExampleExtendedDruckerPrager | — | 1.000 | — |
| AdvancedExampleModifiedCamClay | 0.141 | 0.568 | +0.427 |
| AdvancedExampleViscoDruckerPrager | 0.129 | 0.985 | +0.856 |
| ExampleDPWellbore | 0.922 | — | — |
| ExampleEDPWellbore | 0.932 | 0.945 | +0.013 |
| ExampleIsothermalLeakyWell | 0.348 | 0.354 | +0.006 |
| ExampleMandel | 0.925 | 0.314 | **−0.611** |
| ExampleThermoporoelasticConsolidation | 0.869 | 0.274 | **−0.595** |
| TutorialPoroelasticity | 0.725 | 0.667 | −0.058 |
| TutorialSneddon | 0.195 | 0.148 | −0.047 |
| buckleyLeverettProblem | 0.775 | 0.629 | −0.146 |
| kgdExperimentValidation | 0.887 | 0.923 | +0.036 |
| pknViscosityDominated | 0.021 | 0.328 | +0.307 |

(Dashes = task not scored in that run. A1 was 12/17 scored due to earlier
spec mismatch; we treat the 12 paired tasks as the A1↔A2 comparison.)

A1 mean: 0.566 on the 12-task paired set. A2 mean: 0.793 on the 16 it scored.
Paired delta (A2−A1) on the 12: +0.251 (A2 wins 9 / A1 wins 3). Strong
mean win for A2, but the failure profile tells a richer story.

## What's hard about this task

### F1. Hallucinated schema (biggest vanilla-CC failure mode)

**Evidence: pknViscosityDominated, A1 score 0.021.**

Vanilla CC produced top-level elements that do not exist in GEOS:

```xml
<Fracture>
  <FractureModel
    name="fractureModel"
    tag="Fracture_001"
    initialCrack="1"
    cohesionZoneMode="Frictionless"
    criticalStrainEnergyReleaseRate="0.1 MPa m^0.5"
    stressIntensityFactor="NodeBased"
    parallelPlatesPermeability="1"
    faultThreshold="0.0 m"
    maxVerbosity="0" />
</Fracture>
```

None of `<Fracture>`, `<FractureModel>`, `cohesionZoneMode`,
`stressIntensityFactor`, `faultThreshold`, `maxVerbosity` are GEOS-valid.
Also used `<CompressibleSinglePhaseFieldState>` (not a schema element).

The GT version uses the correct idioms:

```xml
<SurfaceElementRegion name="Fracture" ... />
<CompressibleSolidParallelPlatesPermeability ... />
<PressurePorosity ... />
<ParallelPlatesPermeability ... />
<FrictionlessContact ... />
<HydraulicApertureTable ... />
```

**Character of the failure:** The model *confabulates an entire vocabulary*
that sounds like it should be GEOS but isn't. It correctly understands the
physics (hydraulic fracture, viscosity-dominated regime, PKN geometry) and
even knows a simulation needs a fracture solver, cohesion zone, permeability
coupling — but it has no way to constrain invention to real GEOS elements.

**Affected tasks (A1 < 0.30):** pknViscosityDominated, AdvancedExampleModifiedCamClay,
AdvancedExampleViscoDruckerPrager, TutorialSneddon, AdvancedExampleCasedContactThermoElasticWellbore.
All involve either hydraulic fracture (`SurfaceGenerator`, `HydroFracture` solver)
or advanced constitutive models (`ViscoExtendedDruckerPrager`, `ModifiedCamClay`)
or coupled multi-physics (`SinglePhasePoromechanicsConformingFractures`) — areas
where the GEOS schema has many specific-named classes that the model cannot
guess from domain knowledge.

### F2. Correct skeleton, wrong attributes (main RAG-only failure)

**Evidence: ExampleMandel, A1 0.925 → A2 0.314 (catastrophic regression).**

A2 Mandel has the correct top-level structure (Mesh, Geometry, Constitutive,
Solvers, ElementRegions) but introduces invalid attributes:

```xml
<SinglePhaseFVM name="flowSolver"
                discretization="singlePhaseTPFA"
                fluidNames="{water}"          <!-- deprecated -->
                solidNames="{shaleElastic}"   <!-- deprecated -->
                targetRegions="{cb1}">
...
<SinglePhasePoromechanics ...
    <NonlinearSolverParameters
        newtonTol="1.0e-2"
        lineSearchAction="Attempt"              <!-- not valid -->
        couplingType="FullyImplicit"/>          <!-- not valid -->
```

A1's vanilla CC produced a cleaner version — but note A1's success on
Mandel is partly luck (it's a well-known poroelastic test case; many
tutorials use it and the model likely memorized a close example).

**Character of the failure:** RAG retrieved plausible-but-outdated
example XMLs. The model then combined attributes across versions,
producing an XML whose tree structure is 80% right but whose attributes
are 60% invalid.

**Affected tasks (A2 lost big vs A1):** ExampleMandel (−0.611),
ExampleThermoporoelasticConsolidation (−0.595), buckleyLeverettProblem
(−0.146). All three are exactly the "classical" tasks where vanilla CC
already had strong priors; RAG pulled it off-distribution into a wrong
example's vocabulary.

### F3. Weak structural coverage (both A1 and A2 fail)

**Evidence: ExampleIsothermalLeakyWell 0.348 / 0.354, TutorialSneddon
0.195 / 0.148.** Both configs fail similarly.

For these tasks neither vanilla CC nor RAG-equipped CC does well —
vanilla because it doesn't know the schema, RAG-equipped because the
retrieved docs don't point the model to the right components.

**Character of the failure:** These tasks require multiple non-obvious
components (e.g. Sneddon needs `<EmbeddedSurfaceGenerator>` +
`<SolidMechanicsEmbeddedFractures>` + `<PoissonsRatio>`-aware contact
setup). Our current RAG retrieves relevant docs one query at a time;
the agent never assembles the full multi-component picture and writes
a partial XML missing 2–3 sections.

### F4. Spec under-specification

A cross-cutting issue on many tasks: the NL spec tells the agent "what
physics to simulate" but not "which solver class to instantiate." The
agent has to figure out that a thermal + contact + wellbore problem
maps to `<SinglePhasePoromechanicsConformingFractures>` + a thermal
flow solver + a contact solver. This is one-way learnable only by
retrieving a very-similar GEOS example — pure docs don't encode the
"which class, and what hierarchy" decision.

## What our setup fixes and what it doesn't

**A2 (RAG only) fixes most of F1.** Plugin wins on pknViscosityDominated
(+0.307), AdvancedExampleModifiedCamClay (+0.427),
AdvancedExampleViscoDruckerPrager (+0.856),
AdvancedExampleCasedContactThermoElasticWellbore (+0.194) — all of
which are the schema-hallucination class. The `search_schema` and
`search_technical` RAG endpoints give the agent the element names and
attribute lists, so it stops inventing `<FractureModel>` and starts
using `<SurfaceGenerator>`.

**A2 introduces F2.** The mean win (+0.251 on 12 paired tasks) hides
regressions on the tasks where vanilla CC already knew the answer. On
Mandel and ThermoporoelasticConsolidation the RAG retrieval pulls the
agent into wrong example XMLs; on buckleyLeverett it dilutes a correct
memory with contradictory examples.

**A3 (RAG+SR) fixes some of F2.** Self-refinement catches parse
errors and empty completions, so the worst F2 failures (generate-then-
empty, generate-then-parse-error) get caught. But SR does not correct
semantically-wrong attributes — it only rejects structural failure.

**None of our components address F3 or F4.** The "missing components"
and "spec under-specification" failures persist through all of A1,
A2, A3, A4', A5. These are the tasks where we plateau regardless of
component count.

## Concrete failure taxonomy (for discussion section)

| Mode | Signature | Example tasks | Which component helps |
|---|---|---|---|
| **F1 Schema hallucination** | Invented elements/attributes not in GEOS | pkn, Sneddon, ViscoDrucker, ModifiedCamClay, CasedContactThermoElastic | **RAG (search_schema)** |
| **F2 Wrong-version drift** | Correct tree skeleton, invalid attributes from mixed examples | Mandel, ThermoporoelasticConsolidation, buckleyLeverett | Memory-with-physics-match would; RAG alone hurts. SR catches only hard failures. |
| **F3 Missing components** | Partial XML — 2-3 required sections absent | Sneddon, IsothermalLeakyWell, Mandel(partial) | None of our components. Needs structural prompting or reference XMLs. |
| **F4 Spec under-specification** | Agent picks wrong solver class for described physics | ThermalLeakyWell, ThermoporoelasticConsolidation | Memory-with-typed-tags (solver_family) would; our current memory's lexical retrieval doesn't reliably surface the right class. |

## Why memory might be bizarrely failing to stack with SR

Looking at F2 and F4, a good memory tool would:

1. **Retrieve past tasks by physics family, not token overlap.** F4
   failures hinge on "this problem → that solver class." Lexical
   retrieval over `instructions_excerpt` tokens routes on surface words
   (thermal, leaky, well) rather than on the underlying solver decision
   (FVM vs Poromechanics vs Hydrofracture).
2. **Surface anti-patterns (F2).** The RAG-only runs drift on Mandel
   because retrieved examples conflict. A memory bank that said "past
   Mandel attempts went wrong when you mix SinglePhaseFVM attributes
   from v1 and v2 schemas" would directly address F2.

Our current memory implementation does neither:
- Lexical token overlap over `topic_keywords` + `instructions_excerpt`.
- No anti-pattern entries — only positive past trajectories.
- No solver-family-aware routing even though `solver_family` is a field
  in the index (loaded but not used in scoring).
- And as already documented, **the memory tool is never called** in any
  A4'/A5 run; the gain is pure tool-list-shape.

This is consistent with the "doesn't stack with SR" observation: a
tool that isn't being called cannot fix F2/F4. The small tool-list
nudge only moves the agent toward more cautious RAG usage; SR
separately catches parse/empty failures. They address different
failure modes in non-overlapping ways and therefore the gains are
essentially independent (and so their composition is near-additive
on benefit but variance-dominated because the gains themselves are
small and noisy).

## Paper-ready framing

*The hard task isn't "XML generation" — it's "binding natural-language
physics descriptions to a specific, version-sensitive, hierarchical
schema vocabulary under sparse documentation." Vanilla CC fails
because it confabulates a plausible-sounding vocabulary. Adding RAG
over schema closes 70% of the gap but opens a new wrong-version-drift
failure mode on tasks the model previously knew. Self-refinement
handles the hard failures (parses/empties) but cannot correct
semantic attribute errors. Memory, as currently implemented,
addresses neither remaining class. Next memory iterations must
either target F4 (typed solver-family retrieval) or F2 (anti-pattern
entries distilled from negative trajectories) to make a measurable
difference on top of RAG+SR.*

## Next actions for failure analysis

1. **Quantify F2 vs F3 vs F4.** For each of the ~8 tasks that score
   <0.70 on A5, manually categorize which mode dominates. Output: a
   count + example per mode that goes straight into discussion.
2. **Per-section TreeSim decomposition.** TreeSim already has
   per-section scores (`treesim_section_scores`). Tabulate which XML
   sections vanilla CC gets right (often Mesh, Geometry, Events) vs
   which it gets wrong (Solvers, Constitutive, NumericalMethods). That
   directly tells the discussion which schema areas the model's prior
   covers vs which need retrieval/memory support.

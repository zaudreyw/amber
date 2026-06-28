# Sub-Agent Orchestration for GEOS XML Authoring

**Date:** 2026-04-27
**Status:** Design proposal — pre-implementation
**Motivation:** Scale beyond one monolithic agent that gets distracted, under-reads docs, and pays full input-token tax on irrelevant context.

---

## 1. Question Asked

Are the top-level segments of a GEOS `<Problem>` XML independent enough to assign each to its own sub-agent (parallel where possible, sequential where forced), with each sub-agent carrying only the documentation slice it needs?

**Short answer:** Yes, with a clear dependency structure. About half of the 11 nominal segments can run in true parallel after a foundation pass; the rest fall into 3–4 serial tiers. The bootstrap-from-example pattern collapses most cross-segment naming concerns into a non-issue.

## 2. What I Looked At

- `data/GEOS/src/docs/sphinx/userGuide/Index.rst` and the full RST inclusion tree (Mesh, PhysicsSolvers, Constitutive, FieldSpecification, EventManager, TasksManager, FunctionManager, NumericalMethodsManager, fileIO outputs, etc.).
- `data/GEOS/src/coreComponents/schema/schema.xsd` — 269 `complexType` definitions, ~620 KB total, but **per-element slices average ~33 lines**. The schema is divisible.
- `data/GEOS/inputFiles/poromechanics/PoroElastic_Mandel_base.xml` to ground-truth the cross-segment naming pattern.
- `plugin/GEOS_PRIMER_minimal.md` (current ~35-line global primer).

A full per-segment dependency map sits at `/tmp/geos_segment_map.md` (Explore agent run, 2026-04-27).

## 3. Findings

### 3.1 The 11 nominal segments collapse to 9 in practice

| Nominal segment | Practical home |
|---|---|
| Solvers | own |
| Mesh | own (absorbs Geometry) |
| Geometry | **fold into Mesh** — no standalone module in user guide; treated as `<Geometry>` box/cylinder defs that pair with mesh sets |
| Events | own |
| NumericalMethods | **fold into Solvers** — discretization choice and solver choice are co-determined; the doc itself is a stub of ~13 LOC |
| ElementRegions | own (the binding/glue layer) |
| Constitutive | own |
| FieldSpecifications | own |
| Functions | own |
| Outputs | own |
| Tasks | own |

So the working set is **9 segments**.

### 3.2 Documentation footprint is tractable per segment

| Segment | Doc LOC (RST) | Schema slice (LOC) | Fits in focused subagent context? |
|---|---|---|---|
| Mesh | 390 | ~80 (InternalMesh + VTKMesh) | Yes |
| Solvers (full) | ~2000 across ~9 sub-RSTs | per-solver ~30–60 | **No — must split by physics** |
| Constitutive | ~400 across 8 sub-RSTs | per-model ~20–40 | Yes (with primer-of-primers) |
| ElementRegions | ~80 (in Mesh.rst) | ~40 | Yes |
| FieldSpecifications | ~150 | ~30 | Yes |
| Functions | 229 | ~30 | Yes |
| Events | 145 | ~30 | Yes |
| Outputs | ~150 | ~30 | Yes |
| Tasks | 51 | ~20 | Yes |

The Solvers segment is the only one that doesn't fit as a single subagent. **Split Solvers per physics family** (SolidMechanics, SinglePhaseFlow, CompositionalMultiphaseFlow, Poromechanics, ContactMechanics, …) — the orchestrator picks which solver subagent to spawn from the bootstrap example or from the task spec.

The schema is auto-generated, so primers must reference the relevant `complexType` slice statically (extract once at primer build time) rather than expecting Sphinx-built datastructure RSTs to exist.

### 3.3 Dependency graph (verified against docs and Mandel example)

```
                 Mesh ────────────────────────────────┐
                  │                                    │
                  ▼                                    ▼
            ElementRegions ──────► Constitutive    Geometry sets
                  │                     ▲            (folded in Mesh)
                  │                     │
                  ▼                     │
   ┌──────► Solvers (+ NumericalMethods)
   │              │
   │     ┌────────┴───────┐
   │     ▼                ▼
   │  Tasks ◄─── FieldSpecifications ◄─── Functions
   │     │                ▲
   │     ▼                │
   │  Outputs             │
   │     ▲                │
   └─── Events ───────────┘  (terminal wiring: Events references Solvers, Tasks, Outputs by name)
```

**Coupling classification:**

- **Structural couplings (must agree on substance, not just names):**
  - `Solvers ↔ NumericalMethods` — discretization type (FE vs FV) constrains solver choice; this is why I'd merge them.
  - `ElementRegions ↔ Constitutive` — `materialList` must match the constitutive model interface the solver expects (e.g., a poromechanics solver expects a `PorousSolid` composite).
  - `ElementRegions ↔ Mesh` — `cellBlocks` must match what mesh emits.

- **Name-only couplings (resolved by sharing a name registry):**
  - `Solvers.targetRegions` ← `ElementRegions.name`
  - `Events.target` ← `/Solvers/<n>`, `/Tasks/<n>`, `/Outputs/<n>`
  - `FieldSpecifications.functionName` ← `Functions.name`
  - `Outputs.sources` ← `/Tasks/<n>`
  - `FieldSpecifications.objectPath` ← mesh entity / region / cellBlock names

The structural ones force serial ordering. The name-only ones disappear if every subagent gets the bootstrap example's name inventory and is told "do not rename existing names; you may add new ones".

### 3.4 Bootstrap-from-example dissolves most coordination cost

Inspecting `PoroElastic_Mandel_base.xml`: every cross-segment reference (`materialList="{ shale, water }"`, `functionName="initialUxFunc"`, `sources="{/Tasks/pressureCollection}"`, `targetRegions="{ Domain }"`) is internally consistent because the example was authored as a coherent unit. If the orchestrator copies a similar example as a foundation and feeds each subagent **(a) the current segment XML and (b) a frozen name registry extracted from the bootstrap**, name-only couplings are pre-resolved. Subagents only need to:

1. Adapt values inside their segment to match the new task spec.
2. Add new entities if needed, registering new names back to the orchestrator before any downstream subagent runs.

Structural couplings still force serial order, but they're a small set.

## 4. Proposed Architecture

### 4.1 The pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│ MAIN AGENT (orchestrator)                                            │
│                                                                       │
│ Phase 0  BOOTSTRAP                                                    │
│   - RAG-search for the most similar example XML                       │
│   - Copy it to /workspace/inputs/<task>.xml                           │
│   - Parse it into per-segment text blocks                             │
│   - Extract the name registry (regions, materials, functions, tasks,  │
│     outputs, solver names, discretization names)                      │
│                                                                       │
│ Phase 1  FOUNDATION (serial)                                          │
│   └─► Mesh subagent: refine <Mesh> + <Geometry> for new task          │
│       returns: new mesh segment text + updated cellBlock/set inventory│
│                                                                       │
│ Phase 2  BINDING + MATERIALS (parallel)                               │
│   ├─► ElementRegions subagent                                         │
│   └─► Constitutive subagent                                           │
│       (both read the bootstrap segments + new mesh inventory; they    │
│        only see each other's NAMES via the registry, not full text)   │
│                                                                       │
│ Phase 3  PHYSICS (serial — depends on regions + materials)            │
│   └─► Solvers/<physics> subagent  (also handles NumericalMethods)     │
│       returns: <Solvers> + <NumericalMethods> text                    │
│                                                                       │
│ Phase 4  DRIVERS + I/O (parallel)                                     │
│   ├─► Functions subagent                                              │
│   ├─► FieldSpecifications subagent  (depends on Functions names —     │
│   │      either Functions runs first or the orchestrator commits a    │
│   │      function-name list up front and Functions fills the bodies)  │
│   ├─► Tasks subagent                                                  │
│   └─► Outputs subagent                                                │
│                                                                       │
│ Phase 5  WIRING                                                       │
│   └─► Events subagent: reads the full final name registry, writes     │
│       <Events> from scratch                                           │
│                                                                       │
│ Phase 6  ASSEMBLY + VALIDATION                                        │
│   - Splice returned segments back into the working file               │
│   - xmllint against schema.xsd                                        │
│   - If validation fails, dispatch a focused fix-up subagent on the    │
│     offending segment with the validation error                       │
└──────────────────────────────────────────────────────────────────────┘
```

True parallelism occurs in Phases 2 and 4 — that's 2/6 phases, but the serial phases (Phase 0, 1, 3, 5, 6) are short. Realistic wall-clock win is moderate, not 9×; the bigger wins are quality and per-call token cost (see §5).

**On Phase 4 ordering:** the cleanest variant is to have the orchestrator **pre-commit a name list** for Functions before Phase 4 starts (e.g., "you'll need `loadFunction`, `initialPressureFunc`"), then Functions, FieldSpecifications, Tasks, Outputs all run truly in parallel. Each fills bodies; the names were already pinned. This is a small adaptation, not a redesign.

### 4.2 The shared artifact: name registry

A small JSON-ish object the orchestrator maintains and passes to each subagent:

```yaml
mesh:
  cellBlocks: [cb1, cb2]
  nodeSets: [xneg, xpos, yneg, ypos, zneg, zpos]
regions:
  - name: Domain
    cellBlocks: ["*"]
    materialList: [shale, water]
constitutive:
  solids: [shaleSolid]
  fluids: [water]
  porosity: [shalePorosity]
  permeability: [shalePerm]
numerical_methods:
  finite_element_spaces: [FE1]
  finite_volume_discretizations: [singlePhaseTPFA]
solvers:
  - name: solidSolver
    type: SolidMechanicsLagrangianFEM
  - name: flowSolver
    type: SinglePhaseFVM
functions: [loadFunction, initialUxFunc, initialUzFunc]
tasks: [pressureCollection, displacementCollection]
outputs: [vtkOutput, restartOutput, pressureHistoryOutput, displacementHistoryOutput]
```

Each subagent receives this as part of its briefing and has a **hard rule**: "names listed here exist; you may add new names but must not rename existing ones; report new additions in your return payload".

### 4.3 The file-collision question (raised in the proposal)

**Recommended pattern: subagents do not write to disk.** The orchestrator owns the working file. Each subagent's tool surface is read-only on `/geos_lib/` (docs + examples) plus the RAG tools. The subagent's contract:

- **Input:** the task spec, the current segment text (extracted from the working file by the orchestrator), the name registry, its primer (which includes its schema slice + doc primer + 1–2 example excerpts).
- **Output:** new segment text + delta-to-registry (any new names introduced).

The orchestrator splices returned text into the working file. No two subagents ever touch the file. This is simpler than scratch-files-and-merge and avoids a merge-queue altogether. **It is also the one design choice I'd most resist relaxing** — letting subagents `Write` directly is the obvious source of bugs.

The "subagents merge into a queue" pattern from the original proposal is interesting but probably solves a problem we don't have. If we ever wanted true free-form edits across segments, the queue approach is the right answer; for the structured per-segment task, splicing is enough. Worth flagging as a deferred design dimension if we want to write a method-component note.

### 4.4 Per-segment subagent primers

Each subagent gets a primer of the form:

```
# <SEGMENT> Subagent Primer

## Your job
Author the <SEGMENT> XML block for a GEOS simulation.

## What you receive
- Task spec
- Current <SEGMENT> text from the bootstrap example
- Name registry from the orchestrator (read-only contract)

## Your output
- New <SEGMENT> text (string, no disk write)
- New names added (list) — these get merged back into the registry

## Cross-segment contract
- You MAY reference these names from other segments: <list>
- You MUST NOT rename: <list of incoming refs that other agents see>

## Schema slice (authoritative)
<inlined relevant complexTypes from schema.xsd — typically 1–4 types>

## Doc primer
<condensed prose from the segment's RST — what each attribute means,
 common gotchas, units. Theory/derivations stripped — left as links.>

## When you need more
- mcp__geos-rag__search_schema for attribute names/types
- mcp__geos-rag__search_technical for example XML blocks
- mcp__geos-rag__search_navigator for topical doc lookup
- Read /geos_lib/src/coreComponents/<path>/docs/<file>.rst for deep reference
- Read /geos_lib/inputFiles/<family>/*.xml for additional examples
```

This is the "primer with map of links to deeper docs" pattern from the user's proposal — it's the right shape. The schema slice is non-negotiable: it's the only authoritative attribute reference and it's small enough to inline.

**Solvers is special.** Instead of one Solvers primer, ship one per physics family (SolidMechanics, SinglePhaseFlow, CompositionalMultiphaseFlow, Poromechanics, ContactMechanics, ProppantTransport). The orchestrator picks based on the bootstrap example's solver type or the task spec. Each family primer also covers the NumericalMethods entries it requires.

### 4.5 New global primer for the main agent

The current `GEOS_PRIMER_minimal.md` describes a single-agent loop. The orchestrator needs a primer that explains the new pipeline:

```
# GEOS Orchestrator Primer

GEOS XML is built from ~9 mostly-independent top-level segments. Authoring
proceeds in 6 phases: bootstrap, foundation, binding, physics, drivers/IO,
wiring, assembly. Phases 2 and 4 run subagents in parallel; the rest are
serial.

## Workflow
1. BOOTSTRAP. Find the most similar example via RAG (search_technical).
   Copy to /workspace/inputs/<task>.xml. Extract per-segment text and
   build the name registry.
2. FOUNDATION. Spawn Mesh subagent. Wait. Update registry with new
   cellBlocks/nodeSets.
3. BINDING. Spawn ElementRegions + Constitutive in parallel. Wait both.
   Update registry with regions + materials.
4. PHYSICS. Pick the right Solvers/<physics> subagent based on bootstrap
   solver type. Spawn. Wait. Update registry with solver/NM names.
5. DRIVERS/IO. Pre-commit names: decide what Functions, Tasks, Outputs
   you'll need (mostly inherited from the bootstrap, possibly extended).
   Spawn Functions, FieldSpecifications, Tasks, Outputs in parallel.
6. WIRING. Spawn Events with the final registry.
7. ASSEMBLY. Splice returned segments into the working file. Validate
   with xmllint against the schema. On failure, dispatch a focused fix-up
   subagent.

## You do NOT
- Read full segment docs yourself. The subagents do.
- Write segment XML yourself. Splicing only.
- Let any subagent write to /workspace/. Subagents return text.

## You DO
- Maintain the name registry as the single source of truth.
- Decide which Solvers/<physics> subagent to dispatch.
- Run xmllint and triage failures.
```

## 5. Why this is worth doing — and how to test that

The user's three motivations, restated and graded:

1. **Faithful documentation use.** Plausible win. Current data (XN-001, XN-008) shows the agent leans on examples and under-reads docs; concentrating each subagent's context on a small primer + small schema slice + targeted RAG should *make* it read the relevant doc rather than skim past it. Worth a paired comparison of XML-quality scores (TreeSim) on tasks where the current single-agent pipeline produces partially correct XML.

2. **Wall-clock latency.** Smallest of the three wins, because the dependency graph forces 4–5 serial phases. Optimistic estimate: 1.3–1.8× wall-clock improvement on tasks with non-trivial Constitutive/FieldSpec content.

3. **Token cost / context rot.** Likely the biggest win — and the easiest to measure. Each subagent's input context is a primer (~1–3k tokens) + schema slice (~1k) + segment text (~0.5–2k) + registry (~0.5k) ≈ 4–7k tokens, vs. a single agent that accumulates all RAG returns and a full-file edit history. Cumulative input tokens across all subagents will likely exceed a single agent's, but **per-call** input is much smaller, which is what context-rot studies suggest matters for quality.

**Recommended evaluation order:**

1. Build the orchestrator + Mesh + Constitutive + ElementRegions subagents only. Run on 5–10 representative tasks with the orchestrator falling back to "main agent does this segment" for everything else.
2. If quality holds or improves on those 3 segments alone vs. the current monolithic agent, expand to full pipeline.
3. Headline comparison: paired TreeSim on the existing eval set, single-agent vs. orchestrator. Track per-subagent input/output tokens to make the "context savings" claim concrete.

## 6. Open questions / deferred decisions

1. **Sub-agent transport.** Is each subagent a fresh Claude Code session via the SDK, or in-process via the existing harness? Probably the latter (the harness already runs sequential agents); needs a tweak to spawn N concurrent ones for Phase 2/4 with bounded parallelism.

2. **Failure handling at the splice step.** If a subagent returns malformed XML or violates the registry, do we retry it in-place or escalate? Suggest: retry once with the validator error; on second failure, escalate to the orchestrator to repair manually. Cap retries.

3. **The free-edit method-component idea (subagent merge queue).** Probably out of scope for the first version — the splicing pattern works. But it's worth keeping as an alternative branch in the method DAG; if we later need cross-segment edits (e.g., a Solvers subagent realizing it needs a Constitutive change), the queue becomes load-bearing.

4. **How tightly should Constitutive subagent be split?** Constitutive has 8 sub-modules (solids, fluids, porosity, permeability, …). For poromechanics, a single Constitutive subagent must author a `PorousSolid` that bundles solid + porosity + permeability — the dependency is intra-Constitutive. Probably one subagent with all 8 module primers in context (~12–15k tokens, still tractable), rather than splitting further.

5. **NumericalMethods ownership.** Folded into Solvers in this design. If we ever support a task where the user pre-specifies NumericalMethods, we may need to expose it separately. Defer.

6. **Where does `LinearSolverParameters` live?** It's nested inside Solvers in the schema. The Solvers/<physics> primer should cover it. No separate decision needed.

## 7. Files to produce next (if approved)

Suggested layout under `plugin/` (mirroring existing primer location):

```
plugin/subagent_primers/
  orchestrator.md
  mesh.md
  element_regions.md
  constitutive.md
  solvers/
    solid_mechanics.md
    single_phase_flow.md
    compositional_multiphase_flow.md
    poromechanics.md
    contact_mechanics.md
    proppant_transport.md
  functions.md
  field_specifications.md
  tasks.md
  outputs.md
  events.md
```

Each primer is built once from: the segment RST (condensed by hand or with an LLM), the relevant schema slice (extracted with `awk '/<xsd:complexType name="<Type>Type"/,/<\/xsd:complexType>/'`), and a curated example excerpt.

Build script: ~50 lines. Roughly 1 day of careful primer authoring per segment, less for the small ones.

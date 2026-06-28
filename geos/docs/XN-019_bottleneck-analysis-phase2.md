---
id: XN-019
title: Bottleneck analysis on Phase 2 cells (DSv4-flash + DSv4-pro)
date: 2026-05-02
type: experiment_note
dag_nodes: [I15]
links:
  derived_from: [docs/2026-05-02_bottleneck-analysis-pipeline.md]
  evidence_for: [docs/2026-05-02_autonomous-campaign-results.md]
---

# Bottleneck analysis — auto-generated

## Synthesis (DSv4-pro)

**Baseline weaknesses**  
The no‑plugin agent (autocamp_F0, TreeSim 0.9096) fails most often because it has no schema‑aware feedback. The dominant failure categories are *bad_attribute_value* (12 tasks), *extra_block* (9), *partial_implementation* (7), *missing_block* (6), and *structural_mismatch* (6). These manifest predominantly in the sections that carry the highest failure weight: Geometry (0.856), Outputs (0.810), Solvers (0.704), and Constitutive (0.674). Sample root causes illustrate why: in Solvers the agent invents solver names (“thermoPoromechanicalSolver”), adds extraneous attributes (gravityVector), and omits required parameters (temperature, maxTimeStepCuts); the entire Events block is regularly omitted; Constitutive sections sprout an extra dummy material, producing 7 children instead of 6. The agent lacks any mechanism to verify child counts, check attribute existence, or enforce mandatory structural elements, so it freely hallucinates and drops blocks.

**Adapter impact**  
The best‑config cell (autocamp_F4, TreeSim 0.9214) incorporates a validation‑hook adapter. Its effect is sharply targeted: *missing_block* drops from 6 to 3, and *partial_implementation* dips from 7 to 6, indicating that the adapter reliably catches absent whole sections (e.g., Events, Outputs). However, content‑level errors are untouched. *Extra_block* rises from 9 to 11, *hallucinated_extras* from 4 to 7, and *bad_attribute_value* remains nearly flat (12 → 11). The number of tasks with no failure stays at 4, so perfect generation does not increase. The failure weight shifts: Solvers balloons to 1.58 (from 0.70) because once missing blocks are fixed, the remaining mistakes concentrate in wrong solver parameters and child structures. Geometry (0.65) and Outputs (0.49) remain heavily penalized — the F4 sample root cause still shows a Silo→VTK replacement, incorrect NonlinearSolverParameters, and a wrong stabilization name. In short, the adapter ensures block *presence* but leaves block *content* uncorrected.

**Implications**  
First, adapter designs must pair structural validation with precise child‑count and forbidden‑element rules; without this, extra_block and hallucinated_extras persist (11 and 7 in F4, respectively). Second, the unchanged burden of bad_attribute_value (11) and the Solvers failure weight (1.58) compel a solver‑type oracle that cross‑references attribute names and allowed values against the GEOS schema, preventing nonsense like “TPFAstabilization” for contactStabilization. Third, sections with stubbornly high failure weights — Geometry (0.65) and Outputs (0.49) — need templated enforcement: output elements must be forced to match the exact reference type (Silo, not VTK), and mesh entity attributes must pass a dry‑run geometry check. Finally, because the fraction of flawless tasks did not improve, adapters should add closed‑loop retries driven by validator output, giving the agent a chance to repair attribute and structural errors that static hooks cannot eliminate.

## Perfect-task counts (treesim ≥ 0.999)

| cell | perfect | total | rate |
|---|---:|---:|---:|
| autocamp_F0 | 7 | 51 | 13.7% |
| autocamp_F4 | 6 | 51 | 11.8% |

The adapter does **not** produce more perfect tasks; F4's +1.2pp
mean lift comes from making the *failures less severe*, not from
solving more tasks end-to-end. This shifts the implication: the
adapter operates in a *harm-reduction* mode (catching missing
top-level blocks) rather than a *correctness* mode. Producing
strictly more perfect outputs would require content-level oracles
that the current F4 does not include.

## Cross-cell category distribution (Phase 2 + derisk = 7 cells, n=51 each)

| cell | mean | σ | bad_attr | extra_block | hallucinated | missing | structural | partial |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F0 (baseline) | 0.9096 | 0.110 | 12 | 9 | 4 | **6** | 6 | 7 |
| F2 (RAG only) | 0.9191 | 0.087 | 12 | 8 | 8 | 4 | 8 | 9 |
| F4 (S+X+M, best) | 0.9214 | **0.076** | 11 | **11** | **7** | 3 | 7 | 6 |
| F6 (S+X) | 0.9166 | 0.086 | **15** | 5 | ~ | 2 | 11 | 10 |
| F8 (S+X+M, factorial fill) | 0.9110 | 0.085 | 12 | 7 | ~ | ~ | 9 | 8 |
| F11 (decomposed SE) | 0.9145 | **0.078** | 11 | 11 | ~ | ~ | 10 | 6 |
| SE (v3 monolith) | 0.9191 | 0.082 | 9 | 10 | ~ | ~ | ~ | 9 |

Bold = highest in column; **highlighted findings**:

1. **`bad_attribute_value` is universal** (9-15 across all cells, including
   the best). Memory + xmllint do NOT reduce it. F6 (xmllint + SR-hook,
   no memory) is highest at 15 — adding hooks without memory makes the
   agent attempt more ambitious solvers that miss attributes.
2. **`extra_block` gets WORSE with adapters**: F0 baseline 9 → F4 best
   11 (and F11 also 11). Memory/cheatsheets nudge the agent to include
   "patterns it has seen" even when the GT doesn't have them.
3. **`missing_block` is the one F4 fixes**: 6 → 3. The xmllint hook
   catches missing top-level sections; the cheatsheet enumerates
   required block types. This is the adapter's *unambiguous win*.
4. **Reliability (σ)**: F4 lowest at 0.076 (best mean+best reliability);
   F11 also 0.078 (memory-supplemented configs are tighter). F0
   highest at 0.110 (catastrophic seed-2 missing-Constitutive case
   pulls σ up). Memory regularizes failures more than it lifts mean.

## Top "would_have_helped" themes (F0 baseline, n=51)

DSv4-flash's per-task suggestions, themed:

| theme | count | what it implies |
|---|---:|---|
| xmllint / schema validation | 32 | dominant suggestion; but F4 has xmllint and still misses 45/51, so schema is necessary not sufficient |
| GT example lookup | 10 | reference-based validation: "did the agent compare against an example XML for this physics?" |
| memory cheatsheet | 3 | physics→solver routing memory (already implemented in F4 via m1u, partial coverage) |
| child-count enforcement | 2 | direct fix for the `extra_block` and `hallucinated_extras` modes |
| GEOS run validation | 1 | runtime check (we don't have GEOS executable in eval) |
| attribute oracle | 1 | per-element allowed-attribute lookup |

The two-line takeaway: schema validation is what the LLM judges as
"obvious," but the *unaddressed* failure modes (extra blocks,
hallucinated attributes, geometric drift) need example-based
validation, child-count rules, and reasoning skills — none of which
xmllint provides.

## Concrete failure case-studies (F0 vs F4)

### Adapter trades catastrophic miss for small content error: AdvancedExampleDruckerPrager
- F0_s2: missed the entire `<Constitutive>` block — score 0.333.
- F4 all seeds: 7 Constitutive children instead of 6 (one extra
  ElasticIsotropic from the base template) — score 0.998 across
  all 3 seeds.
- **Pattern**: validation hooks reliably catch missing top-level
  blocks, but the agent's "include base + extend in benchmark"
  pattern leaves a stale ElasticIsotropic from the template. An
  adapter that knew the GT child-count would catch this.

### Adapter regression: ExampleIsothermalLeakyWell (-0.037 mean)
- F0: omitted 4 required `TableFunction` elements (oil property
  tables); other seed assumed CO2 instead of oil (wrong constitutive).
- F4: added a `gravityVector="{ 0.0, 0.0, -9.81 }"` attribute on
  `<Solvers>` not present in GT (consistent across seeds 1+3);
  seed 2 had only 4 of 6 required Functions.
- **Pattern**: F4 fixes the missing-functions problem in one direction
  but hallucinates a plausibly-correct attribute that schema
  validation passes. Schema is necessary, not sufficient —
  example-aware validation is needed too.

### Adapter regression: ExampleThermalLeakyWell (-0.029 mean)
- F0: shifted box z-coordinates by 0.01 (1-unit drift); swapped
  y-extents of north/south boxes.
- F4: 100m-thick boundary slabs instead of 0.02m-thin slabs.
- **Pattern**: both cells fail on Geometry coordinate accuracy.
  Neither validation nor memory helps — needs a geometry-from-spec
  reasoning skill or a ruler-style sanity check.

## Per-cell summary

### autocamp_F0  (n=51, treesim mean=0.9096)

**Failure category distribution:**

```
{
  "structural_mismatch": 6,
  "missing_block": 6,
  "no_failure": 1,
  "extra_block": 9,
  "hallucinated_extras": 4,
  "bad_attribute_value": 12,
  "partial_implementation": 7,
  "wrong_attribute_value": 2,
  "none": 3,
  "wrong_constitutive": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 8,
  "Events": 10,
  "None": 4,
  "Constitutive": 5,
  "Functions": 5,
  "ElementRegions": 5,
  "Outputs": 4,
  "Geometry": 7,
  "Tasks": 1,
  "": 1,
  "N/A": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Geometry": 0.8562,
  "Outputs": 0.8101,
  "Solvers": 0.7041,
  "Constitutive": 0.6735,
  "Functions": 0.493,
  "ElementRegions": 0.445,
  "Events": 0.4403,
  "Tasks": 0.1889,
  "None": 0.0,
  "": 0.0,
  "N/A": 0.0
}
```

### autocamp_F2  (n=51, treesim mean=0.9191)

**Failure category distribution:**

```
{
  "structural_mismatch": 8,
  "bad_attribute_value": 12,
  "extra_block": 8,
  "none": 2,
  "partial_implementation": 9,
  "hallucinated_extras": 8,
  "missing_block": 4
}
```

**Failing section distribution:**

```
{
  "Solvers": 9,
  "Constitutive": 5,
  "null": 1,
  "": 2,
  "ElementRegions": 7,
  "FieldSpecifications": 3,
  "Events": 10,
  "/Problem": 1,
  "Outputs": 3,
  "Geometry": 4,
  "NumericalMethods": 2,
  "/Problem/Constitutive": 2,
  "Functions": 1,
  "None": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 1.1259,
  "Outputs": 0.6578,
  "Events": 0.6498,
  "Geometry": 0.552,
  "ElementRegions": 0.4462,
  "NumericalMethods": 0.2676,
  "FieldSpecifications": 0.2025,
  "/Problem": 0.1229,
  "Functions": 0.0901,
  "Constitutive": 0.0085,
  "/Problem/Constitutive": 0.0034,
  "null": 0.0,
  "": 0.0,
  "None": 0.0
}
```

### autocamp_F4  (n=51, treesim mean=0.9214)

**Failure category distribution:**

```
{
  "bad_attribute_value": 11,
  "hallucinated_extras": 7,
  "extra_block": 11,
  "none": 3,
  "": 1,
  "structural_mismatch": 7,
  "partial_implementation": 6,
  "missing_block": 3,
  "wrong_solver_type": 1,
  "no_failure": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 10,
  "Outputs": 3,
  "Constitutive": 6,
  "None": 4,
  "": 1,
  "Events": 9,
  "ElementRegions": 7,
  "FieldSpecifications": 1,
  "/Problem/Constitutive": 1,
  "Geometry": 5,
  "/Problem/Functions": 1,
  "Functions": 2,
  "/Problem/FieldSpecifications": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 1.5771,
  "Geometry": 0.6544,
  "Outputs": 0.4858,
  "Events": 0.4509,
  "ElementRegions": 0.3657,
  "FieldSpecifications": 0.1406,
  "/Problem/Constitutive": 0.1159,
  "Functions": 0.1049,
  "/Problem/Functions": 0.1032,
  "Constitutive": 0.0102,
  "/Problem/FieldSpecifications": 0.0018,
  "None": 0.0,
  "": 0.0
}
```

### autocamp_F6  (n=51, treesim mean=0.9166)

**Failure category distribution:**

```
{
  "bad_attribute_value": 15,
  "structural_mismatch": 11,
  "extra_block": 5,
  "no_failure": 1,
  "partial_implementation": 10,
  "hallucinated_extras": 4,
  "wrong_solver_type": 1,
  "none": 1,
  "missing_block": 3
}
```

**Failing section distribution:**

```
{
  "Solvers": 9,
  "Mesh": 2,
  "Constitutive": 3,
  "None": 2,
  "Functions": 4,
  "Events": 9,
  "ElementRegions": 7,
  "Geometry": 7,
  "Outputs": 3,
  "/Problem/Functions": 1,
  "None (all sections perfect)": 1,
  "Solvers/SinglePhasePoromechanics": 1,
  "/Problem/Events": 1,
  "FieldSpecifications": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 1.2982,
  "Geometry": 0.8434,
  "Outputs": 0.5329,
  "ElementRegions": 0.4892,
  "Functions": 0.3179,
  "Solvers/SinglePhasePoromechanics": 0.2731,
  "Events": 0.2463,
  "FieldSpecifications": 0.1245,
  "/Problem/Events": 0.1038,
  "/Problem/Functions": 0.0114,
  "Mesh": 0.0053,
  "Constitutive": 0.0051,
  "None": 0.0,
  "None (all sections perfect)": 0.0
}
```

### autocamp_SE  (n=51, treesim mean=0.9191)

**Failure category distribution:**

```
{
  "extra_block": 10,
  "unknown": 7,
  "": 1,
  "partial_implementation": 9,
  "bad_attribute_value": 9,
  "wrong_solver_type": 2,
  "missing_block": 3,
  "structural_mismatch": 6,
  "hallucinated_extras": 3,
  "none": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 9,
  "?": 7,
  "": 3,
  "Functions": 3,
  "Constitutive": 4,
  "Events": 9,
  "ElementRegions": 4,
  "FieldSpecifications": 2,
  "Outputs": 2,
  "Geometry": 5,
  "Problem": 1,
  "None": 1,
  "/Problem/Events": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 1.2523,
  "?": 0.6765,
  "Geometry": 0.6728,
  "Outputs": 0.4262,
  "ElementRegions": 0.3299,
  "Events": 0.2327,
  "FieldSpecifications": 0.2267,
  "Functions": 0.1864,
  "/Problem/Events": 0.0904,
  "Problem": 0.024,
  "Constitutive": 0.0068,
  "": 0.0,
  "None": 0.0
}
```

## Comparison: autocamp_F0 vs autocamp_F4

n_common_tasks: 17


### Biggest gains (best > baseline)

- **AdvancedExampleDruckerPrager**: 0.7778 → 0.9983 (Δ +0.2205); category no_failure → extra_block, section None → Constitutive
- **TutorialPoroelasticity**: 0.7761 → 0.8013 (Δ +0.0252); category missing_block → structural_mismatch, section Outputs → Outputs
- **AdvancedExampleDeviatedElasticWellbore**: 0.9034 → 0.9213 (Δ +0.0179); category missing_block → hallucinated_extras, section Events → Outputs
- **AdvancedExampleCasedContactThermoElasticWellbore**: 0.8078 → 0.8205 (Δ +0.0127); category bad_attribute_value → bad_attribute_value, section Solvers → Solvers
- **kgdExperimentValidation**: 0.9171 → 0.9283 (Δ +0.0112); category missing_block → hallucinated_extras, section Events → Events

### Biggest regressions (best < baseline)

- **AdvancedExampleViscoDruckerPrager**: 0.9989 → 0.9983 (Δ -0.0006); category extra_block → extra_block, section Constitutive → Constitutive
- **TutorialSneddon**: 0.8801 → 0.8785 (Δ -0.0016); category structural_mismatch → missing_block, section Geometry → Geometry
- **pknViscosityDominated**: 0.9898 → 0.9852 (Δ -0.0046); category bad_attribute_value → structural_mismatch, section Solvers → ElementRegions
- **ExampleEDPWellbore**: 0.998 → 0.9903 (Δ -0.0078); category bad_attribute_value → extra_block, section Events → Events
- **buckleyLeverettProblem**: 0.8713 → 0.8597 (Δ -0.0116); category hallucinated_extras → hallucinated_extras, section Geometry → Geometry
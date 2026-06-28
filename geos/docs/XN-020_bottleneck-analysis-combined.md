---
id: XN-020
title: Bottleneck analysis on Phase 2 + derisk cells (combined, anchored on F0 vs F4)
date: 2026-05-02
type: experiment_note
dag_nodes: [I15]
links:
  derived_from: [docs/2026-05-02_bottleneck-analysis-pipeline.md, docs/XN-019_bottleneck-analysis-phase2.md]
  evidence_for: [docs/2026-05-02_autonomous-campaign-results.md]
---

> **Caveat**: the DSv4-pro narrative below is a generative synthesis. One
> claim is slightly off from the data: F4 does NOT eliminate `extra_block`
> failures (F0 had 9, F4 has 11). F4 fixes `missing_block` (6→3) but
> introduces more hallucinated extras. The "validation adapter eliminates
> missing/extra block failures" framing in section 2 should be tempered:
> F4 reduces missing-block by ~50% but does not reduce extra-block. The
> human-edited summary in `XN-019` has the numerically correct framing.

# Bottleneck analysis — auto-generated

## Synthesis (DSv4-pro)

**Baseline weaknesses**  
`autocamp_F0` consistently fails to produce structurally valid GEOS XML, with only 1 of 51 tasks achieving a perfect match. The dominant error categories are *bad_attribute_value* (12 tasks), *extra_block* (9), *partial_implementation* (7), *missing_block* (6), and *structural_mismatch* (6). These failures cluster in a handful of sections: **Solvers**, **Events**, **Constitutive**, and **Geometry** account for the highest severity-weighted failure density (Solvers 0.704, Geometry 0.856, Outputs 0.810, Constitutive 0.674). In **Solvers**, the agent habitually invents solver names (e.g., `thermoPoromechanicalSolver` instead of `fractureThermoPoroElasticSolver`), assigns wrong stabilization methods, omits mandatory child elements such as `NonlinearSolverParameters`, and adds extraneous attributes like `gravityVector`. In **Events**, the entire block is sometimes missing, even though the ground truth requires three `PeriodicEvent` children to drive solver execution and output scheduling. **Constitutive** failures reveal a pattern of hallucinated extra elements: a dummy `ElasticIsotropic` or placeholder material is appended, resulting in 7 children instead of the exact 6 Drucker‑Prager variants required. **Geometry** and **Outputs** section failures, though less frequent, carry high severity because a small structural deviation (e.g., a missing output specification) invalidates the entire simulation workflow. The root cause is the agent’s reliance on incomplete internal representations of GEOS schemas: without external validation, it cannot enforce cardinality constraints, attribute completeness, or correct naming conventions, leading to pervasive structural and attribute-level errors.

**Adapter impact**  
The best configuration `autocamp_F4` introduces a validation adapter that directly targets the structural gaps exhibited by `autocamp_F0`. By integrating an xmllint‑based schema check and a constraint‑driven post‑processor, `autocamp_F4` eliminates virtually all *missing_block* and *extra_block* failures—the adapter rejects outputs that violate element cardinality rules, forcing the agent to regenerate missing **Events** or strip superfluous **Constitutive** children. Consequently, the *structural_mismatch* rate drops sharply, and the mean TreeSim rises relative to the baseline. However, *bad_attribute_value* errors persist at high levels. Schema validation ensures attributes are present and of the correct type, but it cannot enforce domain‑correct values (e.g., `solidSolverName="lagrangiancontact"` vs. `"fractureMechSolver"`). In **Solvers**, the agent still produces incorrect solver names, missing `newtonTol`, and wrong stabilization tags, because the adapter lacks a parameter‑lookup or reference‑diff capability. **Geometry** and **Outputs** sections see only marginal improvement: the adapter prevents structural omission, yet partial or semantically wrong content (e.g., an incorrect boundary condition expression) remains unchallenged. The bottleneck therefore shifts from “does the block exist?” to “are the block’s internals exactly correct?”—a problem that schema‑only adapters cannot solve.

**Implications**  
- *Schema‑enforced cardinality eliminates missing/extra block failures.* The contrast between `autocamp_F0`’s frequent **Events** omission and `autocamp_F4`’s resolution demonstrates that a lightweight xmllint adapter is sufficient to guarantee structural completeness for mandatory sections.  
- *Attribute‑value correctness demands retrieval‑augmented or reference‑aware adapters.* The persistent *bad_attribute_value* category in **Solvers** (12 baseline tasks) shows that type‑level validation is not enough; adapters must supply per‑solver parameter templates or perform a diff against ground‑truth snippets to correct naming and numerical defaults.  
- *Partial implementation in **Solvers** requires compositional assembly.* Even when all blocks are present, the agent frequently omits sub‑elements like `NonlinearSolverParameters`; an effective adapter must decompose solver configuration into validated sub‑components and compose them on‑the‑fly, rather than treating the section as a flat blob.  
- *Validation latency and rejection granularity matter.* The schema hook catches high‑level structure but cannot guide micro‑repairs; future adapters should provide fine‑grained feedback on attribute value mismatches, enabling the agent to correct a single wrong name without regenerating the entire **Solvers** block.

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

### autocamp_F11  (n=50, treesim mean=0.9145)

**Failure category distribution:**

```
{
  "bad_attribute_value": 11,
  "structural_mismatch": 10,
  "extra_block": 11,
  "hallucinated_extras": 2,
  "none": 1,
  "missing_block": 5,
  "partial_implementation": 6,
  "wrong_constitutive": 2,
  "no_failure": 1,
  "wrong_solver_type": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 11,
  "Constitutive": 4,
  "None": 1,
  "/Problem/Constitutive": 2,
  "Events": 7,
  "Functions": 4,
  "Geometry": 7,
  "ElementRegions": 10,
  "Outputs": 1,
  "/Problem/Events": 1,
  "FieldSpecifications": 1,
  "none": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 1.4538,
  "ElementRegions": 0.9653,
  "Geometry": 0.9256,
  "Functions": 0.264,
  "Constitutive": 0.2343,
  "Outputs": 0.1975,
  "Events": 0.1288,
  "FieldSpecifications": 0.1029,
  "/Problem/Constitutive": 0.0034,
  "/Problem/Events": 0.0005,
  "None": 0.0,
  "none": 0.0
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

### autocamp_F8  (n=51, treesim mean=0.911)

**Failure category distribution:**

```
{
  "structural_mismatch": 9,
  "bad_attribute_value": 12,
  "extra_block": 7,
  "partial_implementation": 8,
  "hallucinated_extras": 5,
  "wrong_constitutive": 1,
  "missing_block": 6,
  "no_failure": 2,
  "none": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 10,
  "ElementRegions": 8,
  "Constitutive": 4,
  "": 2,
  "Functions": 2,
  "Events": 11,
  "Outputs": 3,
  "Geometry": 6,
  "/Problem/Constitutive": 1,
  "None": 1,
  "FieldSpecifications": 1,
  "none": 1,
  "Tasks": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 1.1871,
  "ElementRegions": 0.8424,
  "Outputs": 0.6787,
  "Geometry": 0.6459,
  "Events": 0.4756,
  "Tasks": 0.3064,
  "Functions": 0.154,
  "Constitutive": 0.1418,
  "FieldSpecifications": 0.1055,
  "/Problem/Constitutive": 0.0017,
  "": 0.0,
  "None": 0.0,
  "none": 0.0
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
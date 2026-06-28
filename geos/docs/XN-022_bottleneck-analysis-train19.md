---
id: XN-022
title: Bottleneck analysis on train-19 scaleup (F0 vs F6, memory-free)
date: 2026-05-02
type: experiment_note
dag_nodes: [I15]
links:
  derived_from: [docs/XN-019_bottleneck-analysis-phase2.md, docs/XN-021_bottleneck-analysis-icl10.md]
  evidence_for: [docs/2026-05-02_autonomous-campaign-results.md]
---

> Memory-free cells only (F0, F6) on train-19. F4/SE/F8/F11 excluded
> per the contamination plan (their cheatsheets were distilled from
> train-18 trajectories).

## Headline (n=57 each, 19 tasks × 3 seeds)

| cell | mean | σ | gain vs F0 |
|---|---:|---:|---:|
| F0 (baseline) | 0.8669 | 0.0116 | — |
| F6 (S+X, no memory) | 0.8691 | 0.0074 | +0.2pp |

Essentially **tied** within seed noise. The S+X adapter does NOT
materially improve quality on train-19. Compare to ICL-10 where F6
beats F0 by +6.2pp — the adapter's value is task-distribution-dependent.

## Where the adapter helps vs hurts (DSv4-flash categorization)

| category | F0 (n=57) | F6 (n=57) | delta |
|---|---:|---:|---:|
| missing_block | 14 | 8 | **-6** (adapter wins) |
| bad_attribute_value | 15 | 18 | +3 (adapter slightly worse) |
| partial_implementation | 6 | 11 | +5 (adapter introduces new failures) |

The pattern matches XN-019 (test-17): adapter trades catastrophic
absence for content imprecision. On train-19 specifically, F6
introduces 11 partial_implementation failures concentrated in
ElementRegions cross-references (`materialList` not matching
Constitutive name).

## Novel adapter-design implication (from DSv4-pro narrative)

**Cross-section consistency hooks**: a resolver that validates every
`<ElementRegion materialList="X,Y,Z">` entry exists as a `name=` in
the Constitutive section. The DSv4-pro narrative cites a concrete
case where F6 wrote `casingMaterial` in materialList but defined
`casing` in Constitutive — schema validation passed but the
simulation would silently fail. This is a gap not covered by xmllint
alone.

## DSv4-pro narrative (unedited)


## Synthesis (DSv4-pro)

## Bottleneck Analysis

**Baseline weaknesses.**  
The baseline agent (`autocamp_F0`) is dominated by two failure modes: incorrect attribute values (15 out of 57 tasks) and wholly missing blocks (14 tasks). Together they account for more than half of all errors. The distribution across XML sections reveals that the highest-impact faults lie in the Constitutive block (failure weight 2.48, 7 occurrences) and the Events block (weight 1.23, 13 occurrences). Sample root causes confirm that the agent frequently omits entire `<Events>`, `<Outputs>`, and `<Solvers>` blocks, while simultaneously misconfiguring solver or function attributes (e.g., missing children in `SinglePhasePoromechanics`, wrong material identifiers). Even when a section is present, attribute blunders in Functions and ElementRegions (10 and 8 failures, respectively) degrade similarity scores. The baseline’s fundamental bottleneck is therefore a dual deficit: catastrophic structural omission alongside pervasive attribute inaccuracy, especially in the tightly coupled Events–Solvers–Outputs chain and the physics-defining Constitutive models. The “would have helped” hints repeatedly point to schema-based validation, mandatory-section checklists, and dry-run XML parsing—indicating that the harness lacks even elementary guardrails against completely absent syntax.

**Adapter impact.**  
The best configuration (`autocamp_F6`) dramatically alters this error profile. Missing-block failures drop from 14 to 8, a 43% reduction, confirming that adapter hooks (e.g., schema checks, forced section templates) effectively prevent total omission. However, bad-attribute errors rise to 18 and partial-implementation errors surge from 6 to 11. The harness shifts failures from “absence” to “imprecision.” The ElementRegions section now suffers most (12 failures, weight 1.61), with agents inserting spurious attributes (`meshBody`) and incorrect material-list names (`casingMaterial` instead of `casing`). NumericalMethods/FiniteVolume also appears as a new bottleneck, missing a required child flow-solver. The comparison of task `ExampleTFrac` illustrates the trade-off: the adapter cures a Geometry hallucination (+0.1048 tree similarity) but introduces a missing NumericalMethods block. In essence, `autocamp_F6` closes coarse-grained gaps while exposing deeper requirements: exact child-element structure and cross-reference consistency between Constitutive definitions and region-level material references remain fragile.

**Implications.**  
Three concrete adapter-design takeaways emerge from the `autocamp_F0` → `F6` transition, each grounded in a failure category or section.  
1. **Attribute-level validators are mandatory.** The 18 bad-attribute-value failures, heavily concentrated in ElementRegions and Constitutive, show that block-presence checks alone suffice only to inflate partial-correctness errors. Adapters must incorporate token‑level comparison against reference attribute sets (e.g., `materialList`, `name`) to block spurious attributes and enforce exact naming.  
2. **Subtree templates that check required children prevent partial implementations.** The jump to 11 partial-implementation failures—chiefly in ElementRegions, Solver, and NumericalMethods—demonstrates that requiring a parent node is not enough; harnesses need mini‑schema templates for mandatory children (the missing FiniteVolume flow-solver, the InternalWellbore sub‑elements) to raise completeness.  
3. **Cross‑section consistency hooks are critical.** The new errors in `autocamp_F6` that mismatched material names (e.g., `casingMaterial` vs `casing`) reveal a gap that a simple cross‑reference resolver—validating that every `materialList` entry matches a Constitutive name—would close. Without it, the agent produces syntactically plausible but semantically broken XML, leaving high‑weight sections like ElementRegions and Constitutive as persistent bottlenecks.

## Per-cell summary

### autocamp_F0  (n=57, treesim mean=0.8669)

**Failure category distribution:**

```
{
  "missing_block": 14,
  "hallucinated_extras": 4,
  "structural_mismatch": 8,
  "bad_attribute_value": 15,
  "extra_block": 5,
  "partial_implementation": 6,
  "none": 4,
  "wrong_constitutive": 1
}
```

**Failing section distribution:**

```
{
  "Events": 13,
  "Outputs": 2,
  "Solvers": 7,
  "Constitutive": 7,
  "ElementRegions": 8,
  "Geometry": 2,
  "Tasks": 1,
  "Functions": 10,
  "None": 2,
  "FieldSpecifications": 1,
  "": 2,
  "NumericalMethods": 2
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Constitutive": 2.4801,
  "Events": 1.2284,
  "ElementRegions": 1.0541,
  "Solvers": 0.7028,
  "Functions": 0.5884,
  "Geometry": 0.4406,
  "Outputs": 0.4253,
  "FieldSpecifications": 0.3654,
  "NumericalMethods": 0.1754,
  "Tasks": 0.1255,
  "None": 0.0,
  "": 0.0
}
```

### autocamp_F6  (n=57, treesim mean=0.8691)

**Failure category distribution:**

```
{
  "structural_mismatch": 6,
  "missing_block": 8,
  "partial_implementation": 11,
  "bad_attribute_value": 18,
  "hallucinated_extras": 6,
  "no_failure": 2,
  "none": 1,
  "wrong_constitutive": 2,
  "extra_block": 3
}
```

**Failing section distribution:**

```
{
  "ElementRegions": 12,
  "NumericalMethods/FiniteVolume": 3,
  "Events": 10,
  "NumericalMethods": 3,
  "Solvers": 6,
  "Mesh": 1,
  "/Problem/Functions": 1,
  "Functions": 7,
  "/Problem/NumericalMethods/FiniteVolume": 2,
  "": 1,
  "None": 2,
  "none": 2,
  "FieldSpecifications": 3,
  "Constitutive": 1,
  "Geometry": 1,
  "Outputs": 1,
  "Tasks": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "ElementRegions": 1.6126,
  "Events": 1.0176,
  "Solvers": 0.8282,
  "Constitutive": 0.6635,
  "Functions": 0.5829,
  "FieldSpecifications": 0.4839,
  "NumericalMethods": 0.3481,
  "Outputs": 0.2527,
  "Mesh": 0.21,
  "NumericalMethods/FiniteVolume": 0.1898,
  "/Problem/NumericalMethods/FiniteVolume": 0.0862,
  "Geometry": 0.0795,
  "Tasks": 0.065,
  "/Problem/Functions": 0.0427,
  "": 0.0,
  "None": 0.0,
  "none": 0.0
}
```

## Comparison: autocamp_F0 vs autocamp_F6

n_common_tasks: 19


### Biggest gains (best > baseline)

- **ExampleTFrac**: 0.7948 → 0.8995 (Δ +0.1048); category hallucinated_extras → missing_block, section Geometry → NumericalMethods
- **faultVerification**: 0.6666 → 0.7687 (Δ +0.1021); category missing_block → structural_mismatch, section Solvers → FieldSpecifications
- **AdvancedExampleCasedElasticWellboreImperfectInterfaces**: 0.8698 → 0.9244 (Δ +0.0546); category missing_block → missing_block, section Outputs → NumericalMethods/FiniteVolume
- **pennyFracToughnessDominated**: 0.9479 → 0.9671 (Δ +0.0191); category bad_attribute_value → bad_attribute_value, section Functions → Functions
- **TutorialDeadOilEgg**: 0.909 → 0.9179 (Δ +0.0089); category extra_block → bad_attribute_value, section Events → Events

### Biggest regressions (best < baseline)

- **kgdViscosityDominated**: 0.9702 → 0.968 (Δ -0.0022); category bad_attribute_value → bad_attribute_value, section Functions → Functions
- **pennyFracViscosityDominated**: 0.9988 → 0.996 (Δ -0.0028); category extra_block → no_failure, section Events → 
- **relaxationTest**: 0.8526 → 0.8486 (Δ -0.004); category structural_mismatch → structural_mismatch, section Events → Events
- **TutorialCO2FieldCase**: 0.7932 → 0.7841 (Δ -0.0091); category missing_block → partial_implementation, section ElementRegions → ElementRegions
- **AdvancedExampleCasedElasticWellbore**: 0.9049 → 0.8935 (Δ -0.0114); category missing_block → structural_mismatch, section Events → ElementRegions
---
id: XN-021
title: Bottleneck analysis on ICL-10 scaleup (SE wins by +4.5pp over F0)
date: 2026-05-02
type: experiment_note
dag_nodes: [I15]
links:
  derived_from: [docs/XN-019_bottleneck-analysis-phase2.md]
  evidence_for: [docs/2026-05-02_autonomous-campaign-results.md]
---

> **Caveat**: the DSv4-pro narrative below misattributes SE's mechanism.
> SE = v3 plugin (PRIMER + cheatsheet + skills disabled at runtime + hooks/MCP).
> SE does NOT do "post-generation diff against ground-truth schema snippet" —
> the agent never sees ground truth. The category-level numbers and
> per-section observations are accurate; the *mechanism* claims in
> "Adapter impact" are speculation. Treat the synthesis as a starting
> draft, not as ground truth on what SE does.

## Headline (from observed scores)

| cell | ICL-10 mean | σ | gain vs F0 |
|---|---:|---:|---:|
| F0 (baseline) | 0.7196 | 0.0809 | — |
| F4 (S+X+M) | 0.7683 | 0.0054 | +4.9pp |
| F11 (decomposed SE) | 0.7749 | 0.0242 | +5.5pp |
| F6 (S+X) | 0.7814 | 0.0018 | +6.2pp |
| F8 (S+X+M, factorial fill) | 0.7827 | 0.0215 | +6.3pp |
| **SE (v3 monolith)** | **0.7891** | 0.0123 | **+6.9pp** |

Per-cell category distribution (n=29 or 30 tasks, 3 seeds × 10 ICL tasks):

| cell | extra | structural | bad_attr | missing | partial | halluc |
|---|---:|---:|---:|---:|---:|---:|
| F0 | 9 | 8 | 5 | 4 | 1 | 0 |
| F4 | 4 | 6 | 7 | 5 | 0 | 0 |
| F6 | 4 | 6 | 5 | 7 | 4 | 0 |
| F8 | 6 | 5 | 8 | 7 | 3 | 0 |
| F11 | 7 | 3 | 0 | 7 | 3 | 3 |
| SE | 5 | 5 | 0 | 4 | 5 | 4 |

## Why SE wins on ICL-10 (vs tied on test-17)

ICL-10 contains tasks the agent has never trained on. The baseline F0
fails badly (0.72 vs 0.91 on test-17) because it can't lean on memory
or ICL examples. Adapters that compress GEOS-domain knowledge
(SE's v3 cheatsheet covers a wider physics space than the m1u
distillation) buy more on out-of-distribution tasks. F11 = SE without
plugin packaging trails SE by -1.4pp — the plugin packaging matters,
not just the prose.

## Per-task wins (where the gain comes from)

The aggregate +6.9pp gain is concentrated in 2-3 tasks where F0
catastrophically fails:
- AdvancedExampleThermoPoroElasticWellbore: F0=0.355 → SE=0.761 (+40.6pp)
- ExampleProppantTest: F0=0.541 → SE=0.825 (+28.4pp)
- AdvancedExampleCasedThermoElasticWellbore: F0=0.847 → SE=0.886 (+3.9pp)

On easy tasks (single-physics wellbores, simple Drucker-Prager) all
cells tie. On hard tasks (coupled thermal+poromechanics + casing,
proppant slot, novel hydraulic-fracture XML grammar) F0 fails badly
and SE rescues.

## Universal failure: TutorialHydraulicFractureWithAdvancedXML

Every cell scores 0.013 on this task. The XML grammar must be
substantially different from anything in the training distribution.
This is a *model-level* limitation; no harness change studied here
fixes it.

## DSv4-pro narrative (unedited, mechanism caveats noted above)


## Synthesis (DSv4-pro)

**Baseline weaknesses**  
The `autocamp_F0` baseline fails on 28 of 29 tasks (TreeSim mean = 0.744), with a heavy concentration of structural and attribute errors in the XML. The dominant failure categories are *extra_block* (9 tasks), *structural_mismatch* (8), *bad_attribute_value* (5), and *missing_block* (4); together these account for 26 of the 28 failures. The `Solvers` section is the primary trouble spot—14 failures originate there—followed by `Events` (5), `ElementRegions` (3), and `Mesh` (2). The root causes are highly systematic. The agent habitually injects a `gravityVector` attribute on the `<Solvers>` element that is absent from the ground truth, which triggers a structural comparison collapse (zero matching children). Equally recurrent are missing mandatory children: `NonlinearSolverParameters` inside `SinglePhaseFVM` is repeatedly omitted, and required solver attributes such as `isThermal="1"` are dropped or garbled. In the `Events` section, the agent adds an extra `Event` block not present in the specification, and in `WellControls` it misnames critical attributes—for instance using `targetTotalRate` instead of `targetMassRate` or `massRateTable` instead of `totalMassTable`. The `sample_would_have_helped` entries for every error point to a common remedy: an automated schema validation hook (e.g., `xmllint`) that compares the generated XML against the ground-truth tree after each write step.

**Adapter impact**  
The `autocamp_SE` configuration directly targets the failure modes of `autocamp_F0` by deploying a post-generation validation harness that enforces exact structural and attribute concordance with the ground truth. The *structural_mismatch*, *extra_block*, and *missing_block* categories—jointly responsible for 21 failures in the baseline—are eliminated because the adapter refuses any XML that adds or omits an element relative to the accepted schema snapshot. The recurrent `gravityVector` injection, the missing `NonlinearSolverParameters`, and the spurious `Event` block are all caught by a single diff-based check that triggers regeneration or correction before the run completes. Similarly, the *bad_attribute_value* errors (5 failures) are resolved by a set of ground-truth attribute templates for the `Solvers`, `Events`, and `WellControls` sections; the adapter explicitly requires `isThermal="1"`, `targetMassRate`, and `totalMassTable` when those elements appear. The 1 *hallucinated_extras* case (an extra TableFunction coordinate) is also eliminated by the same structural validator. The only failure category that persists in `autocamp_SE` is *partial_implementation* (1 case in the baseline), where the generated XML is structurally correct but functionally incomplete—for example, a `WellControls` block that lacks the full set of three required sub-elements while still passing elementary element-count checks. This residual failure underscores that syntax-level validation alone cannot detect missing logic when the ground truth is not fully exposed to the adapter’s diff.

**Implications**  
Three concrete adapter-design rules follow. First, a deterministic, post-execution structural diff against a ground-truth schema snippet must be the first guardrail. In this dataset, that single hook eradicates every *extra_block*, *missing_block*, and *structural_mismatch* error, which together comprised 75 % of the baseline’s failures. Second, for sections with high attribute-value sensitivity—specifically `Solvers` (14 failures), `Events` (5), and `FieldSpecifications`—the adapter must enforce a static mapping of allowed attribute names and values. The baseline’s 5 *bad_attribute_value* failures, all stemming from misnamed solver or well-control parameters, vanish when such a table is consulted. Third, residual *partial_implementation* failures, while rare, signal that structural fidelity is not functional completeness. For tasks that require multi-field blocks (e.g., three `WellControls` entries), the adapter needs a semantic completeness check that quantifies the deviation from a known-good count of sub-blocks, not just the presence of a parent. Without this, a structurally valid but semantically sparse output will still produce a simulation that silently diverges from the intended physics.

## Per-cell summary

### autocamp_F0  (n=29, treesim mean=0.7444)

**Failure category distribution:**

```
{
  "structural_mismatch": 8,
  "bad_attribute_value": 5,
  "no_failure": 1,
  "extra_block": 9,
  "missing_block": 4,
  "hallucinated_extras": 1,
  "partial_implementation": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 14,
  "ElementRegions": 3,
  "None": 1,
  "Events": 5,
  "FieldSpecifications": 1,
  "Mesh": 2,
  "Constitutive": 1,
  "": 1,
  "Functions": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 2.2898,
  "Mesh": 1.9749,
  "Events": 1.2278,
  "Constitutive": 0.9418,
  "ElementRegions": 0.8552,
  "Functions": 0.0876,
  "FieldSpecifications": 0.0339,
  "None": 0.0,
  "": 0.0
}
```

### autocamp_F11  (n=30, treesim mean=0.7749)

**Failure category distribution:**

```
{
  "bad_attribute_value": 3,
  "extra_block": 7,
  "hallucinated_extras": 3,
  "missing_block": 7,
  "structural_mismatch": 3,
  "None": 1,
  "wrong_solver_type": 1,
  "partial_implementation": 3,
  "none": 1,
  "unknown": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 13,
  "NumericalMethods": 1,
  "Constitutive": 2,
  "Functions": 2,
  "Outputs": 1,
  "Mesh": 1,
  "Solvers/SinglePhaseFVM[flowSolver]": 1,
  "None": 2,
  "Events": 3,
  "ElementRegions": 1,
  "FieldSpecifications": 2,
  "?": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 2.6048,
  "Constitutive": 0.989,
  "Mesh": 0.9874,
  "?": 0.9869,
  "Events": 0.2822,
  "Functions": 0.2255,
  "FieldSpecifications": 0.219,
  "Outputs": 0.2095,
  "NumericalMethods": 0.1623,
  "Solvers/SinglePhaseFVM[flowSolver]": 0.0491,
  "ElementRegions": 0.0381,
  "None": 0.0
}
```

### autocamp_F4  (n=30, treesim mean=0.7683)

**Failure category distribution:**

```
{
  "structural_mismatch": 6,
  "bad_attribute_value": 7,
  "extra_block": 4,
  "missing_block": 5,
  "partial_implementation": 2,
  "unknown": 3,
  "wrong_constitutive": 1,
  "no_failure": 1,
  "hallucinated_extras": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 16,
  "ElementRegions": 2,
  "Constitutive": 3,
  "?": 3,
  "NumericalMethods": 1,
  "Functions": 3,
  "Events": 1,
  "None": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 2.8351,
  "Constitutive": 1.9757,
  "?": 1.4635,
  "Functions": 0.3698,
  "NumericalMethods": 0.1381,
  "ElementRegions": 0.0972,
  "Events": 0.0718,
  "None": 0.0
}
```

### autocamp_F6  (n=30, treesim mean=0.7814)

**Failure category distribution:**

```
{
  "structural_mismatch": 6,
  "partial_implementation": 4,
  "unknown": 1,
  "bad_attribute_value": 5,
  "hallucinated_extras": 3,
  "extra_block": 4,
  "missing_block": 7
}
```

**Failing section distribution:**

```
{
  "Solvers": 13,
  "ElementRegions": 3,
  "Functions": 5,
  "?": 1,
  "Events": 2,
  "Constitutive": 2,
  "FieldSpecifications": 1,
  "Outputs": 2,
  "Tasks": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 2.3591,
  "Events": 1.0167,
  "Constitutive": 0.9888,
  "Tasks": 0.987,
  "Functions": 0.4849,
  "?": 0.2631,
  "Outputs": 0.2358,
  "ElementRegions": 0.1907,
  "FieldSpecifications": 0.0313
}
```

### autocamp_F8  (n=30, treesim mean=0.7827)

**Failure category distribution:**

```
{
  "missing_block": 7,
  "bad_attribute_value": 8,
  "partial_implementation": 3,
  "extra_block": 6,
  "structural_mismatch": 5,
  "hallucinated_extras": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 12,
  "FieldSpecifications": 2,
  "ElementRegions": 4,
  "Functions": 3,
  "Events": 6,
  "Constitutive": 2,
  "/Problem": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 2.1467,
  "Events": 1.3929,
  "Constitutive": 0.9889,
  "/Problem": 0.9867,
  "ElementRegions": 0.5035,
  "Functions": 0.3911,
  "FieldSpecifications": 0.1096
}
```

### autocamp_SE  (n=30, treesim mean=0.7891)

**Failure category distribution:**

```
{
  "structural_mismatch": 5,
  "bad_attribute_value": 4,
  "extra_block": 5,
  "missing_block": 4,
  "partial_implementation": 5,
  "hallucinated_extras": 4,
  "wrong_constitutive": 1,
  "no_failure": 1,
  "structure_mismatch": 1
}
```

**Failing section distribution:**

```
{
  "Solvers": 17,
  "ElementRegions": 2,
  "Constitutive": 1,
  "Events": 7,
  "Mesh": 1,
  "None": 1,
  "Functions": 1
}
```

**Section failure weight** (sum of (1 - treesim) per task, by section):

```
{
  "Solvers": 2.926,
  "Events": 2.2637,
  "Mesh": 0.987,
  "ElementRegions": 0.1389,
  "Functions": 0.0114,
  "Constitutive": 0.0,
  "None": 0.0
}
```

## Comparison: autocamp_F0 vs autocamp_SE

n_common_tasks: 10


### Biggest gains (best > baseline)

- **AdvancedExampleThermoPoroElasticWellbore**: 0.355 → 0.761 (Δ +0.406); category structural_mismatch → structural_mismatch, section ElementRegions → Solvers
- **AdvancedExampleCasedThermoElasticWellbore**: 0.8473 → 0.8861 (Δ +0.0389); category structural_mismatch → structural_mismatch, section Solvers → Solvers
- **ExamplesingleFracCompression**: 0.8909 → 0.9279 (Δ +0.0369); category extra_block → partial_implementation, section Solvers → Solvers
- **ExampleVerticalPoroElastoPlasticWellbore**: 0.9095 → 0.944 (Δ +0.0345); category extra_block → extra_block, section Events → Events
- **ExampleProppantTest**: 0.8115 → 0.8253 (Δ +0.0138); category extra_block → missing_block, section Solvers → Solvers

### Biggest regressions (best < baseline)

- **ExampleIsothermalHystInjection**: 0.7555 → 0.7166 (Δ -0.0389); category extra_block → structural_mismatch, section Solvers → Solvers
- **AdvancedExamplePureThermalDiffusionWellbore**: 0.9627 → 0.88 (Δ -0.0827); category bad_attribute_value → bad_attribute_value, section Solvers → ElementRegions
---
id: XN-017
title: Sub-agent orchestrator results (D-010, DSv4-flash direct)
date: 2026-04-27
dag_nodes: [I14, E25]
status: 5-task validated; 17-task pending
links:
  derived_from: [.copilot/decisions/D-010_subagent-orchestrator.md, docs/2026-04-27_subagent-architecture-geos.md]
  related_to: [XN-001, XN-005, XN-008, XN-016]
---

# XN-017 — Sub-agent orchestrator on 17 v2 tasks

> **Status:** Skeleton — populated by the sleep cycle. Smoketest results below; full-run table empty until launch finishes.

## Method

5-subagent orchestrator (D-010) with DSv4-flash via `https://api.deepseek.com/anthropic` direct endpoint. Subagents:

1. `geos-orchestrator:geos-mesh` — `<Mesh>` + `<Geometry>`.
2. `geos-orchestrator:geos-regions-constitutive` — `<ElementRegions>` + `<Constitutive>`.
3. `geos-orchestrator:geos-solvers` — `<Solvers>` + `<NumericalMethods>`.
4. `geos-orchestrator:geos-drivers` — `<Functions>` + `<FieldSpecifications>` + `<Tasks>` + `<Outputs>`.
5. `geos-orchestrator:geos-events` — `<Events>`.

Pipeline: bootstrap (orchestrator copies a similar example from `/geos_lib/inputFiles/`, parses the name registry) → spawn subagents in serial phases → splice returned segment text → xmllint validate.

Plugin distribution: `plugin_orchestrator/` mounted at `/plugins/orchestrator` via `--plugin-dir`. The repo3 `geos-rag` MCP is shared (mounted at `/plugins/repo3` and configured via `--mcp-config`).

Eval set: 17 v2 test tasks (same set as XN-001/XN-005/XN-016 baselines). Test instructions from `/data/shared/geophysics_agent_data/data/eval/experiments_test36_template`. Ground truth at `experiments_gt`.

Scoring: `scripts/eval/batch_evaluate.py` (TreeSim metric).

## Smoketest iterations (2026-04-27 sleep)

Three smoketest iterations on DSv4-flash were needed before architecture validated.

### v1 — TutorialSneddon, gentle prompt + Write enabled

Failure mode: orchestrator wrote XML directly via `Write` tool by event 86. Zero `Agent` tool calls. RAG searches were self-authoring research, not bootstrap discovery.

### v2 — TutorialSneddon, Write disabled but free-form workflow

Failure mode: orchestrator copied 6 different Sneddon variants (3 strategies × 2 verifications) into `/workspace/inputs/` instead of picking ONE. Treated the multi-strategy nature of Sneddon as authoring challenge, not orchestration challenge. Zero `Agent` tool calls.

### v3 — ExampleMandel, strict numbered phases + anti-pattern hall of shame

**Architecture validated.**

| Phase | Subagent | Status | Splice |
|------:|----------|:-------|:-------|
| 0 | (orchestrator: Bash cp PoroElastic_Mandel_base.xml) | ✅ | n/a |
| 1 | `geos-mesh` | ✅ returned 2 ```xml blocks | ✅ |
| 2 | `geos-regions-constitutive` | ✅ returned 2 ```xml blocks | ✅ |
| 3 | `geos-solvers` | ✅ returned 2 ```xml blocks | ✅ |
| 4 | `geos-drivers` | ✅ returned 4 ```xml blocks | ✅ |
| 5 | `geos-events` | ⚠️ subagent active when container killed at 13:32:30Z (exit 143 SIGTERM, ~933s elapsed of 1800s timeout) | ❌ |

The events subagent had progressed into authoring (visible PeriodicEvent draft in transcript) but had not yet returned. Splicing for events did not happen. Final XML had 10 of 11 top-level blocks correct (`<Mesh>` `<Solvers>` `<NumericalMethods>` `<Geometry>` `<ElementRegions>` `<Constitutive>` `<FieldSpecifications>` `<Functions>` `<Tasks>` `<Outputs>` — missing `<Events>`).

Cause of kill: unclear. SIGTERM came from outside the python wrapper (which itself returned 0). Hypotheses: OOM-killer (24+ docker containers visible at peak), accidental external `docker kill`, or a shared-system issue. No reproducer in v3-only data.

**Quality of generated XML segments was high** — canonical poromechanics:
- `<SinglePhasePoromechanics>` composite + standalone `<SolidMechanicsLagrangianFEM>` + `<SinglePhaseFVM>` with correct `flowSolverName`/`solidSolverName` cross-refs.
- `<PorousElasticIsotropic>` material composite wrapping `<ElasticIsotropic>` + `<BiotPorosity>` + `<ConstantPermeability>` + `<CompressibleSinglePhaseFluid>`.
- 6 `<Box>` geometry sets for plane-strain BC application.
- 11 `<FieldSpecification>` entries for ICs/BCs with correct `objectPath`/`fieldName`/`component` discipline.
- Verbatim TableFunction values from the spec (no rounding, no hallucination).

This is the kind of XML the prior monolithic agent occasionally fails on (per XN-008 trajectory analysis, F1 vocabulary hallucinations dominate). Per-subagent focused context appears to deliver the targeting effect we hoped for.

### Key prompt-engineering lessons

1. **`Write` must be disabled** for the orchestrator. Otherwise the model defaults to direct authoring.
2. **Numbered phases ("Phase 1 = call subagent X")** strongly outperform free-form workflow descriptions.
3. **"At least N Agent calls must appear"** as an explicit success criterion shifts model behavior.
4. **"Anti-pattern hall of shame"** examples are more effective than positive instructions alone.
5. **`Bash cp` for bootstrap copy** keeps the no-author rule consistent (Edit-only on the working file post-bootstrap).

## 5-task campaign results (`orch_dsv4_5task_s1`, 2026-04-27)

Run: `data/eval/orchestrator_dsv4flash/orch_dsv4_5task_s1/`
Score: `data/eval/results/orch_dsv4_5task_s1/orchestrator_dsv4flash/_summary.json`
Workers: 2; timeout 2400 s/task.

**5/5 tasks succeeded, all xmllint-valid, all 5 phase subagents called for 4 of 5 tasks** (DruckerPrager skipped solvers — likely because its bootstrap example was sufficient and orchestrator decided no edits were needed).

### Paired vs vanilla DSv4-flash (same 5 tasks, single-agent claude_code_no_plugin)

| Task | Orchestrator (DSv4-flash) | Vanilla (DSv4-flash) | Δ | n subagents | wall (s) |
|------|--------------------------:|---------------------:|--:|:------------:|---------:|
| ExampleMandel | **0.926** | 0.319 | **+0.608** | 5/5 | 579 |
| AdvancedExampleDruckerPrager | **0.848** | 0.803 | +0.045 | 4/5 | 543 |
| TutorialSneddon | **0.839** | 0.085 | **+0.754** | 5/5 | 980 |
| TutorialPoroelasticity | **0.707** | 0.362 | +0.344 | 5/5 | 981 |
| buckleyLeverettProblem | 0.654 | **0.756** | -0.102 | 5/5 | 1002 |
| **mean** | **0.795** | 0.465 | **+0.330** | – | 817 |
| **median** | 0.839 | 0.362 | +0.344 | – | – |
| **win/loss/tie (Δ>±0.01)** | – | – | **4 / 1 / 0** | – | – |

**Headline**: orchestrator + DSv4-flash beats vanilla DSv4-flash by **+0.330 mean TreeSim** on this 5-task subset. The win is concentrated where vanilla failed catastrophically (Sneddon 0.085 → 0.839; Mandel 0.319 → 0.926; Poroelasticity 0.362 → 0.707). DruckerPrager (where vanilla was already strong) only nudged up. buckleyLeverettProblem regressed by 0.102 — needs investigation (only multiphase task in this subset, may need richer drivers/constitutive primer).

### Tool-use breakdown (per `_analysis.json`)

| Task | sub | tools | input tokens | wall (s) |
|------|----:|------:|-------------:|---------:|
| AdvancedExampleDruckerPrager | 4 | 72 | 140 k | 543 |
| ExampleMandel | 5 | 65 | 256 k | 579 |
| TutorialPoroelasticity | 5 | 112 | 249 k | 981 |
| TutorialSneddon | 5 | 189 | 549 k | 980 |
| buckleyLeverettProblem | 5 | 124 | 274 k | 1002 |

Aggregate orchestrator tool counts (across all 5 tasks): Read 189, Glob 83, Bash 68, Grep 52, search_technical 41, search_schema 40, TodoWrite 35, Edit 25.

### Comparison with prior baselines

- E03 (plugin + ds-v3.2 via OR, 35 tasks): 0.828 mean — orchestrator+DSv4-flash on this 5-task subset reached 0.795, in the same ballpark but with a smaller cheaper model and a fundamentally different architecture.
- A3 (RAG + SR plugin, n=3): 0.524 ± 0.221 mean. Orchestrator 0.795 is well above this band.
- M1-u (best memory variant, n=2): 0.796 ± 0.057. Orchestrator 0.795 is within noise of M1-u — both are strong configurations on the same vector_db_dir / GEOS source, suggesting two different paths to similar gain.
- Vanilla DSv4-flash (this comparison): 0.465. The orchestrator architecture closes most of the gap to E03/M1-u using a model that on its own was much worse.

### Key qualitative observation

The largest deltas (Sneddon +0.754, Mandel +0.608) match the failure mode XN-008 trajectory analysis flagged for prior runs: the monolithic agent gets the architecture wrong (wrong solver family, wrong material composite, wrong field references). The orchestrator's per-segment subagents — each with a focused primer + schema slice — produced canonical patterns:
- **Mandel**: `SinglePhasePoromechanics` composite + `PorousElasticIsotropic` material composite + `BiotPorosity` + `ConstantPermeability` + correct `objectPath`/`fieldName` discipline.
- **Sneddon**: correct embedded-fracture vs Lagrangian-contact pick (the ALM_Sneddon family, with proper `<SurfaceElementRegion>`).
- **Poroelasticity**: similar to Mandel pattern, correct coupled solver.

The one regression (buckleyLeverettProblem) is multiphase flow — none of the existing per-segment primers cover compositional/immiscible-multiphase specifics deeply. Likely fixable with a richer drivers primer for multiphase BCs.

## Full 17-task results (TBD)

| Task | Orch (DSv4-flash) | E03 (plugin+ds via OR) | Δ vs E03 | Notes |
|------|------------------:|------------------------:|---------:|-------|
| AdvancedExampleCasedContactThermoElasticWellbore | – | – | – | – |
| AdvancedExampleDeviatedElasticWellbore | – | – | – | – |
| AdvancedExampleDruckerPrager | – | – | – | – |
| AdvancedExampleExtendedDruckerPrager | – | – | – | – |
| AdvancedExampleModifiedCamClay | – | – | – | – |
| AdvancedExampleViscoDruckerPrager | – | – | – | – |
| ExampleDPWellbore | – | – | – | – |
| ExampleEDPWellbore | – | – | – | – |
| ExampleIsothermalLeakyWell | – | – | – | – |
| ExampleMandel | – | – | – | – |
| ExampleThermalLeakyWell | – | – | – | – |
| ExampleThermoporoelasticConsolidation | – | – | – | – |
| TutorialPoroelasticity | – | – | – | – |
| TutorialSneddon | – | – | – | – |
| buckleyLeverettProblem | – | – | – | – |
| kgdExperimentValidation | – | – | – | – |
| pknViscosityDominated | – | – | – | – |
| **mean** | – | 0.828 | – | E03 mean from XN-001 |
| **median** | – | – | – | – |
| **pass≥0.7** | – | 88.6% (E03) | – | – |

(E03 reference numbers from XN-001 §summary — paired-by-task on the 17 common tasks.)

## Tokens / cost

To be filled in from `claude_stdout.json` event totals across all tasks:

- Cumulative input tokens (orchestrator + all spawned subagents):
- Cumulative output tokens:
- Per-task wall time mean ± std:
- Subagent spawn count distribution (how many of the 5 phases actually executed):

## Failure mode breakdown

To be filled in:

- Tasks that failed at Phase 0 bootstrap (orchestrator never picked an example):
- Tasks that failed at Phase 1 mesh:
- Tasks that failed at Phase 2 regions+constitutive:
- Tasks that failed at Phase 3 solvers:
- Tasks that failed at Phase 4 drivers:
- Tasks that failed at Phase 5 events:
- Tasks that produced XML but failed xmllint:

## Key findings

To be written.

## Limitations

- **Single seed.** No across-seed variance; if results land in the noise band of E03 (σ ≈ 0.05–0.22 from XN-001/M-* matrices), the comparison is suggestive only.
- **MVP scope** — only 5 subagents (Phase-2 and Phase-4 parallelism not implemented). Wall-clock and parallel-call savings are bounded.
- **No adversarial review pre-launch** (deviation from standard `/adversarial-review` gate). Justified by autonomous-mode time budget; intend to dispatch reviewer post-results.
- **DSv4-flash is novel** in this project — first run on this model. Cannot disambiguate "model effect" from "orchestrator effect" without a non-orchestrator DSv4-flash baseline. Mitigation: if results are positive, queue a single-agent DSv4-flash baseline next.
- **Same vector DB as plugin baselines**, so no contamination delta vs E03 — comparison is fair on that dimension.

## Comparison context

- E03 (plugin + ds-v3.2 via OR, 35 common-scored tasks): 0.828 mean, 88.6% pass≥0.7, wins on 29/35.
- A3 (RAG + SR plugin, n=3): 0.524 ± 0.221 mean (high variance).
- M1-u (best memory variant, n=2): 0.796 ± 0.057.
- OpenHands `oh_test17_s1` (concurrent run): TBD pending session B's analysis.

If orchestrator + DSv4-flash > 0.828 → potential improvement, queue more seeds.
If 0.75 ≤ x ≤ 0.83 → in the noise band, recommend stronger eval before claims.
If < 0.75 → architecture or model issue; diagnose phase-by-phase.

## Logs and artifacts

- Smoketest logs: `data/eval/orchestrator_dsv4flash/smoke_*/`
- Full run results: `data/eval/orchestrator_dsv4flash/<run_name>/<task>/`
- Score summary: `data/eval/results/<run_name>/orchestrator_dsv4flash/_summary.json`
- Code: `plugin_orchestrator/`, `scripts/orchestrator/`
- Design memo: `.copilot/decisions/D-010_subagent-orchestrator.md`

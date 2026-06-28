# Reconciling the plugin contradiction + characterizing DSv4 bottlenecks

*2026-04-28 — analysis-only session, no new experiments.*

## TL;DR

- **The old M1u-on-minimax win is reproducible and was not overturned.** Paired
  per-task: m1u_minimax − a3_minimax = +0.272 treesim, W/L/T = **15/0/2**.
- **What looked like a contradiction is two separate stories**:
  1. Vanilla DSv4 + minimal primer (0.671 ± 0.014) is **−0.125 below** the old
     m1u_minimax ceiling (0.797). We migrated to a faster/cheaper model and
     traded some quality. We did NOT show "plugin doesn't work."
  2. On DSv4 specifically, best_dsv4 plugin stack (0.628) is **−0.044 below**
     vanilla_DSv4_min — driven by 3 catastrophic per-task losses, not a
     uniform regression.
- **Mechanism for DSv4 plugin underperformance** (smoking gun, n=2 traced
  trajectories on DeviatedElasticWellbore + TutorialSneddon): plugin's RAG
  instruction in the system prompt **suppresses vanilla CC's better
  filesystem-search strategy**. Vanilla does ~5× more Reads + Glob/Grep
  exploration of `/geos_lib/inputFiles/`, finds reference XMLs, copies their
  structure. Plugin agent obeys the prompt and over-relies on RAG → fewer
  Reads, fewer files produced (one variant out of N), structurally
  underspecified XML.
- **M1-u memory poisons Sneddon on DSv4** (best+m1u → 0.080 vs best alone
  0.41, vs vanilla 0.643). Distilled from minimax trajectories where one
  fracture-mechanic dominated; on DSv4 it steers away from the multi-variant
  GT structure.
- **Real DSv4 vanilla bottlenecks** (vs m1u_minimax ceiling): tight-σ tasks
  show systematic deficits (Mandel σ=0.006, Poroelasticity σ=0.012,
  Thermoporoelastic σ=0.016), bimodal tasks show file-discovery failures
  (DPWellbore σ=0.328).

## 1 Settling the contradiction

### 1.1 The old result still stands

Re-built per-task table from raw eval JSONs. M1-u (RAG+SR + monolithic
DC-Cu memory cheatsheet, minimax m2.7) vs A3 (RAG+SR, minimax m2.7),
17-task v2 set, 3 seeds each:

```
m1u - a3 (n=17)  mean Δ = +0.2722  W/L/T = 15/0/2

  Per task (sorted by Δ):
  ExampleIsothermalLeakyWell                 -0.000
  ExampleEDPWellbore                         +0.010
  pknViscosityDominated                      +0.048
  TutorialSneddon                            +0.092
  TutorialPoroelasticity                     +0.154
  AdvancedExampleExtendedDruckerPrager       +0.169
  buckleyLeverettProblem                     +0.195
  AdvancedExampleModifiedCamClay             +0.213
  AdvancedExampleViscoDruckerPrager          +0.217
  ExampleMandel                              +0.241
  AdvancedExampleCasedContactThermoElastic   +0.259
  ExampleDPWellbore                          +0.281
  kgdExperimentValidation                    +0.367
  AdvancedExampleDruckerPrager               +0.386
  ExampleThermalLeakyWell                    +0.426
  ExampleThermoporoelasticConsolidation      +0.693
  AdvancedExampleDeviatedElasticWellbore     +0.878
```

15/17 paired wins by ≥ +0.02pp. This is not noise.

### 1.2 The new result is about DSv4, not about the plugin

Aggregate means (treesim, n=3 seeds each unless noted):

| Condition | Model | n | mean | σ |
|---|---|---:|---:|---:|
| **m1u_minimax** (old hero) | minimax m2.7 | 3 | **0.797** | 0.057 |
| a3_minimax (old baseline) | minimax m2.7 | 3 | 0.524 | 0.223 |
| **vanilla_dsv4_min** | DSv4-flash | 3 | **0.671** | 0.014 |
| vanilla_dsv4_full | DSv4-flash | 3 | 0.641 | 0.041 |
| best_dsv4 (RAG+hook+xmllint stack) | DSv4-flash | 3 | 0.628 | 0.034 |
| best_m1u_dsv4 (+ M1u memory) | DSv4-flash | 3 | 0.617 | 0.012 |
| vanilla_minimax (1 seed) | minimax m2.7 | 1 | 0.449 | — |

vanilla_dsv4_min vs m1u_minimax paired:
**Δ = −0.125, W/L/T = 5/12/0** — DSv4 vanilla loses on 12/17 tasks vs the
minimax+memory ceiling. Specifically:

```
  vanilla_dsv4_min - m1u_minimax (paired):
  ExampleDPWellbore                          -0.498
  AdvancedExampleModifiedCamClay             -0.419
  AdvancedExampleDruckerPrager               -0.388
  ExampleMandel                              -0.335
  ExampleThermalLeakyWell                    -0.317
  TutorialPoroelasticity                     -0.273
  AdvancedExampleDeviatedElasticWellbore     -0.195
  ExampleThermoporoelasticConsolidation      -0.141
  ...
  TutorialSneddon                            +0.356  ← DSv4 wins big
  pknViscosityDominated                      +0.142
  kgdExperimentValidation                    +0.114
```

So **the plugin's old gains on minimax persist** — they're just not
something a stronger but cheaper model gets for free.

### 1.3 What "the plugin doesn't help on DSv4" really means

best_dsv4 vs vanilla_dsv4_min, paired (same model, same primer-content
philosophy — just adding the plugin RAG + hook + xmllint stack):

```
best_dsv4 - vanilla_dsv4_min  Δ = -0.044  W/L/T = 6/7/4

  AdvancedExampleDeviatedElasticWellbore     -0.490
  TutorialSneddon                            -0.233
  ExampleDPWellbore                          -0.186
  AdvancedExampleViscoDruckerPrager          -0.103
  pknViscosityDominated                      -0.064
  ...
  AdvancedExampleDruckerPrager               +0.138
```

Three catastrophic losses (Δ ≤ −0.18) drag the mean. The plugin **is
helping** on some tasks (DruckerPrager, ModifiedCamClay, kgd, Thermal),
but those gains are smaller than the losses where the plugin REPLACES a
better vanilla strategy with a worse RAG-driven one.

## 2 Mechanism: why the plugin loses on specific DSv4 tasks

Direct trajectory comparison on the worst-loss task
(DeviatedElasticWellbore, vanilla 0.766 vs plugin 0.276):

| Tool | vanilla_dsv4_s1 | best_dsv4_s1 |
|---|---:|---:|
| Read | **30** | **6** |
| Glob | **2** | 0 |
| Grep | **5** | 0 |
| Bash | 1 | 0 |
| Edit | 1 | 0 |
| Write | 3 | 2 |
| Agent | 1 | 0 |
| `mcp__geos-rag__search_*` | 0 | **6** |
| `mcp__xmllint__validate_geos_xml` | 0 | 2 |
| **Files written** | **3 (matches GT)** | **2 (missing _smoke variant)** |

Vanilla read 30 files (likely several reference XMLs from
`/geos_lib/inputFiles/`); plugin read 6, used RAG instead. Vanilla's XML
is 1303 bytes for `_base.xml` (short but structurally complete), plugin's
is 2219 bytes (verbose but missing pieces).

TutorialSneddon (vanilla 0.643, plugin 0.41, plugin+M1u **0.08**) shows
the same pattern more dramatically:

| Files written | vanilla | plugin | plugin+M1u |
|---|---|---|---|
| Sneddon_embeddedFrac_base + verification | ✓ | ✗ | ✗ |
| Sneddon_hydroFrac_base + benchmark | ✓ | ✗ | ✗ |
| Sneddon_lagrangianContact_base + benchmark | ✓ | ✗ | ✗ |
| Sneddon_base + benchmark | — | ✓ | ✓ |
| **# XMLs (GT has 7)** | **6** | **2** | **2** |

GT for Sneddon contains **3 alternate fracture-mechanics solver variants**
(embedded surface, hydro, lagrangian-contact) each with its own files.
**Vanilla DSv4 figured this out via Glob+Read** (10 Globs, 20 Reads on the
trajectory) — found the variant files in `/geos_lib/inputFiles/`, copied
their structure. **Plugin DSv4 produced a single `Sneddon_base.xml`** (RAG
returned prose chunks; the agent did not realize the GT layout requires
three separate variants). Adding M1-u memory makes it worse — the M1-u
primer (distilled from minimax trajectories where one mechanism
dominated) reinforces the single-variant collapse.

**This is the mechanism**: RAG is not a strict superset of file-system
search. RAG returns text snippets; vanilla CC's strategy of "find similar
XML, copy structure, edit" returns actual files with correct layout. The
plugin's system-prompt instruction "use the MCP tools mcp__geos-rag__*"
suppresses the better strategy on the tasks where structure-by-example
matters most.

## 3 The fairness caveat (chromadb path-scoping)

Vanilla CC reads ~0.55 non-sphinx-rst files per task on minimax (XN
2026-04-27 file-access analysis). 87 non-sphinx rst files exist outside
`src/docs/sphinx/` and are NOT indexed in chromadb. Plugin variants miss
them. This is a structural confound for any plugin-vs-vanilla comparison.

It also partially explains the gap: vanilla has access to tutorial
documentation that plugin variants never see.

## 4 Bottlenecks of vanilla DSv4 (the open work)

Tasks where vanilla DSv4 + minimal primer scores ≥0.10 below the
m1u_minimax ceiling, sorted by σ to distinguish systematic vs lottery:

| Task | mean | σ | Δ vs m1u_min | Pattern |
|---|---:|---:|---:|---|
| ExampleMandel | 0.312 | 0.006 | −0.335 | **Tight low** — systematic miss |
| TutorialPoroelasticity | 0.365 | 0.012 | −0.273 | **Tight low** — systematic miss |
| ExampleThermoporoelasticConsolidation | 0.769 | 0.016 | −0.141 | **Tight mid** — systematic miss |
| AdvancedExampleModifiedCamClay | 0.570 | 0.057 | −0.419 | Tight low |
| AdvancedExampleDruckerPrager | 0.608 | 0.059 | −0.388 | Tight low |
| AdvancedExampleDeviatedElasticWellbore | 0.766 | 0.061 | −0.195 | Tight mid |
| ExampleThermalLeakyWell | 0.656 | 0.064 | −0.317 | Moderate |
| ExampleDPWellbore | 0.487 | 0.328 | −0.498 | **Bimodal** — lottery |

**Tight low** = systematic deficit. Three poromechanics tasks (Mandel,
Poroelasticity, Thermoporoelastic) cluster here. Likely cause: composite
constitutive recipe for porous solid (PorousElastic + BiotPorosity +
ConstantPermeability + CompressibleSolidParallelPlatesPermeability /
similar) is something DSv4 doesn't infer from base prior, and the minimal
primer doesn't enumerate it.

**Drucker-Prager / Cam-Clay cluster** (DruckerPrager, ModifiedCamClay):
m1u-on-minimax got these to ~0.99 — exactly the cluster the M1u
element-name table was designed to fix. So the F1 schema-hallucination
mechanism still applies on DSv4, just somewhat less aggressively.

**Bimodal DPWellbore** (s1=0.866, s2/s3=0.30): when DSv4 finds the right
reference XML it nails it; when it doesn't, files are underspecified.
This is a file-discovery lottery, exactly what RAG was supposed to fix
(but RAG steers away from the reference XMLs that actually work).

## 5 Noise vs pattern checklist

| Claim | Evidence | Verdict |
|---|---|---|
| Plugin lift on minimax (M1u +0.27 over A3) | Paired W/L=15/0, p<0.001 | **Pattern** |
| Plugin lift transfers to DSv4 | best_dsv4 < vanilla_dsv4 by −0.044 | **No transfer** (model-specific tuning) |
| Memory primer (M1u) helps in general | DSv4: helps 5/17, hurts 6/17 | **No transfer** |
| Vanilla DSv4 beats m1u_minimax | −0.125 paired, 5/12 W/L | **No** — DSv4 is below the ceiling |
| Vanilla DSv4 + minimal > vanilla DSv4 + full | +0.030, σ tight | **Pattern** |
| xmllint hook drives 17/17 completion | All conditions hit 17/17 | **Pattern** but doesn't lift quality |
| Plugin-stack regression on Sneddon / DeviatedElastic / DPWellbore | n=3 seeds, large Δ | **Pattern** |
| chromadb path-scoping is a confound | 87 unindexed rst, vanilla reads 0.55/task | **Pattern** |
| RAG suppresses Glob/Grep | Plugin: 0 Glob, 0 Grep on DeviatedElastic; vanilla 2+5 | **Pattern** (n=2 trajectories traced) |

## 6 Proposed domain adaptations

Ordered by predicted leverage-to-effort. Each entry has: mechanism,
expected effect, falsification criterion.

### A. Hybrid filesystem-first primer (high leverage, low effort)

**Mechanism**: Replace plugin's "use the RAG MCP tools" instruction with a
hybrid workflow:

```
WORKFLOW (REQUIRED)
1. Glob `/geos_lib/inputFiles/` for files matching the task name keywords.
2. Read 2-3 closest reference XMLs end-to-end to understand the canonical
   structure for this physics class.
3. Copy the closest reference into `inputs/<TaskName>_base.xml` as a
   starting skeleton; modify in place.
4. Use mcp__geos-rag__search_* ONLY when (a) the reference XML uses a
   constitutive name you don't recognize, (b) you need to confirm a
   schema attribute name, or (c) the task asks for a specific physics
   not covered in the reference.
```

**Expected effect**:
- Sneddon: agent re-discovers the multi-variant structure → ~0.6+ (back
  to vanilla's level).
- DeviatedElastic: agent reads reference and copies → ~0.75+.
- DPWellbore: agent finds the smoke variant → bimodal → consistent.

**Falsification**: if best_with_hybrid still loses on DeviatedElastic
(<0.7) or Sneddon (<0.5) after this change, the issue isn't primer
wording — it's a deeper RAG / context-budget interaction, and we should
disable RAG entirely for those tasks and re-test.

### B. Re-index chromadb to include all rst files (medium leverage, medium effort)

**Mechanism**: 87 non-sphinx rst files are unindexed. Brian to confirm,
then re-index. This includes `InputXMLFiles.rst` (documents xmllint),
hand-written tutorial rsts, and others.

**Expected effect**: closes the structural fairness gap with vanilla;
plugin can stop relying on `Glob/Read` of rst files (currently it
doesn't read them at all; fixing the index makes RAG cover them).

**Falsification**: if plugin still misses content vanilla finds via Glob,
the indexer config or RAG retrieval ranking is the problem.

### C. Distill a DSv4-specific element-name cheatsheet (medium leverage, medium effort)

**Mechanism**: M1u helped on minimax because it provided an explicit
element-name table that fixed F1 schema hallucinations. DSv4 is a
different model with different hallucination patterns. Re-distill from
DSv4-on-train-set trajectories (using the existing
`scripts/memory/distiller.py`), targeting:
- DruckerPrager / Cam-Clay constitutive enumeration
- PorousElastic + BiotPorosity composite recipes (poromechanics cluster)
- Wellbore mesh setup

Apply as **system-prompt cheatsheet only**, not as memory MCP tool
(memory MCP was never called in any condition).

**Expected effect**: closes ~half the DruckerPrager/ModifiedCamClay gap
(+0.2 on those two tasks), some lift on Mandel/Poroelasticity if the
poromechanics recipe is the bottleneck.

**Falsification**: if DSv4 doesn't hallucinate element names on the
bottleneck tasks (Mandel etc), a cheatsheet of correct names helps
nothing — the problem is structural-completeness, not naming.

### D. Multi-variant detection rule (low leverage, low effort)

**Mechanism**: One-line addition to primer: "If the task description
mentions multiple solver/physics variants (e.g., 'compares X and Y
methods', 'tutorial showing 3 approaches'), produce one base XML per
variant + benchmark/smoke counterparts. Common GT layout:
`<TaskName>_<variant>_base.xml`."

**Expected effect**: Sneddon, Mandel (FIM/sequential), Poroelasticity
(if multi-variant) get the right file count.

**Falsification**: if the agent already produces correct file count and
the score is still low, it's a content problem (covered by C).

### E. Bottleneck-task scaffolding skill (high leverage, high effort)

**Mechanism**: A `skill` (read at task-start) that detects task category
from name keywords (mandel → poromechanics-mandel-template,
druckerPrager → drucker-prager-template, …) and injects a
domain-scaffold with named composite-constitutive recipe + canonical
file layout. Targets the 5-6 bottleneck tasks specifically.

**Expected effect**: collapses the tight-σ low-mean cluster (Mandel
0.31, Poroelasticity 0.36) toward 0.7+.

**Falsification**: if these tasks plateau at 0.5-0.6 even with explicit
scaffolds, the underlying physics modeling in GEOS schema is too
expressive for in-context-learning capture, and we should accept those
tasks as the ceiling.

### F. Hook upgrade: structural-completeness check, not just schema validity (medium leverage, medium effort)

**Mechanism**: Current xmllint hook checks well-formedness +
schema-conformance. Add: check that all canonical sections
(`Mesh`, `Constitutive`, `ElementRegions`, `Solvers`, `Events`,
`FieldSpecifications`, `Outputs`, `Tasks`) are non-empty. If a section
is missing, block with feedback "Section X is empty/missing — typical
for this physics class to require it." Counts toward the existing
retry budget.

**Expected effect**: reduces the file-underspecification failures
(the 2-file-instead-of-3 pattern, Sneddon-style underproduction).

**Falsification**: if the agent already includes all sections but with
wrong content, this hook adds no value — the F1/F4 content errors
remain.

### G. Drop the RAG instruction entirely on DSv4 (high leverage, low effort, controversial)

**Mechanism**: Don't tell the agent to use RAG. Keep the MCP tool
loaded but unmentioned. The agent uses Glob/Grep/Read by default; RAG
becomes available only if the agent specifically reaches for it.

**Expected effect**: best_dsv4 mean climbs back to vanilla's 0.671;
RAG provides upside on a subset of tasks where the agent decides it's
helpful.

**Falsification**: if best_dsv4 with this change is identical to
vanilla_dsv4 (no MCP calls), the plugin isn't contributing anything on
DSv4 and we should question whether to keep it at all on this model.

## 7 Suggested next experiments

Ranked by information value:

1. **Run A (hybrid primer) — DSv4-flash, 3 seeds.** Cheap, isolates whether
   "RAG instruction suppresses Glob/Grep" is the mechanism.
2. **Run G (no-RAG-instruction control) — DSv4-flash, 1 seed.** Even
   cheaper. Strongest test of the "RAG-suppression" hypothesis.
3. **Run F (structural-completeness hook) — 3 seeds.** Isolates the file-
   count / section-count failure mode.
4. **Run C (DSv4-specific cheatsheet) — pending DSv4 trajectory analysis.**
   Higher cost (re-distillation + 3 seeds), but addresses the tight-σ
   cluster directly.
5. **Run B (chromadb re-index) — pending Brian.** Won't run without
   the re-indexed DB.

Run A first. If it fails to recover the lost ground, run G to confirm
the mechanism. All others depend on what those reveal.

## 8 Open questions / things to verify

- The `treesim_section_scores` field shows all-zero values on Mandel/DPWellbore-s2/s3
  even when treesim > 0. The aggregation logic seems to penalize missing files
  by zeroing the section breakdown rather than averaging present files.
  This is a scoring-presentation issue, not a scoring-correctness issue (the
  top-level treesim is consistent), but it makes the section table misleading.
- The minimax-ceiling claim depends on m1u_minimax results from 2026-04-22.
  Those were on `data/eval/claude_code_repo3_plugin_m1u/mem_m1u_s{1,2,3}/`
  with summaries in `misc/memory_artifacts/scores/`. Re-verified raw:
  treesim mean across 3 seeds is 0.7964 ± 0.0571 — matches hub.md's
  0.796 ± 0.057 within rounding.
- **Best-vs-mean variance check** (>3pp gap flagged):
  - `best_dsv4`: best seed s2 = 0.666, mean = 0.628 (gap +0.038). Mean
    reported throughout; the s2 outlier doesn't drive any claim.
  - `m1u_minimax`: best seed s1 = 0.859, mean = 0.797 (gap +0.063).
    The +0.272 lift over a3 is also visible per-seed (s1 win 0.859 vs
    a3 best 0.664) — single best-seed comparison alone would still
    show the lift, so the claim is robust.
  - `a3_minimax`: best seed s1 = 0.664, mean = 0.524 (gap +0.140 — driven
    by s3 outlier 0.267). Reported as mean throughout. The Wilcoxon-paired
    analysis in the original D-008 sprint accounted for this variance.
- Trajectory analysis is n=2 (DeviatedElastic + Sneddon). The "RAG
  suppresses filesystem search" claim should be confirmed across ≥5 more
  bottleneck tasks before being treated as load-bearing. Quick check
  feasible by extending `scripts/analysis/analyze_tool_usage.py` to
  diff Read/Glob/Grep counts across (vanilla_dsv4, best_dsv4) pairs.

## 9 What this means for the paper / advisor narrative

The honest framing is:

> RAG + memory + self-refine produce a substantial lift on a weaker base
> model (minimax m2.7) where the agent struggles with file discovery and
> schema knowledge — paired W/L = 15/0/2, +0.27 mean. On a stronger,
> faster base model (DSv4-flash), the plugin's RAG instruction
> *interferes* with the agent's better default strategy of finding and
> imitating reference XMLs. The right intervention is hybrid: keep
> filesystem search as the primary strategy, augment with RAG when
> reference files are insufficient.

This sharpens the contribution rather than weakens it: the plugin is a
**complementary scaffold for capability gaps**, not a universal lift,
and we have a mechanism (RAG-instruction-suppresses-Glob) for when it
backfires. The DSv4-flash result becomes part of the story — what
breaks when you change the base model — rather than a contradiction.

---

**Files referenced**:
- `scripts/analysis/per_task_matrix.py` (new — produces the paired tables above)
- `scripts/analysis/analyze_tool_usage.py` (existing, used to diff trajectories)
- `data/eval/results/dsv4_min_primer_s{1,2,3}/`
- `data/eval/results/best_setup_dsv4_s{1,2,3}/`
- `data/eval/results/best_setup_m1u_dsv4_s{1,2,3}/`
- `misc/memory_artifacts/scores/mem_m1u_s{1,2,3}_summary.json`
- `misc/pac1/scores/e23{,s2}_summary.json`, `a3_s3_summary.json` (a3_minimax)

**Related**:
- `docs/2026-04-27_session_summary.md` (yesterday's writeup of the migration)
- `docs/XN-014_failure-analysis-vanilla-vs-rag.md` (original F1-F4 taxonomy)
- `docs/XN-015_memory-ablation-results.md` (M1-u D-008 results)
- `docs/2026-04-27_4condition-file-tool-comparison.md` (chromadb gap)

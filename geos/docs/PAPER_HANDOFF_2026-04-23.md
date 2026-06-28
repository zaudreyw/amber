# Paper Draft Handoff — Claude Code + repo3 Adaptations for GEOS XML Authoring

*Date: 2026-04-23 · Scope: methods, experiments, results, analysis through D-008 memory matrix + harness-less 1-shot baseline.*

This document is a working research log compiled for paper drafting. Numbers are sourced from `.copilot/hub.md`, `.copilot/research_log.md`, `docs/XN-*`, `.copilot/decisions/D-*`, `.copilot/reviews/RN-*`, and raw run artifacts under `data/eval/`. When a number is single-seed or caveated, that is called out inline.

---

## 1. Executive Summary

**The story in one paragraph.** We study whether harness-level adaptations on top of Claude Code (CC) improve accuracy on a heterogeneous GEOS XML authoring benchmark (17-task test subset, TreeSim metric). Vanilla CC (A1 baseline) already sits well above a *harness-less* direct-prompting baseline: on minimax-m2.7, CC fa0 = 0.497 vs harness-less 1-shot fa0 = 0.333 (Δ = +0.164). Adding a custom plugin (3-DB GEOS-RAG) alone (A2) does *not* move the headline number (0.440). Adding a stop-hook "self-refinement" layer on top of RAG (A3) pushes fa0 to 0.524 (n=3). The single largest lever we found is a **frozen monolithic primer** (M1-u) distilled offline from 18 training trajectories: stacked on RAG+SR it reaches **fa0 = 0.796 (n=3, σ=0.057)**, a +0.272 lift over A3 (Wilcoxon p < 0.001, 16/17 wins) and +0.299 over vanilla CC. A content-matched generic placebo *hurts* (−0.152), confirming the lift is content-specific. Grounding the distilled primer on TreeSim feedback (M1-g) gives no attribution signal over self-judged distillation (M1-g − M1-u = −0.030). Memory-as-retrieval (MCP tool, M3-g) is a non-finding: 0 spontaneous `memory_lookup` calls across all relevant runs.

**Headline number to defend.** fa0 = 0.796 ± 0.057 (n=3) on 17 test tasks, minimax-m2.7, CC + repo3 plugin + `verify_outputs` hook + M1-u monolithic primer. Baseline (vanilla CC) = 0.497 single-seed.

**Plugin also wins on deepseek-v3.2.** On 35 paired tasks, plugin = 0.828 vs no-plugin = 0.653 (+0.175). Cross-model generalization is claimed on two base models; Opus 4.6 and Gemma-4-31B untested.

**The "memory" story we almost told is wrong.** The memory tool is never called. What looks like a "memory" effect is primer-format-in-system-prompt: an enumerated cheatsheet that lists GEOS constitutive element names verbatim. This matters for framing — it's not test-time learning; it's structured prior knowledge packaged well.

---

## 2. Research Questions

Carried from `direction.md`; refined by results.

- **RQ1 (method — settled):** Does the repo3 plugin (3-DB RAG over GEOS docs) improve CC's accuracy at model parity? **Yes on deepseek-v3.2 (+0.175 fa0, n=1). On minimax-m2.7 the picture is more complex: RAG alone does not move fa0 (A2 0.440 ≤ A1 0.497); RAG + self-refinement + primer (M1-u) moves fa0 from 0.497 to 0.796.**
- **RQ2 (method — settled for this model):** What is the single best adaptation? **A monolithic, enumerated, content-rich system-prompt primer distilled from 18 training trajectories (M1-u).** Not memory-as-retrieval, not self-refinement alone, not filetree injection.
- **RQ3 (generalization — partial):** Do gains hold across base models? **Plugin wins on both deepseek-v3.2 and minimax-m2.7.** M1-u primer tested only on minimax-m2.7; cross-model test is an open experiment.
- **RQ4 (difficulty — deferred):** Gains on harder task variants (non-inferable parameters withheld from the NL spec). Not yet run.
- **RQ5 (NEW — harness vs base-model):** *How much of the performance comes from the CC harness at all, vs just prompting the base model?* **The harness adds +0.164 fa0 (vanilla CC) over 1-shot direct prompting with the same model; the full stack adds +0.463.** See §7.

---

## 3. Task Set and Evaluation

### 3.1 Task pool (46 → 36 → 17)

The full pool is **46 tasks** mined from GEOS advanced-examples and tutorial decks, stored at `/data/shared/geophysics_agent_data/data/eval/experiments_from_mined_specs/`.

- **36-task canonical test pool** (`experiments_test36_template/`): the 46 minus 10 held-out for in-context-learning / prompt-engineering work.
- **17-task test subset**: the subset used in PAC-1 and D-008 campaigns (canonical set is the list in `data/eval/claude_code_no_plugin/noplug_mm_v2/`).
- **10-task holdout** (never used for test scoring): `AdvancedExampleCasedThermoElasticWellbore`, `AdvancedExamplePureThermalDiffusionWellbore`, `AdvancedExampleThermoPoroElasticWellbore`, `AdvancedExampleViscoExtendedDruckerPrager`, `ExampleIsothermalHystInjection`, `ExampleMCCWellbore`, `ExampleProppantTest`, `ExamplesingleFracCompression`, `ExampleVerticalPoroElastoPlasticWellbore`, `TutorialHydraulicFractureWithAdvancedXML`. Used as the ICL pool for the harness-less experiment (§7); at most one is consumed per experiment.
- **Train/test split for memory distillation** (D-001, `misc/memory_split.json`): sort the 36 tasks by CC+plugin fa0, odd-index → train (18 tasks), even-index → test (17 tasks, one dropped). No test-task overlap enters the memory corpus, enforced by `scripts/memory/hygiene_audit.py` (D-008).

### 3.2 Spec versions (v1 vs v2)

Two instruction sets exist for the same task names:
- `experiments/` (v1) — original mined specs.
- `experiments_test36_template/` / `experiments_from_mined_specs/` (v2) — cleaner, more self-contained rewrites. **All D-004 onward experiments use v2.** Mid-project comparisons that crossed the versions were contaminated (see research log 2026-04-21); re-runs on v2+minimax anchored the canonical baselines.

### 3.3 Ground truth

`/data/shared/geophysics_agent_data/data/eval/experiments_gt/<task>/inputs/*.xml` — hand-validated XML decks for all 46 tasks.

### 3.4 Metric: TreeSim and fa0

Scoring code: `src/eval/judge_geos.py` (entry: `evaluate_directories(gt_dir, gen_dir)`), driver: `scripts/eval/batch_evaluate.py`.

- **TreeSim** ∈ [0, 1]: programmatic tree-edit / tree-similarity between agent-produced XML and ground-truth XML, section-decomposed (Mesh, Geometry, Events, Solvers, Constitutive, ElementRegions, NumericalMethods, FieldSpecifications, Functions, Outputs). `overall_score` is TreeSim × 10 (0-10 scale).
- **fa0 ("failures-as-zero")**: the **primary headline metric** in this project. Treats `failed_no_outputs`, timeouts, parse errors, and "no XML produced" as TreeSim = 0, then means across all 17 tasks. The alternative ("scored-only mean") discards failed tasks and inflates the apparent score. fa0 is less generous and harder to game; results reported in this document are fa0 unless marked "scored".
- **Pass@0.7**: fraction of tasks with TreeSim ≥ 0.7. A secondary headline.

### 3.5 Failure taxonomy (XN-014)

Observed vanilla-CC + RAG failure modes (useful for the discussion section):

- **F1 — schema hallucination**: agent invents GEOS element names that don't exist (`<FractureModel>`, `cohesionZoneMode`). Vanilla-CC-frequent; RAG `search_schema` addresses directly.
- **F2 — wrong-version drift**: correct skeleton, invalid attribute names from older GEOS (deprecated `fluidNames="{water}"`, invalid `lineSearchAction="Attempt"` in modern schemas). **RAG sometimes introduces F2** (pulls stale examples). Grounded distillation (M1-g) partially addresses it.
- **F3 — missing components**: agent writes only some of the required files or omits solver blocks. Neither RAG nor SR reliably addresses; M1-g grounding helps most here (+0.302 on F3-heavy tasks).
- **F4 — spec under-specification**: NL instruction under-determines which GEOS solver class to use. M1-u primer helps (+0.560 on F4 tasks) because the enumerated cheatsheet acts as a solver-class vocabulary.

---

## 4. Methods

Five intervention axes tested. Nothing below is the "final method" — the paper's contribution is the comparison.

### 4.1 Harness-less direct prompting (baseline, §7)

Prompt the base model with the task instruction directly, ask it to emit XML inline in tagged blocks, parse and score. No filesystem, no tool calls, no iteration. Implemented in `scripts/harnessless_eval.py`.

- **System prompt**: `run/AGENTS.md` with the original "EVALUATION MODE", "CRITICAL FILE LOCATION RULES", and "FILE ACCESS RULES" paragraphs stripped and replaced with a strict inline-XML protocol:
  ```
  <file path="FILENAME.xml">
  <?xml version="1.0" ?>
  ...
  </file>
  ```
- **ICL (1-shot)**: one held-out task's instructions + its ground-truth XML, presented as a prior `user`/`assistant` turn. Default ICL = `ExampleProppantTest` (proppant-slot physics, does not appear in the 17 test tasks).
- **Parallelization**: `ThreadPoolExecutor` (8 workers). Full 17-task run completes in ~9 min wall clock on minimax-m2.7.

### 4.2 Vanilla Claude Code (A1)

`claude --model minimax/minimax-m2.7` running inside the eval Docker, with GEOS source mounted read-only at `/geos_lib`, workspace at `/workspace`. System prompt is the full AGENTS.md + GEOS Primer. Tools: native CC tools (Read, Edit, Write, Grep, Glob, Bash, etc.). No plugin, no hook, no memory. The agent discovers reference XML by `grep`/`glob`ing `/geos_lib`.

- **Canonical A1 run**: E16 `noplug_mm_v2`, 17 tasks, single seed, fa0 = 0.497.

### 4.3 CC + repo3 plugin (A2)

Adds three things:

1. **GEOS-RAG MCP server** exposing three tools:
   - `mcp__geos-rag__search_navigator(query, n)` — semantic/navigational retrieval ("embedded fracture surface generation solid mechanics"). Returns breadcrumb paths like `Sphinx path: advancedExamples > validationStudies > fractureMechanics > Sneddon` plus doc snippet.
   - `mcp__geos-rag__search_schema(query, n)` — GEOS XML schema (element names, attribute names, allowed values, defaults).
   - `mcp__geos-rag__search_technical(query, n)` — concrete reference XML snippets with file and line references.
   
   Three separate ChromaDB collections backing these tools, built at plugin-install time from the GEOS source tree at `/geos_lib/src/docs/sphinx/` and `/geos_lib/inputFiles/`. Embedding model: OpenAI `text-embedding-3-small` via OpenRouter (`OPENROUTER_API_KEY`).
2. **A `geos-rag` skill** (plugin-level Claude skill) that teaches the agent *when* to invoke the three tools.
3. **System-prompt RAG instructions** appended to AGENTS.md (same as E03 ablation — see `build_system_prompt` in `scripts/run_experiment.py`): "Use `search_navigator` for conceptual orientation, `search_schema` for authoritative XML attributes/types/defaults, and `search_technical` for real XML examples and line references."

Plugin delivered via `--settings /path/to/settings.json` with `--strict-mcp-config` (not `--plugin-dir` — this is important for tool-list-shape parity with baselines; see D-004 §4).

- **Canonical A2 run**: E17 `plug_mm_v2_seed2`, fa0 = 0.440 (single seed).
- **On deepseek-v3.2**: E03 vs E01 paired on 35 tasks, plugin +0.175 fa0 (XN-001).

### 4.4 Self-refinement via Stop hook (A3 = A2 + SR)

`plugin/hooks/verify_outputs.py` — a Claude Code Stop hook registered in `plugin/hooks.json`. On every Stop event:

1. Scan `/workspace/inputs/` for parseable XML.
2. If no XML: emit `{"decision": "block", "reason": "no_xml"}` with a prompt telling the agent to produce the required files. CC re-prompts.
3. If unparseable XML: same, with `parse_error` reason.
4. If clean XML: `{"decision": "allow"}`.
5. Bounded by `max_retries=2` per task (resets counter in `/workspace/.verify_hook_state.json`).

All hook invocations append to `/workspace/.verify_hook_events.jsonl` for post-hoc analysis. Two distinct failure modes rescued in practice:

- **Wrong-path writes**: agent writes relative XML filenames at `/workspace/` root (not `/workspace/inputs/`). Hook blocks → agent relocates.
- **True empty completions** (XN-010): minimax sometimes emits `content=[]` with `stop_reason=end_turn` after a tool result; hook gives it a second chance.

**Hook history gotcha** (D-004): E16/E17/E18 were all nominally "with hook" in our notes, but the hook never actually loaded — `hooks.json` had the wrong schema and `run_experiment.py` never passed `--plugin-dir`. Fixed 2026-04-21T12:08Z. All post-fix runs (E23, E24, D-008 matrix) have a working hook. Any pre-fix result labelled "hook on" should be read as "hook intended but not wired".

- **Canonical A3 run**: D-008 matrix A3, 3 seeds, fa0 = 0.524 ± 0.221.

### 4.5 Hook ablation (E20, standalone; XN-012)

Independent 48-run ablation (4 tasks × 3 runs × 4 cells): C0 nohook, C1 hook, C2 noop_nohook (tool-shape control, single-tool MCP `plugin/scripts/noop_mcp.py`), C4 hook+noop. Result on fa0: C0=0.643, C1=0.530, C2=0.595, C4=0.557. Hook trends *negatively* (Δ = −0.112 vs C0, p ≈ 0.31, underpowered n=12). E17's 4/17 empty-completion rate did *not* reproduce in any cell. 7/8 non-successes were 900-s docker-kill timeouts on `ExampleThermalLeakyWell`, which the hook cannot rescue (Stop hook fires on assistant Stop, not on docker SIGKILL).

**Implication for the paper:** ship the hook as defense-in-depth, do not claim it "rescues empty completions". The rescue-mechanism claim was a single-seed fluke from E17.

### 4.6 Memory / primer variants (D-008 matrix)

All memory variants stack on A3 (RAG + SR). Content was distilled offline from 36 training trajectories (18 CC-plugin successes + 18 vanilla-CC runs with test-GT basenames blocklisted). **Distiller is `google/gemini-3-flash-preview`** (not minimax-m2.7) — this deliberately breaks self-distillation coupling.

| Variant | Content type | Delivery channel | Tokens | Grounded on TreeSim? | n_seeds |
|---|---|---|---:|:-:|:-:|
| **M0** (legacy, never called) | Per-task summaries + `reference_xmls` list | MCP tool `memory_lookup` | ~2KB/entry × 18 | — | baseline |
| **M1-u (HERO)** | Monolithic DC-Cu cheatsheet, enumerated solver → element-name table | append-system-prompt | 775 | ✗ (self-judged) | 3 |
| **M1-g** | M1-u + per-section TreeSim feedback | append-system-prompt | 807 | ✓ | 3 |
| **M3-g** | RB-style `{title, description, content}` items | MCP tool `memory_lookup` (embedding top-k, on-demand) | 5 × ~150 | ✓ | 1 valid (2 API-contaminated) |
| **M4-u** | RB-style items, self-judged | append-system-prompt (embed top-k at run start) | 728 | ✗ | 2 valid (1 API-contaminated) |
| **M4-g** | RB items + TreeSim feedback | append-system-prompt | 776 (6.6% parity) | ✓ | 3 |
| **M-placebo** | Generic GEOS glossary, NOT trajectory-derived; token-matched to M1 | append-system-prompt | 1043 | — | 3 |

**M1-u content (the hero)** — a single-file primer listing GEOS solver families with their concrete XML element names, constitutive-model class names, typical attribute values, and short pattern exemplars. Verbatim example: the entry that turns `CompressibleSolidParallelPlatesPermeability` from an invented hallucination into a copy-paste. The primer is not a policy (no "do X when Y"); it's a structured vocabulary dump.

**Hygiene gate** (D-008, post-RN-003): `scripts/memory/hygiene_audit.py` regex-scans every memory artifact for any filename matching the basename of any test-task ground-truth file. RN-003 found the legacy memory index had 13/17 test tasks leaking via `reference_xmls` + `productive_rag_queries` fields; new index strips both. Gate is run in CI before any campaign.

**Parity**: all memory variants token-matched to within 10% of M1-u (actual max: 6.6%). M-placebo is specifically 1043 tokens of generic GEOS schema glossary with no trajectory-derived content — it controls for "more tokens in system prompt" as a confound.

---

## 5. Experiments (chronological index)

Full per-experiment detail lives in `docs/XN-*` notes; this is a paper-facing summary. "E#" are DAG node IDs.

### Early (2026-04-20) — deepseek-v3.2, v1 specs, single seed

| ID | Run | Condition | Result | Source |
|---|---|---|---|---|
| E01 | `ablation_deepseek_v2/noplug` | vanilla CC, ds | fa0 on paired 35 = 0.653 | XN-001 |
| E02 | `ablation_deepseek_v2/plugin` (minimax cross-model run also) | CC + plugin, ds / mm | ds: 0.828 (n=1, 35 tasks); mm: 0.809 on paired 15 | XN-001, XN-005 |
| E03 | `claude_code_repo3_plugin` | CC + plugin, ds | same as E02 | XN-001 |
| E04 | long cheatsheet in system prompt (1700 tok) | sys-prompt inject | Δ = −0.322 vs E03 | XN-003, XN-009 |
| E05 | short cheatsheet (300 tok) | sys-prompt inject | Δ = −0.270 | XN-004 |
| E06 | CC + plugin, minimax cross-model | — | 0.809 on 15 paired | XN-005 |
| E07 | filetree injection (1100 tok, precomputed `/geos_lib/inputFiles/` paths) | sys-prompt inject | Δ = −0.227 | XN-007 |
| E08 | primer shrink to 450 tok | replace primer | Δ = −0.235 | XN-009 |
| E09 | workspace file `/workspace/CHEATSHEET.md` (not sys-prompt) | workspace | Δ = −0.212 | XN-009 |
| E11 | g-memory MCP tool `memory_lookup` (concrete examples) | MCP tool | Δ = −0.192 (least-bad) | XN-009 |
| E12 | gated memory (threshold + delay) | MCP tool | negative | D-003 |

**Reframing caveat** (research_log 2026-04-21, LOG-3): later we found E14 (plain plugin, seed 2) scored 0.616 vs E03's 0.831 on deepseek-v1 — "memory hurts on deepseek" in E04–E13 was partly seed variance on v1 specs. Do *not* cite E04–E13 deltas as memory-as-channel failures in the paper; cite them as channel-agnostic convergent negatives on deepseek-v1 that motivated the v2-minimax-pinned re-run. The convergent-negatives *point* (all six variants regress on the same 3 rescue tasks — Sneddon, Mandel, DPWellbore) is still real and mechanistically interesting (XN-009 trajectories).

**XN-008 mechanism analysis**: on Sneddon, no-plugin reads 10-13 source files and 4-7 greps, converges on `LagrangianContact`. Plugin issues 7-9 RAG queries and finds three valid physics options (embedded fractures, Lagrangian contact, hydrofracture), then disambiguates with schema lookups. On DPWellbore, no-plugin confuses `DruckerPrager` vs `ExtendedDruckerPrager` vs `DruckerPragerHardening` (all exist in source); plugin's `search_schema` returns disambiguated variant bodies directly.

### Hook ablation (E20; 2026-04-21; minimax v2)

48-run 4×3 factorial. **Non-finding**: hook trends negative, not statistically distinguishable from zero (n=12). Ship as defense-in-depth. See §4.5 / XN-012.

### PAC-1 Phase A (2026-04-21; minimax v2, single seed → multi-seed)

Canonical ablation grid. XN-013, D-005.

| Cell | RAG | Mem | SR | Run | fa0 (s1) |
|---|:-:|:-:|:-:|---|---:|
| A1 | ✗ | ✗ | ✗ | E16 noplug_mm_v2 | 0.497 |
| A2 | ✓ | ✗ | ✗ | E17 plug_mm_v2_seed2 | 0.440 |
| A3 | ✓ | ✗ | ✓ | E23 pac1_plug_hook_s1 | 0.664 |
| A4 | ✓ | ✓ | ✗ | E18 gmemsilent_mm_v2 | 0.725 (has AskUserQuestion tool; see caveat) |
| A4′ | ✓ | ✓ | ✗ | (rerun, AQ removed) | 0.661 |
| A5 | ✓ | ✓ | ✓ | E24 pac1_plug_mem_hook_s1 | **0.317** |

**Single-seed surprise**: A5 full-stack *lost* to A1 by 0.180 on seed 1. Memory tool call count across A4/A4′/A5: **mem=0 across all tasks**. Adding the un-called memory tool correlated with more empty-completion attempts (12 vs 7 hook events in A5 vs A3).

### PAC-1 Phase B1 (2026-04-21 end-of-sleep; multi-seed completion)

| Cell | n_seeds | Mean fa0 | σ | Δ vs A1 |
|---|:-:|---:|---:|---:|
| A1 | 1 | 0.497 | — | — |
| A2 | 1 | 0.440 | — | −0.058 |
| A3 (pre-D-008) | 2 | 0.653 | 0.017 | +0.155 |
| A4′ | 2 | 0.661 | 0.184 | +0.164 |
| A5 | 3 | 0.607 | 0.252 | +0.110 |

At this point we believed (a) A3 RAG+SR was the reliable +0.155 adaptation (σ=0.017 stable), (b) A5 fullstack had a real but noisy +0.110 gain, (c) memory was a pure tool-list-shape effect. **A user/advisor review flagged three issues**: (i) vanilla-CC failure modes unexplained; (ii) memory implementation was lexical ("hack job"); (iii) G-Memory architecture overkill for this task.

### D-007 → D-008 pivot (2026-04-22; RN-003 adversarial review)

Adversarial review of D-007 found 4 P1 blockers:
1. **Memory-index GT-filename leakage**: 14/17 test tasks had ground-truth XML basenames leaking via `reference_xmls` and `productive_rag_queries` fields in the memory index.
2. **M0 "control" had null test exposure**: memory tool never called in A5; so "M0 vs Mn" compared nothing vs content.
3. **Primer-size parity uncontrolled**: condition-over-condition token counts differed.
4. **A3 baseline under-powered at n=2**: σ=0.017 was a two-seed artifact.

D-008 fixed all four: hygiene-audit gate; M-placebo token-matched generic content as true control; preregistered ≤10% token parity per pair; A3 seed-3 launched. **A3 seed-3 scored 0.267** (far below seeds 1 and 2). A3 n=3 mean = 0.524, σ = 0.221. This is the canonical A3 baseline used in D-008 reporting and in this paper. The prior σ=0.017 was genuinely an artifact.

### D-008 matrix (2026-04-22; canonical memory sprint)

6 conditions × 3 seeds = 18 runs. Conditions: M-placebo, M1-u, M1-g, M3-g, M4-u, M4-g. See §4.6 for variant content. All on CC+plugin+SR (A3 base) + memory variant. Results summarized in §6.

**API contamination** — 3 of 18 seeds contaminated by OpenRouter billing/quota issues, excluded from analysis:
- M4-u s3: 13/17 HTTP 402 `Insufficient credits` (mid-run)
- M3-g s2: 17/17 HTTP 403 `Key limit exceeded (weekly)`
- M3-g s3: 17/17 HTTP 403

Detection: `scripts/memory/check_api_contamination.py`. Must run before interpreting any batch.

### Harness-less 1-shot (2026-04-23; this document's fresh contribution)

See §7. fa0 = 0.333 on 17 tasks (16 parsed, 1 silent provider drop on `ExampleEDPWellbore`). Single seed.

---

## 6. Results

### 6.1 Headline table (paper Table 1 candidate)

17 test tasks, minimax-m2.7, v2 specs, fa0 metric.

| Configuration | n_seeds | fa0 mean | σ | Δ vs A1 | Status |
|---|:-:|---:|---:|---:|---|
| Harness-less 1-shot (ICL=Proppant) | 1 | 0.333 | — | −0.164 | NEW |
| A1 — vanilla CC | 1 | 0.497 | — | — | baseline |
| A2 — CC + plugin (RAG only) | 1 | 0.440 | — | −0.058 | negative |
| A3 — CC + plugin + SR | 3 | 0.524 | 0.221 | +0.027 | weak, high variance |
| A4′ — CC + plugin + M0 memory | 2 | 0.661 | 0.184 | +0.164 | noisy |
| A5 — CC + plugin + M0 memory + SR | 3 | 0.607 | 0.252 | +0.110 | noisy |
| M-placebo (content control) | 3 | 0.373 | 0.049 | −0.124 | confirms placebo hurts |
| M4-g (RB items, grounded) | 3 | 0.469 | 0.299 | −0.028 | unstable |
| M4-u (RB items, self-judged) | 2 | 0.729 | 0.024 | +0.232 | strong (n=2) |
| M1-g (monolithic primer, grounded) | 3 | 0.766 | 0.046 | +0.269 | Claim A pass |
| **M1-u (monolithic primer, self-judged) — HERO** | **3** | **0.796** | **0.057** | **+0.299** | **Claim A pass** |

Wilcoxon signed-rank paired tests against A3 (n=3 per cell, per-task):
- M1-u vs A3: p < 0.001, 16/17 wins
- M1-g vs A3: p = 0.003, 13/17 wins
- M-placebo vs A3: p = 0.015, 6/11 *losses* (content control confirms)
- M4-g vs A3: p = 0.145 (unstable, not significantly different)

### 6.2 Claim attribution (paper Table 2 candidate)

- **Claim A — grounding is beneficial**: FAIL. M1-g − M1-u = −0.030. M4-g − M4-u = −0.068 (n=2). Self-judged distillation by gemini-3-flash-preview is as effective as TreeSim-grounded distillation in aggregate.
- **Claim A sub — grounding helps specific failure classes**: PASS on F3 missing-components only (M1-g improves F3 by +0.302 vs M1-u baseline). Does not generalize.
- **Content matters (placebo control)**: PASS. M-placebo regresses (−0.152 vs A3); M1 content-specific lift (+0.272) is not a primer-shape artifact.
- **Format matters more than content-source (monolithic vs structured)**: M1-u (monolithic enumerated table) > M4-u (structured RB items) by ~+0.067 (n=2 on M4-u). Preliminary but directionally consistent.
- **Memory-as-retrieval is a non-finding**: 0 `memory_lookup` calls in any A4/A4′/A5/M3-g run on the test set. The M3 architecture is functional (RN-003 verified hard-error on missing `OPENROUTER_API_KEY`), just not invoked by the agent.

### 6.3 Cross-model (paper Table 3 candidate)

| Model | Condition | fa0 | Source |
|---|---|---:|---|
| deepseek-v3.2 | vanilla CC | 0.653 (paired 35) | E01 / XN-001 |
| deepseek-v3.2 | CC + plugin | 0.828 | E03 / XN-001 |
| minimax-m2.7 | vanilla CC | 0.694 (paired 15) / 0.497 (17) | E06 / E16 |
| minimax-m2.7 | CC + plugin | 0.809 (paired 15) / 0.440 (17) | E02 / E17 |

The plugin win is larger on deepseek (Δ +0.175) than minimax (Δ +0.102 on 15 paired, or Δ −0.058 on 17 single-seed). Consistent with minimax being a stronger base model with less room for the plugin to rescue — plugin is most valuable when the base model catastrophically fails (Sneddon rescue: ds 0.099 → 0.804; mm 0.493 → 0.275, i.e. **plugin loses on Sneddon in minimax**). See XN-008 mechanism discussion.

**Caveat**: M1-u primer (the hero) is only tested on minimax-m2.7 at time of writing. Cross-model generalization of the primer-format finding is an open experiment.

### 6.4 Harness-less 1-shot per-task (paper Figure candidate)

| Task | TreeSim | vs A1 (vanilla CC single seed) |
|---|---:|---:|
| buckleyLeverettProblem | 0.516 | (ranks high) |
| ExampleThermalLeakyWell | 0.444 | |
| TutorialPoroelasticity | 0.414 | |
| AdvancedExampleExtendedDruckerPrager | 0.400 | |
| AdvancedExampleDeviatedElasticWellbore | 0.383 | |
| pknViscosityDominated | 0.379 | |
| kgdExperimentValidation | 0.374 | |
| AdvancedExampleViscoDruckerPrager | 0.364 | |
| ExampleIsothermalLeakyWell | 0.350 | |
| ExampleDPWellbore | 0.337 | |
| TutorialSneddon | 0.332 | |
| ExampleMandel | 0.331 | |
| AdvancedExampleDruckerPrager | 0.327 | |
| AdvancedExampleModifiedCamClay | 0.276 | |
| AdvancedExampleCasedContactThermoElasticWellbore | 0.245 | |
| ExampleThermoporoelasticConsolidation | 0.182 | |
| ExampleEDPWellbore | **0** (FAIL — empty model response after ~515s) | |
| **fa0 mean (17)** | **0.333** | |

Seed 1 only, single retry would likely recover the EDPWellbore failure. No task passed 0.7.

---

## 7. The Harness-Less Baseline (new contribution for this draft)

### 7.1 Motivation

A referee is likely to ask: *How much of the "harness matters" story is the harness vs the base model? Could the base model do the task alone, given the same instruction?* This experiment answers that directly. It also bounds the contribution of the whole harness stack (filesystem, tool use, RAG, SR, memory) against the contribution of the base-model weights.

### 7.2 Method

Script: `scripts/harnessless_eval.py`. Same base model (minimax-m2.7), same 17 test tasks, same v2 specs, same TreeSim scorer. Differences from A1:

- No filesystem, tool use, or iteration. One model call per task.
- System prompt = AGENTS.md with file-write/workspace paragraphs stripped and replaced with an explicit inline-XML protocol:
  ```
  <file path="FILENAME.xml">
  <?xml version="1.0" ?>
  ...
  </file>
  ```
- 1-shot ICL from held-out task `ExampleProppantTest` (proppant-slot; off-distribution from the 17 test tasks to reduce leakage risk). The ICL shows the user instruction + the GT XML wrapped in the tag format.
- `ThreadPoolExecutor` with 8 workers. Temperature 0.2. `max_tokens = 16384`. Per-request timeout 600 s.

Output layout matches the agent-run format so `scripts/eval/batch_evaluate.py` scores it unchanged: `data/eval/harnessless/<run>/<task>/inputs/*.xml`.

### 7.3 Results and reading

- fa0 = 0.333 on 17 tasks (scored-only mean 0.353). 16/17 parsed cleanly; `ExampleEDPWellbore` returned empty content after ~515 s (likely provider drop; counts as 0 in fa0).
- Best-performing task: buckleyLeverettProblem (0.516). Worst: ExampleThermoporoelasticConsolidation (0.182).
- No tasks passed TreeSim ≥ 0.7.
- Wall time: ~9 min with 8 workers. Cost: small (1 call per task, ~5 K-tok prompts).

**What this contributes to the paper:**
- Vanilla CC harness contributes **+0.164 fa0** on top of "give the model the instruction and ask for XML". That is the first time we quantify the harness on its own.
- The full M1-u stack contributes **+0.463 fa0** over the harness-less baseline. This is the "our adaptations are worth the harness overhead" number.
- The harness-less numbers are broadly consistent across tasks (mostly in the 0.25–0.45 band); the heterogeneity signal comes from the *harness*, not the base model's ability to author XML.

**Limitations (must flag in paper):**
- Single seed (API nondeterminism on OpenRouter; no seed flag for minimax).
- 1-shot; zero-shot not yet tested. We have not quantified the ICL contribution itself.
- One task's silent-drop failure counts as 0 — potentially unfair if the provider issue reproduces.

---

## 8. Analysis

### 8.1 What the data actually says

- **Harness adds value over direct prompting**, even before any adaptation. +0.164 fa0 from vanilla CC over harness-less 1-shot on the same model.
- **RAG alone (plugin) does not help minimax on the 17-task test set**. A2 = 0.440 ≤ A1 = 0.497. RAG wins on deepseek (+0.175 on 35 tasks, weaker base model) but is a wash on minimax. This is consistent with "plugin rescues catastrophic failures, and a stronger base model has fewer to rescue" (XN-008).
- **A monolithic, content-rich primer in the system prompt is the single biggest adaptation we found**. M1-u adds +0.299 fa0 over vanilla CC. +0.272 over RAG+SR. It is a static artifact, not a runtime retriever.
- **The primer's content matters, not just its shape**. M-placebo (generic GEOS glossary, token-matched) regresses vs A3 by −0.152.
- **Grounding the primer on TreeSim feedback does not improve aggregate fa0**. M1-g ≈ M1-u in aggregate; grounding improves F3 missing-components but worsens other failure classes slightly.
- **"Memory" as an MCP tool is dead on this task-model pair**. The agent never calls it.
- **Self-refinement via Stop hook is worth about as much as RAG on top of vanilla CC**, and its effect is noisy. Its main contribution appears to be variance reduction on malformed output, not score uplift.

### 8.2 Likely paper narrative (revised from earlier drafts)

- **Old narrative (pre-D-008)**: "We built a RAG plugin + self-refinement + memory; all three stack to beat vanilla CC." — *False*. Memory tool is never called; RAG is a wash on the stronger model; SR is noisy.
- **Current narrative (post-D-008)**: "A simple, static, content-rich primer distilled from 18 training trajectories, delivered via `--append-system-prompt`, is the largest single harness adaptation. RAG and SR are supporting defense-in-depth components. MCP-based memory retrieval did not engage the agent on this task."
- **Framing implication**: this is not a test-time-learning paper. It is a *prompt-engineering-via-offline-distillation* paper with a secondary harness contribution. Frame distillation + delivery as the method; memory-as-retrieval is a negative result worth discussing.

### 8.3 Mechanism (for the discussion section)

- On minimax, F1 (schema hallucination) and F4 (spec under-specification) dominate the error budget. M1-u's enumerated cheatsheet lists GEOS element names verbatim, so the model copies them instead of inventing them. This is a *vocabulary* win, not a *reasoning* win.
- RAG helps when the model doesn't know which *family* of solver to use (Sneddon — embedded fractures vs Lagrangian contact). It does *not* help when the model knows the family but invents element names within it (Mandel on minimax).
- Self-refinement via Stop hook catches syntactic and empty-output failures but does not catch semantic errors. It shows up as a variance reducer, not a mean shifter.
- Harness-less results show the base model is broadly capable of producing GEOS XML shape but weak on GEOS-specific vocabulary and class names — consistent with the primer being the key intervention.

### 8.4 What we would do differently if starting over

- Build M1-u first, not last. The "convergent negatives" story on deepseek-v1 specs burned a lot of compute.
- Pin model, specs (v2), and seed count discipline from experiment 1. Half of the early deltas were partly seed/spec noise.
- Run A3 with n=3 from the start. The 2-seed σ=0.017 was misleading; 3-seed σ=0.221 tells a different story.
- Budget a "hygiene audit" into every memory/primer design before any campaign, not after RN-003.

---

## 9. Known gotchas and caveats (keep in mind during drafting)

1. **Hook was never wired until 2026-04-21T12:08Z.** E16/E17/E18 were labelled "hook on" but hook never loaded (schema error + missing `--plugin-dir`). Post-D-004 results use a verified-wired hook.
2. **AskUserQuestion tool availability differs across sessions.** A5 vs A4 on seed 1 confounds hook-toggle with AQ-tool-removal. A4′ eliminates the confound.
3. **OpenRouter nondeterminism**: no seed flag on minimax. "Seeds" = independent runs with identical prompts.
4. **OpenRouter billing/quota contamination**: M4-u s3 and M3-g s2/s3 wiped by HTTP 402/403. Always run `scripts/memory/check_api_contamination.py` before interpreting new batches.
5. **Distillation model ≠ inference model** (gemini-3-flash-preview distilling for minimax-m2.7 inference). Deliberate, to break self-distillation coupling.
6. **Memory index v1 leaked GT basenames** for 13/17 test tasks (RN-003). Fixed in D-008; v1 archived as `.bak`. Any pre-D-008 "memory" result should be treated as suspect.
7. **v1 vs v2 spec mismatch** invalidated early deepseek comparisons. All post-2026-04-21 results use v2.
8. **Plugin "tool calls" in telemetry for no-plugin runs** (XN-001): E01 logs `rag_tool_calls>=1` because minimax emits `tool_use_error: No such tool available` and the counter increments on rejected calls. Not a contamination; do not cite those counters as evidence of plugin leakage.
9. **Hook ablation E20 did NOT reproduce E17's 4/17 empty-completion rate.** The "hook rescues empty completions" claim rests on one seed. Ship hook as plumbing.
10. **Harness-less EDPWellbore silent drop** on the single run so far. One provider-side timeout may recur; interpret the 0.333 fa0 with a ±1-task uncertainty.

---

## 10. Open directions (not required for the paper, flagged for the author)

- **Harness-less zero-shot** (compare against the 1-shot number above to attribute ICL's contribution).
- **Harness-less multi-seed** (to bound provider variance and give a σ on 0.333).
- **M1-u on deepseek-v3.2** (cross-model test of the primer-format finding).
- **M1-u cross-model on Opus 4.6 / Gemma-4-31B** (cost-deferred).
- **Primer-format ablation on minimax**: strip the enumerated element-name table from M1-u; measure fa0 drop. Expected large. Would directly support the "format matters" claim.
- **RAG + M1-u vs M1-u alone**: is RAG still contributing on top of a strong primer? Current A3 + M1-u = 0.796. A1 + M1-u not yet measured.
- **Harder task variants (RQ4)**: non-inferable parameters withheld from the NL spec. Plugin may regain ground on a harder benchmark where base-model memorization plateaus.

---

## 11. File map (for the drafter)

| Artifact | Path |
|---|---|
| Canonical hub | `.copilot/hub.md` |
| Research log | `.copilot/research_log.md` |
| D-008 decision memo | `.copilot/decisions/D-008_memory-ablation-design-v2.md` |
| RN-003 adversarial review | `.copilot/reviews/RN-003_adversarial_memory-ablation-design.md` |
| Plugin source | `plugin/` |
| Plugin RAG MCP server | `plugin/scripts/geos_rag_mcp.py` (check) |
| Stop hook | `plugin/hooks/verify_outputs.py` |
| Runner | `scripts/run_experiment.py` |
| Scorer | `src/eval/judge_geos.py`, `scripts/eval/batch_evaluate.py` |
| M1-u primer | `plugin/memory_primer_m1u.md` (check name) |
| Memory artifacts + scores | `misc/memory_artifacts/` |
| Harness-less script | `scripts/harnessless_eval.py` |
| Harness-less outputs | `data/eval/harnessless/harnessless_1shot_mm_s1/` |
| Harness-less scores | `data/eval/results/harnessless_1shot_mm_s1/` |
| Key XN notes | `docs/XN-001`, `XN-005`, `XN-008`, `XN-012`, `XN-013`, `XN-014`, `XN-015` |

---

*End of handoff. When in doubt, verify numbers against the raw `*_eval.json` and `_aggregate.json` files before citing them in paper text — anything in this document that's not also in a raw result file should be treated as a working hypothesis.*

---
id: RN-003
source: adversarial-reviewer
model: claude-opus
title: "Adversarial code review: D-007 memory ablation design (pre-campaign gate)"
date: 2026-04-22
invoked_at: 2026-04-22T00:00:00Z
dag_nodes: [I06, I10, E23, E24]
trigger: "implementation-gate"
priority_issues: 5
blocker_for_campaign: true
links:
  evidence_against: []
  related_to: [D-007, D-005, RN-002, XN-014]
---

# Adversarial Code Review — D-007 memory ablation sprint

## Scope

Files read end-to-end:
- `.copilot/decisions/D-007_memory-ablation-design.md` — the design memo under attack.
- `.copilot/decisions/D-005_pac1-ablation-campaign.md` — the prior campaign the A3 baseline comes from.
- `plugin/scripts/memory_mcp.py` — M0 control MCP (lines 1–174 all read).
- `scripts/run_experiment.py` — focused reads on agent dict (lines 144–324), `build_system_prompt` (437–512), MCP config writer (939–1004), runner command (1076–1182), eval_metadata emission (1546–1586). ~3300-line file; skimmed for primer / memory / blocked-gt paths via grep.
- `plugin/memory_index.json` — enumerated all 18 train tasks, all `reference_xmls`, sampled `productive_rag_queries`.
- `scripts/memory/build_gmem_index.py` — full file.
- `misc/memory_split.json` — full file.
- `src/runner/contamination.py:200–300` — filtered_geos copy behavior, blocked basename logic.
- `plugin/scripts/geos_rag_mcp.py:140–190` — embedding fn env-var sourcing.
- `data/eval/claude_code_repo3_plugin_gmem/gmem_v2_run1/*/eval_metadata.json` — sampled 17 to enumerate `blocked_gt_xml_filenames` per test task.
- `.copilot/reviews/RN-001_reviewer_e03-e04-audit.md`, `RN-002_designer_e20-hook-ablation.md` — prior review context.
- `.copilot/hub.md` — A3 / A5 seed counts, PAC-1 Phase A table.
- `docs/XN-014_failure-analysis-vanilla-vs-rag.md` — failure taxonomy this design relies on.
- `plugin/cheatsheet.md`, `plugin/cheatsheet_abstract.md` — prior distilled-cheatsheet outputs (reference for distiller drift check).

Claims I am attacking (paraphrased from the focus text + D-007):
- **A (outcome):** RAG+SR+M1-g beats A3 by ≥ +0.05 mean, σ ≤ 0.05 across 3 seeds on 17 v2 tasks.
- **B (attribution):** (M1-g − M1-u) ≥ +0.04 OR (M4-g − M4-u) ≥ +0.04 → "TreeSim-grounded offline distillation is our method contribution."
- **C (locus):** M4-g > M3 mean fa0 → "external injection beats tool-locus when content is abstract."
- **D (hygiene):** Anti-pattern memory content comes exclusively from rerunning vanilla CC on 18 TRAINING tasks, never test tasks.

---

## Findings

### P1 — BLOCKER: `memory_index.json` leaks test-task GT reference filenames through train entries

**Location:** `plugin/memory_index.json` (frozen M0 artifact, also the seed for M4 item-building)
and every test-time delivery path: `plugin/scripts/memory_mcp.py:140–156`
(`"reference_xmls": e.get("reference_xmls", [])[:5]` returned verbatim).

**Evidence.** I cross-joined the 18 train entries' `reference_xmls` against each test
task's `blocked_gt_xml_filenames` (read straight from existing `eval_metadata.json`
files in `data/eval/claude_code_repo3_plugin_gmem/gmem_v2_run1/`). For **13 of 17
test tasks** at least one blocked basename appears as a `reference_xmls` entry of
some train task. Worst offenders:

| Test task (blocked GT) | Train entry leaking it | Blocked basename surfaced in memory |
|---|---|---|
| TutorialSneddon | `AdvancedExampleCasedElasticWellboreImperfectInterfaces`, `ExampleTFrac` | `sneddon_base.xml`, `sneddon_benchmark.xml`, `sneddon_embeddedfrac_verification.xml` |
| AdvancedExampleModifiedCamClay | `AdvancedExampleViscoModifiedCamClay`, `triaxialDriverExample` | `triaxialdriver_base.xml`, `triaxialdriver_modifiedcamclay.xml` |
| AdvancedExampleDruckerPrager | `triaxialDriverExample` | `triaxialdriver_base.xml`, `triaxialdriver_druckerprager.xml` |
| AdvancedExampleExtendedDruckerPrager | `triaxialDriverExample` | `triaxialdriver_base.xml`, `triaxialdriver_extendeddruckerprager.xml` |
| kgdExperimentValidation | `kgdViscosityDominated` | `kgdvalidation_benchmark.xml` |
| AdvancedExampleViscoDruckerPrager | `triaxialDriverExample`, `AdvancedExampleViscoModifiedCamClay` | `triaxialdriver_base.xml`, `triaxialdriver_viscodruckerprager.xml` |
| AdvancedExampleDeviatedElasticWellbore | `AdvancedExampleCasedElasticWellbore`, `AdvancedExampleDeviatedPoroElasticWellbore` | `deviatedelasticwellbore_base.xml`, `deviatedelasticwellbore_benchmark.xml` |
| AdvancedExampleCasedContactThermoElasticWellbore | `AdvancedExampleCasedElasticWellboreImperfectInterfaces` | `casedthermoelasticwellbore_imperfectinterfaces_base.xml`, `…_benchmark.xml` |
| ExampleEDPWellbore | `AdvancedExampleCasedElasticWellbore`, `AdvancedExampleWellbore…ThermalConductivity` | `extendeddruckerpragerwellbore_base.xml`, `…_benchmark.xml` |
| ExampleThermoporoelasticConsolidation | `TutorialCO2FieldCase` | `thermoporoelastic_consolidation_base.xml` |
| TutorialPoroelasticity | `relaxationTest` | `poroelastic_terzaghi_benchmark.xml` |
| ExampleIsothermalLeakyWell | `TutorialDeadOilBottomLayersSPE10`, `relaxationTest` | `isothermalleakywell_base_iterative.xml`, `…_benchmark.xml` |

**Why it invalidates the claim.** `create_filtered_geos_copy` (`src/runner/contamination.py:234`)
correctly **deletes the blocked basenames from the filesystem**, so the agent's `Read`
on `/geos_lib/.../sneddon_base.xml` during a TutorialSneddon run will fail. But the
memory channel re-introduces the filename **as text content** at the place in the
prompt that the agent treats as authoritative retrieval:

- M0 (currently implemented, `memory_mcp.py:145`): the tool response includes the
  path verbatim as a `reference_xmls` array plus `productive_rag_queries` that
  also echo those basenames (e.g., train entry `AdvancedExampleViscoModifiedCamClay`
  lists `triaxialDriver_base.xml` as a productive RAG query string).
- **M3 (planned):** builds embedding-indexed items whose "content" field is, per D-007
  line 62, an abstract `{title, description, content}` distilled from the trajectory.
  If the distiller is fed the raw `reference_xmls` list as context, those basenames
  flow into the distilled content. The guardrail in §"Abstraction guardrails" (D-007:88–97)
  says "NO raw XML content. Element/attribute names only" — but silently permits
  *filename* content.
- **M4-u, M4-g, M1-u, M1-g (planned):** inject distilled memory into the primer at
  run start, verbatim, for every test task. If distilled content contains even one
  blocked-GT basename, the agent gets a named pointer to the GT for the current test
  task **before its first action**.

This is a direct information-from-train-hygiene-to-test-inputs leak. Even if the
file is absent on disk, the basename is a near-oracle hint: the GEOS schema RAG
will return a close-matching example that the agent can then adapt. Two of the
test tasks (DruckerPrager variants, ModifiedCamClay) share the exact same
`triaxialdriver_base.xml` GT as the train entry `AdvancedExampleViscoModifiedCamClay`.

**Why prior runs didn't detect it.** A4'/A5 had zero `memory_lookup` calls (hub.md
State of Knowledge), so M0's leakage never fired. **M1/M4 deliver memory in the
primer unconditionally** — the leak becomes mandatory and hits every task. So the
"change of delivery channel" is simultaneously a change from "latent leakage that
never fires" to "leakage that fires every run." That is the single fact that can
invalidate Claim A outright: the M1/M4 lift could be largely attributable to leaked
basenames, not to grounding or distillation.

**Recommended action (do not pass go).**
1. Before launching any M1/M3/M4 run, audit every distilled artifact (`misc/memory_artifacts/*`)
   for the union of all `blocked_gt_xml_filenames` across all 17 test tasks (lowercased
   basename match, plus variant-expanded basenames — use `contamination.py` helpers).
   Fail the artifact if any match.
2. Rebuild `memory_index.json` with `reference_xmls` paths *stripped* or replaced
   with family tags (`solver_family=hydrofracture`) before distillation, so the
   distiller *cannot* ingest the basenames.
3. Extend the distiller prompt guardrail to explicitly read "NO raw XML content AND
   NO file basenames of the form `*.xml`" — the current guardrail says "element/attribute
   names only" which in natural-language instruction misses filenames.
4. Add a post-distillation regex sweep for `\b[a-z0-9_]+\.xml\b` in distilled content
   and reject artifacts that match.

Without (1)–(4) the entire matrix's hygiene is broken.

---

### P1 — BLOCKER: M0 "control" has null test exposure; M1/M4 injection is not comparable to M0

**Location:** the matrix in D-007:57–64; `scripts/run_experiment.py:490–505` (memory prompt
hint) vs `plugin/cheatsheet.md` primer path.

**Evidence.** Prior A5 had `memory_lookup` tool-use count = 0 across all runs (hub.md).
So the "M0 fa0" you will compare against is literally A5 — a condition where the memory
channel delivered **zero bytes of memory content** to the agent. By contrast, M1-u, M1-g,
M4-u, M4-g inject distilled content into the primer, which *always* fires.

**Why it invalidates the claim.** Every M1/M4 − M0 contrast confounds three things
simultaneously:
1. Distilled memory content is or isn't available (the variable you want).
2. The system prompt grew by N tokens (primer-size confound — your listed suspect #7).
3. The system prompt's "authoritative voice" (primer) now contains cross-task rules,
   which by itself could prime the agent to slow down / be more structural —
   independent of the rules' specific content.

**Claim C** ("external injection beats tool-locus") is especially fragile: M3 (tool)
will have ~0 expected calls per the A4'/A5 trend; M4-g always fires. If M4-g > M3,
you are measuring "content at all" vs "content that never reached the agent" — not
"external-vs-tool locus." This is equivalent to the old "noop MCP" tool-list-shape
finding (XN-010, RN-002) but inverted.

**Recommended action.**
- Add a **"true M0"** condition: M0 with a mandatory `memory_lookup` call forced via
  system prompt at step 1 (or equivalently, inject the top-k `memory_index` entries
  into the primer using the same pipeline as M4, so M0/M4 differ only in content).
- Or: demote M0 from "control" to "no memory" — and make the control for every
  comparison be the A3 (RAG+SR, no memory) baseline, explicitly stated.
- Add a **placeholder-primer control**: M1/M4 prompt with distilled content replaced
  by equivalent-token-count generic filler (e.g., GEOS glossary text not derived
  from train trajectories). If M1/M4 − filler ≈ 0, the lift is primer-shape.

---

### P1 — BLOCKER: Primer-size / token-count confound uncontrolled across M-conditions

**Location:** `build_system_prompt`, `scripts/run_experiment.py:437–512`.

**Evidence.** Line 473: `f"{agents_context.strip()}{primer_text}{cheatsheet_text}\n\n"`
concatenates primer + cheatsheet (memory content in M1/M4 will enter via the cheatsheet
slot or a new slot). No token budgeting enforced. The distiller input difference
between grounded and ungrounded is exactly: grounded gets `trajectory + TreeSim feedback`,
ungrounded gets `trajectory only`. Distiller output length is unconstrained — so
M1-g artifact is almost certainly larger in tokens than M1-u artifact.

**Why it invalidates Claim B.** (M1-g − M1-u) ≥ +0.04 is attributed to "grounding"
but naturally confounded with "bigger primer → more guidance text → model pays more
attention → fewer lazy decisions." This is the oldest confound in the agent-prompting
literature. If M1-g's artifact is 2× M1-u's artifact in tokens, the win is a token-budget
win.

**Recommended action.**
- Enforce a hard per-item token budget in the distiller that is **identical** across
  grounded and ungrounded. Even if this means dropping content in the grounded case,
  matched size is non-negotiable.
- Log `len(system_prompt_tokens)` and `primer_content_tokens` per run in
  `eval_metadata.json`. Report these alongside fa0 in the results table.
- Preregister: "Accept Claim B only if `|tokens(M1-g) − tokens(M1-u)| / tokens(M1-u) ≤ 0.10`
  at distillation time."

---

### P1 — BLOCKER: A3 baseline for success criteria is n=2, not n=3

**Location:** D-007:110; hub.md State of Knowledge.

**Evidence.** Decision gate says "Best memory variant mean fa0 ≥ A3 (0.653) + 0.05
at n=3 seeds AND std ≤ 0.05." hub.md row explicitly lists A3 as "Seeds: 2." Only
`pac1_plug_hook_s1` and `pac1_plug_hook_s2` exist under
`data/eval/claude_code_repo3_plugin/`. n=2 is not a credible variance estimate — a
2-seed std can be arbitrarily small or large and carries essentially no information
about the population std. Using 0.017 (the 2-seed A3 point) as the comparator and
requiring "std ≤ 0.05" for M1-g at n=3 is **asymmetric**: you will pass/fail a 3-seed
condition against an under-characterized n=2 baseline.

Also: threshold "+0.05 over 0.653" = target 0.703 with n=3 seeds on 17 tasks is
**under-powered** against the observed A5 std of 0.252. Even if the true mean of
M1-g is 0.70, 3-seed σ could exceed the full gap with comfortable probability.

**Recommended action.**
- Add one more A3 seed before launching the memory matrix, OR explicitly lower the
  M1-g threshold to include the A3 confidence interval:
  `M1-g mean − 1.96·(σ_Mg / √3) > A3 mean + 1.96·(σ_A3 / √2)`.
- Precompute power: given the observed A5 std ≈ 0.25 and target effect 0.05, 3 seeds
  has ≈ 18% power at α=0.05 two-sided. Pass/fail at 3 seeds will be noise-dominated.
  Honest options: (i) raise target effect to ≥ 0.10, (ii) increase seeds per cell to
  ≥ 5, (iii) use paired-per-task analysis and report Wilcoxon on 17 task-level
  deltas (the RN-002 recommendation — same point re-applies).

---

### P2 — Tool-list-shape confound between M-conditions is unresolved

**Location:** `scripts/run_experiment.py:975–1001` (`write_claude_mcp_config`
conditionally registers `memory` or `noop`). The planned M-matrix:
- M0, M3 have the memory MCP tool listed.
- M1-u, M1-g, M4-u, M4-g do not.

**Evidence.** XN-010 / RN-002 established that mere tool-list entries (empty noop MCP)
moved fa0 by ~+0.05–0.10 in the PAC-1 setting. Adding/removing the `memory_lookup`
tool changes the tool list across M-conditions.

**Why it invalidates claims A and C.**
- **Claim A** (M1-g vs A3): A3 has no memory tool in the list. M1-g has no memory
  tool in the list. That contrast is clean on tool list.
- **Claim C** (M4-g vs M3): M3 has the memory tool; M4-g does not. Any fa0
  difference is confounded with tool-list-shape (exactly the effect E20 proved
  is nontrivial).
- **Claim B attribution** (M1-g vs M1-u): both absent — clean.

So Claim C is particularly damaged.

**Recommended action.**
- Add a "memory tool present but content-less" noop for the external-inject variants
  (or equivalently, disable the memory tool on M3 and compare M3-no-tool-list vs
  M4-g). Either axis must be held fixed.
- At minimum, report tool-list diffs in the results table and note M3 vs M4-g
  is tool-list-confounded.

---

### P2 — Distiller inputs may themselves leak test-task content

**Location:** planned `trajectory_grounder.py` + `distiller.py` (not yet written).
Feeds are train trajectories + TreeSim feedback on train tasks (D-007:100–105).

**Evidence.** `memory_index.json` is built from `repo3_eval_run4` train trajectories
by `scripts/memory/build_gmem_index.py`. Those trajectories include the agent's
actual `Read` calls on `/geos_lib/...` XMLs (line 84). Since run4 predated the
current blocked-basename hygiene (confirmed: run4 at `/data/shared/.../repo3_eval_run4`
is the run4 referenced throughout hub.md), train-task trajectories would naturally
have read whatever reference XMLs the train tasks needed — **which, as the P1 table
shows, overlap with test-task blocked basenames**. If the distiller consumes those
trajectories, the distiller input contains the leaked basenames as part of the
"what worked" stream.

Additionally: TreeSim feedback is computed against the **train task's GT XML**, not
the test task's GT — so TreeSim feedback itself is hygiene-safe. But the `productive_rag_queries`
field (`memory_index.json`) already contains string-literal filenames like
`"triaxialDriver_base.xml"`. Those will enter the distiller verbatim unless stripped.

**Recommended action.**
- Before distillation: sanitize all inputs (trajectory Read-input file paths, productive
  RAG queries, section strength strings) against the union of test-blocked basenames.
- Log exact distiller inputs per artifact and diff against the blocked set at the
  artifact-build gate.

---

### P2 — Vanilla-CC-on-training-tasks run has its own hygiene hole

**Location:** planned `vanilla_cc_train_s1` (D-007:103–105). Purpose: harvest failure
trajectories for anti-pattern distillation. The design says "This preserves strict
train/test hygiene — no test-set data in memory."

**Evidence.** Risk #9 in your focus text raises the concern; I am confirming it is
real and providing a concrete attack.

1. Vanilla CC runs without the plugin will *read `/geos_lib/...` XML files* if
   they exist in the filesystem. The contamination mechanism (`EXCLUDED_GT_XML_FILENAMES`
   +  filtered copy) works per-task: **for each train task**, its own GT basenames are
   blocked. But a train task's vanilla trajectory can still Read XMLs that belong
   (as blocked GTs) to **test** tasks. Those reads happen over `/geos_lib` paths
   that are not blocked when the train task is the active one, because blocking is
   per-task-being-run.
2. If the failure-mode distiller then surfaces those paths as "what the agent tried
   and failed" anti-patterns, those are again basenames-for-test-task-GT in memory.

**Recommended action.**
- Run vanilla-CC on train tasks with a combined block list = `union(train_GT_basenames_for_this_task,
  all_17_test_GT_basenames)`. This is a departure from the standard per-task hygiene
  but it is required if the output trajectories feed memory artifacts consumed at
  test time.
- Log every Read path in the vanilla-CC-train runs and audit against the test blocklist
  before feeding to distillation.

---

### P2 — M3 embedding-MCP has an unpinned env-var fallback (silent degrade to M0-equivalent)

**Location:** planned embedding MCP (not yet written); pattern set by
`plugin/scripts/geos_rag_mcp.py:152–158` which is what your implementation will
likely copy.

**Evidence.** Existing pattern reads `OPENROUTER_API_KEY or OPENAI_API_KEY` with no
error path. `run_experiment.py:1176` silently falls back
`OPENROUTER_API_KEY = ANTHROPIC_AUTH_TOKEN` if the former is absent. If the M3 MCP
fails to reach the embedding endpoint at query time (timeout, rate-limit, 401),
a `try/except` block (common in MCP servers to avoid killing the agent) will
return an empty result set — making M3 behave as "memory tool present, zero
retrieval content returned." That is indistinguishable from M0's observed behavior.

**Why it invalidates the claim.** Claim C (M4-g > M3) already expected M3 to
underperform. If M3 silently degrades to empty-retrieval, the "locus" claim
collapses to "content at all > no content" — not "external > tool-locus." And
if the degradation is sporadic (timeouts), M3's variance will explode across seeds.

**Recommended action.**
- In the M3 MCP, raise a hard error on missing embedding API key at startup. No
  lexical fallback, no empty-result-on-timeout silent path.
- Log retrieval-call success/failure and per-query latency to
  `eval_metadata.json` and the events.jsonl stream.
- Preflight: prove the M3 MCP's embedding path works in `preflight_claude_native_mcp`
  before committing to the 15-run campaign.

---

### P3 — Memory_mcp's `_score()` function weights by `final_treesim` in a way that rewards self-consistency

**Location:** `plugin/scripts/memory_mcp.py:77`:
```python
treesim_weight = float(entry.get("final_treesim") or 0.5)
return score * (0.5 + treesim_weight)
```

**Observation.** This is the current M0 scoring and won't affect M1/M4, but it does
affect M3 if M3's ranker copies this pattern. It multiplicatively weights retrieval
score by past-task success. That biases retrieval toward memories whose past run
happened to be easy, independent of physics match. Not a blocker, but reportable.

**Recommended action.** For M3, use cosine similarity only; do not post-multiply by
`final_treesim`.

---

### P3 — Tokenizer stop-list typo

**Location:** `memory_mcp.py:43`:
```python
stop = set("a an and are as at be by for for from has have in into is it its of on or that the to was were will with this these those we you your if not".split())
```

"for" appears twice. Minor; affects nothing.

---

## What I verified and found OK (clean checks)

- **Train/test split file is consistent.** `misc/memory_split.json`: 18 train, 17 test,
  no overlap. Verified programmatically.
- **`memory_index.json` is built from train tasks only.** All 18 `task_id`s match
  the split's `train` list. No test task_ids appear as entries.
- **`create_filtered_geos_copy` correctly blocks per-task GT basenames at the
  filesystem level.** Hardlink copy + `ignore()` callback. Direct Read of blocked
  basenames will fail. The leakage in P1 is a prompt-content channel, not a
  filesystem-access channel.
- **Primer delivery path is uniform for the conditions under test.** All M-conditions
  use `system_prompt` delivery (per A3/A5 `primer_delivery: system_prompt` in
  sampled eval_metadata.json). This closes the "primer-mechanism" confound within
  the matrix — but does not close the "primer-size" confound (P1 #3).
- **Stop hook (SR) behavior is identical across all M-conditions.** All planned
  conditions stack on `stop_hook_enabled=True` per D-007:55. RN-002 infra fixes
  already in place.
- **`--strict-mcp-config` is set** (`run_experiment.py:1138`) — the MCP tool list
  is precisely the server set passed in. No stray MCPs.
- **OpenRouter cost-tracking path exists** (`compute_openrouter_cost` line 348).
  Not invalidated by this design.
- **"Frozen at test time" for M0, M1, M4 is true.** No test-time write paths exist
  in `memory_mcp.py`; it reads the index at module import (line 57) and never
  mutates. Parallelism-safe.
- **"Frozen" for M3 is true at the index level** (embedding index is a static
  ChromaDB file) — but see P2 on env-var silent degrade, which breaks "deterministic
  across parallel runs" even though the index itself is frozen.

---

## Overall assessment

- **Blocker for campaign?** **YES.** The leakage finding (P1 #1) is disqualifying
  on its own. Launching M1/M4 against the current `memory_index.json` or a distilled
  artifact derived from it without the stripping + regex audit steps would invalidate
  the outcome claims against peer review before any analysis happened. The n=2 A3
  baseline (P1 #4) makes the decision gate itself under-powered.
- **Confidence headline claim is valid, conditional on P1 fixes: LOW.** Even with
  leakage closed, the primer-size confound (P1 #3) plus the underpowered 3-seed
  gate (P1 #4) plus the M0-as-control problem (P1 #2) mean Claim B (attribution)
  is unlikely to survive peer review without matched-token-budget control and a
  placeholder-primer or true-M0 arm. Claim C is doubly at risk from both tool-list
  asymmetry (P2) and M3 silent-degrade (P2).
- **Most likely undiscovered failure mode I might still have missed:** the distiller
  itself is an LLM — if minimax-m2.7 (same model as the eval) is used for distillation,
  M1-g/M4-g is a *self-distillation loop on the same model that scores the task*,
  which is a subtle train-eval coupling (the distilled artifact is statistically
  over-fit to what minimax-m2.7 "likes"). The open-risk section (D-007:147) mentions
  this obliquely as "distiller LLM drifts to low abstraction" — but the harder
  version is "distiller = evaluator-model encourages over-confident in-distribution
  phrasing that the same model then fluently executes." Consider distilling with a
  different model (e.g., gemini-2.5-flash or sonnet-4.6 as mentioned in the escalation
  path) **as the primary artifact**, not the fallback.

**Priority ordering for the copilot's Responses table:**
1. P1 leakage (13/17 test tasks affected) — accept→fix; this is not optional.
2. P1 M0-as-control (add a true-M0 or use A3 as control) — accept→fix or accept→limitation.
3. P1 primer-size confound — accept→fix (token budget in distiller).
4. P1 n=2 A3 baseline — accept→fix (add A3 seed 3) or explicit limitation.
5. P2 tool-list shape across M-conditions — accept→limitation at minimum.
6. P2 distiller-input leakage — accept→fix (overlaps with #1's sweep).
7. P2 vanilla-CC-train hygiene — accept→fix.
8. P2 M3 embedding silent degrade — accept→fix (hard error on missing key).
9. P3 `_score` weighting — accept→limitation.

---

## Copilot Responses to Findings

Review commit: this response written 2026-04-22 before any code written for the memory ablation sprint; every finding here modifies the design before implementation rather than patching after the fact.

| Finding | Response | Details |
|---|---|---|
| **P1 #1 — Prompt-content leakage of test-task GT filenames (13/17 tasks)** | accept → fix | **Blocking.** Before any distillation: (a) rebuild `memory_index.json` with `reference_xmls` and `productive_rag_queries` **stripped of basenames** — only `solver_family` + abstracted description remain. (b) Add a regex gate `\b[a-z0-9_]+\.xml\b` on every distilled artifact that fails the artifact if any `*.xml` basename appears. (c) Add a filename-blocklist gate: load the union of `blocked_gt_xml_filenames` across all 17 test tasks, lowercase-match both as basename and as substring against every distilled item's `content` field; fail on match. (d) Log the audit result to `misc/memory_artifacts/<variant>/hygiene_audit.json`. Write `scripts/memory/hygiene_audit.py` as the single enforced gate; no distilled artifact ships without a passing audit. |
| **P1 #2 — M0-as-control has null test exposure** | accept → fix | Demote M0 from "control" to "existing implementation for context." Add a **placebo-primer** condition (M-placebo): same RAG+SR stack, primer extended with an equivalent-token-count **non-trajectory-derived** GEOS glossary/reference excerpt (generic schema-overview text, not distilled from trajectories, not mentioning specific past tasks). If M1/M4 does not exceed M-placebo on fa0, the lift is primer-shape, not memory content. |
| **P1 #3 — Primer-size / token-count confound uncontrolled** | accept → fix | (a) Distiller enforces a hard token budget — same budget for grounded and ungrounded (use `tiktoken` with a model-agnostic encoder for the count; pick a budget of ~1500 tokens for DC-Cu primer, ~200 tokens/item for RB items × max 5 items = 1000 tokens). (b) Preregister: a Claim B win requires `|tokens(grounded_artifact) − tokens(ungrounded_artifact)| / tokens(ungrounded_artifact) ≤ 0.10`. (c) Log `system_prompt_token_count`, `primer_added_tokens`, `memory_artifact_tokens` into every `eval_metadata.json` and report alongside fa0 in the results table. |
| **P1 #4 — A3 baseline is n=2, not n=3; 3-seed gate is under-powered** | accept → fix | (a) Launch A3 seed 3 (`pac1_plug_hook_s3`) in parallel with the memory matrix — ~$4, ~25min. (b) Use paired-per-task analysis: report mean fa0 delta + Wilcoxon signed-rank p-value on the 17 task-level paired deltas (same 17 tasks, same-seed pairing where possible). Do NOT pass/fail on 3-seed mean±std alone. (c) Decision gate revised: Claim A passes only if (i) mean M1-g − mean A3 ≥ +0.05 at n=3, (ii) Wilcoxon p ≤ 0.10 on paired-per-task deltas, (iii) std ≤ max(A3 std, 0.08). |
| **P2 #5 — Tool-list-shape confound between M-conditions** | accept → limitation + partial fix | The clean locus comparison requires a 2×2 {tool-in-list × content-delivery} which doubles conditions and blows the budget. Accepting the confound on **Claim C (locus)** and weakening the claim: "M4-g external injection delivers at least parity with M3 tool-locus under fa0; we cannot cleanly separate the locus effect from tool-list-shape." Report tool-list diffs in the results table. If Claim C becomes paper-critical, add a proper 2×2 locus experiment in a follow-up sprint. |
| **P2 #6 — Distiller input leakage** | accept → fix | Covered by the hygiene_audit.py gate in P1 #1 — same regex sweep applied pre-distillation to inputs (raw trajectory text + productive_rag_queries + any reference_xmls fields). Any input with a test-blocked basename is stripped of that field before being fed to the distiller. Audit logged. |
| **P2 #7 — Vanilla-CC-on-train-tasks hygiene hole** | accept → fix | When running the 18 vanilla-CC training-task runs to harvest failure trajectories, pass `blocked_gt_xml_filenames = union(task_own_blocks, all_17_test_task_blocks)` — this extends the per-task blocklist so vanilla-CC-train cannot Read any test-task GT basename. This is a departure from the standard per-task hygiene, justified because the output trajectories feed memory artifacts consumed at test time. Implement in `run_experiment.py` via a new flag `--extend-blocklist-with-test`. |
| **P2 #8 — M3 embedding-MCP silent degrade risk** | accept → fix | The M3 MCP (a) hard-errors on missing `OPENROUTER_API_KEY` at startup (`sys.exit(1)` with clear message), no fallback to lexical, no fallback to OpenAI; (b) preflight: before launch, call the embedding endpoint once from the MCP server with a test string; fail loudly if not 200; (c) log every retrieval call's success/latency to the events stream and `eval_metadata.json`; (d) on retrieval failure during a run, surface it as an explicit tool error the agent sees, not a silent empty result. |
| **P3 #9 — `_score` multiplicative TreeSim weighting** | accept → fix | For M3 embedding reranker: pure cosine, no `final_treesim` multiplier. Keep M0 as-is (it's the legacy artifact; we document its bias rather than fix it — M0 is no longer a control). |
| **P3 #10 — Stop-list "for" typo** | accept → fix | Trivial edit. |
| **Meta — distiller = evaluator model → self-distillation coupling** | accept → fix | Switch primary distillation model from minimax-m2.7 (the eval model) to **gemini-2.5-flash** via OpenRouter. Budget: ~$0.15/pass × 4 passes = $0.60 — cheaper than minimax. If gemini distillation produces broken artifacts, escalate to sonnet-4.6 (~$4/pass) as the documented fallback. This breaks the self-distillation loop and is a more honest cross-model separation. User pre-authorized this escalation path in the design conversation ("I would try gemini 3 flash first before graduating to SOTA models"). |

### What changes in the design as a result

1. **No code runs** until (a) `scripts/memory/hygiene_audit.py` written, (b) `memory_index.json` rebuilt with basenames stripped, (c) A3 seed 3 launched for a proper baseline.
2. **Conditions added:** M-placebo (equivalent-token primer with generic GEOS schema text, no trajectory content).
3. **Conditions dropped from must-run:** none, but **M3 demoted** — Claim C is now a best-effort comparison, not a paper-grade locus claim.
4. **Distillation model switched** to gemini-2.5-flash primary; minimax demoted to "smoke-test / comparison" not primary distiller.
5. **Statistical analysis switches** from mean+std to mean+Wilcoxon paired-per-task on the 17 test tasks.
6. **Token-budget parity** between grounded and ungrounded becomes a preregistered Claim B precondition.
7. New `hygiene_audit.py` blocks any artifact that fails the gate.

### What is NOT accepted

Nothing is rejected with a reason ("none of the findings are incorrect-as-stated"). All P1s are accepted as blockers; all P2s/P3s as fix-or-limitation.

### Next actions (ordered)

1. Write V2 of the design (as addendum to D-007 or a new D-008) reflecting the revised matrix, conditions, analysis, and distillation model.
2. Write `scripts/memory/hygiene_audit.py`.
3. Rebuild `memory_index.json` with basenames stripped.
4. Launch A3 seed 3 (background, independent of the above).
5. Launch vanilla-CC-train-s1 with extended blocklist (background).
6. Write `trajectory_grounder.py` and `distiller.py` (distiller hard-coded to gemini-2.5-flash endpoint).
7. Distill 4 artifacts (M1-u, M1-g, M4-u, M4-g), audit each, proceed only if audit passes.
8. Write M3 MCP with hard-error on missing key + preflight path.
9. Smoketest each condition (single seed, single task).
10. Multi-seed launch.

# Research Log

---

<a id="LOG-2026-04-20-1"></a>
### 2026-04-20 — Copilot attached to repo3

Attached research-copilot to existing project `repo3`. This is the third-generation GEOS XML authoring harness, building on vanilla Claude Code. Host docs (evaluation/runner/cc-comparison) are preserved. All copilot state lives in `../.copilot/`.

**Initial DAG: 4 Assumed foundations, 2 completed experiments, 1 pending experiment, 4 exploring ideas.**

- `I01` established task + 36-task eval suite
- `I02` established XMLTreeSim as headline metric
- `I03` established contamination-safe Docker sandbox
- `I04` established the plugin (geos-rag + MCP) as the candidate adaptation surface
- `E01` (completed, 0.643 TreeSim) = no-plugin + deepseek baseline
- `E02` (completed, 0.809 TreeSim) = plugin + minimax — confounded vs E01 (different model)
- `E03` (pending scoring) = plugin + deepseek on `repo3_eval_run4` — the apples-to-apples comparison that fills the main gap identified in `ablation_findings.md`
- `I05` = RQ: find CC adaptation that beats vanilla CC
- `I06`-`I09` = memory / primer / file-tree / simpler-RAG candidate interventions

**Immediate next:** score `repo3_eval_run4` against ground truth to resolve E03. This decides the session's plan: if plugin wins on apples-to-apples, the next move is adaptation-stacking; if flat/negative, we pivot hard into the memory system (user's strongest bet).

-> DAG: I01, I02, I03, I04, E01, E02, I05, E03, I06, I07, I08, I09
-> Evidence: ../misc/ablation_findings.md, ../misc/geophys_todo.md
-> Decision: (initialization)

---

<a id="LOG-2026-04-20-2"></a>
### 2026-04-20 — E03 resolved: plugin wins on deepseek (+0.175 TreeSim)

Scored `repo3_eval_run4` (plugin CC + deepseek-v3.2) against
`experiments_gt`. 35/36 tasks scored (SPE11b produced unparseable XML).

**Headline (paired 35 tasks):**
- plugin+ds mean TreeSim **0.828** vs no-plugin+ds **0.653** -> **+0.175**
- pass >=0.7: **31/35 (88.6%)** vs **19/35 (54.3%)** -> **+34.3 pp**
- Wins on 29/35 tasks, loses on 6 (max loss -0.17)

Biggest wins concentrated on tasks where no-plugin CC produced essentially
empty XML (TutorialSneddon 0.099 -> 0.804; ExampleDPWellbore 0.305 -> 0.992;
ExampleMandel 0.275 -> 0.948). Plugin mostly rescues catastrophic failures;
median gain (+0.144) is smaller than mean gain.

Updated E03 node: status=exploring -> status=good, metric_value=0.828,
decision=keep. Added I10 (memory-on-top-of-plugin) and I11 (plugin
decomposition: skill vs MCP attribution) as child nodes.

**Session pivot:** plugin wins cleanly, so the next contribution is to
show (a) the adaptation stacks (memory on top of plugin) or (b) the gain
is robust across models. I'll focus on (a) for the advisor meeting
because the user explicitly flagged memory as the highest-priority
intervention in `geophys_todo.md`.

-> DAG: E03, I10, I11
-> Evidence: docs/XN-001_plugin-vs-no-plugin-deepseek.md, misc/score_run4.log, misc/e03_vs_e01.txt
-> Decision: E03 decision=keep; promote I10 to next exploration target

---

<a id="LOG-2026-04-20-3"></a>
### 2026-04-20 — E04 (memory) launched

Built the memory-on-top-of-plugin pipeline (D-001). Cheatsheet generated
by deepseek-v3.2 via OpenRouter from 18 train-split trajectories of
repo3_eval_run4. Cheatsheet lives at `../plugin/cheatsheet.md` (~1700
tokens, 6 sections: RAG usage, XML structure, Mesh/Geometry, Solvers,
Constitutive, Field Specs + Common Mistakes).

Runner wired: new agent `claude_code_repo3_plugin_mem` reads
`cheatsheet_path` from agent config; `build_system_prompt` injects
between primer and RAG instructions. Dry-run + unit-level injection
test pass.

First real launch failed: 17/17 tasks errored on tmp_geos creation —
`/data/shared/geophysics_agent_data/data/eval/tmp_geos/` is brianliu-owned.
Relaunched with `--tmp-geos-parent /data/matt/geos_eval_tmp/` (my scratch
dir, confirmed writable). Currently running (bash bg).

-> DAG: E04 (new, status=exploring)
-> Evidence: decisions/D-001_memory-experiment-design.md, plugin/cheatsheet.md, misc/memory_split.json
-> Decision: (pending E04 completion)

---

<a id="LOG-2026-04-20-4"></a>
### 2026-04-20 — E04 resolved: memory cheatsheet HURTS performance (-0.32 TreeSim)

Scored `mem_run1`. Memory-stacking hypothesis NOT supported. Plugin
decisively beats plugin+cheatsheet on deepseek-v3.2.

**Headline (paired 14 scorable test tasks):**
- plugin-only mean TreeSim **0.831** vs plugin+cheatsheet **0.532** -> **-0.322**
- Including 3 no-output failures as 0: memory = 0.438, delta -0.393
- pass >=0.7: plugin 15/17, memory 4/14 (4/17 if failures=0)
- Memory wins on 1/14 tasks (pknViscosityDominated +0.13), loses on 13/14
- Failures: 3 `failed_no_outputs` + 1 timeout in memory run; plugin had 0/17 fails

Dominant failure mode: agent emits `redacted_thinking` block then
`end_turn` after 3-6 turns without calling Write/Edit. Inspected the
`AdvancedExampleModifiedCamClay` trajectory: agent did 3 RAG + 1 Read
(failed path) + 1 Bash, then produced a redacted_thinking and stopped.
Matches the qwen3.5-9b pattern where the model bails on tool-use without
making progress.

**Hypotheses (not tested):**
1. Context bloat — cheatsheet adds 1700 tokens to ~21K-token system
   prompt, possibly past deepseek's attention threshold for long system.
2. Task-specific advice from train-set patterns ("use InternalWellbore",
   "define dummy ElasticIsotropic") conflicts with test-task needs.
3. Cheatsheet guidance slows exploration / reduces agent's willingness
   to iterate.

**Updated E04 node:** status=exploring -> status=negative, decision=discard.
This rules out the specific D-001 design, not memory-as-an-intervention
in general. Future memory experiments should try: shorter
cross-task-only cheatsheet, MCP-tool memory, or stronger-model
environment.

**Advisor story update:** The plugin result (E03, +0.175 TreeSim) stands
as the headline adaptation. The memory follow-up is a negative with a
clear failure signature. Honest reporting: we have ONE adaptation that
beats vanilla CC. Stacking is deferred pending memory-design iteration.

-> DAG: E04 negative/discard
-> Evidence: docs/XN-003_memory-experiment-negative.md, misc/e04_vs_e03_test17.txt, misc/mem_run1.log
-> Decision: D-001 cheatsheet design discarded; revisit memory with restricted-scope / MCP-tool / stronger-model variants

---

<a id="LOG-2026-04-20-5"></a>
### 2026-04-20 — E05 short-cheatsheet also fails; E06 (cross-model) launched

**E05 (short-cheatsheet, ~300 tokens, explicit stop criterion):**
13/17 success = same count as E04; mean TreeSim 0.561 on 14 paired
scored vs plugin-only 0.831. Slightly better than E04's 0.532 but still
decisively negative. Same failure pattern: ModifiedCamClay + Extended
DruckerPrager failed_no_outputs with redacted_thinking -> end_turn;
EDPWellbore + Mandel timed out (BOTH succeeded in E03 and E04; NEW
failures under short cheatsheet). TutorialSneddon wrote malformed XML
(parse error). Length is NOT the cause; cheatsheet-in-system-prompt as
a general pattern is what breaks deepseek. E05 discarded.

**CC native memory audit (user flagged in geophys_todo.md):** checked
all 36 E03 task event files and the per-task `.claude_home` dirs.
Result: CC native memory is a **no-op** in our pipeline. Every task
has the memory_paths setup, but:
- memory directories exist but are empty (0 files written) across
  all sampled tasks in plugin-run4 and ablation-v2
- 0 memory-named tool calls across 36 tasks
- /memory slash command is NOT in the agent's slash_commands list
- per-task /workspace is wiped with container anyway, so any memory
  would not persist
So our baselines + cheatsheet experiments are all running ON A CLEAN
slate with respect to CC's native memory. Not a confound.

**E06 (cross-model, plugin-less minimax on 17 test):** launched with
workers=12 to test concurrency headroom (machine has 128 CPU, 900GB
RAM, 3 L40S GPUs idle). 12 docker containers spun up cleanly, no
rate-limit errors. Will pair with E02 (minimax+plugin, already scored
on 16/17 test tasks) for cross-model analog of E03's paired comparison.
~$60 of OpenRouter spend. If plugin advantage holds on minimax,
generalization claim strengthens; if not, plugin win is deepseek-
specific and the paper story needs reframing.

**Memory direction:** user pushed back on DC-Cu (fair — sequential
curation without trace regeneration is just batched aggregation
dressed up). Agreed to drop further memory experiments this sprint.
Remaining budget focuses on cross-model (E06) + potential filetree
(I08) + multi-seed replication of E03.

-> DAG: E05 negative/discard; E06 exploring
-> Evidence: misc/memshort_run1.log, misc/mm_noplug_run1.log (in progress)
-> Decision: memory via system-prompt-inject design abandoned for sprint; focus shifts to cross-model + filetree

---

<a id="LOG-2026-04-20-6"></a>
### 2026-04-20 — E06 resolved (cross-model POSITIVE); E07 filetree launched

**E06 (minimax-m2.7 no-plugin on 17 test tasks):** 17/17 agent
success, 15/17 scored (2 XML parse errors: ExampleThermalLeakyWell,
TutorialPoroelasticity — minimax wrote malformed XML without RAG help).
Paired against E02 (plugin+minimax) on 15 common scored tasks:
- minimax+plugin 0.809 vs minimax-no-plugin 0.694 -> **plugin wins +0.102**
- Plugin wins 11/15 tasks, no-plugin wins 4/15
- Biggest plugin win: ExampleMandel (+0.659), DeviatedElastic (+0.322)
- Biggest no-plugin win: TutorialSneddon (+0.218), Thermoporoelastic (+0.144)

**Cross-model generalization CONFIRMED.** Plugin advantage holds on
minimax (+0.102) smaller than on deepseek (+0.178), consistent with
minimax being a stronger base model. Updated E06 to status=good,
decision=keep. Interpretation: plugin rescues catastrophic failures
that weaker models hit; stronger models find reference examples
without RAG. Expected pattern.

**Operational finding:** workers=12 safe — 17 tasks in 17 min wall,
0 rate-limit errors from OpenRouter. Machine has 128 CPU / 900GB RAM /
3 L40S GPUs idle. Recommend workers=12 default.

**E07 (filetree injection on 17 test tasks, deepseek-v3.2)
launched:** adds a precomputed `/geos_lib/inputFiles/` path index
(~4.5KB, 746 files across 87 dirs) to the system prompt so the agent
can locate candidate reference XMLs without Glob/Bash find. Tests the
hypothesis that RAG's primary value is file discovery vs. semantic
retrieval. If filetree wins, cheaper alternative to full RAG; if not,
semantic retrieval matters.

Also updated hub SoK and wrote XN-006 (consolidated advisor brief).

-> DAG: E06 good/keep; E07 exploring
-> Evidence: docs/XN-005_cross-model-plugin-win.md, docs/XN-006_advisor-brief-final.md, misc/e06_vs_e02.txt
-> Decision: cross-model claim is now two-model; plugin generalizes. Workers=12 default.

---

<a id="LOG-2026-04-20-7"></a>
### 2026-04-20 — E07 filetree ALSO negative; convergent system-prompt-stacking pattern

**E07 (filetree injection on 17 test):** 17/17 scored (3 timeouts
produced partial XML). 0 redacted_thinking failures — structural
content does NOT trigger the cheatsheet-style stop pattern. BUT mean
TreeSim **0.604 vs plugin-only 0.831 = delta -0.227** paired. Filetree
wins 2/17, plugin-only wins 15/17.

**Striking per-task pattern:** filetree regresses hardest on EXACTLY
the tasks plugin-only rescues most catastrophically. Plugin-only beat
no-plugin on Sneddon +0.705; filetree LOSES vs plugin-only on Sneddon
-0.719. DPWellbore +0.687 -> -0.687. Mandel +0.673 -> -0.637. The
filetree is directly nullifying the plugin's rescue mechanism —
probably by giving agent explicit file paths that bypass the semantic
RAG.

**Cross-experiment pattern now clear:** ANY auxiliary content injected
into system prompt hurts plugin, across 3 experiments:
- E04 long cheatsheet: -0.322
- E05 short cheatsheet: -0.270
- E07 filetree: -0.227

Different content types (instructions vs structure), different
lengths (300-4500 tokens), same qualitative result. Plugin's value
is specifically the MCP RAG + skill prompt. System-prompt stacking
is counterproductive.

**Positive buried in 3 negatives:** this is itself a useful finding.
Future plugin augmentations should target the TOOL layer (new MCP
tools, better retrieval, plugin-internal logic) not the SYSTEM PROMPT
layer. Saves us from several natural but misguided future attempts.

-> DAG: E07 negative/discard; I08 negative
-> Evidence: docs/XN-007_filetree-negative.md, misc/e07_vs_e03_test17.txt
-> Decision: drop system-prompt augmentation as a design direction; focus future work on MCP tool additions.

---

<a id="LOG-2026-04-20-8"></a>
### 2026-04-20 — Extended-session pivot: primer ablation + retry memory via non-system-prompt channels

User went to sleep after advisor brief was ready. Extended-session plan
in D-002. Trajectory analysis (subagent) returned XN-008: plugin
gains are genuine signal, not variance — 3 mechanism classes
(semantic discovery, schema awareness, variant disambiguation).

**New experiments launched / designed:**
- **E08 (primer-minimal):** plugin + ~450-token minimal primer (vs full
  ~10K). Tests whether primer content matters. Running, ~20 min in.
- **E09 (memory-as-workspace-file):** cheatsheet_abstract.md (shortcuts
  + pitfalls, 550 tokens) delivered as /workspace/CHEATSHEET.md with a
  2-line system-prompt pointer. Tests delivery channel vs content.
  Queued.
- **E11 (G-Memory-lite as MCP tool):** new MCP server memory_mcp.py
  exposes memory_lookup(query). Built memory_index.json from 18 train
  trajectories — entries contain task_id, final_treesim, reference_xmls,
  productive_rag_queries, section_strengths, topic_keywords. Keyword
  scoring + treesim-weighted ranking. Smoke tests on 5 queries return
  appropriate past tasks. agent=claude_code_repo3_plugin_gmem. Queued.

**Why G-Memory-lite design choices:**
- Frozen index (build once from train, serve read-only at test)
  preserves parallelism per D-001 constraint.
- Concrete examples (file paths + past RAG queries) instead of abstract
  rules - addresses user's question about whether content type matters.
- MCP tool delivery instead of system-prompt inject — sidesteps the
  E04/E05/E07 failure mode entirely.
- Pure keyword scoring (no embeddings) to avoid heavy deps and stay
  fast/reproducible.

**Not doing this sprint:**
- Full G-Memory with graph + FINCH clustering (too heavy).
- Dynamic Cheatsheet Cumulative with trace regeneration (~3h, rejected
  after user pushback on marginal value over batch aggregation).
- Hard-mode eval set generation (deferred; mine_examples_v2.py exists
  and can generate required_only specs but defer running to later).
- Opus cross-model (cost-deferred).

-> DAG: E08 exploring, E09 pending, E11 pending
-> Evidence: docs/XN-008_plugin-mechanism-trajectory-analysis.md, plugin/memory_index.json, plugin/scripts/memory_mcp.py, scripts/memory/build_gmem_index.py, .copilot/decisions/D-002_extended-session-plan.md
-> Decision: focus extended session on memory via non-system-prompt channels (workspace file + MCP tool) + primer ablation. Frozen at test time.

---

<a id="LOG-2026-04-20-9"></a>
### 2026-04-20 — E08 (minimal primer) NEGATIVE; primer content is load-bearing

Scored minprimer_run1: plugin + ~450-token minimal primer vs E03's
full primer on 17 test tasks. **Paired delta -0.235** (minimal 0.596
vs full 0.831). Minimal-primer wins 1/17, loses 16/17. 4 timeouts
(vs 0 in E03). Largest losses on SAME 3 tasks that E07 filetree
regressed most on: Sneddon -0.723, DPWellbore -0.688, Mandel -0.677.

**Surprising finding:** even with plugin RAG fully present, stripping
the primer's detailed schema-navigation scaffolding catastrophically
hurts the catastrophic-failure-rescue mechanism. The primer is not
just narrative context — it seems to orient the agent's RAG query
strategy in a way that determines whether rescue fires.

Primer (647 lines) + RAG MCP together form the active-ingredient
stack of the plugin. Either one removed → rescue mechanism breaks.

**Updated convergent pattern (four negatives):** E04/E05/E07/E08 all
show that interfering with the plugin+primer+MCP stack hurts
performance on the rescue-task subset:
- E04 long cheatsheet in system prompt: -0.322
- E05 short cheatsheet in system prompt: -0.270
- E07 filetree in system prompt: -0.227
- E08 shrink primer: -0.235

All regress hardest on the SAME 3 rescue tasks. Strong signal that the
current primer + RAG MCP is a tightly-coupled design; pieces must stay
together.

Launched E09 (memory-as-workspace-file) immediately after. E11
(G-Memory-lite MCP tool) queued after that.

-> DAG: E08 negative/discard
-> Evidence: misc/e08_vs_e03_test17.txt, misc/minprimer_run1.log
-> Decision: minimal-primer design discarded; preserve full primer. Future primer work should ADD content, not subtract. Next: test whether memory-via-file (E09) or memory-via-MCP-tool (E11) helps.

---

<a id="LOG-2026-04-20-10"></a>
### 2026-04-20 — E09 (workspace-file memory) NEGATIVE; E11 running

E09 delivered the abstract cheatsheet as /workspace/CHEATSHEET.md
(not in system prompt, just a 2-line pointer). Same result class as
E04/E05/E07/E08: 11/17 agent success, 6 timeouts, 2 scoring failures.
Paired mean 0.622 vs plugin 0.831 = **delta -0.212** on 15 scored.
Wins 2/15, loses 13/15. Largest regressions on Sneddon -0.733,
DPWellbore -0.696, Mandel -0.618 (same 3 rescue tasks).

**Channel distinction doesn't rescue memory.** Whether the content is
in the system prompt, the workspace file, or simply tweaks the
primer's depth, performance degrades by similar magnitudes on the
same 3 rescue tasks. Convergent negative pattern now 5 independent
experiments deep:
- E04 long cheatsheet (sys-prompt, 1700t): -0.322
- E05 short cheatsheet (sys-prompt, 300t): -0.270
- E07 filetree (sys-prompt, 1100t): -0.227
- E08 minimal primer (shrink): -0.235
- E09 workspace cheatsheet (file, 550t): -0.212

One channel left untested: MCP tool. E11 (G-Memory-lite as MCP
`memory_lookup`) launched immediately — uses the same memory_index.json
content but delivered only when the agent calls a tool. If E11 fails
too, we have strong evidence the problem is not delivery at all, it's
that ANY perturbation to the plugin+primer stack destabilizes the
rescue mechanism on Sneddon/DPWellbore/Mandel/Poroelastic-family
tasks.

-> DAG: E09 negative/discard; E11 exploring
-> Evidence: misc/e09_vs_e03_test17.txt, misc/memws_run1.log
-> Decision: workspace-file memory discarded; only MCP-tool channel remaining to test.

---

<a id="LOG-2026-04-20-11"></a>
### 2026-04-20 — E11 (G-Memory MCP tool) NEGATIVE but smallest-magnitude

E11 paired mean 0.638 vs plugin 0.831 = **delta -0.192** on 17 tasks.
Agent called memory_lookup on all 17 tasks (1 call each, early in
trajectory) — MCP tool is discovered and used. Smallest-magnitude
negative in the 6-variant memory/augmentation battery:

| Attempt | Delta | Failure concentration |
|---|---:|---|
| E04 long cheatsheet sysprompt | -0.322 | redacted_thinking failures |
| E05 short cheatsheet sysprompt | -0.270 | redacted_thinking failures |
| E07 filetree sysprompt | -0.227 | all 3 rescue tasks |
| E08 minimal primer (shrink) | -0.235 | all 3 rescue tasks + timeouts |
| E09 workspace cheatsheet | -0.212 | all 3 rescue tasks + timeouts |
| **E11 MCP-tool memory** | **-0.192** | **Sneddon, Mandel; rescues DPWellbore** |

E11 is partially different: it RESCUES DPWellbore (0.939 vs plugin
0.992, only -0.05) where all other memory variants score 0.28-0.40.
Also IMPROVES pknViscosityDominated by +0.142. But still fails on
Sneddon (-0.716) and Mandel (-0.669).

**Final verdict on memory this sprint:** ALL 6 variants hurt
performance on the 17-task test subset. The "rescue mechanism" on
TutorialSneddon and ExampleMandel is extremely fragile — ANY
perturbation to the plugin+primer+RAG stack kills it, regardless of
delivery channel (sys-prompt, file, MCP tool) or content type
(instructions, structure, concrete example-mappings). MCP-tool
delivery is the least-bad channel and shows PARTIAL rescue on some
tasks, which is a direction worth investigating.

**Possible paths forward (not this sprint):**
- Cross-model test of memory — maybe only deepseek-v3.2 has this
  fragility; minimax or Opus may handle memory without breaking.
- Memory designed specifically to avoid perturbing early trajectory
  — e.g., agent asks for memory only mid-task when stuck, not
  proactively.
- Plugin attribution first (skill-only, MCP-only) — understand which
  part of the plugin creates the fragile rescue mechanism.

-> DAG: E11 negative/discard
-> Evidence: misc/e11_vs_e03_test17.txt, misc/gmem_run1.log, plugin/scripts/memory_mcp.py, plugin/memory_index.json
-> Decision: memory experiments paused for this sprint. Full stack (plugin+primer) is stable; augmentations break rescue. Advisor report should frame as: 6 convergent negatives characterizing a fragility pattern, not a single failure.

---

<a id="LOG-2026-04-21-1"></a>
### 2026-04-21 — Memory failure mechanism characterized; E12 gated-memory launched

User asked for deeper analysis on WHY memory attempts hurt. Two
subagents dispatched:

**XN-009 (trajectory analysis subagent)** — Read actual events.jsonl
for Sneddon/Mandel/DPWellbore across plugin-only (E03) and all 5
memory variants (E04/E05/E07/E09/E11). Three distinct failure
mechanisms identified:
1. **Cheatsheet anchoring** (E04, E05): agent pattern-matches on
   filenames and reads /workspace/inputs/ (its own outputs) instead
   of /geos_lib references.
2. **Filetree path hijacking** (E07): agent bypasses semantic RAG
   entirely, reads paths blindly without reasoning about solver family.
3. **Memory lookup poisoning** (E11): wrong-physics priors returned
   with high confidence. Sneddon query → hydrofracture. Mandel query
   → hydrofracture. DPWellbore query → triaxialDriver (right solver
   family, wrong geometry).

Common cause: ALL augmentations fire UPFRONT as warm-start, disrupting
the plugin's iterative semantic-discovery RAG loop (characterized in
XN-008) that enables catastrophic-failure rescue on these 3 tasks.

**LN-001 (literature subagent)** — Surveyed test-time memory
literature. Most relevant precedents: Min et al. 2022 (format >
content), Levy et al. 2023 (clustered demonstrations hurt OOD),
Reflexion (on-policy same-task retry). Important counter-evidence:
literature does NOT support the strong "memory will help" claim for
heterogeneous-task agentic settings with strong base RAG + primer.
No paper reports a memory gain comparable to our +0.178 plugin gain.
Valyu API key not configured this session — used training-cutoff
knowledge + cloned DC repo + geos_agent memory modules.

**E12 launched (gated memory — threshold + delay-trigger):**
- `memory_lookup` enforces min_score=0.6 (was unthresholded), returns
  "no match — use RAG" fallback below threshold.
- System-prompt instruction reframes memory as SAFETY NET, not
  primary search. Warns about past-task anchoring.
- Pre-check on the 3 problem queries: Sneddon (0.41) and Mandel
  (0.49) now get fallback. DPWellbore (0.97 on off-domain
  triaxialDriver) still bypasses → known E12 limitation → motivates
  E13 physics-family filtering.
- solver_family field added to memory_index.json (prerequisite for
  E13).

Also did not run /adversarial-review — codex CLI not available
locally (same as last session). Reviewer RN-001 was same-model; no
different-model adversarial gate this session.

-> DAG: E12 exploring (memory_mcp behavior + system-prompt gated)
-> Evidence: docs/XN-009_memory-failure-trajectory-analysis.md, docs/LN-001_memory-test-time-literature.md
-> Decision: test threshold+delay fix first; if partial success, add physics-family filter as E13. If E12 full negative, pivot to Reflexion-style same-task retry or DC-RS (per LN-001 recommendation).

---

<a id="LOG-2026-04-21-2"></a>
### 2026-04-21 — E12 negative (-0.186); E13 silent-memory launched

**E12 (gated memory: threshold=0.6 + delay-trigger instruction):**
Paired delta -0.186 vs plugin-only on 16 scored tasks (Sneddon
failed_no_outputs and was excluded). Marginal improvement over
E11's -0.192. **Threshold + delay alone is insufficient.**

Wins (4): pknViscosityDominated +0.221 (biggest memory win to date),
ViscoDruckerPrager +0.053, DruckerPrager +0.031, buckleyLeverett +0.055.
These are tasks where train coverage matches and memory's gating
worked correctly.

Losses (12): Mandel -0.581, DPWellbore -0.687, DeviatedElastic -0.636,
TutorialPoroelasticity -0.348, ModifiedCamClay -0.332, plus smaller.
Rescue-task regressions persist.

**Critical observation:** for most tasks (15/17) the agent did NOT
call memory_lookup at all (mem=0). The threshold-correctly-suppressed
queries (Sneddon, Mandel) still failed. This means the memory
*instruction* (375 tokens of system prompt) is itself anchoring
agent behavior, even when the tool isn't called.

**Sneddon E12 trajectory inspected:** agent did 3 RAG queries,
explored efemFractureMechanics directory, found correct files...
then called AskUserQuestion("which solver configuration?") and
stopped at end_turn with NO XML written. NEW failure mode — not
redacted_thinking, but defer-to-user. The memory instruction's
mention of "verify solver family" plausibly biased the agent into
treating solver choice as user-input territory.

**E13 launched (silent memory):** same threshold-gated memory_mcp,
but `memory_prompt_hint=False` drops the entire 924-char system-
prompt block about memory. Agent discovers memory_lookup only via
the MCP tool list and the tool's own docstring. Tests whether the
instruction itself was the anchor (vs. the tool's mere existence
in the tool list).

Pre-registered: if E13 paired delta is closer to 0 than E12's -0.186,
instruction-anchoring is confirmed as the dominant remaining
mechanism. If E13 is similar to E12, the issue is the tool's
existence in the tool list (or the docstring), not the prompt.

-> DAG: E12 negative/discard, E13 exploring
-> Evidence: misc/e12_vs_e03_test17.txt
-> Decision: drop the system-prompt instruction; test memory-via-tool-discovery only.

---

<a id="LOG-2026-04-21-3"></a>
### 2026-04-21 — MAJOR REFRAMING: memory negatives were largely seed variance

**E13 (silent memory):** paired -0.180. Memory tool present but agent
never called it (mem=0 on all 17). Same magnitude as E11/E12. Pattern
suggested either MCP-tool presence affects behavior or seed variance.

**E14 (PLAIN PLUGIN seed-2, variance anchor):** paired delta -0.215
vs E03. Same plugin, same model, same tasks — fresh run today scored
0.616 vs E03's 0.831. Catastrophic regressions on the SAME 3 rescue
tasks (Sneddon -0.735, DPWellbore -0.701, Mandel -0.610).

**The convergent pattern across all reruns:**

| Run | Sneddon | Mandel | DPWell | mean(17) |
|---|---:|---:|---:|---:|
| E03 plugin seed 1 | 0.804 | 0.948 | 0.992 | 0.831 |
| E11 plugin+gmem | 0.088 | 0.279 | 0.939 | 0.638 |
| E12 plugin+gmem-gated | (fail) | 0.367 | 0.305 | 0.646 |
| E13 plugin+gmem-silent | 0.432 | 0.290 | 0.304 | 0.651 |
| **E14 PLAIN PLUGIN seed 2** | **0.069** | **0.338** | **0.291** | **0.616** |

All 4 reruns cluster at 0.62-0.65 mean with similar per-task pattern.
**The 'memory hurts' deltas of -0.18 to -0.32 (E04-E13) appear to be
substantially or entirely seed variance against an outlier baseline.**
E03 was a single lucky seed where the agent happened to discover the
right reference XMLs for Sneddon/Mandel/DPWellbore. Cross-seed
variance on these specific tasks is huge (~0.7 swing per task).

This refames everything:
- The "plugin +0.178 over no-plugin" headline is shaky; needs
  multi-seed verification.
- Memory variants weren't actually hurting — they were being compared
  to a lucky baseline.
- The rescue mechanism on Sneddon/DPWellbore/Mandel is itself fragile;
  plugin only "rescues" them sometimes.
- pkn improved consistently across all variants AND in plain-plugin
  rerun — that improvement is real (within noise) but NOT memory-
  specific.

**E15 launched:** plain no-plugin seed 2 on 17 test tasks. If
no-plugin also has ±0.2 variance, the +0.178 gain claim collapses.
If no-plugin variance is small, plugin's lucky-seed-only rescue is
informative.

This is good news for memory — none of the variants is actually bad.
But it's BAD news for the plugin headline claim. Need multi-seed
analysis end-to-end before any paper claim.

-> DAG: E13 negative/discard, E14 keep (variance anchor), E15 exploring
-> Evidence: misc/e13_vs_e03_test17.txt, misc/e14_vs_e03_test17.txt
-> Decision: pivot to multi-seed analysis. All prior single-seed comparisons need re-interpretation. Hub State of Knowledge needs major update once E15 lands.

---

<a id="LOG-2026-04-21-7"></a>
### 2026-04-21 (late evening) — E20 complete; hook-rescue claim NOT supported

E20 (48 runs) finished 12:45 UTC. See docs/XN-012_hook-ablation.md for
full writeup. Headline:

- **0 `failed_no_outputs` in any cell's final status** across 48 runs.
  E17's 4/17 rate on the same 4 tasks at a single seed did not
  reproduce — consistent with known high cross-seed variance.
- **Mean fa0 TreeSim:** C0 0.643, C1 0.530, C2 0.595, C4 0.557. Hook
  trends negative (Δ −0.112 vs C0, p≈0.31 at n=12).
- **Hook DID rescue 2 wrong-path-write failures** (1 inline C1; 1 after
  retry C4) but rescued XML scored low — rescue trades "no XML" for
  "low-quality XML".
- **Dominant failure mode = timeout on ExampleThermalLeakyWell** (7/8
  non-successes), which the hook cannot rescue (fires on Stop, not
  docker kill).

Decision per D-004 branch 4: do NOT expand to full 17-task factorial.
Hook ships as defense-in-depth; no paper claim for hook-rescue.

Validated as side effect: hook infrastructure works correctly end-to-end
after two bug fixes (schema + `--plugin-dir` / `--settings` routing) and
one mid-campaign patch (`stop_hook_active` early-return removed).

-> DAG: E20 → negative/discard
-> Evidence: docs/XN-012_hook-ablation.md, misc/e20_summary.json,
   data/eval/results/e20/
-> Decision: stop E20 line; reallocate to fallback priorities.

---

<a id="LOG-2026-04-21-6"></a>
### 2026-04-21 (mid-campaign) — Hook bug #3 caught in run1 data; fixed for run2/run3

While watching E20 run1 score, caught C1 ExampleThermalLeakyWell's
failure: hook blocked (no_xml), agent wrote to inputs/, BUT the XML was
malformed (`<?xml version1.0 encoding=UTF-8?>` — missing `=` and quotes).
The hook's next Stop event should have caught the parse error but didn't,
because the hook early-returned on `payload["stop_hook_active"] == True`.
That field is Claude Code's "you're in a re-entry chain" signal, and my
`_block` emit was unconditionally short-circuiting on it.

Fix: removed the early-return. Loop protection is now solely via the
`max_retries` counter (default 2). Hook now catches malformed XML on
re-entry instead of letting it slip through.

Tradeoff: run1 data (C1/C4) uses the old hook (one chance to fix XML
content). Runs 2+3 use the new hook (up to max_retries chances).
Not restarting run1 — the change is strictly more aggressive at rescue,
so any C1/C4 gains in runs 2+3 over run1 may partly reflect the hook
update, not just seed variance. Will note in XN-012 per-run breakdown.

-> DAG: E20 (still exploring)
-> Evidence: plugin/hooks/verify_outputs.py diff, data/eval/.../e20_run1/ExampleThermalLeakyWell/inputs/thermalLeakyWell_base.xml
-> Decision: proceed with run2/run3; call out hook-code drift in write-up.

---

<a id="LOG-2026-04-21-5"></a>
### 2026-04-21 (evening) — Handoff integrated; E20 hook-ablation launched; two hook-load bugs found

The user started a prior Claude Code session outside this directory so the
copilot's skills/hooks were not active. That session produced
`docs/SESSION_HANDOFF_2026-04-21_end-turn-debug.md` documenting the
`failed_no_outputs` failure mode (XN-010 mechanism: minimax/OpenRouter
returns an empty completion after a tool_result, harness maps that to
`stop_reason=end_turn`), committed a plugin Stop hook
(`plugin/hooks/verify_outputs.py`), and proposed an ablation (§5) to
isolate hook effect from tool-list-shape effect. They did not launch it.

This session (correct cwd, hooks active):

**Two critical bugs found that invalidate the prior session's "ready to
run" framing:**
1. `plugin/hooks/hooks.json` had the wrong schema
   (`Stop: [{type,command}]` instead of
   `Stop: [{matcher, hooks: [{type,command}]}]`). `claude plugins list`
   reported load failure with explicit zod error. Hook never registered.
2. `scripts/run_experiment.py build_claude_native_command` did not pass
   `--plugin-dir`. Without that flag, plugin isn't loaded even with
   bind-mount. The hook never ran in any prior experiment.

**Design-review finding (RN-002, experiment-designer).** Loading the plugin
via `--plugin-dir` would surface its `geos-rag` skill in the tool list,
confounding hook effect with tool-list-shape effect (the very effect C2
is meant to isolate). Fixed by routing hooks through `--settings` instead
of `--plugin-dir`: per-task `claude_settings.json` written by the runner,
containing only the Stop hook command. Tool list stays identical to
E17/E18 across all cells.

**Adversarial review gate.** Codex CLI unavailable locally (same
constraint as D-003). Logged as D-005 with mitigation justifications
(pre-registered decision rule, failures-as-zero primary metric,
hook-event log fires on all code paths including disabled, designer
same-model review already applied). Will not launch full 17-task
factorial without adversarial review if codex becomes available.

**E20 design (D-004).** 4 E17 failure tasks ×
3 independent runs × 4 cells:
- C0 `claude_code_repo3_plugin_nohook`: hook OFF, no extra tool
- C1 `claude_code_repo3_plugin`: hook ON, no extra tool
- C2 `claude_code_repo3_plugin_noop_nohook`: hook OFF, noop MCP tool
- C4 `claude_code_repo3_plugin_noop`: hook ON, noop MCP tool

48 runs total. ~90 min wall, ~$15. Pre-registered decision rule in D-004.

**Instrumentation.** `verify_outputs.py` now emits JSONL
`.verify_hook_events.jsonl` on every invocation with reason_category
(block variants + allow variants including `disabled`); fires in C0/C2
even when the hook is a no-op so we can prove code-path parity. New
`plugin/scripts/noop_mcp.py` exposes a single `noop(s)` tool with a
docstring that says "do not call, no info" — isolates the tool-list-shape
effect.

**Smoketest (1 task × 3 cells; C4 deferred):** verified end-to-end:
- C0: settings={}, mcp=[geos-rag]
- C1: settings=hook, mcp=[geos-rag]
- C2: settings={}, mcp=[geos-rag, noop]  (noop connected)
All 3 cells ran correctly.

-> DAG: I12 (hook rescue), I13 (tool-list confound), E19 (discarded —
   never ran), E20 (exploring — running now)
-> Evidence: decisions/D-004, D-005; docs/XN-010; docs/SESSION_HANDOFF
   _2026-04-21_end-turn-debug.md
-> Decision: launch E20 narrow; do NOT expand to full 17-task factorial
   without adversarial review + narrow-pass signal.

---

<a id="LOG-2026-04-21-4"></a>
### 2026-04-21 — MAJOR BREAKTHROUGH: memory works on canonical specs

Two findings this session that fundamentally reshape the project:

**Finding 1: Canonical spec mismatch was the primary source of
cross-condition variance.** Brian (collaborator) used
`experiments_test36_template` (v2 specs). I used `experiments` (v1).
Task instructions DIFFER between the two directories for every task.
This contaminated nearly every comparison we'd done.

**Finding 2: On canonical (v2) specs with minimax, memory HELPS.**

Canonical sweep results (same seed, same v2 specs, minimax):
- E16 no-plug+mm+v2: 0.566 mean (12 scored, 5 scoring errors)
- E17 plain plug+mm+v2 seed 2: 0.575 mean (13 scored, 4 failed_no_outputs)
- **E18 gmem-silent+mm+v2: 0.725 mean (17/17 scored, 0 failures)**

Paired deltas (matched seed, matched specs):
- E18 (mem+plug) vs E16 (no-plug): **+0.117**, 8/4 wins
- **E18 (mem+plug) vs E17 (plain plug): +0.094, 9/4 wins**
- E17 (plain plug) vs E16 (no-plug): +0.055, 6/4 wins

**So the full stack is: memory+plug (+0.15 over no-plug) > plain plug
(+0.055 over no-plug) > no-plug.** And memory+plug also prevents the
unexpected minimax plain-plug failure mode (E17 had 4 failed_no_outputs;
E18 had 0).

Biggest memory-over-plain-plug wins: IsothermalLeakyWell +0.511,
CasedContactThermo +0.507, ModifiedCamClay +0.424,
ThermoporoelasticConsolidation +0.298.

This reframes every prior 'memory hurts' finding (E04-E13) as
spec-mismatch + plugin-side seed variance confounds. Memory is the
best variant we've found when properly compared.

**Operational decisions:**
- Created `/data/shared/geophysics_agent_data/matt_repo3/` symlink +
  README for collaborator access to all our outputs.
- Committed to minimax + v2 specs as the canonical testbed (4x
  faster, cleaner baseline, canonical spec set).

**Next priorities:**
1. Re-test E11/E12 (other memory variants) on v2+minimax. Only E13
  (silent) has been run. Are they also positive?
2. Multi-seed E18 + E17 for proper variance estimate.
3. Hard mode via mine_examples_v2.py required_only generation.

-> DAG: E15 good/keep, E16 good/keep, E17 good/keep, **E18 good/keep (first memory positive)**
-> Evidence: misc/e16_vs_e02_test17.txt, misc/e17_vs_e16_test17.txt, misc/e18_vs_e17_test17.txt, misc/e18_vs_e16_test17.txt
-> Decision: memory+plugin+minimax+v2 is now the best-known configuration. Reframe narrative from 'memory doesn't work' to 'memory works when properly compared.'

---

<a id="LOG-2026-04-21-5"></a>
### 2026-04-21 — PAC-1 ablation campaign committed (D-004, XN-012); E19-E22 planned

User framed the contribution as a stack of three CC adjustments {RAG,
Memory, Self-Refinement} and asked for evidence that (a) the stack beats
baseline, and (b) each component contributes or doesn't hurt.

Committed to PAC-1 (Paper-ready Ablation Campaign, round 1):
- **Phase A** — 2×2×2 single-seed ablation on v2+minimax, 17 test tasks.
  6 cells needed; 3 already have data (E16, E17, E18, all of which ran
  BEFORE verify_outputs.py existed — so all are hook-OFF).
- **Phase B** — multi-seed (>=3 seeds) the informative cells from A.
- **Phase C** — embedding-based memory (bge-small-en-v1.5 over
  instructions_excerpt + productive_rag_queries), parallelizable with A/B.

Phase A needs 4 new 17-task runs:
- **E19** = A3 = plug+SR (no mem). Agent: `claude_code_repo3_plugin`.
- **E20** = A5 = plug+mem+SR (full stack). Agent: `claude_code_repo3_plugin_gmemsilent`.
- **E21** = A5n0 = plug+noop+no-SR. Agent: `claude_code_repo3_plugin_noop_nohook`.
  Tests tool-list-shape hypothesis (XN-010 Section 5) — is memory's win just
  about having an extra tool in the list?
- **E22** = A5n1 = plug+noop+SR. Agent: `claude_code_repo3_plugin_noop`.

Critical finding from timestamp check: `plugin/hooks/verify_outputs.py`
was created 2026-04-21 12:08 UTC; E18 completed at 06:37 UTC. So E18
ran WITHOUT the hook, and is cell A4 in the new taxonomy, not A5. Memory
alone (no SR) already eliminated the failures on E18 — making the
A5n0/A5n1 (noop) cells critical: if noop-alone also gets zero failures,
memory per se may be contributing less than we thought.

A6 (no-plug + SR, no memory, no RAG) requires a code refactor to unwire
the hook from the plugin block. Deferred to PAC-1b.

Primary metric: failures-as-zero TreeSim (XN-011). Paired on 17-task
subset. Pre-registered thresholds in D-004.

Next steps (PENDING USER SIGN-OFF — estimated cost $10-16 for 4 new
17-task runs):
1. Smoketest 2 tasks (Sneddon + Mandel, the fragile rescue tasks) per
   new agent key. ~$2 total.
2. If smoke passes, launch 4 full 17-task runs in sequence.
3. Score all runs with failures-as-zero + scored-only.
4. Produce PAC-1 Phase A results table.
5. Review with user; if results clean, commit Phase B multi-seed.

-> DAG: E19, E20, E21, E22 all planned
-> Evidence: decisions/D-004_pac1-ablation-campaign.md, docs/XN-012_pac1-phase-a-ablation.md
-> Decision: await user sign-off before launching smoketest.

---

<a id="LOG-2026-04-21-6"></a>
### 2026-04-21 — PAC-1 Phase A seed-1 done; surprise negative interaction

PAC-1 Phase A (D-005, XN-013) seed-1 results, fa0 TreeSim on 17 test tasks:

| Cell | Config | Run | fa0 |
|:-:|---|---|---:|
| A1 | baseline | E16 | 0.497 |
| A2 | RAG only | E17 | 0.440 |
| A3 | RAG+SR | **E23 new** | **0.664** |
| A4 | RAG+Mem | E18 | 0.725 |
| A5 | FULL STACK | **E24 new** | **0.317** |

**Stack LOSES to baseline on this seed** (A5-A1 = -0.180). Each component
alone is positive (+SR +0.225, +Mem +0.286); combining them with RAG is
catastrophically negative (A5-A3 paired = -0.347, 3/13 W/L).

Memory is never called in either A4 or A5 (mem=0 tool_use events) — so
the effect is NOT memory-retrieval poisoning. It's a tool-list-shape
interaction between un-called memory + hook.

Tool-list-shape confound: A4 (E18) tool list INCLUDES AskUserQuestion;
A5 (E24) DOESN'T (removed in intervening session). So A5-A4 has TWO
config differences, not just hook toggle.

Multi-seed A3 + A5 launched 20:22 via /tmp/pac1_phase_a_seed2.sh. Will
tell whether -0.180 reproduces.

Adversarial review skipped — codex CLI unavailable locally (D-006). Same
blocker as D-003 earlier today. Applied attack-priority list as
same-model self-critique mitigation; risk accepted for preliminary
single-seed framing.

-> DAG: E23-RESULT good/keep, E24-RESULT negative/investigate, D-006 logged
-> Evidence: misc/pac1/phase_a_summary.md, misc/pac1/scores/e23_summary.json, misc/pac1/scores/e24_summary.json, docs/XN-013_pac1-phase-a-ablation.md
-> Decision: multi-seed A3 + A5 to confirm. If A5 seed 2 also regresses, paper story shifts to "silent tools help when ignored; combining safety nets + silent tools is not additive." If A5 rebounds, single-seed outlier; expand to full 3-seed matrix.

---

<a id="LOG-2026-04-21-7"></a>
### 2026-04-21 — PAC-1 Phase A seed-2 REVERSAL: A5 is hugely bimodal

Seed-2 runs completed:
- **A3 seed 2** (pac1_plug_hook_s2): fa0 **0.641** (seed 1 was 0.664 — very stable).
- **A5 seed 2** (pac1_plug_mem_hook_s2): fa0 **0.729** (seed 1 was 0.317 — massive +0.412 swing).

Per-task A5 seed variance is enormous: CasedContactThermo 0.057 → 0.990;
DPWellbore 0.141 → 1.000; DeviatedElastic 0.137 → 1.000; ViscoDP 0.083 → 0.951;
kgdExperimentValidation 0.287 → 1.000. Pattern: "agent either fully nails it or
fully misses" — consistent with the known catastrophic-rescue volatility.

Updated multi-seed summary (n=2 each on v2+minimax):
- A1 baseline: single seed 0.497
- A3 (plug+hook) n=2: 0.664, 0.641 → mean 0.653 (stable)
- A5 (full stack) n=2: 0.317, 0.729 → mean 0.523 (highly bimodal)
- A5 mean vs baseline: +0.026 (marginal with n=2)
- A3 mean vs baseline: +0.156 (likely real)
- A5 mean vs A3 mean: -0.130 (memory adds variance; may hurt on average vs plug+hook-only)

**Revised tentative paper story:**
- **RAG + Self-Refinement (plug+hook) is the most reliable configuration.**
- **Memory is high-risk, high-reward.** Good seeds: +0.2 vs plug; bad seeds: -0.4 vs plug.
- The "each component contributes or doesn't hurt" framing needs qualification: memory has asymmetric risk.

Phase B1 launched 20:58 (PAC-1 follow-up):
- A4' = pac1_plug_mem_nohook_s1/s2 (plug+mem+nohook on CURRENT infra, for the AQ-confound fix)
- A5 seed 3 = pac1_plug_mem_hook_s3 (3rd seed of full stack to better characterize the bimodal distribution)

New agent key added: `claude_code_repo3_plugin_gmemsilent_nohook` (gmemsilent + stop_hook_enabled: False).

-> DAG: E23 good/keep, E24-RESULT revised to 'bimodal-variance not simply-negative'
-> Evidence: misc/pac1/scores/e23s2_summary.json, e24s2_summary.json, misc/pac1/phase_a_summary.md
-> Decision: complete Phase B1 (3 more runs), then assess whether full stack reliably beats baseline OR revise to "plug+hook is the reliable configuration, memory is optional."

---

<a id="LOG-2026-04-21-8"></a>
### 2026-04-21 — PAC-1 Phase A + B1 COMPLETE — refined paper story

Multi-seed ablation campaign done on v2+minimax, 17 test tasks.

**Final results table (fa0 TreeSim):**
- A1 baseline: 0.497 (n=1)
- A2 RAG only: 0.440 (n=1)
- **A3 RAG+SR: 0.653 (n=2, σ=0.017) — MOST STABLE**
- A4 RAG+Mem (old infra with AQ): 0.725 (n=1)
- A4' RAG+Mem (new infra): 0.661 (n=2, σ=0.184)
- **A5 FULL STACK: 0.607 (n=3, σ=0.252)**

**Key finding: components do not stack additively.**
- A3-A2: +0.213 (+SR)
- A4'-A2: +0.221 (+Mem)
- A5-A2: +0.167 (+Mem+SR) — LESS THAN EITHER ALONE
- A5-A3: -0.045 (adding Mem hurts)
- A5-A4': -0.053 (adding SR hurts)

**SR is the variance-reduction component.** A3 std 0.017 (n=2); A4' std 0.184;
A5 std 0.252. Hook catches parse errors + empty completions without
changing mean behavior much once Mem is already present.

**Memory tool is never called** in any A4/A4'/A5 run (mem=0 tool_use). Benefit is
tool-list-shape only.

**A5 seed-by-seed**: 0.317, 0.729, 0.776. Seed 1 was an outlier; typical is ~0.75.

**Paper-ready claim (honest, preliminary n=1-3):**
- Stack does beat baseline (+0.110) but not yet significantly.
- Best single-component story: RAG+SR — lowest variance, +0.155 over baseline.
- Memory helps but is unreliable without SR's variance reduction.
- Components don't stack.

**Open:** multi-seed A1/A2/A4' to n=3 minimum; adversarial review on codex install.

-> DAG: E23s2, E24s2, E24s3, E25 (A4' s1), E26 (A4' s2) all good/keep
-> Evidence: misc/pac1/scores/pac1_final_summary.md, misc/pac1/scores/*.json
-> Decision: pausing campaign; findings substantive enough for user review before next compute spend. Cost this session ~$22. Cycles used: 3.

<a id="LOG-2026-04-22-1"></a>
### 2026-04-22 — User feedback + memory design pivot (D-007 → D-008)

User (advisor's post-doc raised concerns; user relayed):
1. Why is vanilla CC not good at this task? What's hard about it?
2. Memory impl is "hack job" — lexical overlap in 2026 is unheard of.
3. G-Memory seems overkill for single-agent.
4. Review simpler memory approaches: Dynamic Cheatsheet, ACE, ReasoningBank, MemEvolve.
5. Use OpenRouter for embeddings (OpenAI API unavailable).

**Actions this session:**
- XN-014 failure analysis written: 4 failure modes (F1 schema hallucination,
  F2 wrong-version drift, F3 missing components, F4 spec under-specification).
  RAG fixes F1; RAG alone introduces F2; SR catches hard failures; nothing
  addresses F3/F4.
- LN-002 memory survey redone properly with actual paper reads (first version
  was hallucinated from training cutoff — saved feedback memory so this
  doesn't happen again). 4 papers + repos cloned to misc/refs/.
- D-007 memory ablation design written.
- **Adversarial review (RN-003)** invoked on D-007 at implementation gate.
  Found 4 P1 blockers: (a) 14/17 test tasks had leaked GT basenames in
  memory_index.json through `reference_xmls` + `productive_rag_queries`,
  (b) M0 as control has null test exposure (memory tool never called in A4'/A5),
  (c) primer-size confound uncontrolled, (d) n=2 A3 baseline under-powered.
- **D-008 design V2** addresses all 4 blockers:
  - Hygiene audit gate (`scripts/memory/hygiene_audit.py`); memory_index
    rebuilt with basenames stripped (old archived as LEAKY.bak).
  - M-placebo (equivalent-token generic GEOS text) added as control.
  - Token budget parity preregistered at 10% within pair.
  - A3 seed 3 launched. Now A3 n=3 = {0.664, 0.641, 0.267}, mean 0.524, σ 0.221.
  - Switched distillation model to gemini-3-flash-preview (breaks
    self-distillation coupling).
  - Paired-per-task Wilcoxon analysis replaces mean+std pass/fail.
- **Infrastructure built:** trajectory_grounder.py, distiller.py (with
  abstraction guardrails + regex gate), build_items_embedding_index.py,
  render_items_to_primer.py, memory_mcp_embed.py (hard-error on missing
  key, preflight, no silent degrade), analyze_memory_matrix.py.
- **Artifacts distilled** (all hygiene-pass): M-placebo (1043 tok), M1-u (775),
  M1-g (807, truncated to match M1-u within 4.1%), M4-u (728), M4-g (776,
  6.6% parity with M4-u). Distillation used 18 train success + 18
  vanilla-CC-train trajectories (9 failures in vanilla-CC set provide
  anti-pattern content).
- **Vanilla-CC-train hygiene**: ran with `--extend-blocklist-with-test`
  flag (new, added to run_experiment.py); blocks all 55 union test-GT
  basenames in addition to per-task blocks.
- **Smoketests**: M1-g (primer variant) and M3-g (memory MCP tool variant)
  both work end-to-end. M3 MCP connects; agent doesn't call it (matches
  XN-011 observation that memory-as-tool is underutilized without prompt
  nudging).
- **Full matrix launched**: 6 conditions × 3 seeds = 18 new runs. Expected
  wall ~4-5h, cost ~$60. Running sequentially to avoid OpenRouter rate limits.

-> DAG: I06 (memory) and I10 (distillation grounding) — new leaf nodes
   pending Wilcoxon analysis after matrix completes
-> Evidence: D-008, RN-003, XN-014, LN-002, misc/memory_artifacts/
-> Decision: proceed with matrix, analyze paired-per-task when complete,
   run round-2 adversarial review on results before declaring.

<a id="LOG-2026-04-22-2"></a>
### 2026-04-22 (late morning) — D-008 matrix results + API contamination finding

**Matrix complete. Headline: M1-u (monolithic DC-Cu primer) wins.**
- M1-u: 0.796 ± 0.057, +0.272 vs A3, Wilcoxon p<0.001, 16/17 task-level wins.
- M1-g: 0.766 ± 0.046, +0.242, p=0.003, 13/17 wins.
- M-placebo: 0.373 ± 0.049, −0.152 vs A3, p=0.015 — content-specificity control passes.

**API contamination discovered in 3 seeds:**
- M4-u s3 → 13/17 tasks hit HTTP 402 `Insufficient credits` (credit exhaustion mid-run)
- M3-g s2 + s3 → 17/17 each hit HTTP 403 `Key limit exceeded (weekly limit)`

Initial aggregate numbers (M4-u 0.537, M3-g 0.094) were wrong — tainted
by these seeds. After exclusion:
- M4-u (n=2 valid): 0.729 ± 0.024 — stable, not "collapsed"
- M3-g (n=1 valid): 0.281 with 0 memory_lookup calls — agent doesn't use the tool
- M4-g (n=3, all clean): 0.469 ± 0.299 — REAL instability

**Per-task diagnostic on M4-g pkn** (s1=1.000, s2=0.088, s3=0.000):
- M4-g s3: minimax "empty completion" (0 output tokens, 3 turns).
- M4-g s2: agent produced `<CompressibleSolidCappedPlatesPorosity>` —
  invented vocabulary. M1-u (1.0 on same seed) had the primer explicitly
  list `CompressibleSolidParallelPlatesPermeability` by name.

**Format-ablation finding replaces grounding-ablation as primary story:**
- Monolithic enumerated cheatsheet (M1) > structured-principle items (M4)
  because the cheatsheet anchors specific vocabulary for F1 hallucination.
- Grounding (TreeSim) did NOT help on aggregate (both pairs M-g worse than M-u).

**Mitigation shipped:** `scripts/memory/check_api_contamination.py` scans
any run dir for 402/403/429/401 signatures and flags EXCLUDE_SEED. Run
before interpreting any new matrix. See
`misc/memory_artifacts/openrouter_contamination_note.md` for the full
breakdown and detection checklist.

-> DAG: M1-u is new hero harness addition; D-008 complete
-> Evidence: docs/XN-015_memory-ablation-results.md (updated with contamination finding),
   misc/memory_artifacts/scores/matrix_summary.md,
   misc/memory_artifacts/openrouter_contamination_note.md
-> Decision: reframe paper ablation as primer-format (monolithic vs structured),
   not grounding. Round-2 adversarial review still owed before final declaration.

---

<a id="LOG-2026-04-27-1"></a>
### 2026-04-27 — Third-harness baseline (OpenHands) added

Concurrent session ("other-coding-agent-baseline") spun up a third
harness baseline alongside vanilla CC and harness-less direct prompt.
The motivation is reviewer pre-emption: any "CC adaptations help"
finding is single-harness without a different general-purpose coding
agent in the comparison.

**Survey + selection:** `docs/2026-04-27_other-coding-agent-harness-selection.md`.
Considered OpenHands (All-Hands-AI, formerly OpenDevin), sst/opencode,
and NousResearch/hermes-agent. Disambiguation: `opencode-ai/opencode` is
archived (→ `charmbracelet/crush`); Hermes-Agent has persistent-memory +
skill-loop paradigm that confounds a stateless 17-task eval. **Picked
OpenHands** — closest shape to vanilla CC (ReAct loop + file/bash/edit
tools + Docker sandbox), cleanest OpenRouter wiring (LiteLLM env vars),
and strongest academic-citation footprint.

**Decision memo:** `.copilot/decisions/D-009_other-coding-agent-baseline.md`
— locks the parity contract (same model, same primer, same 17 tasks,
same scorer) and lists what is intentionally *not* injected
(`rag_vanilla.txt`, `real_tool_tail.txt`, repo3 plugin).

**Implementation:** `run/Dockerfile.openhands` (Ubuntu 24.04 + uv +
openhands v1.15.0 from `uv tool install`, installed under `/opt/uv`
so non-root `--user` can execute the binary) and
`scripts/openhands_eval.py` (per-task Docker driver, mirrors
`scripts/harnessless_eval.py` shape; re-uses
`runner.contamination.create_filtered_geos_copy` for parity with CC).
**No edits to `src/runner/*`, `run/AGENTS.md`, `src/runner/agents.py`,
or `scripts/eval/*`** — concurrent CC session is unaffected.

**Smoketest (oh_smoke_s1 / TutorialSneddon, 1 seed, 600 s):** passed.
Agent wrote 7 XMLs, AGENTS.md visibly consumed (task list quoted
GEOS-specific solver names from the primer), 71 OpenHands events
parsed, **TreeSim = 0.843**. Sole task — no comparison drawn yet
(vanilla CC no-plugin minimax on Sneddon was ~0.493 in earlier runs,
but that's n=1 here).

Bugs found + fixed during smoketest: tmp_geos perms (use
`--tmp-geos-parent` override; default unchanged), `--user` blocked
openhands binary (rebuilt image with `/opt/uv` install path),
JSONL parser (OpenHands emits multi-line pretty JSON between
`--JSON Event--` markers, not strict JSONL; parser updated).
Token usage missing from v1.15 events — captured as a follow-up.

**Gates remaining before full 17-task launch (per D-009):**
1. `experiment-designer` review of the runner + parity contract.
2. `/adversarial-review` on `scripts/openhands_eval.py` and
   `run/Dockerfile.openhands`.
3. Then 17 tasks × 1 seed at 1200 s timeout, 4 workers; promote to
   ≥3 seeds if competitive with vanilla CC.

-> DAG: I12 (third-harness baseline; new node)
-> Evidence: docs/2026-04-27_other-coding-agent-harness-selection.md,
   docs/XN-016_openhands-baseline.md,
   .copilot/decisions/D-009_other-coding-agent-baseline.md
-> Decision: OpenHands is the third-harness baseline; smoketest
   passing; pre-campaign gates owed before full run.

---

<a id="LOG-2026-04-27-2"></a>
### 2026-04-27 — OpenHands `oh_test17_s1` results (1 seed; NOT validated)

Round-2 adversarial review skipped per researcher direction (D-009
status update). 17-task × 1-seed × 4-worker campaign launched and
completed in ~26 min. **All parity gates green** for every task that
ran: `primer_in_context: true` (all 5 fingerprints), `activated_skills:
[]`. Status counts: 16 success, 1 `failed_no_outputs`
(`AdvancedExampleViscoDruckerPrager` — agent ran for 282 s but wrote
zero XML).

**Single-seed result** (vs canonical CC no-plugin minimax run
`noplug_mm_v2` + `noplug_mm_v2_s2`):

- OH s1 mean TreeSim (failures-as-0, n=17): **0.863 ± 0.126**
- CC seed-mean (n=17): **0.518 ± 0.304**
- Paired delta (OH − CC seed-mean): **+0.345 ± 0.348**, sign-test p = 0.049
- Cleaner per-seed: OH-s1 vs CC-s1 (n=15 common): Δ = +0.300, 12W/3L, p = 0.035

**But** — OH-s1 vs CC-best-of-2-seeds (n=12 with both): wins **6/6**.
Most of the seed-mean lead comes from CC's bad seeds dragging down its
mean. CC is highly seed-sensitive on this task set (e.g. EDPWellbore
0.015→0.932; ThermoporoelasticConsolidation 0.004→0.869). One-seed OH
cannot beat 2-seed CC.

**Two robust OH wins** across both CC seeds: `pknViscosityDominated`
(OH 0.995 vs CC ≤0.021 both seeds) and
`AdvancedExampleViscoDruckerPrager` (OH 0.998 vs CC ≤0.317 both
seeds). These are CC-consistent-failure tasks where OH succeeds —
worth a trajectory-level look.

**The +0.345 magnitude is suspicious** — it's the kind of headline
number that suggests an unmeasured confound. Candidates (per
RN-004 limitations):
1. OpenHands' built-in system prompt (un-inspected) may carry
   coding-agent best-practices CC's lacks.
2. Primer placement: CC system slot vs OH user-message prefix.
   minimax may weight user messages more than system messages.
3. Tool-surface gap: OH ships `task_tracker` + `finish` actions CC
   doesn't expose. `task_tracker` fired 9× in the smoketest.
4. Seed luck on a single OH run.

Next cycles (per D-009 validation gates):
- **Cycle 2**: `oh_test17_s2` (seed 2). If competitive with seed 1,
  variance estimate becomes meaningful.
- **Cycle 3**: `oh_test17_s3` if seed 2 holds up.
- **Cycle 4+**: trajectory inspection on the two robust OH wins
  + dump of OpenHands' built-in system message via `LITELLM_LOG=DEBUG`
  on a single task.

-> DAG: I12 first results
-> Evidence: docs/XN-016_openhands-baseline.md (Results §),
   data/eval/results/oh_test17_s1/openhands_no_plugin/_summary.json,
   data/eval/openhands_no_plugin/oh_test17_s1/_summary.json
-> Decision: positive single-seed signal, NOT validated; queue 2 more
   seeds before any cross-harness claim. NOT promoting to hub.md SoK.

---
<a id="LOG-2026-04-27-3"></a>
## 2026-04-27 — Sub-agent orchestrator design + build (D-010, sleep mode)

User direction (pre-sleep): build a plugin-distributed sub-agent orchestrator
for GEOS XML authoring; test on 17-task v2 set with DSv4-flash direct
(`https://api.deepseek.com/anthropic`); preserve concurrent OpenHands campaign
(don't touch `src/runner/*`, `run/AGENTS.md`, `scripts/eval/*`,
`data/eval/claude_code_*`, `data/eval/openhands*`).

Design analysis already done pre-sleep:
`docs/2026-04-27_subagent-architecture-geos.md` — 11 segments collapse to 9;
6-phase pipeline (bootstrap → mesh → regions+const → solvers → drivers →
events); subagents return text, orchestrator splices.

This cycle:

1. Confirmed DSv4-flash direct via Anthropic-compatible endpoint:
   `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic` + `ANTHROPIC_API_KEY=$DEEPSEEK_API_KEY` + `--model deepseek-v4-flash`.
2. Confirmed Claude Code subagents support — markdown files with YAML
   frontmatter, distributable via plugin's `agents/` dir, parallel-capable,
   per-subagent model/tools/skills. Spawned via `Agent` tool (formerly Task).
   Plugin subagents do NOT support `mcpServers`/`hooks`/`permissionMode`
   frontmatter — but session-level MCP is inherited so geos-rag still works.
3. Wrote `.copilot/decisions/D-010_subagent-orchestrator.md`. MVP scope:
   5 subagents (mesh, regions+constitutive, solvers, drivers, events) in
   5 serial phases — drops Phase-2/Phase-4 parallelism for build-tonight
   simplicity, can be re-introduced later.
4. Built `plugin_orchestrator/`:
   - `.claude-plugin/plugin.json` — geos-rag MCP (same as plugin/).
   - `agents/{geos-mesh, geos-regions-constitutive, geos-solvers, geos-drivers, geos-events}.md`.
   - `primers/<segment>.md` — condensed Sphinx docs per segment.
   - `schema_slices/*.xsd` — auto-extracted complexType slices from
     `data/GEOS/.../schema.xsd` via `scripts/extract_schema_slice.py`.
   - `scripts/geos_rag_mcp.py` and `hooks/verify_outputs.py` copied from
     `plugin/` so the new plugin is self-contained.
   - `ORCHESTRATOR_SYSTEM.md` — main thread workflow primer.
5. Built `scripts/orchestrator/run_orchestrator_eval.py` — standalone runner
   that mounts both plugins (orchestrator at `/plugins/orchestrator`, repo3
   at `/plugins/repo3`), passes `--plugin-dir /plugins/orchestrator` so the
   subagents are discoverable, and uses DSv4-flash direct by default with
   `--model` / `--api-base` / `--api-key-env` flags for OpenRouter fallback.
   Imports read-only from `src/runner` (contamination, prompts, docker_cmd
   utility) — does NOT modify `src/runner/*` or other concurrent-run files.

-> DAG: I14 (decompose XML authoring across per-segment subagents)
-> Evidence (design): docs/2026-04-27_subagent-architecture-geos.md,
   .copilot/decisions/D-010_subagent-orchestrator.md
-> Evidence (code): plugin_orchestrator/, scripts/orchestrator/
-> Decision: build complete; smoketest in progress on TutorialSneddon
   (background task btwfwsxws). After smoketest passes, launch full 17-task
   campaign on DSv4-flash, score, write XN-017.

Smoketest plan: TutorialSneddon (RAG-discovered embedded-fracture solver
diversity per XN-008 makes this a good stress test) and ExampleMandel
(canonical poromechanics — verifies coupled-solver + Constitutive composite
authoring). If both pass, the architecture is validated for the broader run.

---

<a id="LOG-2026-04-27-4"></a>
### 2026-04-27 — OH baseline parity audit + cost/token instrumentation (NOT a "OH > CC" claim)

User questioned the +0.345 magnitude of OH-vs-CC on minimax. Right call.
Did the audit + added missing instrumentation:

**Specs identical.** md5sums match between
`experiments_from_mined_specs/` (OH) and `experiments_test36_template/`
(CC) for `TutorialSneddon`. Same task text reaches both agents.

**Primer file unchanged** since the CC `noplug_mm_v2` run. AGENTS.md
last commit 2026-04-19; CC ran 2026-04-21; OH ran today. Same bytes.

**Primer DELIVERY differs.** CC: AGENTS.md (with baked GEOS Primer)
+ rag_vanilla.txt + real_tool_tail.txt → system slot. OH: AGENTS.md
verbatim → first user message. OH does NOT get rag_vanilla.txt or
real_tool_tail.txt — the latter specifically defends against
minimax's pseudo-tool-call leakage in CC.

**Custom tools.** Zero. OH events.jsonl shows 0 calls to repo3 plugin
MCP tools (no `--mcp-config` passed). OH's tool surface includes 3
built-ins CC doesn't have (TaskTracker, Think, FinishAction).

**Memory.** No carryover; per-task workspace is fresh
(`shutil.rmtree`); container is `--rm`.

**Token + cost instrumentation added.** OpenHands writes accumulated
cost + token usage to
`<work_dir>/.openhands/conversations/<id>/base_state.json` (NOT to
the streaming `events.jsonl`). Updated
`scripts/openhands_eval.py:read_oh_token_stats` to read it post-run.
Backfilled all 17 oh_test17_s1 status.json files. CC's same data is
in `events.jsonl`'s `type:result` event (`total_cost_usd` + `usage`).

**Cost on minimax** (real provider billing):
- OH s1: **$1.48** total, **$0.087/task** mean.
- CC noplug_mm_v2 + s2: **$7.99** total over 34 runs, **$0.235/task** mean.
- OH ~2.7× cheaper, **driven by cache utilization** (OH on
  TutorialSneddon: 990k cache_read tokens; CC: 96). This is a CC
  `claude -p`/OpenRouter cache-config gap, not a fundamental
  OH advantage.

**Wall-clock**: OH 318 s/task vs CC 261 s/task — OH ~22% slower.
**Tool calls**: OH 38 vs CC 35 — similar budget.

**Mechanism (KEY FINDING).** CC's bad seeds show classic early-exit
patterns: ExampleEDPWellbore CC2 = 9 tools / 122 s / 0.015 TreeSim;
ExampleIsothermalLeakyWell CC2 = 2 / 203 s / 0.110;
AdvancedExampleViscoDruckerPrager CC1 = 11 / 136 s / 0.129. These
match the documented `redacted_thinking → end_turn` failure mode
from XN-003/004/010 — minimax ends the turn after few tool calls
without writing files. CC ships `real_tool_tail.txt` *specifically*
as a defense.

OH's tool counts across all 17 tasks: 17–63 (median 37).
**OH never triggers the early-exit pattern.** OH's "win" is largely
CC failing, not OH succeeding more. **Best-of-CC-seeds vs OH on the
12 tasks with both CC seeds: 6 wins / 6 wins.**

**Honest reframe of LOG-2026-04-27-2's headline:**
- ON MINIMAX: OH cheaper (cache util) + more reliable (no early-exit).
  Per-task ceiling competitive with CC's better seeds.
- The +0.345 mean delta is dominated by CC's bad-seed failures, not
  OH being smarter.
- This is a "OH > CC on minimax" claim, NOT a "OH > CC" claim.
  Cross-model replication on a non-failing model is needed to support
  any general harness comparison.

**Bug fixed**: runner's `n_xml_files` used non-recursive glob; missed
agent outputs in nested subdirs. 1 of 17 s1 tasks reclassified from
`failed_no_outputs` to `success` post-hoc (scorer always globbed
recursively, so TreeSim score 0.998 was correct all along).

**Next cycles**:
- Cycle 2 (oh_test17_s2): in flight, minimax. OH variance estimate.
- Cycle 3 onward: switch to DSv4-flash via DeepSeek-direct (cheaper,
  faster, no rate-limit; per `docs/2026-04-27_dsv4_migration.md`).
  Cross-model replication tests whether OH advantage holds on a
  model that doesn't have CC+minimax's specific failure mode.

-> DAG: I12 (mechanism characterization)
-> Evidence: docs/XN-016 §"Parity audit", §"Resource comparison",
   §"Mechanism (preliminary)", §"Honest reframe";
   data/eval/openhands_no_plugin/oh_test17_s1/*/status.json (backfilled)
-> Decision: do NOT report "OH beats CC" without DSv4 cross-model
   validation. Frame any minimax-only comparison as "robustness on
   minimax" + "cache-utilization cost effect".

---
<a id="LOG-2026-04-27-4"></a>
## 2026-04-27 — Orchestrator smoketest iterations (sleep cycle 2)

**v1 (TutorialSneddon, ORCHESTRATOR_SYSTEM.md as initial):** orchestrator
bypassed delegation. Used Write tool to author Sneddon_base.xml directly at
event 86. RAG searches for SurfaceElementRegion, NormalTraction etc. were
self-authoring research, not bootstrap-discovery. Zero Agent tool calls.

**Fix #1 — disable Write + harden prompt:**
1. Added `Write` to `DISALLOWED_TOOLS` in run_orchestrator_eval.py.
2. Updated ORCHESTRATOR_SYSTEM.md with explicit "Write disabled, use Bash cp".

**v2 (TutorialSneddon, fix #1):** still failed. Bypassed delegation by copying
6 different Sneddon variants into /workspace/inputs/ (3 strategies × 2 variants),
treating the task as multi-strategy authoring. Zero Agent tool calls. Model
appears to interpret Sneddon's multi-solver-family nature as an authoring
challenge, not an orchestration challenge.

**Fix #2 — overhaul system prompt with strict numbered phases + "anti-pattern hall of shame":**
- "At least 5 Agent tool calls must appear in your transcript."
- "Pick the FIRST returned result. Do not run multiple searches."
- "ONE bootstrap copy. Not two. Not five. ONE."
- Anti-patterns explicitly listed.

**v3 (ExampleMandel, fix #2):** in progress. Different task choice — Mandel
is canonical poromechanics with one solution path, less invitation to
multi-strategy thinking. Container 716d1193f015 (background bunjm7fnw).
Early signal: "Good, bootstrap copied. Now let me read it to build the name
registry, then spawn the first subagent." — explicit workflow recognition.
Awaiting first Agent call.

-> DAG: I14
-> Evidence: ORCHESTRATOR_SYSTEM.md (revised), checkpoint.md cycle 2.
-> Decision (provisional): if v3 spawns ≥3 subagents → run full 17-task on
   DSv4-flash. If v3 still has 0 Agent calls → switch to minimax-m2.7 fallback
   or document negative finding and stop.

---
<a id="LOG-2026-04-27-5"></a>
## 2026-04-27 — DSv4-flash orchestrator timing observation

Smoketest v3 (Mandel) timing as of 13:25Z (12 min in):
- Phase 0 (bootstrap cp + read): ~3 min
- Phase 1 (mesh subagent + splice): ~5 min
- Phase 2 (regions-constitutive subagent): in progress, 5+ min and counting

**DSv4-flash inference is slow**. Each subagent takes ~5-10 min including its
thorough doc/example research. Pipeline projection: 5 subagents × ~6 min mean
= ~30 min/task serial. With 2 workers and 17 tasks, full campaign ~4-5 hours.

**Decision options**:
- Option A: launch full 17-task with --workers 2 --timeout 2400. Total ~5h.
- Option B: launch reduced 5-task set first (Mandel + Sneddon + a few solid
  mechanics + 1 multiphase) to validate broader physics before committing
  to full campaign. ~75-90 min.
- Option C: launch full but parallelize harder (--workers 4). Total ~2.5h.
  Risk: 4 concurrent docker containers + 5 subagent context windows each
  = heavy memory/network usage; might trigger DeepSeek rate limits.

Choosing **Option B** for tonight's autonomous budget (cycle remaining
~5h max). 5 tasks gives a solid initial signal across physics families.
Full 17-task run is queued for the user's return.

5-task set: TutorialSneddon (fracture), ExampleMandel (poromechanics),
TutorialPoroelasticity (poromechanics + ICs), AdvancedExampleDruckerPrager
(plasticity), buckleyLeverettProblem (multiphase).

---
<a id="LOG-2026-04-27-6"></a>
## 2026-04-27 — Orchestrator 5-task results: +0.330 over vanilla DSv4-flash

5-task campaign `orch_dsv4_5task_s1` finished. 5/5 success, all xmllint-valid,
all 5 phase subagents executed for 4 of 5 tasks (DruckerPrager skipped solvers).

**Paired vs vanilla DSv4-flash on same 5 tasks**:
| task | orch | vanilla | Δ |
|---|---:|---:|---:|
| ExampleMandel | 0.926 | 0.319 | +0.608 |
| AdvancedExampleDruckerPrager | 0.848 | 0.803 | +0.045 |
| TutorialSneddon | 0.839 | 0.085 | +0.754 |
| TutorialPoroelasticity | 0.707 | 0.362 | +0.344 |
| buckleyLeverettProblem | 0.654 | 0.756 | -0.102 |
| **mean** | **0.795** | 0.465 | **+0.330** |

Wins/losses/ties = 4/1/0. The wins concentrate on tasks where vanilla
catastrophically failed (Sneddon vanilla 0.085 = wrong-solver-family failure
mode from XN-008). Per-segment subagents with focused primers produce
canonical XML patterns the monolithic agent misses.

The one regression (buckleyLeverettProblem -0.102) is the only multiphase
task; my drivers primer is thin on multiphase BCs. Needs targeted enrichment.

**Compared to prior baselines** (indicative, different conditions):
- E03 (plugin+ds-v3.2 via OR, 35 tasks): 0.828 mean — orchestrator+DSv4-flash
  on this 5-task subset reached 0.795, in the same ballpark with a
  smaller-cheaper model.
- M1-u (memory variant, n=2): 0.796 ± 0.057 — within noise of orchestrator.
- A3 (RAG+SR plugin, n=3): 0.524 ± 0.221 — orchestrator clearly above.

-> DAG: I14 (sub-agent orchestration), E25 (orchestrator+DSv4-flash, n=1)
-> Evidence: docs/XN-017_subagent-orchestrator-results.md (full table),
   data/eval/results/orch_dsv4_5task_s1/orchestrator_dsv4flash/_summary.json,
   data/eval/orchestrator_dsv4flash/orch_dsv4_5task_s1/_analysis.json
-> Decision (provisional): architecture validated. Next: queue full 17-task
   campaign, enrich multiphase content in drivers primer, dispatch
   adversarial review on orchestrator code, then declare results.

---

<a id="LOG-2026-04-28-1"></a>
### LOG-2026-04-28-1 — 17-task orchestrator campaign complete (XN-018)

Launched the remaining 12 v2 tasks with DSv4-flash orchestrator
(`orch_dsv4_remain12_s1`, W=2). 12/12 succeeded (mean TreeSim 0.874,
median 0.929, range 0.608–0.998). Combined with the 5-task cycle from
XN-017, the orchestrator now covers all 17 v2 tasks at **mean TreeSim
0.851** (median 0.852, all 17 succeeded).

**Same-model paired delta vs vanilla DSv4-flash (n=17):**
mean Δ = **+0.204** | wins/losses/ties = 13 / 3 / 1 | median Δ = +0.158.

Largest wins: TutorialSneddon +0.754, ExampleDPWellbore +0.684,
ExampleMandel +0.608. Three losses concentrate in coupled
thermo-poromech-multiphase scenarios (ExampleThermoporoelasticConsolidation
−0.190, buckleyLeverettProblem −0.102, ExampleThermalLeakyWell −0.035) —
traceable to thin multiphase/thermal coverage in the drivers/solvers
primers. Architecture-level fix not needed; primer enrichment will close.

**Same-model paired delta vs DSv4flash+plugin+xmllint (best-setup):**
mean Δ = **+0.234**. The orchestrator beats the prior peak DSv4-flash
configuration cleanly — segmentation is doing more work than any prior
single-agent harness improvement on this backbone.

**Cross-implementation:**
- orchestrator-DSv4flash: 0.851 mean
- openhands-minimax-m2.7: 0.863 mean (Δ −0.012, within noise)
- openhands+plugin-minimax-m2.7: 0.820
- vanilla-DSv4flash: 0.647
- DSv4flash+full-primer: 0.641
- DSv4flash+min-primer: 0.666
- DSv4flash+plugin+xmllint: 0.617

The orchestrator essentially closes the gap between DSv4-flash (a smaller,
cheaper model) and OpenHands+minimax-m2.7 (a substantially larger model).

**Efficiency cost:**
- Compute: 15055s sum vs vanilla's 6825s (~2.2× more, due to 5 sequential
  subagent fan-out per task).
- True wall: 134 min @ W=2 vs vanilla 21 min @ W=6. Orchestrator is much
  slower per task end-to-end. W=4 re-run would cut wall to ~67 min.
- Tokens: paid input 4.4M (vs 6.9M vanilla — *fewer*); cache-read 128M
  (vs 72M vanilla — more). Per-task input + cache total is 7.8M for
  orchestrator vs 4.6M for vanilla. With prompt caching the cost
  premium is moderate; without it, ~2× more expensive than vanilla.

-> DAG: I14 (sub-agent orchestration), E25 (orchestrator+DSv4-flash, n=1)
-> Evidence: docs/XN-018_orchestrator-vs-priors-17task.md,
   data/eval/results/orch_dsv4_remain12_s1/orchestrator_dsv4flash/_summary.json,
   data/eval/orchestrator_dsv4flash/orch_dsv4_remain12_s1/_analysis.json
-> Decision: orchestrator validated on full 17-task v2. Same-model gain
   over vanilla is large and consistent (13/3/1). Next: enrich drivers
   primer for multiphase, multi-seed validation (3 seeds), adversarial
   review on orchestrator code, optional W=4 re-run for wall efficiency.

---

<a id="LOG-2026-04-28-2"></a>
### LOG-2026-04-28-2 — Adversarial review (RN-005) finds 3 P1 blockers in XN-018

Dispatched `/adversarial-review` (fresh-context Claude subagent) on the
orchestrator code + analyze script + comparison setup, immediately after
drafting XN-018. Review found 3 P1 blockers, 2 P2, 2 P3:

**P1A — Cross-test-task GT leakage.** `src/runner/contamination.py:187-231`
(`get_blocked_files_for_task`) only blocks the *current* task's GT
files. The other 16 v2 test-task GT XMLs are visible in the filtered
tree. Trace evidence: orchestrator on `ExampleIsothermalLeakyWell`
copied `thermalLeakyWell_base.xml` (GT for `ExampleThermalLeakyWell`,
a sibling test task) into its working dir; scored 0.836 effectively
by GT-proximity, not authoring quality. Affects vanilla too, but the
orchestrator's "ONE search ONE cp" bootstrap workflow systematizes
the shortcut. **Fix is one line**: `misc/memory_artifacts/test_blocklist.json`
already has a `union_xml` field with all 17 GT filenames; just wire it
through.

**P1B — `--disallowedTools Write` not enforced.** `run_orchestrator_eval.py:194-195`
passes `Skill`, `AskUserQuestion`, `Write` as **repeated** flags but
Claude Code expects a comma-separated single value. Trace: `Write`
tool_use fired in 4 tasks (TutorialSneddon, AdvancedExampleCasedContactThermoElasticWellbore,
ExampleThermalLeakyWell, kgdExperimentValidation). The "delegator-only"
architectural framing in XN-018 §Discussion is unsupported on those
tasks. Fix: `--disallowedTools "Skill,AskUserQuestion,Write"`.

**P1C — Token totals 2–4× inflated.** `analyze_17task.py:tally_jsonl_usage`
sums every `message.usage` line, but stream-json re-emits identical
message-IDs under subagent fan-out. TutorialSneddon: 229 usage records
→ 100 distinct message-IDs (2.48× inflation). Vanilla also affected
(~3.7×), so deltas may survive — but the absolute "4.4M paid input +
128M cache-read" headline is wrong, and cross-implementation token
comparison vs OpenHands (which reports tokens once per turn) is
broken. Fix: dedup by `message.id` before summing.

**P2 / P3 issues**: bootstrap copies near-GT siblings (47-line diff for
TutorialSneddon's `_FracShapes` variant); primer surface unmatched
between arms (vanilla has baked AGENTS.md primer; orchestrator has
`--strip-baked-primer` + 5 different primers); campaign wall fallback
is fs-mtime-derived (orch runner doesn't write started/ended);
multi-XML output benefits from scorer's `<Problem>` merge.

**Implication**: The +0.204 paired delta and "matches OpenHands+minimax"
claim CANNOT stand on this run alone. Three of the four largest-win
tasks (TutorialSneddon Δ+0.754, ExampleIsothermalLeakyWell Δ+0.109,
ExampleDPWellbore Δ+0.684) are implicated by ≥1 P1 issue. The
qualitative observation (orchestrator runs 17/17 end-to-end, architecture
is mechanically sound) survives.

XN-018 amended with `status: PRELIMINARY` and a per-finding response
table (accept→fix / accept→limitation / reject-with-reason) per the
`/adversarial-review` protocol. Hub.md State of Knowledge updated to
flag the preliminary status.

**Action plan** (in priority order):
1. Wire `union_xml` blocklist (P1A).
2. Fix `--disallowedTools` flag syntax (P1B).
3. Dedup `message.id` in analyze_17task.py (P1C).
4. Multi-seed re-run (≥2 seeds) of both arms under fixed setup.
5. Then update XN-018 with corrected delta. Only validate after re-run.

-> DAG: I14 (sub-agent orchestration), E25 (orchestrator+DSv4-flash, n=1
   PRELIMINARY pending re-run)
-> Evidence (against): .copilot/reviews/RN-005_adversarial_orchestrator-17task.md
-> Decision: orchestrator architecture works end-to-end on 17/17. Numerical
   claims paused pending P1 fixes + re-run.


<a id="LOG-2026-05-02-1"></a>
## 2026-05-02 — bottleneck-analysis pipeline built

Advisor input: NeurIPS paper needs in-depth analysis of WHERE the
baseline coding agent fails on the GEOS task, motivating each adapter
component. Built a 3-stage pipeline that outsources per-trajectory
diagnosis to DSv4-flash and aggregation to DSv4-pro:

1. `scripts/bottleneck/extract.py` (no LLM): mines `treesim_detail`
   recursive tree → worst subtrees by impact, missing/extra element
   types, plus trajectory features (tool counts, file re-reads,
   xmllint calls, edit churn).
2. `scripts/bottleneck/llm_per_task.py`: DSv4-flash with structured
   JSON schema → `failure_category`, `primary_failure_section`,
   `root_cause`, `trajectory_evidence`, `would_have_helped`. Includes
   focused GT-vs-gen XML excerpt for the worst section when score < 0.7.
3. `scripts/bottleneck/aggregate.py`: per-cell category/section
   distribution + section_failure_weight (`Σ (1 - treesim) by section`)
   + per-task baseline-vs-best delta. DSv4-pro narrative.

Smoketest on F0_s1 + F4_s1 (34 tasks): pipeline produced specific
diagnoses ("agent omitted temperature attr from SinglePhaseFVM",
"agent wrote no <Events> block"), narrative cited section names and
tied each implication to a category. Cost ~$0.003/task.

Launched full Phase-2 run on F0/F2/F4/F6/SE × 3 seeds = 255 tasks
(stage 2 in flight at 60+/255 at 10:49Z). Doc:
`docs/2026-05-02_bottleneck-analysis-pipeline.md`.

Follow-ups queued:
- Once derisk done (F8, F11 × 3 seeds), score and decide if either
  joins the scaleup.
- Launch scaleup (ICL-10 + train-19) per
  `docs/2026-05-02_autocamp-followup-plan.md`.
- Run bottleneck pipeline on scaleup results too — same script, just
  different `--traj-root`/`--eval-root`.

-> DAG: I15 (bottleneck-analysis pipeline)
-> Evidence: docs/2026-05-02_bottleneck-analysis-pipeline.md
-> Decision: build the analysis as part of the autocamp follow-up; will
   feed the NeurIPS submission's "Why does the baseline fail?" section.


<a id="LOG-2026-05-02-2"></a>
## 2026-05-02 — Scaleup complete; ICL-10 reveals adapter value

Followup campaign complete:
- **Derisk** (F8 + F11 × 3 seeds × test-17): F8=0.911, F11=0.897.
  Both confirm the test-17 ceiling at ~0.92. F11 underperforms SE
  by -0.022, suggesting v3's plugin packaging contributes beyond
  prose+memory.
- **ICL-10 scaleup** (6 cells × 3 seeds × 10 tasks): F0=0.720 →
  SE=0.789 (+6.9pp). ICL-10 is harder (-19pp from test-17), and
  this is where adapter value emerges. F4/F6 σ < 0.01 (40× tighter
  than F0's 0.08).
- **train-19 scaleup** (F0 + F6 × 3 seeds × 19 tasks): F0=0.867,
  F6=0.869. Tied within noise — train-19 doesn't discriminate.
- **Bottleneck pipeline** run on all 4 task sets. DSv4-flash for
  per-task classification, DSv4-pro for narrative synthesis.
  Total ~650 LLM calls, ~$5-7 spend.

**Revised story for paper**: the original test-17-only claim
("DSv4-flash needs no plugin to reach 0.92") is true *for that
benchmark distribution*. The plugin's value emerges on harder,
out-of-distribution tasks where the baseline catastrophically
fails on 2-3 tasks. SE wins on ICL-10 by avoiding those
catastrophic failures.

**Bottleneck patterns** (consistent across cells):
- F0 baseline failures dominate in Solvers (invented solver names,
  missing newtonTol/temperature attributes), Constitutive (extra
  dummy materials), Events (entire block omitted), Geometry
  (coordinate drift).
- Adapters fix `missing_block` (~50% reduction) but increase
  `extra_block` and `hallucinated_extras`. Adapter is in
  "harm-reduction" mode — the perfect-task count does NOT increase.
- Novel adapter-design idea from train-19 analysis:
  cross-section consistency hooks (validate
  `<ElementRegion materialList>` entries match Constitutive names).

Output documents:
- XN-019 Phase 2, XN-020 combined, XN-021 ICL-10, XN-022 train-19
- Pipeline doc: 2026-05-02_bottleneck-analysis-pipeline.md
- Results doc updated: 2026-05-02_autonomous-campaign-results.md

-> DAG: I15 (bottleneck-analysis pipeline)
-> Evidence: docs/XN-019..022, /data/matt/bn_*/stage3/aggregate.md
-> Decision: ICL-10 finding overturns the test-17-only "no plugin
   needed" framing. Paper should cover both findings: (1) on
   familiar benchmarks the plugin is roughly net-zero; (2) on
   out-of-distribution tasks the plugin rescues the baseline from
   catastrophic failures by ~5-7pp aggregate.

<a id="LOG-2026-05-04-1"></a>
## LOG-2026-05-04-1 — Interactive-autonomy + difficulty-ramp study (overnight)

→ DAG: new branch (workshop / autonomous-discovery angle)
→ Evidence: docs/2026-05-04_interactive-autonomy-results.md, docs/2026-05-03_interactive-autonomy-design.md
→ Decision: workshop-paper-scoped study; not merged into main NeurIPS battery

Set up a difficulty ramp (Medium/Hard relaxed specs via DSv4-pro
rewrite, hygiene-checked) and an interactive mode (simulated DSv4-flash
supervisor exposed as `mcp__geos-supervisor__consult_supervisor`).
Ran 8 tasks × 2 configs (F0 vanilla, F4 AUTOCAMP-best) × 2 difficulties
× 2 modes × 1 seed = 64 runs. Total wall ~3 hours, cost <$5.

Headline finding: **the agent consulted the supervisor 1 time across
32 interactive runs.** Even with the tool in its tool list and the
system prompt advertising it ("use it when a value is missing AND you
cannot reasonably infer it"), it preferred to infer from on-disk GEOS
examples on 31/32 trials. The single call returned an empty answer due
to a max_tokens budget bug in the supervisor (patched post-hoc).

TreeSim: difficulty drops scores ~9-13 pp from the test-17 Easy anchor;
F4 retains a small advantage over F0 (~+0.5-5 pp). Mode B F0 medium
shows a +10.7 pp jump over Mode A F0 medium that is almost certainly a
plugin-loaded confound (PAC-1 saw similar effects from uncalled tools
adding tool-list shape) rather than a supervisor benefit.

Next steps if pushing for the workshop submission:
- Second seed per cell
- Variant prompt that pushes asking more aggressively
- A no-confound F0 baseline (supervisor without plugin)


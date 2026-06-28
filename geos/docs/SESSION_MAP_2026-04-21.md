# Session Map — 2026-04-20 to 2026-04-21

*Comprehensive map of everything tried, found, and discovered since the copilot attached to repo3.*

## TL;DR — single-paragraph state

We have **18 experiments** (E01–E18) covering plugin/no-plugin × 6 memory variants × 2 models × 2 spec sets × 2 seeds. The project's headline finding — plugin beats vanilla CC by +0.178 TreeSim — was **confounded by a task-spec-version mismatch** (Brian's runs used `experiments_test36_template`/v2; mine used `experiments`/v1). When apples-to-apples on canonical v2 specs with minimax, **plugin beats no-plugin by +0.055 on matched seed, and plugin + G-memory-lite MCP tool beats plain plugin by +0.094** (E18 vs E17), memory also eliminates a failure mode the plain plugin hits on this model. We identified and characterized two distinct failure modes (timeout-after-exploration vs premature-end_turn-without-XML) and corrected several earlier mis-framings (the "redacted_thinking" blocks are actually just base64-encoded duplicates of the visible thinking — not hidden reasoning). Next priorities are multi-seed variance estimates, E11/E12 memory variants on v2, and generating hard-mode task specs.

---

## 1. Experiments catalog (E01–E18)

`test subset` = 17 test tasks from `misc/memory_split.json` (half of E03's 35 scored tasks, alternating-by-score split).

| # | Run name | Agent / condition | Model | Spec set | Tasks | Mean TreeSim (scored) | Scored/total | Decision | Key fact |
|---:|---|---|---|---|---:|---:|:---:|---|---|
| E01 | ablation_deepseek_v2 | no-plug, vanilla CC | deepseek-v3.2 | v1 | 36 full | 0.643 | 34/36 | keep | Earlier Matt baseline |
| E02 | repo3_eval_run2 | plug | minimax-m2.7 | **v2** | 36 full | 0.809 | 34/36 | keep | **Brian's run** (rescore 2026-04-21: +DeviatedPoroElastic 0.816) |
| E03 | repo3_eval_run4 | plug | deepseek-v3.2 | **v2** | 36 full | 0.809 | 36/36 | keep | **Brian's run — headline baseline** (rescore 2026-04-21: +SPE11b 0.130; mean 0.828→0.809) |
| E04 | mem_run1 | plug + long cheatsheet (sys-prompt) | deepseek-v3.2 | v1 | 17 test | 0.532 | 14/17 | discard | 3 failed_no_outputs; originally flagged "memory hurts" |
| E05 | memshort_run1 | plug + short cheatsheet (sys-prompt) | deepseek-v3.2 | v1 | 17 test | 0.548 | 15/17 | discard | Rescore 2026-04-21: +Sneddon 0.358; mean 0.561→0.548 |
| E06 | mm_noplug_run1 | no-plug | minimax-m2.7 | v1 | 17 test | 0.662 | 16/17 | keep | Rescore 2026-04-21: +ThermalLeakyWell 0.193; mean 0.694→0.662 |
| E07 | tree_run1 | plug + filetree index (sys-prompt) | deepseek-v3.2 | v1 | 17 test | 0.604 | 17/17 | discard | 3 timeouts; XML quality degraded |
| E08 | minprimer_run1 | plug + minimal primer | deepseek-v3.2 | v1 | 17 test | 0.596 | 17/17 | discard | 4 timeouts; shorter primer hurts |
| E09 | memws_run1 | plug + cheatsheet in /workspace/CHEATSHEET.md | deepseek-v3.2 | v1 | 17 test | 0.592 | 16/17 | discard | Rescore 2026-04-21: +ViscoDruckerPrager 0.141; mean 0.622→0.592 |
| E11 | gmem_run1 | plug + G-memory-lite MCP tool | deepseek-v3.2 | v1 | 17 test | 0.638 | 17/17 | discard (v1) | Memory tool called 1×/task |
| E12 | gmem_v2_run1 | E11 + threshold=0.6 + delay-trigger instruction | deepseek-v3.2 | v1 | 17 test | 0.646 | 16/17 | discard | 1 failed_no_outputs (AskUserQuestion failure) |
| E13 | gmemsilent_run1 | E11 + NO system-prompt mention of memory | deepseek-v3.2 | v1 | 17 test | 0.651 | 17/17 | discard (v1) | Agent never called memory (mem=0) |
| E14 | plugin_seed2 | plain plugin (variance anchor) | deepseek-v3.2 | v1 | 17 test | 0.616 | 13/17 | keep | **Showed plug+v1 is much lower than Brian's plug+v2** |
| E15 | noplug_seed2 | plain no-plugin (variance anchor) | deepseek-v3.2 | v1 | 17 test | 0.597 | 15/17 | keep | **No-plugin variance = ~0.01; very stable** |
| E16 | noplug_mm_v2 | no-plug | minimax-m2.7 | **v2** | 17 test | 0.564 | 15/17 | keep | **Canonical no-plug baseline**. Rescore 2026-04-21: +Deviated 0.651, +ModifiedCamClay 0.141, +Thermoporo 0.869; mean 0.566→0.564 |
| E17 | plug_mm_v2_seed2 | plain plugin | minimax-m2.7 | **v2** | 17 test | 0.575 | 13/17 | keep | 4 failed_no_outputs (min+v2 unexpected) |
| E18 | gmemsilent_mm_v2 | plug + G-memory-lite MCP, silent | minimax-m2.7 | **v2** | 17 test | **0.725** | **17/17** | **keep (memory positive!)** | **First clean evidence memory helps** |

Spec sets:
- **v1**: `/data/shared/.../experiments/` — older mining generation; different `instructions.txt` per task
- **v2**: `/data/shared/.../experiments_test36_template/` — canonical mining; Brian's runs used this

---

## 2. Key findings (what we actually know)

### Finding 1: Plugin's headline +0.178 was spec-confounded

All "plugin wins +X" comparisons up through 2026-04-20 had a confound: Brian's plug+ds run (E03, 0.828) used v2 specs; Matt's no-plug+ds run (E01, 0.643) used v1 specs. Per-task instructions.txt **differs for every task** between the two spec sets (v1 is sometimes longer, sometimes shorter than v2).

When apples-to-apples on v1 (same model, same specs, different seeds):
- plug+ds seed 2 (E14): 0.616
- no-plug+ds seed 2 (E15): 0.597
- **Paired delta: +0.019** (not +0.178)

When apples-to-apples on v2 (same model, same specs, same seed, minimax):
- plug+mm seed 2 (E17): 0.575 (13 scored) 
- no-plug+mm (E16): 0.566 (12 scored)
- **Paired delta: +0.055** on 10 tasks in common (still small)

So on v2, plugin's real gain over no-plugin is modest — not the +0.178 we claimed in XN-001.

### Finding 2: Plugin has large cross-seed variance; no-plugin does not

- no-plug+ds on 17 test: E01 seed 1 = 0.589, E15 seed 2 = 0.597 → **Δ +0.008** (essentially zero variance)
- plug+ds on 17 test: E03 seed 1 (Brian) = 0.831, E14 seed 2 = 0.616 → **Δ 0.215** (huge variance)
- plug+mm on 17 test: E02 seed 1 (Brian) = 0.776 on subset, E17 seed 2 = 0.575 → **Δ 0.201** (huge variance)

Plugin-side variance is concentrated on the **same 3 "rescue tasks"** (Sneddon, Mandel, DPWellbore). These tasks score 0.7–0.99 when plugin "finds" the right reference and 0.06–0.35 otherwise. Whether the rescue fires is seed-dependent.

**Hypothesis:** the plugin's RAG enables a high-variance "catastrophic-failure rescue" mechanism — sometimes it works brilliantly, sometimes it doesn't. No-plugin is consistently low. Multi-seed runs are needed for any paper claim.

### Finding 3: Memory does help, on the right config

E18 = G-memory-lite MCP tool + minimax + v2 specs:
- **0.725 mean on 17/17 scored** (vs E17 plain-plug = 0.575 on 13/17)
- Paired vs E17 (same seed/specs): **+0.094, wins 9/4**
- Paired vs E16 (no-plugin): +0.117, wins 8/4
- **Zero failed_no_outputs** (vs E17's 4)

Memory wins biggest on: IsothermalLeakyWell +0.511, CasedContactThermo +0.507, ModifiedCamClay +0.424, Thermoporoelastic +0.298. Loses on: EDPWellbore -0.478, buckleyLeverett -0.236.

**Caveat:** single seed. The memory MCP was E13's "silent" variant (tool present, no system-prompt instruction). Other variants (E11 with instruction, E12 with threshold + instruction) have only been run on v1. Needs v2+minimax rerun to compare.

### Finding 4: Plugin's rescue mechanism is genuine signal (not variance/luck)

Trajectory-level analysis (XN-008) on the 3 biggest-delta tasks in E03 showed the plugin wins systematically via:
- (a) **Semantic discovery** of alternative solver families the agent would otherwise miss (e.g., Sneddon has 3 valid solvers: EmbeddedFractures, LagrangianContact, HydroFracture — plugin finds all; no-plugin finds only one)
- (b) **Schema-aware filtering** that excludes irrelevant source-code hits (e.g., DPWellbore: no-plugin reads 13 files including .hpp/.cpp source; plugin filters directly to wellbore context)
- (c) **Variant disambiguation** via documentation context (e.g., Mandel FIM vs sequential benchmark variants)

Grep/Glob cannot match these because files don't share filename patterns and source-code keywords match irrelevant files.

The rescue is genuine; its inconsistency (Finding 2) is what needs multi-seed to characterize.

### Finding 5: Memory failures on v1 were largely seed variance, not memory design

The "memory hurts -0.18 to -0.32" finding from E04–E13 was largely artifacts of:
- E04/E05/E07/E08/E09/E13 vs **Brian's E03** → spec-set confound PLUS seed variance
- After re-running plain plugin on same seed/specs (E14 = 0.616), memory variants are **within ±0.05 of plain plugin**:
  - E11 (gmem with instruction): -0.022 vs E14 → slightly positive
  - E12 (gmem gated): +0.004 vs E14 (16 paired)
  - E13 (gmem silent): +0.035 vs E14
  - E09 workspace-cheatsheet: +0.010 vs E14
  - E04/E05 (cheatsheet in sys-prompt): still real negatives -0.08 to -0.12 (smaller than originally reported)

Only system-prompt cheatsheet has a real, smaller regression (-0.08 to -0.12) due to the premature-end_turn failure mode.

### Finding 6: Minimax is ~4× faster than deepseek at similar quality and cost

From E06/E02/E16/E17/E18 timing:
- Minimax median per-task wall: ~200s (range 180–600)
- Deepseek median per-task wall: ~800s (range 500–1200)
- Minimax median input tokens: ~767K; deepseek median: ~1500K
- OpenRouter cost/task: similar (~$0.40)
- Quality (plug+mm vs plug+ds same seed): deepseek slightly higher but within variance

**→ Recommend minimax as default for future experiments.** Used throughout E16–E18.

### Finding 7: Concurrency headroom exists

Machine has 128 CPU / ~900GB RAM / 3× L40S idle. Started at workers=6, moved to workers=12 with no OpenRouter rate-limit issues. Rate limits appear comfortably above our current usage.

### Finding 8: CC native memory is a no-op in our pipeline

Every task has `memory_paths/` dir but it's always empty across all sampled runs. Zero `memory`-named tool calls. `/memory` slash command not even in agent's tool list. Per-task workspace is wiped with the container anyway. **Not a confound for any result.**

### Finding 9: `redacted_thinking` is NOT Anthropic encryption

The `redacted_thinking` blocks in our event logs are an **OpenRouter adapter construct**. The `data` field is `openrouter.reasoning:` followed by base64-encoded JSON. Decoded content is **byte-identical** to the adjacent visible `thinking` block in the same turn.

OpenRouter is duplicating each reasoning output as both visible `thinking` and "redacted" `redacted_thinking` (just base64 passthrough). Our model's reasoning is **not hidden** — we can read every reasoning trace directly.

This corrects my earlier (wrong) framing that "the stop reason is hidden in redacted_thinking." The reasoning is fully visible.

---

## 3. Failure modes (sorted by importance)

### Failure mode A: Premature end_turn without XML (E04/E05/E17)

**Signature:**
- `status: failed_no_outputs`
- Elapsed 27–250s (way below 1200s wall clock)
- Few tool calls (2–8)
- `stop_reason: end_turn`, `is_error: false`, `terminal_reason: completed`
- `workspace_inputs_present: False`
- Last trajectory events: tool_result → RESULT (no assistant message in between)

**What we know:**
- The agent was mid-investigation when it stopped
- After a specific tool_result, the model produced **zero content** in response
- Not a timeout (way under 1200s)
- Not an error (API says completed)
- Not anchoring (agent's last thinking stated forward intent)
- Shows up on **both deepseek** (E04, ~3-5 of 17 tasks when cheatsheet in system prompt) **and minimax** (E17, 4 of 17 tasks even without cheatsheet)

**Mechanism (identified 2026-04-21 — see docs/XN-010):** after a
`tool_result` the OpenRouter → minimax call occasionally returns an empty
completion (no text, no thinking, no tool_use). Claude Code's agent loop
ends when the latest message has no `tool_use`, so an empty completion is
faithfully turned into `stop_reason=end_turn`. Not a max-tokens issue
(observed at 386 output_tokens, cap 32k). Not a context-window issue
(28k input, 200k window). Not an API error.

**Fix applied 2026-04-21:** new plugin Stop hook
(`plugin/hooks/verify_outputs.py`) blocks `end_turn` when
`/workspace/inputs/` has no `.xml` files or any XML fails to parse, feeding
a concrete complaint back to the agent. Forces a second chance in the
same context (preserves tool-call history, unlike the runner-level retry
which restarts from scratch).

**Hypotheses (not tested):**
1. OpenRouter adapter drops final streaming content under certain conditions
2. OSS model produces empty completion when context reaches certain shape
3. Minimax has rare "decided done with no output" failure mode

**Interesting observation:** E18 (same spec/seed/model as E17 but with memory MCP tool available) had **0 failures** on those same 4 tasks. Having the memory tool in the tool list apparently changes behavior enough to avoid this mode.

**Workaround options:**
- Retry mechanism in runner: detect `failed_no_outputs` at short elapsed, re-launch once with same prompt
- Add a dummy tool to the tool list
- Switch to a different model/provider
- Minimal reproducer via `curl` against OpenRouter to isolate model-side vs adapter-side

### Failure mode B: Timeout after exploration (E03 Brian's, E06, others)

**Signature:**
- `status: timeout`
- Elapsed = 1200s (wall-clock hit)
- Many tool calls (30–80)
- `workspace_inputs_present: True` (partial XML written before timeout)

**What we know:**
- Agent is actively working; just runs out of wall time
- Scorer may parse partial XML and return a score (or fail with ParseError if the XML is truncated mid-tag)
- Brian's original timeout concern (from geophys_todo.md): "agent kept exploring instead of writing"
- Minimax rarely hits this (mean ~200s/task); deepseek often does (~800s/task median)

**Workaround options:**
- Raise wall-clock (we're already at 20 min; diminishing returns)
- Run on minimax (4× faster → less timeout exposure)
- Add a "soft deadline" mid-task nudge to tell agent to start writing

### Failure mode C: Scorer errors on successfully-authored XML

**Observed in E16 / E17 / others:**
- ~~`RecursionError: maximum recursion depth exceeded`~~ **FIXED 2026-04-21** — was NOT a deep tree-walk; was a cycle in `<Included>`-file resolution (agent hallucinated self/mutual file includes). Scorer's `_resolve_included` now uses an ancestor-chain guard. See `docs/XN-010_scorer-recursion-bug-fix.md`. Rescoring recovered 8 tasks across E02/E03/E05/E06/E09/E16.
- `ParseError: not well-formed (invalid token): line N column M` — XML agent wrote is syntactically invalid. Partially mitigated by XN-010's `try/except ET.ParseError` around the inner include-parse; still fires when ALL top-level files are unparseable (e.g. E06/TutorialPoroelasticity).

### Failure mode D: AskUserQuestion deadlock

**Observed in E12 (Sneddon):** agent called `AskUserQuestion` for solver choice, got "Answer questions?" back (no user present), then emitted text restating options and ended turn. No XML written.

This happens occasionally — also observed in E01 no-plug Sneddon (per XN-008) and E03 plug Sneddon when given ambiguous multi-option tasks.

**Fix applied 2026-04-21:** `AskUserQuestion` added to
`NATIVE_CLAUDE_DISALLOWED_TOOLS` in `scripts/run_experiment.py`. Closes this
failure mode for all future runs. See XN-010 for mechanism writeup and
XN-011 for the failures-as-zero metric reframe.

### Failure mode E: MCP preflight timeouts (rare)

Observed in E14 (2 tasks: ExtendedDruckerPrager, Mandel) — status `error: "The read operation timed out"`. MCP RAG server didn't respond to preflight in time; runner marked task as error before agent ran. Not an agent failure.

**Workaround:** bump preflight timeout in runner.

---

## 4. Methodological issues and confounds

### Issue 1 (CRITICAL): spec-set mismatch

Brian's runs used `/data/shared/.../experiments_test36_template/` (v2). My runs through 2026-04-20 used `/data/shared/.../experiments/` (v1). Different `instructions.txt` per task (all 20 sampled tasks differ). This confounded EVERY comparison up through E13.

**Fix status:** E16, E17, E18 use v2 specs. All canonical comparisons should use v2 going forward.

### Issue 2: Single-seed everywhere

Plugin has ±0.2 cross-seed variance on the rescue tasks. All our single-seed paired comparisons are therefore noisy. Memory's +0.094 win (E18 vs E17) needs multi-seed to know if it's robust.

**Fix status:** E14 (plugin_seed2) and E15 (noplug_seed2) established that no-plugin is low-variance and plugin is high-variance. But we haven't done multi-seed on the memory variant yet.

### Issue 3: Score-mean excludes failures

`batch_evaluate.py` writes `*_eval.json` only for scorer-successful tasks. My reported means are over scored files. Failed_no_outputs / ParseError / RecursionError tasks are excluded. This **favors runs with more failures** (their mean looks higher than it should).

**Fairer framings available:**
- **Scored mean** (what I usually reported): excludes failures
- **Paired mean**: tasks both runs scored; uses only common tasks
- **Failures-as-zero**: all N tasks, unscored counted as 0

**Fix status:** `misc/compare_runs_per_task.py` reports both scored-only mean and failures-as-zero mean in the summary. Per-task tables show all tasks.

### Issue 4: Task subset (17/35) may not represent full eval

My 17-task test subset is half of E03's 35 scored tasks (alternating-by-score split). It's stratified by difficulty but **biased toward tasks plugin+deepseek could score**. Tasks that timed out in E03 are NOT in the split (like SPE11b). For paper claims on the full 46-task suite, we'd need to re-expand.

---

## 5. Infrastructure / artifacts produced this session

### Code changes
- `scripts/run_experiment.py` — added agent variants:
  - `claude_code_repo3_plugin_mem` (E04, long cheatsheet in sys-prompt)
  - `claude_code_repo3_plugin_memshort` (E05, short cheatsheet)
  - `claude_code_repo3_plugin_tree` (E07, filetree)
  - `claude_code_repo3_plugin_memws` (E09, workspace-file cheatsheet; `cheatsheet_in_workspace=True`)
  - `claude_code_repo3_plugin_gmem` (E11/E12, memory MCP with instruction)
  - `claude_code_repo3_plugin_gmemsilent` (E13/E18, memory MCP no instruction; `memory_prompt_hint=False`)
- `plugin/scripts/memory_mcp.py` — new MCP server exposing `memory_lookup(query, n, min_score)` and `memory_stats()` tools
- `plugin/memory_index.json` — frozen G-memory-lite index built from 18 train-split trajectories
- `plugin/cheatsheet.md`, `cheatsheet_short.md`, `cheatsheet_abstract.md`, `cheatsheet_raw_lessons.md` — cheatsheet variants
- `plugin/GEOS_PRIMER_minimal.md` — ~450-token minimal primer
- `plugin/filetree.md` — precomputed inputFiles/ path index
- `scripts/memory/build_cheatsheet.py`, `build_gmem_index.py`, `dc_cu_orchestrate.py` — memory-building pipelines

### Analysis / comparison scripts
- `misc/compare_runs.py` — aggregate paired comparison
- `misc/compare_runs_per_task.py` — per-task comparison with agent-level metadata (new today)
- `misc/score_and_compare_mem.sh` — wrapper for scoring + paired compare

### Docs / findings notes
- `docs/XN-001_plugin-vs-no-plugin-deepseek.md` — original E03 vs E01 (confounded)
- `docs/XN-002_advisor-brief-2026-04-20.md` — advisor brief after E03/E04
- `docs/XN-003_memory-experiment-negative.md` — E04 memory analysis (largely superseded by variance discovery)
- `docs/XN-004_failure-mode-analysis-and-memory-plan.md` — timeouts + early-exit taxonomy
- `docs/XN-005_cross-model-plugin-win.md` — E06/E02 cross-model (confounded)
- `docs/XN-006_advisor-brief-final.md` — consolidated 2026-04-20 report (pre-variance-discovery)
- `docs/XN-007_filetree-negative.md` — E07 filetree
- `docs/XN-008_plugin-mechanism-trajectory-analysis.md` — mechanism analysis of plug wins
- `docs/XN-009_memory-failure-trajectory-analysis.md` — memory failure modes (pre-variance-discovery)
- `docs/LN-001_memory-test-time-literature.md` — literature survey
- `docs/REPORT_2026-04-20.md` — full-sprint report (pre-variance-discovery; needs update)
- `docs/SESSION_MAP_2026-04-21.md` — this doc
- `misc/RUN_COMMANDS.md` — exact run commands for every experiment I launched (diff vs Brian's at the bottom)

### .copilot state (tracking artifacts)
- `.copilot/method_tree.jsonl` — 22-node DAG, append-only
- `.copilot/hub.md` — State of Knowledge (auto-generated)
- `.copilot/research_log.md` — 11 chronological log entries
- `.copilot/decisions/D-001..D-003.md` — design decisions
- `.copilot/reviews/RN-001_reviewer_e03-e04-audit.md` — adversarial review notes

### Git commits (from this session)
8 commits ahead of `origin/main` on `repo3`. Clean logical chunks: gitignore, runner, plugin artifacts, memory scripts, misc outputs, docs, .copilot, E12 changes. Not pushed.

### Sharing with collaborators
- `/data/shared/geophysics_agent_data/matt_repo3` — symlink to `/home/matt/sci/repo3/` (one path for everything)
- `/data/shared/geophysics_agent_data/matt_repo3_README.md` — orientation doc

---

## 6. Open questions

1. **Does E18's memory win survive multi-seed?** Single-seed +0.094 over plain plugin. Needs replication.
2. **Why does having memory tool in tool list prevent the failed_no_outputs mode?** E17 had 4 such failures; E18 (same config + memory tool available) had 0. Is it the extra tool in the list, or the tool description content, or something else?
3. **Is minimax's empty-response-after-tool_result pattern model-side or adapter-side?** Testable with `curl` against OpenRouter.
4. **What's the right baseline for hard mode?** If easy-mode plugin gain is only +0.055 on canonical specs, hard mode should have more room — but needs validating with actual runs.
5. **Can we fix the scorer's RecursionError?** 2 tasks in E16 hit it. `sys.setrecursionlimit` is likely enough.
6. **Is DC-Cu (Dynamic Cheatsheet with test-time updates) worth trying?** Infrastructure is built (`scripts/memory/dc_cu_orchestrate.py`) but never run.
7. **Are there ANY memory variants we haven't tried that literature suggests?** LN-001 has suggestions. Reflexion-style same-task retry is untried.

---

## 7. Where to go next (for your consideration)

Unprioritized list of directions. I have no strong preference — you pick.

### Quality-of-evidence track
- **Multi-seed E18** (2-3 more seeds of gmem-silent+mm+v2) — firms up the +0.094 memory win
- **Multi-seed E17** (plain plug+mm+v2) — firms up plugin-only baseline
- **E11/E12 on v2+minimax** — other memory variants on canonical specs
- **Plugin attribution** (skill-only vs MCP-only) — which part of the plugin drives the win

### Cross-condition expansion
- **Plug+ds+v2 seed 2** (replicate Brian's E03 on our side) — reproducibility check
- **No-plug+ds+v2** — we have E01 on v1 but not v2
- **Opus 4.6 cross-model** (cost-expensive, would give SOTA data point)
- **Gemma cross-model**

### New directions
- **Hard mode generation** via `mine_examples_v2.py --required-only` + fresh 17-task set
- **Reflexion-style retry** — give the agent its own first-attempt trajectory on a 2nd attempt
- **DC-Cu orchestrator run** — use the built-but-unused `dc_cu_orchestrate.py`
- **Physics-family filter** on memory_lookup (from XN-009 Proposal 2)
- **Anti-pattern-only cheatsheet** (LN-001 Variant 11)

### Failure-mode sorting (what you flagged)
- **A (premature end_turn):** minimal `curl` reproducer to isolate model-side vs OpenRouter adapter. Add retry in runner. Consider tool-list-padding experiment (does ANY extra tool prevent the failure?)
- **B (timeout after exploration):** mostly solved by switching to minimax. Could add a soft-deadline nudge mid-task.
- **C (scorer bugs):** `sys.setrecursionlimit` fix. Iterative scorer walk as fallback.
- **D (AskUserQuestion):** add system-prompt instruction forbidding it, or remove from tool list
- **E (MCP preflight timeout):** bump preflight timeout in runner

### Infrastructure
- **Push branch to origin** (8 commits ahead, not pushed)
- **Score previously-failed tasks** manually if Brian's scorer has fixes
- **Update XN-001/006 and REPORT** to reflect the variance reframing

---

## 8. How to give me overnight instructions

Areas where I can operate autonomously with minimal risk:
- Multi-seed runs (I know the commands, costs, time)
- Memory variants on v2+minimax (cheap, <$10 each)
- Scorer fixes + rescoring
- Failure-mode minimal reproducers (curl tests)
- Doc updates to reflect variance reframing
- Hard-mode task-set generation

Areas where I'd prefer not to auto-decide:
- Running Opus (cost)
- Pushing to origin
- Any destructive action on shared data
- Committing to a specific paper narrative before you've seen the data

If you want a concrete overnight-ready worklist, give me:
1. How many minimax runs' worth of budget you're OK with (I can estimate at $0.40/task × 17 tasks × N runs)
2. Which of §7's directions you want to prioritize (rank 3-5 of them)
3. Any failure-mode fixes you want me to land (§7's "sorting" list)
4. Whether I should touch Brian's scored results dir vs keeping strict read-only

I'll execute and leave a summary at `docs/OVERNIGHT_LOG_<date>.md`.

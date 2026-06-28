---
id: XN-016
title: "OpenHands harness baseline — design, smoketest, full-run"
date: 2026-04-27
dag_nodes: [I12]
links:
  derived_from: [D-009]
  related_to: [XN-005, XN-013, XN-014]
tags: [baseline, harness, openhands, cross-harness]
status: in-progress
---

# XN-016 — OpenHands harness baseline

*Implementation in progress 2026-04-27. This note will be updated with
smoketest results, then full-run results.*

## Why

Add a third harness baseline alongside vanilla CC + harness-less
direct prompt. See selection survey
`docs/2026-04-27_other-coding-agent-harness-selection.md` and decision
memo `.copilot/decisions/D-009_other-coding-agent-baseline.md` for the
full reasoning. The 30-second version: a third coding-agent harness
running the same model + primer + 17 tasks lets us disambiguate
"CC-specific adaptation wins" from "harness-shape effects."

## Design (frozen 2026-04-27)

**Harness**: OpenHands SDK v1.17.0 (`openhands` CLI, headless +
JSON mode, `--override-with-envs`).
**Model**: `openrouter/minimax/minimax-m2.7` via LiteLLM.
**Domain primer**: `run/AGENTS.md` verbatim (incl. `# GEOS Primer`
block) — copied to per-task workspace root, auto-loaded by OpenHands
as a project skill via its `load_project_skills` mechanism.
**Per-task spec**: `BEGIN/END SIMULATION SPECIFICATION` wrapper —
identical to vanilla CC.
**Workspace**: `/workspace/inputs/*.xml` (writable),
`/geos_lib/...` (filtered, read-only) — same mount paths as CC, so
the primer's absolute-path references resolve correctly.
**Container**: `geos-eval-openhands` (Ubuntu 24.04 + uv +
`openhands` v1.17.0 from `uv tool install`).
**Tasks**: same 17 as `TEST_TASKS_17` in
`scripts/harnessless_eval.py`.
**Timeout**: 1200 s/task — same as CC.
**Contamination filter**: `runner.contamination.create_filtered_geos_copy`
re-used as-is; same per-task XML/RST blocklist.
**Scorer**: `scripts/eval/batch_evaluate.py`, same GT dir.

## What is *not* injected (intentional, per parity-contract)

- `rag_vanilla.txt` — CC-specific note about the primer location.
  Inapplicable to OpenHands.
- `real_tool_tail.txt` — CC-specific guard against minimax pseudo-
  tool-call leakage under CC's tool surface. May or may not be needed
  under OpenHands' tool surface; defer until smoketest reveals.
- The CC-specific `--disallowedTools Skill, AskUserQuestion`. OpenHands
  does not expose those tool names.
- The repo3 plugin / GEOS RAG MCP server — this is the *no-plugin*
  baseline, parallel to `claude_code_no_plugin`.

## Files added

- `run/Dockerfile.openhands` — image build.
- `scripts/openhands_eval.py` — per-task driver (mirrors
  `scripts/harnessless_eval.py` shape).
- `data/eval/openhands_no_plugin/<run>/...` — output root (separate
  from CC outputs to avoid any collision with the running CC session).

## Files NOT touched (concurrent CC session safety)

- `src/runner/*` — untouched.
- `run/AGENTS.md` — read-only consumption.
- `src/runner/agents.py` — no new agent entry; OpenHands is outside
  the CC runner.
- `scripts/eval/*` — re-used as a subprocess.

## Smoketest plan

1 task (`TutorialSneddon` — known to be a relatively short / simple
task in vanilla CC's E06 run) × 1 seed, 600 s timeout. Verify:
- [ ] Container starts; OpenHands authenticates with OpenRouter.
- [ ] AGENTS.md is loaded into the system context (visible in
      `events.jsonl`'s system-prompt event).
- [ ] Agent writes ≥1 XML to `/workspace/inputs/`.
- [ ] `events.jsonl` is parseable JSONL.
- [ ] Scorer produces a non-error TreeSim score.

## Smoketest results

**2026-04-27 — passed.**

`oh_smoke_s1 / TutorialSneddon`, single seed, 600 s timeout.

- Container started, OpenHands authenticated with OpenRouter using
  `openrouter/minimax/minimax-m2.7`.
- Agent ran for ~7.5 min, wrote 7 XML files to `/workspace/inputs/`:
  `Sneddon_base.xml`, `Sneddon_benchmark.xml`,
  `Sneddon_embeddedFrac_base.xml`,
  `Sneddon_embeddedFrac_verification.xml`,
  `Sneddon_hydroFrac_base.xml`, `Sneddon_hydroFrac_benchmark.xml`,
  `ContactMechanics_Sneddon_benchmark.xml`.
  AGENTS.md was visibly consumed — the agent produced a 6-step task
  list quoting GEOS solver names (Embedded Fractures / Lagrangian
  Contact / Hydrofracture) directly from the primer.
- Trajectory captured in `events.jsonl`: 71 OpenHands events parsed
  (22 `FileEditorAction`, 9 `TerminalAction`, 3 `TaskTrackerAction`,
  1 `FinishAction`, plus paired observations). No `<invoke>`
  pseudo-tool-call leakage observed in the visible turns.
- **TreeSim = 0.843 (overall_score = 8.43/10).** Sole task in
  smoketest; passes scorer compatibility check.

### Bugs found + fixed

1. **`tmp_geos` permission**: default `TEMP_GEOS_PARENT`
   (`/data/.../tmp_geos`) is owned by `brianliu`. Resolved by
   running with `--tmp-geos-parent
   /data/shared/geophysics_agent_data/data/eval/tmp_geos_matt`.
   *Documented as a runner CLI flag; default unchanged so concurrent
   CC session continues using its own scratch dir.*
2. **Docker `--user` blocked openhands binary**: `uv tool install`
   put the venv under `/root/.local/share/uv/tools` (mode 700).
   Rebuilt the image with `UV_TOOL_DIR=/opt/uv/tools` + `chmod
   a+rX`. Image rebuilt at 11:31 UTC; bug no longer reproducible.
3. **JSONL parser**: OpenHands `--json` emits **multi-line
   pretty-printed** JSON between `--JSON Event--` markers, not
   strict JSONL. Parser updated to chunk on the marker and balance
   `{...}` braces; verified on smoketest trajectory.
4. **Token usage missing**: OpenHands v1.15 events do not include
   `usage.{prompt,completion}_tokens` directly. `tokens_in /
   tokens_out` are 0 in the parsed summary. *Workaround for full
   run*: query OpenRouter's cost API per session_id, or upgrade
   OpenHands to a version that surfaces usage events. Tracked as
   a follow-up; does not block the cross-harness comparison since
   tool-call counts and wall-clock are still captured.

### Smoketest checklist (re-stated)

- [x] Container starts; OpenHands authenticates with OpenRouter.
- [~] ~~AGENTS.md loaded into the system context~~ — **FALSE**, see
      RN-004 P0 #1. AGENTS.md was written to the workspace but never
      reached the model. The agent did `ls /workspace`, saw the file
      listed, and never opened it. The 0.843 TreeSim was achieved
      with **no GEOS primer at all** — the agent worked from the
      task spec alone. The "primer-specific terminology" attributed
      above came from the task spec itself, which mentions Embedded
      Fractures / Lagrangian Contact / Hydrofracture by name.
- [x] Agent writes ≥1 XML to `/workspace/inputs/`.
- [x] `events.jsonl` is parseable (71 events).
- [x] Scorer produces non-error TreeSim score (0.843).
- [!] **NEW (must add):** primer present in agent's system or first
      user message — verified by post-run grep.
- [!] **NEW (must add):** OpenHands `activated_skills == []` — see
      RN-004 P0 #2 (Linear API skill auto-injected on Sneddon match).

## Adversarial review — RN-004, 2026-04-27

The smoketest "passed" but the adversarial review surfaced **two P0
blockers** that invalidate the parity claim. See full note at
`.copilot/reviews/RN-004_adversarial_openhands-baseline.md` and
the per-finding Responses table in the same file.

Headline:
- **P0 #1:** AGENTS.md primer never reached the model. CC has the
  primer; OpenHands did not. The 17-task comparison would have
  been "primer vs no-primer," not "harness vs harness."
- **P0 #2:** OpenHands auto-injects keyword-matched "skills" from a
  bootstrap cache (`~/.openhands/cache/skills/public-skills/` —
  40+ public skills). The Sneddon spec's "linear elastic" matched
  the `linear` skill (Linear API GraphQL instructions injected as
  `<EXTRA_INFO>`). Different tasks would activate different skills,
  silently varying the OpenHands prompt per-task.

Plus P1 #3 (re-readable `task.txt` differential), P1 #4 (stale
`inputs/*.xml` not wiped on re-run), P3 (unpinned OpenHands
version), P3 (tool-surface gap).

**Gate decision: 17-task campaign HALTED.** Smoketest result
invalidated. Fixes in progress (this note will be updated when
the patched runner re-smoketests cleanly).

## Smoketest #2 — RN-004 fixes verified (2026-04-27)

`oh_smoke_s2 / TutorialSneddon`, single seed, 600 s timeout, patched
image (`openhands==1.15.0` pinned, `load_user_skills/load_public_skills`
sed-patched to `False`), patched runner (inline primer+spec via
`--task`, no `task.txt` or `AGENTS.md` in workspace, `task_dir` wiped on
prepare, post-run `verify_parity()` enforced).

**Results:**

| Check | Result |
|---|---|
| `status` | `success` |
| `exit_code` | `0` |
| `elapsed_seconds` | 600.5 (hit timeout boundary; agent had already issued FinishAction) |
| `primer_in_context` | **`true`** — all 5 fingerprints (`GEOS Expert`, `PRIMARY RESPONSIBILITY`, `# GEOS Primer`, `two-file pattern`, `GEOSDATA`) seen in stream |
| `activated_skills` | **`[]`** — no public skills injected |
| `n_xml_files` | 7 (full Sneddon set) |
| `n_events` parsed | 92 (32 FileEditorAction, 9 TaskTrackerAction, 3 TerminalAction, 1 FinishAction) |
| TreeSim | **0.743** (overall_score 7.43/10) |
| Workspace contents | `inputs/`, `outputs/`, `metadata.json`, `events.jsonl`, `status.json`, `stderr.txt`, `exit_code.txt` — no `AGENTS.md`, no `task.txt` (P1 #3 fix verified by absence) |

Notes:
- TreeSim 0.743 is slightly *lower* than smoketest #1's contaminated
  0.843. This is consistent with RN-004's observation that Sneddon
  scored 0.843 with **no** primer — for this task, primer presence may
  be neutral-to-slightly-negative. Sample of 1; no conclusion drawn.
  Actual cross-harness comparison must come from the full 17-task run.
- Bumping to `--timeout 1200` for the campaign (CC parity); the
  600 s smoketest just barely fit Sneddon.
- Token usage still 0 in `status.json` (OpenHands v1.15 events don't
  surface usage). Documented limitation; not a parity break.

**Gate decision update:** RN-004 P0 #1, P0 #2, P1 #3, P1 #4, P3 #6 all
verified fixed by this smoketest. P3 #7 (tool-surface gap — task_tracker
exists in OpenHands and not in CC) accepted as documented limitation.
Finding #8 (OpenHands' built-in system prompt content vs CC's)
**deferred** to limitations section (round-2 adversarial review skipped
per researcher direction; see D-009 status update + Limitations §
below).

## Full campaign — `oh_test17_s1`

**Launched:** 2026-04-27 (after smoketest #2).
**Config:** 17 tasks (`TEST_TASKS_17`) × 1 seed × 4 workers ×
1200 s/task × patched `geos-eval-openhands` image.
**Output:** `data/eval/openhands_no_plugin/oh_test17_s1/<task>/`.
**Scoring:** invoked via `--score` after all tasks complete →
`data/eval/results/oh_test17_s1/openhands_no_plugin/`.

### Results — single-seed (NOT VALIDATED, replication queued)

**Status counts** (17 tasks, 1 seed):
- `success`: 17 ★ (was 16; see correction note below)
- `failed_no_outputs`: 0
- `failed_parity_*`: 0
- `timeout`: 0
- All 17 successes have `primer_in_context: true` + `activated_skills: []`.

★ **Post-hoc correction (2026-04-27).** Original campaign reported
`AdvancedExampleViscoDruckerPrager` as `failed_no_outputs` because the
runner's `n_xml_files` count used a non-recursive glob; the agent
nested its outputs under `inputs/triaxialDriver/*.xml`. The scorer
*always* globbed recursively, so its TreeSim score (0.998) was correct
all along — only the runner's status classification was wrong. Bug fixed
in `scripts/openhands_eval.py` (`rglob` instead of `glob`); the s1
status.json + `_summary.json` were backfilled.

**Wall clock**: 26 min (16 successful tasks × ~5 min avg / 4 workers).

**Per-task TreeSim** (CC values pulled from
`data/eval/results/noplug_mm_v2/claude_code_no_plugin/` and
`data/eval/results/noplug_mm_v2_s2/claude_code_no_plugin/` —
the canonical no-plugin minimax runs from XN-005, two seeds where
available; `--` = task not scored in that CC seed):

| Task | OH s1 | CC s1 | CC s2 | CC mean | Δ (OH − CC mean) |
|---|---:|---:|---:|---:|---:|
| AdvancedExampleCasedContactThermoElasticWellbore | 0.772 | 0.146 | 0.950 | 0.548 | +0.224 |
| AdvancedExampleDeviatedElasticWellbore | 0.834 | 0.651 | -- | 0.651 | +0.182 |
| AdvancedExampleDruckerPrager | 0.989 | 0.788 | 0.173 | 0.480 | +0.508 |
| AdvancedExampleExtendedDruckerPrager | 0.820 | -- | 0.396 | 0.396 | +0.424 |
| AdvancedExampleModifiedCamClay | 1.000 | 0.141 | -- | 0.141 | +0.859 |
| AdvancedExampleViscoDruckerPrager | 0.998 | 0.129 | 0.317 | 0.223 | +0.776 |
| buckleyLeverettProblem | 0.625 | 0.775 | 0.961 | 0.868 | **−0.243** |
| ExampleDPWellbore | 0.911 | 0.922 | 1.000 | 0.961 | **−0.049** |
| ExampleEDPWellbore | 0.995 | 0.932 | 0.015 | 0.473 | +0.522 |
| ExampleIsothermalLeakyWell | 0.602 | 0.348 | 0.110 | 0.229 | +0.373 |
| ExampleMandel | 0.946 | 0.925 | 0.269 | 0.597 | +0.349 |
| ExampleThermalLeakyWell | 0.889 | -- | 0.951 | 0.951 | **−0.062** |
| ExampleThermoporoelasticConsolidation | 0.851 | 0.869 | 0.004 | 0.436 | +0.415 |
| kgdExperimentValidation | 0.897 | 0.887 | 1.000 | 0.944 | **−0.047** |
| pknViscosityDominated | 0.995 | 0.021 | 0.000 | 0.011 | +0.984 |
| TutorialPoroelasticity | 0.782 | 0.725 | -- | 0.725 | +0.057 |
| TutorialSneddon | 0.756 | 0.195 | 0.133 | 0.164 | +0.591 |

**Aggregate** (failures-as-0 over all 17 tasks, OH only):

- OH s1 mean TreeSim: **0.863 ± 0.126**
- CC mean (per-task seed-mean): **0.518 ± 0.304**
- Paired delta (n=17, OH − CC seed-mean): **+0.345 ± 0.348**
- OH wins / losses: **13 / 4**
- Sign-test p (2-sided): **0.049**

**Cleaner per-seed paired comparison** (avoids the seed-mean mush):

- OH-s1 vs CC-s1 (n=15 common): mean Δ = **+0.300**, wins 12/3, sign-test p = **0.035**
- OH-s1 vs CC-s2 (n=14 common): mean Δ = +0.412, wins 9/5, sign-test p = 0.424 (NS — high std σ=0.469)
- OH-s1 vs CC best-of-two-seeds (n=12 with both): wins **6/6** — most of the headline OH advantage *evaporates* when CC is given its better-seed pick.

**Key seed-variance observation in CC**: across the 12 tasks with both
CC seeds scored, the seed-to-seed range is large (e.g. EDPWellbore
0.015→0.932; ThermoporoelasticConsolidation 0.004→0.869;
ModifiedCamClay seed 1 only at 0.141; CasedContactThermoElastic
0.146→0.950). CC is highly seed-sensitive on this task set.
OpenHands single-seed result *cannot be claimed to beat CC* until we
have at least 2–3 OH seeds and can compare distributions, not point
estimates.

### What this result IS

- A first data point that the OpenHands harness, with our domain
  primer delivered inline, can author GEOS XML on this 17-task set
  with high reliability (16/17 produce parseable XML; mean TreeSim
  0.863).
- Strong evidence that OpenHands does NOT *underperform* CC on this
  task — the headline number is at minimum competitive.
- Two specific tasks where OH solidly beats CC across both CC seeds:
  `pknViscosityDominated` (OH 0.995 vs CC ≤0.021) and
  `AdvancedExampleViscoDruckerPrager` (OH 0.998 vs CC ≤0.317). These
  are CC consistent-failure tasks where OH succeeds. Worth a
  trajectory-level look in a follow-up.

### What this result is NOT

- A validated cross-harness comparison. `n=1` seed on the OH side
  vs `n=1–2` seeds on the CC side is statistically thin given CC's
  visible seed variance.
- A claim that OpenHands is "better" than vanilla CC. The
  best-of-CC-seeds comparison is 6/6 wins/losses on the 12 tasks
  with both CC seeds — the magnitude of the seed-mean lead is
  partly explained by CC's bad-seed runs dragging down its mean.
- A controlled measurement of "agent-loop shape." Per the
  Limitations § above, the residual confounds (primer placement,
  un-inspected OpenHands built-in system prompt, tool surface
  including task_tracker) all live on the OpenHands side. If
  OpenHands' built-in system prompt contains directives that
  materially shape agent behavior, the +0.345 mean-delta is
  attributable in unknown proportion to that vs the agent loop
  itself.

### Required next steps before any "OH > CC" claim

1. **OH seed 2** (`oh_test17_s2`) — running next as cycle 2.
2. **OH seed 3** (`oh_test17_s3`) — if seed 2 is also competitive.
3. Per-seed Wilcoxon (n=17 pairs per seed pair) once we have 3
   seeds.
4. Variance comparison: is OH less seed-sensitive than CC on this
   task set?
5. Trajectory inspection on the two big OH wins (pkn,
   ViscoDruckerPrager) — what does OH do that CC fails at?
6. (Deferred) Inspection of OpenHands' built-in system-prompt
   template to bound the round-1-RN-004 finding-#8 confound.

### Parity audit (2026-04-27 — triggered by user skepticism of +0.345 magnitude)

User asked the right questions. Findings:

**Specs.** Identical. `experiments_from_mined_specs/<task>/instructions.txt`
(used by the OH runner) and `experiments_test36_template/<task>/instructions.txt`
(used by CC's `noplug_mm_v2` per `src/runner/constants.py`) have the
same md5sum on `TutorialSneddon` (`0dc117a3...`). Same task text reaches
both agents.

**Primer.** `run/AGENTS.md` committed `2026-04-19`, only one commit
total. CC's `noplug_mm_v2` ran `2026-04-21`; same bytes both then and
now.

**Primer delivery DIFFERS** (was always documented; flagged here for
visibility):
- CC: AGENTS.md (with `# GEOS Primer` baked in) + `rag_vanilla.txt` +
  `real_tool_tail.txt` → `--append-system-prompt` slot. ~20.8 KB.
- OH: AGENTS.md verbatim → first user message prefix. ~20.4 KB.
- **OH does NOT get** `rag_vanilla.txt` or `real_tool_tail.txt`. The
  latter specifically tells minimax not to print pseudo-tool-call XML
  blocks — a known minimax+CC failure mode (XN-003/004/010).

**Schema.xsd** is referenced 3 times in AGENTS.md as documentation
(`geosx -s schema.xsd`). Same content in both prompts. Neither agent
has GEOS installed in eval mode, so the command is purely
documentation.

**Custom tools.** Zero. OH events.jsonl across all 17 tasks has 0
calls to `search_navigator`/`search_schema`/`search_technical`/
`memory_lookup` (the geos-rag MCP tools). The MCP is not loaded for
this baseline (no `--mcp-config`). OH tool inventory across all 17
tasks: `FileEditorAction` 368, `TerminalAction` 237, `FinishAction`
17, `TaskAction` 12, `TaskTrackerAction` 10, `ThinkAction` 3.
`Finish`/`TaskTracker`/`Think` have no CC-no-plugin analog (already
documented as Limitation #3).

**Memory.** None across tasks. `prepare_task_workspace` does
`shutil.rmtree(task_dir)` before each run; each container is `--rm`;
per-task workspace is fresh. OH's MEMORY directive (in its built-in
system prompt) tells the agent to use AGENTS.md as memory, but we
removed AGENTS.md from the workspace per RN-004 P1 #3 fix — the
agent has no memory file to read.

### Resource comparison (token / cost / wall-clock / tool calls)

**OH s1 cost** (from OpenHands' own `base_state.json`):
- Total: **$1.48** for 17 tasks
- Per task: **$0.087** mean
- Per task: 889k input tokens (~75% cache-read), 12k output, 26.5 LLM calls

**CC noplug_mm_v2 + s2 cost** (from CC's `events.jsonl` `type:result` event):
- Total: **$7.99** across 34 runs (2 seeds × ≤17 tasks each)
- Per task: **$0.235** mean
- Cache utilization: **negligible** (e.g., TutorialSneddon CC: 96
  cache_read tokens; OH on same task: 990,383 cache_read tokens)

**OH is ~2.7× cheaper per task than CC**, mostly from prompt-cache
hits. OpenHands' internal flow appears to prompt-cache aggressively
(LiteLLM cache_control headers); CC's `claude -p` over OpenRouter
shows essentially zero cache utilization on this baseline.

**Wall-clock**: OH mean 318 s/task vs CC mean 261 s/task — OH is
**~22% slower** per task despite being cheaper. So OH isn't winning
by being faster, just by using cached input tokens at much lower
cost.

**Tool calls**: OH mean 38/task; CC mean 35/task. Similar tool budget.

### Mechanism (preliminary, key finding)

CC's bad seeds show classic **early-exit** patterns:
- `ExampleEDPWellbore` CC2 = 9 tools / 122 s / **TreeSim 0.015**
- `AdvancedExampleViscoDruckerPrager` CC1 = 11 / 136 s / **0.129**
- `ExampleIsothermalLeakyWell` CC2 = 2 / 203 s / **0.110**
- `AdvancedExampleModifiedCamClay` CC2 = 12 / 271 s / **0.005** (per
  the broader status set)

These look like **the documented `redacted_thinking → end_turn`
failure mode** (XN-003 / XN-004 / XN-010) where minimax ends the
turn after a few tool calls without writing files. CC ships
`real_tool_tail.txt` specifically as a defense against minimax's
pseudo-tool-call leakage; the early-exit pattern is the same family
of failure.

**OH's tool counts across all 17 tasks: 17–63 (median 37). OH never
triggers the early-exit pattern.** That's not a primer effect, not a
fancier built-in system-prompt effect, not a tool-surface effect —
it's that **OH+minimax doesn't have CC+minimax's specific failure
mode.**

When CC doesn't trigger the failure (its better seed), CC scores
competitively. Best-of-CC-seeds vs OH on the 12 tasks with both CC
seeds: **6 OH wins / 6 CC wins**.

### Honest reframe

The "+0.345 single-seed mean delta" is mostly **OH avoiding a
CC-specific minimax failure mode** (~25–30% of CC-minimax seeds
silently early-exit), not OH being generically better. The real
findings worth reporting:

1. **Cost**: OH cheaper than CC on minimax (cache utilization).
2. **Reliability**: OH consistent (17/17 produce parseable XML; no
   early-exits). CC seed-sensitive (failures cluster on early-exit).
3. **TreeSim point estimate**: When CC succeeds (no early-exit), it's
   competitive with OH. Not a clean "harness X > harness Y" claim.

These are publishable, but the framing must be "harness-package
robustness on minimax" not "harness-loop quality."

### OH seed 2 added (oh_test17_s2; 2026-04-27)

| Aggregate | OH s1 | OH s2 | OH 2-seed mean | CC 2-seed mean |
|---|---:|---:|---:|---:|
| Mean TreeSim (all 17 tasks, failures-as-0) | 0.863 | 0.823* | **0.843 ± 0.135** | 0.518 ± 0.304 |
| Paired Δ vs CC-2-seed-mean (n=17) | +0.345 | +0.305 | **+0.325 ± 0.345** | — |
| Wins / losses vs CC-mean | 13/4 | 13/4 | 13/4 | — |

\* OH s2 had one bad seed: `AdvancedExampleExtendedDruckerPrager` 0.188 (s1 = 0.820).
OH per-task σ across 2 seeds: top is that one task (σ = 0.447); all others σ < 0.16.
OH is much less seed-sensitive than CC but not immune.

**Best-of-seeds comparison** (max of each side's 2 seeds, per task):
- OH best mean: **0.896**, CC best mean: 0.657
- Paired Δ: **+0.239 ± 0.362** (smaller than seed-mean Δ but still
  substantial)
- Wins / losses: **12 / 5**, sign-test p = 0.143 (NS)

So even removing the "CC bad seed drags down its mean" effect by
taking CC's better seed, OH still wins on 12 of 17 tasks. Five
losses are all small (max −0.20). Five wins are huge (>+0.4 each):
ModifiedCamClay, ViscoDruckerPrager, ExtendedDruckerPrager,
Sneddon, ExampleIsothermalLeakyWell, plus the catastrophic
pknViscosityDominated (CC ≤0.021 both seeds vs OH 0.996 both seeds).

So: **the OH advantage is real, but narrower than the seed-mean
suggests.** It's concentrated on tasks where CC has a catastrophic
failure mode that OH does not trigger. The DSv4 cross-model run
will tell us whether this is "OH+minimax avoids CC+minimax's
specific failure" (model-specific) or "OH harness has structural
advantages on this task class" (general).

## Cycle 3+ campaign plan: OH ablation matrix on DSv4

User direction (2026-04-27 session checkpoint): "Implement plugin +
external memory for OH; test if customizations improve over the
baseline; use DSv4 for multi-seed."

**Conditions** (× 1 seed for first cut; escalate to ≥3 if signal):
| Run name | Model | Plugin | Memory | Notes |
|---|---|---|---|---|
| `oh_dsv4or_s1` | DSv4-flash via OpenRouter | — | — | OH no-plugin baseline (cross-model check) |
| `oh_plugin_dsv4or_s1` | DSv4-flash | repo3 geos-rag MCP | — | plugin-only ablation |
| `oh_pluginmem_dsv4or_s1` | DSv4-flash | repo3 geos-rag MCP | M1-u primer | plugin+memory (full stack) |

**Why DSv4 for these**:
- ~10× cheaper than minimax (per `docs/2026-04-27_dsv4_migration.md`)
- Faster
- Different failure mode profile — tests whether OH advantage on
  minimax is "harness > harness" or "OH avoids CC+minimax-specific
  bug"

**Why OpenRouter route, not DeepSeek-direct**:
- DSv4-direct via Anthropic-compat endpoint failed in OH smoketest
  with `litellm.BadRequestError: ... reasoning_content in the
  thinking mode must be passed back to the API`. LiteLLM doesn't pass
  back DeepSeek's reasoning between turns.
- DSv4-direct via OpenAI-compat endpoint not yet probed (would
  bypass the thinking-mode protocol issue)
- For now: use `openrouter/deepseek/deepseek-v4-flash` route. If
  rate limits bite (per migration doc) we'll revisit.

**Wiring already in place** (`scripts/openhands_eval.py`):
- `--plugin` flag mounts `plugin/` + vector_db, writes
  `<workspace>/.openhands/mcp.json` with the geos-rag server, and
  injects `RAG_INSTRUCTIONS_OH` into the user message.
- `--memory-primer <path>` reads the file and prepends it as a third
  user-message section (above the spec, below the GEOS primer).
- Model + endpoint selectable via `--model`, `--base-url`,
  `--api-key-env`.

### Smoketest results (2026-04-27)

| Run | Model | Plugin | Memory | XMLs | TreeSim | Cost | Notes |
|---|---|---|---|---:|---:|---:|---|
| `oh_dsv4or_smoke` | DSv4-flash via OpenRouter | — | — | 0 | — | — | TIMEOUT at 600s. Agent did 16 file_views + 0 writes. DSv4 over OH gets stuck in exploration. (Bug also: TimeoutExpired returns bytes; fixed in runner.) |
| `oh_plugin_smoke_s1` | minimax-m2.7 | ✓ | — | 8 (incl. 1 extra) | **0.813** | $0.12 | MCP fired 3× (`search_navigator/schema/technical`). All parity gates green. |

### DSv4 verdict (preliminary)

DSv4-flash on OH is **not viable as-is**. Two failed attempts:

1. **DSv4-direct (Anthropic-compat endpoint)**: LiteLLM error
   `reasoning_content in the thinking mode must be passed back to the
   API`. OH's LiteLLM call doesn't pass back DeepSeek's reasoning
   content between turns.
2. **DSv4 via OpenRouter**: timed out at 600s on TutorialSneddon
   without writing a single XML file. 16 file_view actions, 0 writes.
   Either DSv4 is much slower than minimax over OH's loop, or it
   gets stuck in exploration without committing to file authoring.

**Decision**: pivot the ablation matrix to **minimax** for now. The
cross-model story (does OH advantage hold on a model that doesn't
have CC's early-exit failure mode?) is deferred. To unlock DSv4 on
OH we'd need to (a) probe DSv4-direct via OpenAI-compat endpoint
(not Anthropic-compat) — different protocol, may avoid the
`reasoning_content` issue; (b) try a non-thinking DSv4 variant if
one exists; (c) use a different cheap model (e.g. gpt-4o-mini, or
claude-haiku via Anthropic).

### Updated cycle plan (minimax-only for first cut)

| Cycle | Run name | Plugin | Memory | Status |
|---|---|---|---|---|
| 1 | `oh_test17_s1` | — | — | done, mean 0.863, $0.087/task |
| 2 | `oh_test17_s2` | — | — | done, mean 0.823 (1 outlier) |
| 3a | `oh_plugin_test17_s1` | ✓ | — | **launched 2026-04-27** |
| 3b | `oh_pluginmem_smoke_s1` | ✓ | M1-u | **smoketest launched in parallel** |
| 4 | `oh_pluginmem_test17_s1` | ✓ | M1-u | gated on 3b smoketest pass |

## Limitations (must be carried into the paper writeup)

The following parity differentials are **known and unfixable in v1.15**
of OpenHands (or accepted as the cost of "different harness, same
problem"). Any cross-harness claim must frame the comparison as
"package vs package," not "agent loop alone vs agent loop alone."

1. **Primer placement.** Vanilla CC injects the primer into the
   *system slot* via `--append-system-prompt`. OpenHands has no
   user-injectable system-prompt CLI flag in v1.15, so we deliver the
   primer as the prefix of the first *user message*. Same content,
   different role. Whether minimax weights system-message
   instructions differently from user-message instructions is an open
   question; we have not measured it.

2. **OpenHands' built-in system-prompt template (PARTIALLY
   INSPECTED 2026-04-27).** OpenHands ships a 147-line Jinja2
   template at `openhands/sdk/agent/prompts/system_prompt.j2`
   (preserved as
   `docs/2026-04-27_openhands_system_prompt_template.j2.txt`). Major
   sections: ROLE, MEMORY (tells the agent to use `AGENTS.md` as
   persistent repository memory), EFFICIENCY ("combine multiple
   actions"), FILE_SYSTEM_GUIDELINES (explicit "explore the file
   system to locate the file" directive), CODE_QUALITY,
   VERSION_CONTROL, PULL_REQUESTS, **PROBLEM_SOLVING_WORKFLOW**
   (numbered EXPLORATION → ANALYSIS → TESTING → IMPLEMENTATION →
   VERIFICATION recipe), SELF_DOCUMENTATION, SECURITY,
   EXTERNAL_SERVICES, ENVIRONMENT_SETUP, **TROUBLESHOOTING** ("Step
   back and reflect on 5–7 different possible sources of the
   problem"), PROCESS_MANAGEMENT. There is also a model-family
   addendum (`anthropic_claude.j2` / `google_gemini.j2` /
   `openai_gpt`) — none of which match `minimax`, so no extra block
   is added in our runs.

   **Bound on the confound:** OpenHands' built-in template carries
   substantial *meta-cognitive* and *workflow-discipline* directives
   (explicit numbered workflow, troubleshooting meta-prompt,
   exploration directive) that **do not appear in CC's
   `--append-system-prompt` payload** (CC's system prompt is just
   `AGENTS.md` + `rag_vanilla.txt` + `real_tool_tail.txt` for
   `claude_code_no_plugin`). CC has its own built-in system prompt
   (closed source) that we have NOT inspected, so we cannot say
   which package has more agent-discipline scaffolding *in total* —
   only that OpenHands' is rich and explicitly visible.

   **One concrete soft conflict:** OpenHands' MEMORY block tells the
   agent to use `AGENTS.md` under the repo root as persistent
   memory. We removed `AGENTS.md` from the workspace in the RN-004
   P1 #3 fix (so the spec isn't re-readable). The agent therefore
   gets a system-prompt directive to use a memory file that doesn't
   exist. In smoketest #2 + the s1 campaign, agent did `ls
   /workspace`, saw no AGENTS.md, and just proceeded — no observable
   harm, but this is a residual mismatch worth noting for the
   writeup.

   **Implication for the cross-harness comparison:** It is now
   established that the comparison is "OpenHands harness package
   (loop + built-in 147-line system message + tool surface
   including task_tracker / finish) vs CC harness package (loop +
   closed-source built-in system message + lean tool surface)" —
   not "isolated agent loop behavior". The +0.345 single-seed mean
   delta is attributable in unknown proportion to: (a) primer
   placement (system vs user); (b) OpenHands' explicit workflow /
   exploration / troubleshooting scaffolding; (c) OpenHands' wider
   tool surface (task_tracker fired 9× in smoketest); (d) seed
   luck. Multi-seed runs partially address (d). (a)–(c) require
   further ablations to attribute.

3. **Tool surface (RN-004 P3 #7).** OpenHands ships built-in
   `TaskTrackerAction` and `FinishAction` tools that CC does not
   expose. We did not find a v1.15 CLI flag to disable individual
   tools. Tool-surface confound is uncontrolled.

4. **Token-usage accounting.** OpenHands v1.15 events do not
   surface `usage.prompt_tokens / usage.completion_tokens` in the
   format our parser reads, so per-task token totals are recorded as
   0. Wall-clock and tool-call counts ARE captured. Cost-per-task
   comparison across harnesses requires querying OpenRouter's cost
   API per session; treated as future work, not blocking.

5. **Public-skills auto-loader is patched off.** We monkeypatch
   `openhands_cli/stores/agent_store.py:418-419` to set
   `load_user_skills=False, load_public_skills=False` because
   keyword-matched public skills (e.g. Linear API GraphQL injected
   for the substring "linear elastic") are a non-deterministic
   prompt confound. This is "OpenHands with one feature off" — we
   document this as a deliberate ablation, not "OpenHands as
   shipped."

6. **n=1 seed.** First-cut campaign is single-seed. Multi-seed
   variance estimation deferred — escalate to ≥3 seeds if the
   single-seed result is competitive enough to merit deeper
   investigation.

7. **Primer is not load-bearing on every task.** Smoketest
   evidence: TutorialSneddon scored 0.843 *without* the primer
   (smoketest #1, contaminated) and 0.743 *with* the primer
   (smoketest #2, clean). On this task the primer is
   neutral-to-slightly-negative. Per-task variance in
   primer-load-bearingness will dominate the run-to-run noise.

## Full-run plan

After smoketest passes + `/adversarial-review` clears the runner:

- 17 tasks × 1 seed, 1200 s timeout, 4 workers.
- Compare per-task TreeSim against vanilla CC's
  `claude_code_no_plugin` minimax run on the same 17 tasks.
- If competitive, escalate to ≥3 seeds for variance estimation.

## Full-run results

*Pending.*

## Validation gates (per D-009)

- [ ] Smoketest produces parseable XML for ≥1 task.
- [ ] Full 17-task run completes with ≥80% non-error / non-timeout.
- [ ] Per-task `metadata.json` confirms model, base URL, primer
      content hash all match CC parity.
- [ ] Scorer output for OpenHands run lands in
      `data/eval/results/<run>/openhands_no_plugin/`.
- [ ] `/adversarial-review` on the runner before promoting any
      cross-harness comparison to hub.md State of Knowledge.

## Open risks

| Risk | Status |
|---|---|
| Docker-in-Docker / sandbox runtime fights /geos_lib mount | Mitigated by running OpenHands inside our own image (no DiD); sandbox runtime defaults to local exec inside the container |
| OpenHands' default system prompt competes with our primer | OpenHands appends our AGENTS.md as a project skill — placed AFTER OpenHands' built-in instructions; primer hash recorded in metadata.json |
| minimax pseudo-tool-call leakage re-surfaces under different tool surface | Will inspect `events.jsonl` for any `<invoke name=...>` text; port `real_tool_tail.txt` if so |
| OpenHands rejects custom OpenRouter model name | Use `--override-with-envs` + `LLM_MODEL=openrouter/minimax/minimax-m2.7` (LiteLLM accepts this directly) |
| LLM_API_KEY leak via `ps`/process listing | API key only passed via `-e LLM_API_KEY=...` on the docker CLI, which is visible in `ps` for the host. Same exposure as the existing CC runner; not a regression. Audit-log entries redact the key. |

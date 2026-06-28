---
id: RN-001
source: reviewer
title: "Adversarial audit of E03 plugin-win and E04 memory-HURTS claims"
date: 2026-04-20
dag_nodes: [E01, E03, E04, I10]
links:
  related_to: [E03, E04, I10]
  evidence_against: []
trigger: "pre-advisor-meeting gate"
recommendation: "Weak Accept (claim directions are defensible; several framing claims in hub.md / XN-001 are inaccurate or sloppy and MUST be corrected before advisor meeting)"
priority_issues: 4
---

## Scope of audit
Checked the two headline claims:
1. E03 (plugin+ds) beats E01 (no-plugin+ds) by +0.175 TreeSim on paired 35 tasks.
2. E04 (plugin+cheatsheet+ds) loses to E03 (plugin) by -0.322 TreeSim on paired 14 test tasks.

Verified by reading `*_eval.json`, `status.json`, `eval_metadata.json`, and a sample
of events/tool logs. Cross-checked the copilot's own artifacts (XN-001, XN-002,
XN-003, hub.md, checkpoint.md, research_log.md, D-001, compare_runs.py,
score_run4.log, e04_vs_e03_test17.txt).

The direction of both claims is supported by the raw data. But several
specific framings in XN-001/hub.md/checkpoint.md are **factually wrong** and
will not survive a careful advisor reading.

## Critiques (numbered, with severity)

### C1. (MAJOR) "ExampleSPE11b parse error" framing is misleading — it was a TIMEOUT

**Claim (XN-001, hub.md, checkpoint.md, XN-002):** "Plugin run had 1 task with
a parse-error XML (`ExampleSPE11b`) that could not be scored."
hub.md: "ExampleSPE11b parse error in E03. One task's XML was unparseable.
Not investigated."

**What I checked:**
- `/data/shared/.../repo3_eval_run4/ExampleSPE11b/status.json`
- `/home/matt/sci/repo3/misc/score_run4.log` (the actual scoring log)

**What I found:**
- SPE11b's `status` in E03 is `"timeout"` at elapsed_seconds=1200.0 with
  `exit_code: null`. The agent was wall-clocked out, not the scorer.
- The scoring failure (`ParseError: junk after document element: line 16,
  column 0`) is a DOWNSTREAM symptom of the timeout leaving a
  half-written XML on disk.
- This is NOT "one task's XML was unparseable". It is "the agent
  timed out mid-write, producing corrupt XML." That changes the
  interpretation: the plugin run had 5 timeouts, not 3 (see C2), and
  SPE11b is one of them.

**Why it matters:** Advisor will read "parse error" and assume either a
scoring bug or an agent-side XML syntax mistake. The actual situation is
a timeout — which has different implications (the 20-minute cap is the
binding constraint, not agent capability). The copilot's own hub.md says
"Not investigated" — one `cat status.json` would have settled it.

**What to do:**
- Reword SPE11b framing everywhere to "timeout at 1200s; partial XML
  unparseable".
- Acknowledge E03 had 5 timeouts (see C2), not 3.
- Re-examine whether the headline mean would change if timeout-at-1200s
  tasks are excluded from both runs.

### C2. (MAJOR) Timeout counts in hub.md and XN-001 are wrong

**Claim (hub.md, XN-001):** "Current run4 had 3 timeouts (borderline tasks:
IsothermalLeakyWell, TFrac, DeadOilEgg)." This is listed under "What's
working" in hub.md.

**What I checked:** grepped every E03 `status.json` for `"status": "timeout"`.

**What I found — E03 (plugin+ds, run4) actually had FIVE timeouts:**
| Task | elapsed_s | treesim (scored) |
|---|---:|---:|
| AdvancedExampleCasedContactThermoElasticWellbore | 1200.4 | 0.847 |
| kgdExperimentValidation | 1200.4 | 0.864 |
| pknViscosityDominated | 1200.0 | 0.740 |
| TutorialDeadOilEgg | 1200.0 | 0.804 |
| ExampleSPE11b | 1200.0 | unparseable (was scored 0.287 in E01) |

**E01 (no-plugin+ds) had only THREE timeouts:** TutorialDeadOilEgg (1200),
ExampleTFrac (1200), ExampleIsothermalLeakyWell (1200). The list of
"borderline tasks" in hub.md is actually the E01 timeout list, not E03.
The copilot likely copy-pasted from ablation_findings.md and didn't
re-check against run4.

**Crucially:** IsothermalLeakyWell and ExampleTFrac did NOT time out in
E03 — they completed in 1066.9s and 657.6s respectively. So the plugin
appears to prevent timeout on 2 tasks while inducing timeout on 4
different tasks (CasedContactThermo, kgdExperimentValidation,
pknViscosityDominated, SPE11b — SPE11b is the only one timing out in
both; wait, SPE11b in E01 scored 0.287 at elapsed 1145.0s status
"success" so it didn't time out in E01). **So E03 adds 4 new timeouts
while only rescuing 2.** Net: +2 timeouts from adding the plugin.

**What to do:**
- Fix hub.md line: "3 timeouts" -> "5 timeouts on E03 (plugin). List the
  actual task names."
- Acknowledge that plugin *trades* timeouts: fewer on some tasks
  (explicitly which), more on others (explicitly which).
- This is not fatal to the +0.175 claim, but "plugin reduces timeouts"
  is NOT currently supported. The opposite appears true.

### C3. (MAJOR) E01 and E03 are NOT perfectly apples-to-apples — E01 had a retry on TutorialSneddon that E03 did not

**Claim (XN-001):** "Only difference: plugin vs no plugin."

**What I checked:**
- `/home/matt/sci/repo3/data/eval/claude_code_no_plugin/ablation_deepseek_v2/TutorialSneddon/attempt_1/status.json`
- The runner's retry logic at `scripts/run_experiment.py:1370-1420`

**What I found:**
- E01 TutorialSneddon first attempt (`attempt_1/status.json`):
  `failed_no_outputs`, 352.6s, `AskUserQuestion=1`, `workspace_inputs_present: false`.
  The agent emitted a "which solver?" question and bailed with no XML.
- The runner (`no_outputs_retry_prompt`) retried. The retry
  (`TutorialSneddon/status.json`) ran 683.9s and produced XML scored 0.099.
- E03 had 0 `attempt_1/status.json` files in `/data/shared/.../repo3_eval_run4/*/` —
  zero retries.

**Why it matters:** TutorialSneddon in E01 got 683.9s + 352.6s = **1036.5s of
agent compute**, nearly 2x the median E01 task. E03 got 1065.5s
(single shot). Wall-time-matched. BUT: the retry prompt includes a
"notice" appended to the task prompt telling the agent about the
previous failure. That's a different prompt than E03 got. Minor
effect for this single task (Sneddon remains E01's worst task at
0.099), but XN-001 claim of "only difference is plugin vs no plugin"
is literally false.

Scan across E03: no `*/attempt_1/` dirs exist, so no E03 task was
retried. Scan across E01: only Sneddon was retried. So the asymmetry
is confined to one task — the same task that is XN-001's biggest
headline gain (+0.705 for plugin).

**What to do:**
- XN-001: qualify the "apples-to-apples" claim — state the retry
  asymmetry explicitly, with the caveat "the retry helped E01
  marginally; it cannot explain the +0.705 gap on Sneddon."
- Before paper submission: either (a) force-retry on E03 to match, or
  (b) report numbers both including and excluding the retried task.
- Report the Sneddon-excluded delta as a sensitivity number.
  Mean(29 wins incl Sneddon) drops from 0.828 to ~0.827 if Sneddon
  removed, E01 goes to ~0.669; delta stays +0.16. Sign-robust but
  shrinks ~8%.

### C4. (MAJOR) Every E01 "no-plugin" task logs `plugin_tool_calls >= 1` — contamination-sensor flag needs explanation before anyone reads it

**Claim (XN-001 / eval_metadata):** no-plugin run has plugin disabled,
different harness, same primer.

**What I checked:**
- All 35 E01 `status.json` files for `plugin_tool_calls`, `rag_tool_calls`,
  `rag_requirement_met`, `per_tool_counts`.
- Events log for AdvancedExampleExtendedDruckerPrager to see what the
  MCP tool "call" actually was.

**What I found:**
- **Every E01 task shows `plugin_tool_calls >= 1`, `rag_tool_calls >= 1`,
  `rag_requirement_met: true`, and one or more `mcp__geos-rag__search_*`
  entries in `per_tool_counts`.** Yet `eval_metadata.json` says
  `plugin_enabled: false`, `mcp_config_path: null`, and
  `mcp_server_statuses: {}` in every `status.json`.
- Reading `events.jsonl` for ExtendedDruckerPrager: the agent's tool
  call returned `"tool_use_error": "No such tool available:
  mcp__geos-rag__search_navigator"`. So the agent attempted to invoke
  the MCP tool, the tool did not exist, and no data was returned.
  **No contamination occurred.** But the counter is still incremented.
- The fact that the E01 model (deepseek-v3.2) reliably attempts
  to call `mcp__geos-rag__*` tools that were never declared in its
  system prompt is itself suspicious — either the primer mentions
  these tool names, or the model's training leaks them. Either way,
  the counters say "rag_requirement_met: true" for the no-plugin run,
  which is misleading telemetry.

**Why it matters:** An advisor or reviewer opening a single E01
`status.json` will see `rag_requirement_met: true` and `plugin_tool_calls: 1`
and immediately ask "wait, the no-plugin run was calling plugin tools?"
The copilot has not pre-empted this. A careful reader would check
events.jsonl and find the error; a less careful reader would doubt the
whole ablation.

**What to do:**
- Add one sentence to XN-001 / XN-002 stating the counter semantics:
  "E01 task logs `plugin_tool_calls >= 1` because the model attempted
  to call MCP tools that were not declared; all such calls returned
  `tool_use_error: No such tool available` and carried no information."
- Audit the primer (`GEOS_PRIMER.md`) and AGENTS.md to check whether
  the MCP tool names leak into the no-plugin condition's system prompt.
  If they do, the primer differs between conditions — stricter ablation
  needed.
- Fix the logging (post-hoc) so the counter ignores rejected tool calls.

### C5. (MAJOR) E04 retry discipline was NOT surfaced — "3 premature terminations" understates instability

**Claim (XN-003, hub.md):** "Plugin had 17/17 successes; memory had 13/17
(3 failed_no_outputs within ~3 min, 1 timeout). Failure signature: agent
emits `redacted_thinking` block then `end_turn`."

**What I checked:**
- `attempt_1/status.json` files for mem_run1.
- `AdvancedExampleModifiedCamClay/attempt_1/status.json` and the final
  `status.json` in the same dir.

**What I found:**
- mem_run1 **did invoke the retry logic** for `failed_no_outputs`:
  AdvancedExampleModifiedCamClay had `attempt_1` (failed at 175s, 6
  tool calls) AND a main `status.json` (also failed, 66s, 5 tool calls).
- So the "3 failures" are actually "3 tasks that failed BOTH their
  initial attempt AND their retry" — a stronger negative signal than
  the copilot reported. The first retry also produced no XML.
- Telling the advisor "3 tasks failed once" vs "3 tasks failed twice
  consecutively with the retry prompt in hand" is a different story.
  The latter is stronger evidence for the cheatsheet breaking
  deepseek's tool-use, because the retry prompt explicitly asks the
  agent to produce outputs and it still failed.

**What to do:**
- XN-003: update failure count language. "3 tasks failed on both
  initial and retry attempts." Also worth noting the retry paths in
  Artifacts section.
- Consider this a stronger (not weaker) negative for the D-001 design.

### C6. (MINOR) XN-003 memory-wins task `pknViscosityDominated` is the one task where E03 ALSO timed out — possibly confounded

**Claim (XN-003):** memory wins only on pknViscosityDominated (+0.13).

**What I checked:** E03's `pknViscosityDominated/status.json`.

**What I found:** E03 pkn timed out at 1200s (workspace_inputs_present=true
means it wrote partial XML, scored 0.740). E04 pkn scored 0.870 at unknown
status (need to verify). If E04 pkn did NOT time out, the 0.13 delta could
be "memory helps the agent finish before the 20min wall" rather than
"memory improves XML quality." This is the one task where memory "wins" —
worth checking before interpreting.

**What to do:**
- Read `mem_run1/pknViscosityDominated/status.json` and report
  elapsed_s + status. If memory finished in <1200s, note that
  "memory's single win may be time-budget rescue rather than quality
  uplift."

### C7. (MINOR) "Failure signature ... caused by the cheatsheet" is not isolated from "deepseek/OpenRouter quirk on these specific tasks"

**Claim (XN-003, hub.md, XN-002):** "Dominant failure mode: agent emits
`redacted_thinking` block then `end_turn`... triggered by the cheatsheet
addition... matches qwen3.5-9b pattern."

**What I checked:** XN-003 inspected exactly ONE trajectory
(AdvancedExampleModifiedCamClay). It did not check the three failing tasks'
E03 counterparts for the same signature.

**What I found:**
- E03's AdvancedExampleModifiedCamClay succeeded in 566.7s, 0.918 TreeSim.
  No retry needed. So the cheatsheet does seem to be the differential
  cause on this task.
- But: the three tasks that failed in E04
  (AdvancedExampleModifiedCamClay, ExampleThermoporoelasticConsolidation,
  TutorialPoroelasticity) all share a specific property — they're
  lower-scoring tasks in E03 (0.918, 0.583, 0.670 respectively) AND
  they're all "elasto/poro" physics tasks. It's possible deepseek-v3.2
  has a task-family-specific instability that the cheatsheet *triggers*
  rather than *causes*. The cheatsheet's "Common Mistakes to Avoid"
  section has poroelastic-heavy advice from the 18 train tasks (several
  wellbore + poroelastic patterns). Advice that contradicts the agent's
  intended approach on a poro-task could send it into a thinking loop.
- The copilot's "long-context attention degradation" hypothesis in
  XN-003 is one plausible mechanism, but the XN-003 itself says
  "not yet tested." That's fine — but the phrasing "dominant failure
  mode" overclaims from n=1 trajectory inspection.

**What to do:**
- XN-003: downgrade "Dominant failure mode" to "Failure mode in the
  one trajectory we inspected."
- For the advisor meeting, inspect at least the other 2 failed-no-output
  tasks' events.jsonl (cheap — it's a JSONL grep). If all three end with
  `redacted_thinking -> end_turn`, then the signature claim is better
  supported. If only one does, downgrade the generalization.

### C8. (MINOR) Adversarial review (codex) was NEVER invoked

**Claim (hub.md phase=TEST transitioning to THINK, updated XN-002 for
advisor):** implicit — claiming validation.

**What I checked:** `/home/matt/sci/repo3/.copilot/reviews/` (only README.md),
grep of .copilot for "adversarial" or "codex" (only the README).

**What I found:** No RN-NNN note with an `adversarial` source has been
written. The project's own `rules/research-principles.md` is explicit:
"if you are declaring results are validated or updating hub.md's State
of Knowledge, you owe an `/codex:adversarial-review` first." Hub.md was
updated with a State of Knowledge that makes strong claims ("Plugin wins
on deepseek-v3.2 at model parity", "Frozen-cheatsheet memory ... HURTS
performance"). Neither /adversarial-review nor /codex:adversarial-review
was run.

**What to do:**
- Before advisor meeting: dispatch `/adversarial-review` on the results
  (not code — the results themselves + XN-001, XN-002, XN-003). Codex
  at GPT-5.4 is specifically the different-model gate for this kind
  of claim. Capturing the output verbatim to RN-NNN also makes the
  audit reproducible for the paper.
- If time-constrained, at least dispatch for E04 (the negative result)
  because single-seed negative claims with n=17 are exactly what
  reviewers will attack first.

## Claims that ARE defensible (briefly)

- **Direction of the E03 plugin win is robust.** Mean 0.828 vs 0.653,
  29/35 paired wins, max plugin loss -0.17 — size of effect is far
  beyond any seed variance I would expect on this scale of
  comparison. Including SPE11b as 0 (0.805 vs 0.645 with E01 at 0.643
  full-36) does not change the sign. Excluding TutorialSneddon
  (the retried task) does not change the sign. The comparison is
  imperfect (see C1-C4) but the DIRECTIONAL claim "plugin beats
  no-plugin on deepseek-v3.2 at model parity on this task set" is
  well-supported.
- **Direction of the E04 memory-hurts claim is robust.** -0.322 on
  14 paired + 3 two-retry failures is overwhelming. Even if the
  cheatsheet is somehow "bad by construction" rather than memory
  being hopeless (XN-003 acknowledges this), this specific D-001
  design is decisively discarded. Good.
- **Contamination enforcement appears consistent.** Both E01 and E03
  have the identical `blocked_gt_xml_filenames` and `blocked_rst_relpaths`
  in `eval_metadata.json` for the tasks I spot-checked (TutorialSneddon,
  AdvancedExampleModifiedCamClay). The blocklist is task-specific
  (Sneddon's list has 11 entries; ModifiedCamClay's has 2), which is
  correct behavior. Filtered GEOS copy dir differs (expected — different
  tmp scratch dirs). Same model, same primer, same delivery mechanism,
  same `anthropic_base_url`. The ablation design is sound. 2-layer
  contamination enforcement (blocklist + filtered GEOS copy) is honored.
- **"Catastrophic-failure rescue" mechanism story is plausible.** Biggest
  wins (Sneddon, DPWellbore, Mandel, CasedElasticWellboreImperfectInterfaces)
  are all cases where E01 scored <0.31. The treesim detail for E01
  Sneddon shows it produced ~12 of 66 required sub-elements, with
  huge sections empty; the RAG helped the agent find the right
  reference example. The mechanism is consistent with the data.

## Per-dimension ratings

| Dimension | Score | Justification |
|---|---|---|
| Relevance | 4/4 | Directly answers RQ1 at model parity, which is the paper's main rest-point. |
| Novelty | 2/4 | Single domain-RAG-over-technical-docs plugin. Standard pattern. Novelty is only "shown in this domain." |
| Technical Quality | 2/4 | Headline numbers robust in direction. But several framing errors (C1, C2), missing adversarial review (C8), retry asymmetry un-noted (C3), misleading telemetry (C4). |
| Presentation | 2/4 | XN-001/002/003 are well-organized. But hub.md carries factual errors (C2) and SPE11b mischaracterization (C1). These are 5-minute fixes that currently mislead an advisor. |
| Reproducibility | 3/4 | Results paths well-pointed. Scripts are present. `memory_split.json` documents train/test. Missing: cross-seed replication (acknowledged), and attribution (I11 acknowledged). |
| Reviewer Confidence | 3/4 | I can verify the raw numbers but cannot verify (a) whether primer content differs between conditions (see C4 investigation item), and (b) whether the retry notice changes E01 Sneddon's behavior substantively. |

## Recommendation

**Weak Accept for the advisor meeting**, pending the following fixes BEFORE
the meeting (all are ~30-60 min of work total):
1. Correct the timeout count in hub.md (C2).
2. Reword SPE11b framing as "timeout not parse error" (C1).
3. Add one sentence about Sneddon retry asymmetry (C3).
4. Add one sentence explaining `plugin_tool_calls` counter in E01 (C4).
5. Update XN-003 to say "failed on both initial and retry attempts" (C5).
6. Check the pknViscosityDominated E04 status (C6).
7. Downgrade "dominant failure mode" to "observed in n=1 trajectory" (C7)
   or inspect the other 2 failed trajectories.
8. Dispatch `/adversarial-review` (C8).

**Reject for paper submission** in current form. None of the fixes above
are individually fatal, but the accumulation means a careful reviewer
opening the `status.json` files will find enough inconsistencies to
doubt the entire ablation narrative. Multi-seed replication (already on
the copilot's TODO) is required.

## Addressable vs structural

- **Addressable (all above items):** Timeout count fix; SPE11b reframing;
  retry-asymmetry note; plugin_tool_calls explanation; E04 failure framing;
  pkn confound check; adversarial review. All are doc edits + one grep.
- **Structural (paper-blockers):** Single-seed everywhere. Plugin
  attribution (skill vs MCP) unknown. Cross-model robustness absent
  (plugin+minimax exists but not paired against no-plugin+minimax).
  These are the things that WILL come up in review — they are
  acknowledged in XN-001 "Honesty/limitations" but not yet addressed.

## Questions for the copilot

1. **Verify (quick):** Open `mem_run1/pknViscosityDominated/status.json`
   and report `elapsed_seconds` + `status`. If not "timeout at 1200s",
   your memory-win explanation needs updating.
2. **Verify (quick):** Open the three E04-failed tasks'
   `attempt_1/events.jsonl` and grep for `redacted_thinking`. Confirm
   n=3 or downgrade your claim to n=1.
3. **Primer audit:** Does `modules/profile/GEOS_PRIMER.md` (or AGENTS.md)
   mention `mcp__geos-rag__search_navigator` / `search_schema` /
   `search_technical` tool names verbatim? If yes, the no-plugin
   condition's system prompt is NOT identical to the plugin condition's
   minus MCP — it still mentions tools the no-plugin agent doesn't have.
   That's a subtle unfairness.
4. **Explain:** Why was `/adversarial-review` skipped despite hub.md
   being updated with State-of-Knowledge claims? The project's own
   rules require it.
5. **Assumption probe:** The "plugin rescues catastrophic failures"
   story is compelling but is it *attributable to RAG retrieval* or to
   *the skill prompt instructing the agent to use RAG at all*? The
   two are fundamentally different contributions. I11 is tracked but
   not run. What would change your mind about the attribution story
   before running I11?

## Bottom line

Results directionally survive the audit. The numbers aren't fabricated,
and the contamination enforcement is in place. But the current copilot
write-ups contain enough small factual errors that a ten-minute advisor
grill would find them. Fix the framing issues in hub.md / XN-001 / XN-003
before the advisor meeting. Before paper: multi-seed, plugin-attribution,
cross-model, and adversarial-review. None of that is news to the copilot,
but the state-of-knowledge claim strength needs to come down a click
until those are done.

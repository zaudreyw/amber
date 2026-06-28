---
id: RN-005
source: adversarial-reviewer
model: claude-opus-4-7-1m
title: "Adversarial code review: sub-agent orchestrator full-17 vs vanilla DSv4-flash (XN-018)"
date: 2026-04-28
invoked_at: 2026-04-28T00:00:00Z
dag_nodes: [I14, E25]
trigger: "pre-findings"
priority_issues: 4
blocker_for_campaign: true
links:
  evidence_against: [XN-018]
---

# Adversarial Code Review: Orchestrator vs vanilla DSv4-flash (XN-018)

## Scope

Files I actually read:

- `scripts/orchestrator/run_orchestrator_eval.py` — orchestrator runner.
- `scripts/orchestrator/launch_5task.sh`, `launch_remaining_12.sh` — campaign launchers.
- `scripts/orchestrator/score_run.sh` — scorer wrapper.
- `scripts/orchestrator/analyze_17task.py` — cross-implementation analysis (dispatch flagged this as recently authored).
- `plugin_orchestrator/ORCHESTRATOR_SYSTEM.md` — orchestrator system prompt.
- `plugin/scripts/geos_rag_mcp.py` — RAG MCP server (filter logic).
- `src/runner/contamination.py` — GT-blocking + filtered-tree creation.
- `src/runner/prompts/__init__.py` — primer assembly.
- `src/eval/judge_geos.py:112-152, 784-801` — XML loader + directory evaluator.
- `scripts/eval/batch_evaluate.py` — task evaluation entrypoint.
- `data/eval/orchestrator_dsv4flash/orch_dsv4_5task_s1/*/{status.json,claude_stdout.json,eval_metadata.json}`.
- `data/eval/orchestrator_dsv4flash/orch_dsv4_remain12_s1/*/{status.json,claude_stdout.json,eval_metadata.json}`.
- `data/eval/claude_code_no_plugin/dsv4flash_direct_s1/*/status.json` and `acpx_output.json` for one task.
- `misc/memory_artifacts/test_blocklist.json`.

Claims I am attacking (XN-018 + dispatch text):

- C1: Orchestrator mean TreeSim = 0.851 vs vanilla 0.647, paired Δ = +0.204 on 17 v2 tasks.
- C2: Orchestrator on DSv4-flash matches OpenHands+minimax-m2.7 within −0.012.
- C3: Per-segment subagent architecture is doing the work (not the primer).
- C4: Token usage profile: 4.4M paid input + 128M cache-read on the orchestrator vs 6.9M + 72M vanilla.
- C5: Comparison is fair; orchestrator vs vanilla is on equal footing.

## Findings

### P1 — Cross-test-task ground-truth leakage in BOTH arms (filtered tree only blocks current task's GT)   [BLOCKER for the +0.204 number being meaningful]

**Locations:**
- `src/runner/contamination.py:187-231` (`get_blocked_files_for_task`).
- `scripts/orchestrator/run_orchestrator_eval.py:284-298` (per-task filtered tree).
- `data/eval/orchestrator_dsv4flash/orch_dsv4_remain12_s1/ExampleIsothermalLeakyWell/claude_stdout.json` and the corresponding vanilla task.

**Evidence:**

`get_blocked_files_for_task` blocks **only the current task's** GT XMLs (plus variant-suffix siblings). The other 16 test tasks' GT XMLs sit unblocked in the filtered GEOS tree. The agents read and copy them.

For task `ExampleIsothermalLeakyWell` (orchestrator), the trace shows:

```
READ /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_base.xml
READ /geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/thermalLeakyWell_benchmark.xml
BASH cp .../thermalLeakyWell/thermalLeakyWell_benchmark.xml /workspace/inputs/isothermalLeakyWell_benchmark.xml
BASH cp .../thermalLeakyWell/thermalLeakyWell_base.xml /workspace/inputs/isothermalLeakyWell_base_iterative.xml
```

`thermalLeakyWell_base.xml` and `thermalLeakyWell_benchmark.xml` are the GT XMLs for **another** test task (`ExampleThermalLeakyWell`) — confirmed at `experiments_gt/ExampleThermalLeakyWell/inputs/`. They live in the source tree at `/data/shared/.../GEOS/inputFiles/compositionalMultiphaseFlow/benchmarks/thermalLeakyWell/` and are not in `IsothermalLeakyWell`'s blocklist:

```
"blocked_gt_xml_filenames": [
    "isothermalleakywell_base_direct.xml",
    "isothermalleakywell_base_iterative.xml",
    "isothermalleakywell_benchmark.xml"
]
```

The orchestrator literally copied a sibling test task's GT, renamed it to its own task's GT-shaped name, and that became the working file. Score: 0.836.

Vanilla on the same task also reads the cross-task GT (≥10 read events on `thermalLeakyWell_*` files in `dsv4flash_direct_s1/ExampleIsothermalLeakyWell/acpx_output.json`). So both arms can shortcut. **However**, the orchestrator's bootstrap workflow (Phase 0: "ONE search, ONE copy") *systematizes* that shortcut — the ORCHESTRATOR_SYSTEM.md explicitly tells the model to find a similar example and `cp` it into `/workspace/inputs/`. It is built to find these neighbors.

**Why it (partially) invalidates the claim:** This is a pre-existing leak that affects *all* 17-task v2 comparisons. The +0.204 delta is between two leakable conditions, so the comparison itself can stand IF you're willing to claim "orchestrator + leaky filter > vanilla + leaky filter." But you cannot claim "the orchestrator authors better XML" — you are partly measuring "how well the orchestrator copies neighboring test-task GTs." The dispatch-named eval set (`test_blocklist.json` defines a 17-task family with strong physics overlap; e.g., 3 wellbore + Drucker-Prager families are all in the test set together) maximizes this leak.

**Recommended action:**
1. Re-run the comparison with the **union** blocklist applied to all tasks: `union_xml` already exists at `misc/memory_artifacts/test_blocklist.json` and contains 55 entries. The runner currently ignores it. Pass these as the union blocklist for every task in the 17-task v2 set, not the per-task list.
2. Until that re-run happens, do not claim "+0.204" as evidence of a harness improvement. Reframe as "orchestrator wins under the existing (leakable) protocol" and add a Limitations bullet that the GT filter is per-task only.

---

### P1 — `--disallowedTools Write` is NOT actually being enforced; agent successfully wrote files in 4 tasks   [BLOCKER]

**Locations:**
- `scripts/orchestrator/run_orchestrator_eval.py:102` (`DISALLOWED_TOOLS = ["Skill", "AskUserQuestion", "Write"]`).
- `scripts/orchestrator/run_orchestrator_eval.py:194-195` — passes each as `--disallowedTools <name>`.
- Multiple `claude_stdout.json` files showing successful `Write` tool calls.

**Evidence:**

```python
DISALLOWED_TOOLS = ["Skill", "AskUserQuestion", "Write"]
...
for d in DISALLOWED_TOOLS:
    cmd += ["--disallowedTools", d]
```

But across the 17 tasks, the trace shows these `Write` tool_uses fired:

| task | Write count |
|---|---:|
| TutorialSneddon | 1 |
| AdvancedExampleCasedContactThermoElasticWellbore | 2 |
| ExampleThermalLeakyWell | 1 |
| kgdExperimentValidation | 1 |

Example from TutorialSneddon (`orch_dsv4_5task_s1/TutorialSneddon/claude_stdout.json`):

```
WRITE /workspace/inputs/Sneddon_embeddedFrac_base.xml  (3194 chars)
```

The `tool_use` event was actually executed (file appears on disk; the agent later read it back and edited it). `Write` is not denied at all.

Possible cause: Claude Code's `--disallowedTools` flag may expect a comma-separated list (`--disallowedTools Skill,AskUserQuestion,Write`) rather than repeated invocations, or the tool name format may be wrong (spelling, case). Either way, the runner's denial mechanism does not function.

**Why it invalidates the claim:**

XN-018 §Discussion claim 1: *"the orchestrator beats DSv4flash+full-primer by +0.21 mean despite each subagent seeing less primer content than the single-agent full-primer baseline. The segment-specific focus + per-segment schema slice is what helps."*

This claim depends on the orchestrator doing *only* delegation + splice, not direct authoring. With `Write` actually working, the orchestrator main thread is free to author XML directly (which it did, at least 5 times). Combined with the heavy `Bash cat > .xml << 'EOF'` heredoc usage (1-2 per task across all 17 tasks — see token analysis), it is **unclear how much of the 0.851 score is from subagent-segmented authoring vs. main-thread shortcut authoring**.

The ORCHESTRATOR_SYSTEM.md prohibition (lines 128-131 "**No `Write` tool** (disabled). **No authoring XML by hand**, even via `Edit`") is an LLM-honor-system instruction, not a hard guarantee — and the model is partially ignoring it.

**Recommended action:**
1. Verify the correct flag syntax for Claude Code's deny list. Repro the smoketest with `Write` and confirm denial. If repeated `--disallowedTools` is wrong, switch to comma-separated.
2. Add a verifier in `run_one_task` that scans `claude_stdout.json` for `Write`/`Bash cat > /workspace/inputs/*.xml` events and either fails the run or marks the task as "tooling-violated." Until this exists, no orchestrator paper-claim can be defended.
3. Re-run any task where Write fired. The current 0.851 mean includes those 4 tasks at scores: TutorialSneddon 0.839, CCTEW 0.852, ThermalLeakyWell 0.689, kgdValidation 0.950 — i.e., 3 of those are top-bucket scores that the architecture takes credit for.

---

### P1 — Token totals in XN-018 are inflated 2-4x by double-counting `message.usage` lines   [Decoration, but XN-018's Tokens table is unsupported]

**Location:** `scripts/orchestrator/analyze_17task.py:128-153` (`tally_jsonl_usage`).

**Evidence:**

```python
def tally_jsonl_usage(path: Path) -> tuple[int, int, int, int]:
    inp = out = cr = cw = 0
    ...
    for line in path.read_text().splitlines():
        ...
        m = d.get("message")
        ...
        u = m.get("usage")
        ...
        inp += int(u.get("input_tokens") or 0)
        ...
```

Every JSONL line is summed. Stream-json emits the same `message` repeatedly across deltas / re-broadcasts under subagent fan-out. Spot check on TutorialSneddon (`orch_dsv4_5task_s1`):

```
naive (analyze_17task):  inp=549,389  cache_read=8,826,624
dedup by message.id:     inp=221,743  cache_read=4,125,952
inflation factor:        2.48x input,  2.14x cache-read
```

Vanilla is also affected (`dsv4flash_direct_s1/TutorialSneddon/acpx_output.json`):

```
60 messages with usage, 15 distinct UUIDs (4x dup)
naive: inp=88,673  cr=2,412,800
dedup: inp=23,701  cr=658,560
```

Both arms over-report similarly, so the *delta* shape is roughly preserved. But **every absolute number in XN-018's Tokens section (table line 156-160; 4.4M / 128M / 79.0M / 6.9M / 72.1M) is wrong by 2-4x**. The "tokens-per-quality-point" comparison vs OpenHands is also wrong because OpenHands status.json reports tokens once (no JSONL-replay), so its number is ~real while the Claude Code numbers are inflated. That makes orchestrator and DSv4 variants look 2-4x **more** token-hungry than they actually are.

XN-018 §Discussion claim 4 *"With Anthropic-style caching ... it's a much smaller cost premium"* is built on these inflated numbers; the actual premium is even smaller than stated.

**Recommended action:**
1. Dedup `tally_jsonl_usage` by `message.id` before summing.
2. Re-render the Tokens section of XN-018 with corrected numbers.
3. Add a unit test against a small synthetic JSONL with known duplicate messages.

---

### P2 — Bootstrap "ONE search ONE cp" is allowed to copy near-GT examples; effectively a low-effort GT-adjacent baseline floor

**Locations:**
- `plugin_orchestrator/ORCHESTRATOR_SYSTEM.md:18-24` (Phase 0).
- Run traces showing `cp` from sibling examples.

**Evidence:**

The orchestrator workflow says: do ONE `mcp__geos-rag__search_technical`, take the FIRST result, `cp` it to `/workspace/inputs/<name>.xml`. The MCP filters results with `policy.is_blocked_xml_path`, so the chosen file is not a blocked GT exact match.

But variant-key matching uses `_XML_VARIANT_SUFFIXES` which does not include `_shapes`, `_staticCondensation`, etc. Example for TutorialSneddon: GT is `Sneddon_embeddedFrac_base.xml` (blocked). The agent picked `Sneddon_embeddedFracShapes_base.xml` (not blocked: stem `sneddon_embeddedfracshapes` doesn't share a variant key) and copied it. Diff against GT: same physics, same solver, very similar parameters (47-line diff against a 158-line file). So Phase 0 effectively delivers a nearly-correct skeleton, and the subagents do "small fixups" to that skeleton. Their +0.20 over vanilla isn't "the architecture authors XML well" — it's "we let the bootstrap do most of the work via a lookup heuristic that the variant filter doesn't fully cover."

This compounds with P1 (cross-task GT leakage): for many tasks the bootstrap source is not just a sibling, it's another test task's GT (`thermalLeakyWell_base.xml` for IsothermalLeakyWell; `kgdViscosityDominated_*` for `pknViscosityDominated`; `extendedDruckerPragerWellbore_base.xml` for `ExampleEDPWellbore`).

**Why it qualifies the claim:** Headline framing ("subagent architecture closes the small-model–big-model gap") is overstated. A more honest framing is "an MCP-driven sibling-example bootstrap + 5-segment subagent fixup beats a single-agent re-author from scratch." The architectural contribution and the bootstrap-shortcut contribution are not separated.

**Recommended action:**
1. Either (a) extend `_XML_VARIANT_SUFFIXES` to include the additional patterns observed in real bootstraps (`_shapes`, `_staticcondensation`, etc.) and re-run, OR (b) ablate: orchestrator-without-bootstrap (have the workflow start from an empty `<Problem></Problem>` and force subagents to author from scratch). The ablation is the only way to measure "subagent architecture" contribution independent of bootstrap copy.
2. Update the leakage-aware blocklist (P1 fix) and re-run.

---

### P2 — Vanilla baseline includes the baked GEOS Primer; orchestrator strips it and inlines a different one. Primer surface is not matched

**Locations:**
- `src/runner/prompts/__init__.py:32-53` (`load_agents_md`, default keeps baked primer).
- `scripts/orchestrator/launch_*.sh:55,69` (orchestrator passes `--strip-baked-primer`).
- `data/eval/claude_code_no_plugin/dsv4flash_direct_s1/TutorialSneddon/status.json`: `"primer_in_system_prompt": true`.

**Evidence:**

- Vanilla: `dsv4flash_direct_s1` was run via `src/runner/cli.py`, which calls `load_agents_md(strip_baked_primer=False)`. AGENTS.md contains a `# GEOS Primer` section starting at line 108, so vanilla's system prompt has the baked primer (≈480 lines).
- Orchestrator: `--strip-baked-primer` removes the baked primer, then `build_system_prompt` inlines `--geos-primer-path` (default `/home/brianliu/.../GEOS_PRIMER.md`, 647 lines), THEN appends `ORCHESTRATOR_SYSTEM.md` (147 lines), THEN a tail.
- The two primers are similar but not identical. The external one is longer and adds a "RAG Tools Reference" section.
- Subagents additionally each get their own per-segment primer (`plugin_orchestrator/primers/*.md`) baked into their persona.

**Why it weakens the C3 claim:** XN-018 §Discussion: *"The orchestrator beats DSv4flash+full-primer by +0.21 mean despite each subagent seeing less primer content than the single-agent full-primer baseline. The segment-specific focus + per-segment schema slice is what helps."* But the orchestrator's *aggregate* primer surface (external GEOS_PRIMER + ORCHESTRATOR_SYSTEM + 5 segment primers + 5 schema slices) is substantially larger than vanilla's. "Each subagent sees less" is a per-agent statement; the *system as a whole* sees more. The fairness baseline for "is segmentation the cause" needs to give the single-agent equal total primer mass.

**Recommended action:**
1. Re-run vanilla with the same `--strip-baked-primer` + external primer to match the orchestrator's primer-and-only-primer surface. Or, run an "orchestrator-with-baked-primer-only" arm to remove the external-primer confound.
2. Soften C3 in the paper: the harness improvement is "segmentation + per-segment focused primers + auto-extracted schema slices + RAG bootstrap" — multiple conflated levers, not "segmentation alone."

---

### P3 — Campaign-wall fallback to filesystem mtimes is brittle; the 8069s "true wall" is mtime-derived, not started/ended

**Location:** `scripts/orchestrator/analyze_17task.py:89-125` (`compute_campaign_wall`).

**Evidence:** Orchestrator `status.json` files have `updated` but no `started` (`run_orchestrator_eval.py` line 372-381 only writes `updated`). So the timestamp branch never fires; the function falls back to `eval_metadata.json` mtime → `status.json` mtime. This works *if no later process touches those files*. If `score_run.sh`, `analyze_17task.py`, or the user touches them post-hoc (e.g., re-running scoring after editing the analyze script), the mtimes shift and the wall-clock changes silently.

For the vanilla run, `started`/`updated` are both populated, so its 1248s "true wall" is real. Comparing 8069s (mtime) to 1248s (real) is order-of-magnitude OK, but the precision implied by 4-digit numbers in XN-018's table is overstated.

**Recommended action:**
1. In `run_one_task`, write `started` (already in `eval_metadata.json`) into `status.json`. One-line fix.
2. Re-run the analyze script after this so wall numbers come from real timestamps, not mtimes.

---

### P3 — Orchestrator's "single deliverable" rule is widely violated; multi-XML output benefits from scorer's `<Problem>`-merge

**Locations:**
- `plugin_orchestrator/ORCHESTRATOR_SYSTEM.md:131` ("The single deliverable is `/workspace/inputs/<task>.xml` — exactly one file").
- `src/eval/judge_geos.py:138-147` — when generated dir has multiple top-level XMLs, all are merged under one `<Problem>` and scored together.
- All 17 orchestrator tasks have ≥2 XMLs; TutorialSneddon has 7.

**Evidence:** Scorer at `judge_geos.py:138-147`:

```python
entries = [fp for fp in parsed if fp not in referenced]
if len(entries) == 1:
    return _resolve_included(parsed[entries[0]], entries[0].parent, {entries[0]})

merged = ET.Element("Problem")
for file_path, root in parsed.items():
    resolved = _resolve_included(root, file_path.parent, {file_path})
    for child in list(resolved):
        merged.append(child)
return merged
```

When the orchestrator produces 7 XMLs (TutorialSneddon: `Sneddon_base.xml`, `Sneddon_benchmark.xml`, `Sneddon_hydroFrac_base.xml`, `Sneddon_hydroFrac_benchmark.xml`, `Sneddon_embeddedFrac_base.xml`, `Sneddon_embeddedFrac_verification.xml`, `ContactMechanics_Sneddon_benchmark.xml`), the scorer merges all of them under `<Problem>` and bipartite-matches against GT. Because TreeSim rewards matched elements without strongly penalizing extra ones, dumping multiple "alternative skeletons" can only help the score.

Vanilla also produces multiple XMLs in some tasks (e.g., `sneddon_embeddedFrac_base.xml` + `sneddon_embeddedFrac_verification.xml` for TutorialSneddon). But the orchestrator's behavior is more aggressive — Sneddon = 7 files. This is partly an artifact of the bootstrap (Phase 0 copies one XML, then the agent decides 6 more file copies are useful "for completeness").

**Recommended action:** Confirm whether TreeSim penalizes extra-content. If not, score against only the file matching the GT primary stem, not the merged `<Problem>`. At minimum, document this scorer behavior in XN-018's Limitations.

---

## Clean checks (verified, no issue)

- **GT blocklist environment plumbing** (`run_orchestrator_eval.py:209-228`, `geos_rag_mcp.py:108-126`): `EXCLUDED_GT_XML_FILENAMES` and `EXCLUDED_RST_PATHS` are populated from `get_blocked_files_for_task`, passed via env to the container, and read at MCP startup. The MCP filters `xml_reference` and `source_path` against the policy at `geos_rag_mcp.py:246-251`. Per-task blocking works for the **current** task; the bug is that it doesn't include other test tasks (P1-1).

- **No silent fallback if `DEEPSEEK_API_KEY` is missing**: `run_orchestrator_eval.py:447-449` errors and exits non-zero. `OPENROUTER_API_KEY` for embeddings — if unset, the OpenAI client raises on first MCP call (not a silent degrade).

- **Bootstrap source paths checked against blocklist**: All 23 `cp` commands across 17 tasks copy from non-blocked basenames (verified by grepping cp source filenames against `eval_metadata.json:blocked_gt_xml_filenames`). The agent doesn't bypass the per-task GT block; it bypasses the *cross-task* one (P1-1) and the variant-suffix gap (P2-bootstrap).

- **No `try/except: pass` in the runner**. `run_one_task` writes status.json on every error path including `TimeoutExpired` and the catch-all `Exception` (lines 389-405). Task failures are recorded, not swallowed.

- **TreeSim numbers in XN-018 reproduce exactly**: 17/17 paired, mean 0.851 vs 0.647, Δ = +0.204, 13W/3L/1T. This part of the analyze script is correct.

- **Vanilla and orchestrator scored against the same GT dir** with the same `judge_geos.evaluate_directories` path. No scorer-side asymmetry.

- **Workers parameter does not affect per-task behavior**: Each task is its own subprocess; the only effect of `--workers` is concurrency. Vanilla used 6, orchestrator used 2 — XN-018 already calls this out as a wall-clock caveat, not a quality confound.

## Overall assessment

- **Blocker for paper claim:** **YES**. The +0.204 paired delta is real *as-measured* but the measurement protocol has three serious holes:
  1. Cross-test-task GT leakage (P1-1) inflates BOTH arms but rewards the orchestrator's bootstrap-and-cp workflow more.
  2. `Write` denial does not work (P1-2). The orchestrator's "delegate-only" architecture is not actually enforced.
  3. The "segmentation, not primer" attribution claim (C3) is unfounded because primer surface differs between arms (P2-primer).

- **Confidence headline claim is valid, conditional on P1 fixes:** **Low-to-medium**. After fixing the union blocklist and Write enforcement, the paired delta could shrink substantially or even invert on tasks where the win came from copy-shortcut (TutorialSneddon, ExampleIsothermalLeakyWell, ExampleDPWellbore — three of the four largest wins involve cross-task or variant-shortcut copies).

- **Most likely undiscovered failure mode:** The orchestrator's `Edit`-based splicing logic on subagent return values may have its own bugs that don't show up in scoring because the multi-XML `<Problem>`-merge masks them. If a subagent returns malformed `<Solvers>` content but the agent has already `cp`d a near-correct sibling, the splice failure may not register as a TreeSim drop. I did not verify this end-to-end.

- **What XN-018 should say before paper claim:** Reframe the result as "an MCP-driven bootstrap-from-sibling-examples + 5-segment subagent fixup + larger primer surface beats a single-agent author-from-scratch baseline by +0.20 under the existing per-task contamination filter." Each of those four levers is a separate experimental question. The paper-grade claim would need (a) union-blocklist re-run; (b) `Write`-actually-denied re-run; (c) primer-surface-matched baseline; (d) bootstrap-removed orchestrator ablation. Any one of these likely changes the headline.

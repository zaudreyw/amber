---
id: RN-004
source: adversarial-reviewer
model: claude-opus
title: "Adversarial code review: OpenHands harness baseline (D-009, pre-campaign gate)"
date: 2026-04-27
invoked_at: 2026-04-27T00:00:00Z
dag_nodes: [I12]
trigger: "implementation-gate"
priority_issues: 4
blocker_for_campaign: true
status: findings
links:
  derived_from: [D-009]
  evidence_against: []
  related_to: [RN-003, XN-016, "docs/2026-04-27_other-coding-agent-harness-selection.md"]
---

# Adversarial Code Review: OpenHands harness baseline

## Scope

Files read independently:
- `scripts/openhands_eval.py` — OpenHands per-task driver (the new code)
- `run/Dockerfile.openhands` — OpenHands container image
- `src/runner/orchestrator.py` — vanilla CC per-task driver (parity reference)
- `src/runner/docker_cmd.py` — `build_claude_native_command`, `build_claude_native_env`
- `src/runner/agents.py` — `claude_code_no_plugin` definition
- `src/runner/prompts/__init__.py` + `rag_vanilla.txt` + `real_tool_tail.txt`
- `src/runner/constants.py` — `DEFAULT_CLAUDE_MODEL`, `NATIVE_CLAUDE_DISALLOWED_TOOLS`, timeout
- `src/runner/contamination.py` — shared filter (re-used)
- `run/AGENTS.md` — the primer (read in full; 588 lines, contains `# GEOS Primer` block)
- `data/eval/openhands_no_plugin/oh_smoke_s1/TutorialSneddon/` — full smoketest artifact set
  (`metadata.json`, `status.json`, `events.jsonl` (2502 lines), `task.txt`, `inputs/*.xml`,
  `.home/.openhands/cache/skills/*`)
- `.copilot/decisions/D-009_other-coding-agent-baseline.md`

Claims attacked (paraphrased from D-009 + dispatch focus text):
- **A. Parity:** OpenHands runs with the same model, primer, task set, contamination
  filter, scorer, and per-task workspace as `claude_code_no_plugin`; differences in
  TreeSim therefore reflect harness shape, not training/data confounds.
- **B. Non-disruption:** Adding the baseline does not perturb concurrent CC runs.
- **C. Smoketest passes:** Container starts, agent writes 7 XMLs to `/workspace/inputs/`,
  scorer produces TreeSim=0.843. Harness is ready for the 17-task campaign.

## Findings

### P0 — AGENTS.md primer never reaches the model    [BLOCKER, invalidates Claim A]

**Location:** `scripts/openhands_eval.py:122-130, 151-152`

**Evidence — code:**
```python
def load_agents_md() -> str:
    """Load run/AGENTS.md verbatim. This is the entire 'domain adaptation'.

    Vanilla CC appends this via ``--append-system-prompt``. OpenHands
    auto-discovers AGENTS.md in the working directory and loads it as a
    project skill into the system context — same effective placement.
    """
    return AGENTS_MD_PATH.read_text()
```

```python
# OpenHands auto-loads AGENTS.md from the work dir as a project skill.
primer_path = task_dir / "AGENTS.md"
primer_path.write_text(primer_text)
```

This claim is the basis for parity. It is **false** — OpenHands does not auto-load
`/workspace/AGENTS.md` into the system prompt. The driver passes nothing to OpenHands
that would route the primer into the model context (no `--system-prompt` flag, no
microagent file, no `.openhands/microagents/` location).

**Evidence — smoketest stream (`data/eval/openhands_no_plugin/oh_smoke_s1/TutorialSneddon/events.jsonl`):**

The agent's first message (line 24, `"role": "user"`, `"source": "user"`) is:

```
Starting this session with file context.

File path: /workspace/task.txt

File contents:
--------------------
--- BEGIN SIMULATION SPECIFICATION ---
I am looking to simulate Sneddon's problem ...
--- END SIMULATION SPECIFICATION ---
--------------------
```

That is the entirety of the user-side context the agent receives. A literal grep across
the 2502-line `events.jsonl` for the primer's distinctive strings returns zero matches:

- `GEOS Expert` — 0 hits
- `PRIMARY RESPONSIBILITY` — 0 hits
- `GEOS Primer` — 0 hits
- `two-file pattern` — 0 hits
- `inputs/ directory` — 0 hits

The agent did `ls -la /workspace` once (line 1340), saw `AGENTS.md` listed, and
**never opened it**. The Sneddon TreeSim=0.843 result was produced **with no domain
primer at all** — no GEOS overview, no XML conventions, no file-organization rules,
no `# GEOS Primer` block.

CC, by contrast, passes the entire AGENTS.md (incl. `# GEOS Primer`) via
`--append-system-prompt`: see `src/runner/docker_cmd.py:174` and the
`build_system_prompt` path at `src/runner/prompts/__init__.py:80-129`.

**Why it invalidates the claim:**

The headline cross-harness comparison is "vanilla CC no-plugin vs OpenHands no-plugin
on the same primer". But OpenHands has *no primer at all*. This is the largest
possible parity break: ~20 KB of curated domain context (XML block ordering,
SI-units rules, common pitfalls, mesh examples, `inputs/` write rule, `/geos_lib`
read rules, GEOSDATA path mapping, docstring map…) is delivered to CC and silently
dropped for OpenHands. Any TreeSim delta this campaign produces — in either direction —
is dominated by primer presence/absence, not by harness shape.

That the smoketest still scored 0.843 is *more* alarming, not less: it suggests the
primer is not load-bearing on Sneddon, which means the cross-task variance from
"primer matters / doesn't" will be large and structurally biased.

**Recommended action:**
1. Halt the 17-task campaign.
2. Pick a real injection mechanism for OpenHands. Options, in order of code cost:
   (a) Concatenate `primer_text` into `task.txt` at the top, before
       `--- BEGIN SIMULATION SPECIFICATION ---`. Cheap, but mixes primer and task
       in a single user message — placement no longer matches CC's system-message
       slot. Document as "primer-as-user-prefix" in metadata.
   (b) Use OpenHands' microagent mechanism — drop the primer at
       `/workspace/.openhands/microagents/repo.md` (or whatever the v1.15 path is)
       and verify in `events.jsonl` that the contents flow into the system context.
   (c) Patch the OpenHands invocation to accept a `--system-prompt-file` analog if
       one exists in v1.15.
3. Re-run the smoketest. Verify primer presence by grepping for the same five
   distinctive strings. Re-record TreeSim. Only then proceed.
4. In `metadata.json`, record `primer_delivery_channel` (system / user-prefix /
   microagent) and `primer_in_context_verified` (bool, set by post-run grep on
   `events.jsonl`). The current `primer_sha256` field gives false confidence —
   the bytes were on disk but never read.

---

### P0 — OpenHands auto-injects keyword-matched "skills" into LLM context that CC has no analog for    [BLOCKER, invalidates Claim A]

**Location:** OpenHands runtime behavior; observed in
`data/eval/openhands_no_plugin/oh_smoke_s1/TutorialSneddon/events.jsonl:7-14` and
`/workspace/.home/.openhands/cache/skills/public-skills/`

**Evidence:**

The first agent event in the smoketest stream contains an `extended_content` block
appended by OpenHands' skill activation system:

```json
"activated_skills": ["linear"],
"extended_content": [{
  "text": "<EXTRA_INFO>\nThe following information has been included based on a
   keyword match for \"linear\".\nIt may or may not be relevant to the user's request.\n
   \nSkill location: /workspace/.home/.openhands/cache/skills/public-skills/skills/
   linear/SKILL.md\n...\n# Linear\n\n<IMPORTANT>\nBefore performing any Linear
   operations, check if the required environment variable is set: ...",
  ...
}]
```

The trigger is the substring `linear` in the task spec ("**linear** elastic isotropic
medium"). OpenHands matched it against a public-skills cache containing 40+ skills:

```
add-javadoc, add-skill, agent-creator, agent-memory, agent-sdk-builder,
azure-devops, bitbucket, code-review, code-simplifier, datadog, deno,
discord, docker, flarglebargle, frontend-design, github, github-pr-review,
gitlab, iterate, jupyter, kubernetes, learn-from-code-review, linear,
notion, npm, openhands-api, openhands-automation, openhands-sdk, pdflatex,
prd, release-notes, security, skill-creator, spark-version-upgrade, ssh,
swift-linux, theme-factory, uv, vercel
```

(plus 9 plugin bundles: `city-weather, cobol-modernization, magic-test,
migration-scoring, onboarding, openhands, pr-review, release-notes,
vulnerability-remediation`). All cached at container start by OpenHands' bootstrap.

The `linear` skill content is irrelevant on Sneddon (it instructs Linear API GraphQL
calls), but the *injection mechanism* fires unconditionally per task. Different tasks
have different keyword overlap → different skills injected → different system context.
This is non-deterministic, task-dependent, prompt-level enrichment that CC absolutely
does not have.

**Why it invalidates the claim:**

Across 17 tasks, the keyword matches will vary. Tasks with words like `docker`,
`github`, `notion`, `kubernetes`, `npm`, `security`, `iterate`, `jupyter`, `pdflatex`,
`vercel`, `discord`, `release-notes`, `openhands`, `release` are all live triggers
in the cache. We cannot reason about cross-task TreeSim patterns when the prompt
silently changes per task on the OpenHands side and not the CC side.

Worse: nothing in `metadata.json` records *which* skills activated for a given task,
so the campaign would not be reproducible or auditable after the fact.

**Recommended action:**
1. Disable skill auto-activation for the campaign. The cleanest path: prevent the
   bootstrap from populating `~/.openhands/cache/skills/`. Options:
   (a) Set an OpenHands env var that disables the public-skills bootstrap (check
       v1.15 docs — likely `OPENHANDS_DISABLE_PUBLIC_SKILLS=1` or similar).
   (b) Pre-create an empty `/workspace/.home/.openhands/cache/skills/` in
       `prepare_task_workspace` and write-protect it.
   (c) Patch the bootstrap during `Dockerfile.openhands` build.
2. After fix, smoketest again and grep `events.jsonl` for `"activated_skills"` —
   must be `[]`.
3. Add `activated_skills_list` to `status.json` so any future skill activation is
   visible at audit time.
4. If keeping skills active is desired (deliberate harness equipment), document it
   as a harness feature and stop calling this "parity with no-plugin CC".

---

### P1 — `task.txt` in workspace gives OpenHands a re-readable spec; CC cannot re-read its task    [degrades Claim A]

**Location:** `scripts/openhands_eval.py:155-157`; cf. `src/runner/orchestrator.py`
(no equivalent file write).

**Evidence — code:**
```python
task_text = build_task_prompt(instructions)
task_file = task_dir / "task.txt"
task_file.write_text(task_text)
```
And it's mounted into the container as `/workspace/task.txt` (workspace bind-mount,
`build_docker_cmd:184`), then referenced by `openhands ... -f /workspace/task.txt`
(`build_docker_cmd:208-209`).

CC's path: `src/runner/orchestrator.py:100` calls
`load_task_instructions(task_dir)` where `task_dir = experiments_dir / task_name`
(NOT `result_dir`). The instructions are then folded into the prompt argv passed
to `claude -p ... -- "{prompt}"` (`docker_cmd.py:196`). The CC workspace mount is
`result_dir`, which contains `inputs/`, `outputs/`, `.claude_home/`, `.uv_cache/`,
`claude_settings.json`, `claude_mcp_config.json`, `eval_metadata.json` — **no
task spec file**. The CC agent cannot Read the spec at any later turn.

**Why it (mildly) invalidates the claim:**

For long sessions where the agent forgets early instructions, OpenHands can `cat
/workspace/task.txt` to refresh; CC cannot. On a multi-XML task where the spec
lists 7 filenames + per-strategy mesh details, this is a real differential.
Likely small effect on a single-pass agent (the spec is in the first user turn
either way), but it compounds with the no-primer issue (P0 #1) — OpenHands gets a
re-readable spec but no primer; CC gets a non-re-readable spec but a primer.
These are not the "same starting context modulo harness".

**Recommended action:**
- Either delete `task.txt` from the workspace mount (move it into the container
  via stdin or argv) so the file isn't visible to the agent's own tools;
- Or accept the differential and pin it in metadata + the methods writeup. Do
  not call this exact parity.

---

### P1 — `prepare_task_workspace` does not wipe stale `inputs/*.xml`; re-runs with the same `--run-name` will be silently scored on a mix of old + new outputs    [invalidates Claim C robustness]

**Location:** `scripts/openhands_eval.py:136-159`

**Evidence:**
```python
def prepare_task_workspace(...):
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "inputs").mkdir(exist_ok=True)
    (task_dir / "outputs").mkdir(exist_ok=True)
    primer_path = task_dir / "AGENTS.md"
    primer_path.write_text(primer_text)
    ...
    task_file = task_dir / "task.txt"
    task_file.write_text(task_text)
```

Nothing wipes `inputs/`, `outputs/`, `events.jsonl`, `status.json`, `.openhands/`,
or `.home/`. `mkdir(exist_ok=True)` is a no-op when present.

If the operator re-runs:
```
python scripts/openhands_eval.py --run-name oh_test17_s1 --include TutorialSneddon ...
```
after a previous attempt that produced 7 XMLs, and the second attempt produces only
3 XMLs (or different XMLs with overlapping basenames), the scorer (`scripts/eval/
batch_evaluate.py`, invoked at line 542-552 with `--experiments-dir <output_dir>`)
will see whatever set is in `inputs/` after the second run completes. The agent
overwrites file-by-file via `FileEditorAction` with `command: create` (verified in
event stream); files from the first attempt that the second attempt does not
re-create remain.

**Why it matters:**
1. Multi-seed runs that re-use a base run name (e.g. seed 2 accidentally collides
   with seed 1's output dir) will silently mix outputs.
2. Retry-after-failure operationally: the first run timed out at 800s; the
   operator extends timeout to 1800s and re-runs the same task — result is now
   the union of both attempts' outputs.
3. The `metadata.json` is overwritten by the second run (line 360), but
   `events.jsonl` is also overwritten (line 402) so the audit trail of attempt 1
   is destroyed at the same time as the file-mixing happens.

**Recommended action:**
Before writing into `task_dir`, explicitly clear it:
```python
if task_dir.exists():
    shutil.rmtree(task_dir)
task_dir.mkdir(parents=True, exist_ok=False)
```
Or, more conservatively, refuse to start when `task_dir/inputs` is non-empty unless
`--force` is passed. CC's `orchestrator.py` has the same shape gap (it also uses
`mkdir(parents=True, exist_ok=True)` at lines 95-98), but CC's MCP/settings file
generation tends to fail-loud when re-running, and CC writes `.json` artifacts that
are diff-able. The OpenHands path lacks any such guardrail.

---

### P2 — `summarize_events` token-count silently zero; no error on malformed `--JSON Event--` stream    [degrades observability, not parity]

**Location:** `scripts/openhands_eval.py:217-278`

**Evidence — observed:** `status.json` for the smoketest reports `tokens_in: 0,
tokens_out: 0` while the agent clearly performed many LLM turns (71 events, 22
file edits, 9 terminal calls). The parser walks the stream, finds events with no
`usage` / `llm.usage` field (because OpenHands v1.15 doesn't surface usage in the
event format the parser expects), and silently sums zeros.

**Why it matters for the campaign:**
- Cost-per-task and tokens-per-task become uncomparable across harnesses (CC
  reports real numbers via the `analyze_event_stream_text` path —
  `runner/events.py`).
- If a future OpenHands version *does* surface usage but under a different key
  (e.g., `metrics.input_tokens`), the parser will still return 0 with no warning.
- More dangerous: the chunk-extraction loop swallows any `JSONDecodeError` and
  continues. If the marker `--JSON Event--` ever changes (likely between minor
  OpenHands versions), `n_events` silently drops to 0 and `tool_call_counts`
  becomes `{}`. Combined with the success classification at line 408
  (`if status == "success" and n_xml == 0: failed_no_outputs`), a run with
  non-zero XMLs still records `success` even if the entire trajectory is
  unparseable. The fairness-vs-CC story (which uses real tool counts) becomes
  asymmetric.

**Recommended action:**
- Log a warning when `n_events == 0` or `tokens_in == 0` after a non-trivial run
  (e.g., elapsed > 30s).
- Pin OpenHands version in `Dockerfile.openhands` (currently `uv tool install
  openhands` with no version pin — line 24) to avoid silent format drift between
  smoketest and full campaign. **This is a separate sub-issue** — see P3 below.

---

### P3 — OpenHands version unpinned in `Dockerfile.openhands`    [reproducibility risk]

**Location:** `run/Dockerfile.openhands:24`

**Evidence:**
```dockerfile
RUN mkdir -p /opt/uv/tools \
    && uv tool install openhands --python 3.12 \
    && chmod -R a+rX /opt/uv \
    && chmod a+rX /usr/local/bin/openhands /usr/local/bin/openhands-acp
```

No version constraint. PyPI publishes OpenHands releases frequently. The image
built today and the image rebuilt next week will likely differ in event-stream
format, default skill cache contents, system prompt template, and tool surface.

**Why it matters:**
- A multi-day campaign rebuilt midstream silently changes the harness.
- The smoketest result (TreeSim=0.843) was on whatever version `uv tool install`
  resolved on 2026-04-27. The pre-campaign rebuild may resolve a different
  version. The campaign result is then not comparable to the smoketest.

**Recommended action:**
- Pin to the smoketest's installed version. Inside the container:
  `pip show openhands | grep Version` (or `uv tool list`) → record version → bake
  into Dockerfile: `uv tool install openhands==1.15.X --python 3.12`.
- Record the resolved version in `metadata.json` (call `openhands --version`
  inside the container before each run, or once at smoketest, and assert match).

---

### P3 — Disallowed-tools parity not addressed for OpenHands tool surface    [documented limitation, not a code bug]

**Location:** `scripts/openhands_eval.py:166-210`; cf.
`src/runner/constants.py:48` `NATIVE_CLAUDE_DISALLOWED_TOOLS = ("Skill", "AskUserQuestion")`
and `docker_cmd.py:177-178`.

**Evidence:**
CC explicitly disallows `Skill` and `AskUserQuestion`. The OpenHands driver
disallows nothing. From the event stream we observe OpenHands exposes at minimum:
`task_tracker` (TaskTrackerAction), `terminal` (TerminalAction), `file_editor`
(FileEditorAction), `finish` (FinishAction). The `task_tracker` tool fires 3 times
in the Sneddon smoketest and is non-trivial (it builds a multi-step plan). Whether
it materially helps on this task is unclear, but it is structurally distinct from
anything CC has access to.

**Why it matters:**
- Tool surface differences are a known ~+0.05–0.10 fa0 effect on this project
  (`memory MEMORY.md`, RN-002 / XN-010). The OpenHands tool surface is wider
  than CC's. The "harness shape" claim conflates "different agent loop" with
  "different tool surface".
- This is P3 (not P1) only because the parity contract in D-009 was already
  somewhat hand-wavy on tool surface, and because it is documented somewhere.
  It needs to be called out explicitly in the methods section of any writeup.

**Recommended action:**
- Disable `task_tracker` if there is a flag (`--disable-tools task_tracker`?)
  to bring tool surfaces closer.
- Otherwise document explicitly: "OpenHands harness exposes a built-in
  task-tracker tool with no CC analogue. Tool-surface confound is uncontrolled."

---

## Clean checks (verified OK)

- **Contamination filter parity (P0 attack 1.b in focus text).** `get_blocked_files_for_task`
  is called with the same arguments as CC's path (`scripts/openhands_eval.py:319-321` vs
  `src/runner/orchestrator.py:138-144`); same `geos_source_dir`, same task id. The
  smoketest `metadata.json` blocked list contains 11 sneddon variants — matches what
  CC's filter produces. No `extra_blocked_xml_basenames` is passed by either path for
  the no-plugin baseline (only used for memory-build runs); parity holds.
- **Filtered GEOS lifecycle.** `create_filtered_geos_copy` and `cleanup_filtered_geos_copy`
  used identically; `cleanup` flag set in the same shape; `finally` block guarantees
  cleanup. `tmp_geos_parent` defaults to `TEMP_GEOS_PARENT` (line 447); the operator must
  pass `--tmp-geos-parent` to use a matt-owned dir, which the smoketest did
  (`/data/shared/geophysics_agent_data/data/eval/tmp_geos_matt/...` per
  `metadata.json`). Documented hazard, not a code bug.
- **Case-insensitive blocking.** `contamination.py:266, 274` lowercases both sides;
  the agent's `Sneddon_base.xml` (mixed case) cannot read GT `sneddon_base.xml` (lower
  case in blocked list). The agent's matching capitalized output filenames are inferred
  from the spec's `XML files to create:` line, not from filesystem leakage.
- **API key handling.** `os.environ.get(args.api_key_env, "").strip()` then
  `if not api_key and not args.dry_run: ... return 2` (lines 465-471). Empty-string and
  unset both error out. The earlier `try: load_dotenv() except ImportError: pass`
  (lines 60-63) silently no-ops if dotenv is missing, but downstream error path still
  catches missing keys. OK.
- **Output-dir collision avoidance (Claim B / non-disruption).** Outputs go to
  `data/eval/openhands_no_plugin/<run_name>/<task>/` — disjoint from CC's
  `data/eval/claude_code_no_plugin/<run_name>/<task>/`. No shared mutable state.
- **`src/runner/*` not modified.** Confirmed by reading all five referenced runner
  files; the only cross-call is `from runner.contamination import ...` and
  `from runner.constants import ...`, both pure imports of non-mutated state.
- **Per-task workspace isolation.** Each task gets its own bind-mounted directory.
  The `OPENHANDS_PERSISTENCE_DIR=/workspace/.openhands` setting (line 188) keeps
  OpenHands' settings inside the per-task workspace, not at host `~/.openhands`.
  Cross-task contamination via OpenHands' own state is *probably* prevented (the
  workspace is fresh per-task, modulo the stale-input issue P1 above), but see P0 #2
  re: per-task skill cache.
- **Model-name and base-URL routing.** `openrouter/minimax/minimax-m2.7` (LiteLLM
  prefix form, line 105) and CC's `minimax/minimax-m2.7` (line `constants.py:33`)
  are conventional duals. CC's `ANTHROPIC_BASE_URL=https://openrouter.ai/api`
  (`docker_cmd.py:208-211`) and OpenHands' `LLM_BASE_URL=https://openrouter.ai/api/v1`
  (line 106) are the OpenRouter Anthropic-compatible vs OpenAI-compatible endpoints.
  Same upstream provider; routing to the same `minimax/minimax-m2.7` model on
  OpenRouter is safe to assume modulo the provider's own router. **Not a P-finding,
  but flag in metadata as `routing_path: anthropic-compat` vs `openai-compat` for
  audit.**

## Overall assessment

- **Blocker for campaign?** **YES.** P0 #1 (no primer reaches OpenHands) and
  P0 #2 (skill auto-injection from public-skills cache) each independently
  invalidate the parity claim. Running the 17-task campaign now would burn
  compute on a comparison whose headline confound (presence/absence of
  ~20 KB of curated GEOS context, plus task-dependent random skill blobs)
  swamps the harness-shape signal it is meant to measure.
- **Confidence headline claim is valid, conditional on P1 fixes:** **low.**
  Even after P0 fixes, P1 (re-readable `task.txt`) and P3 (tool surface,
  unpinned version) introduce smaller but real confounds. The honest framing
  for any cross-harness number is "different harness AND different tool surface
  AND different spec re-readability"; the comparison should be presented as a
  triangulation, not a controlled experiment.
- **Most likely undiscovered failure mode I might still have missed:**
  OpenHands may ship default microagents/system-prompt content I didn't
  inspect. The system prompt for OpenHands is built by the OpenHands runtime,
  not by us, and I have not read it line-by-line. It may contain instructions
  like "always use task_tracker before editing" or "always plan first" that
  systematically change agent behavior in ways CC doesn't have. To check:
  dump the first system message OpenHands sends to LiteLLM (intercept at the
  LLM call site or run with `LITELLM_LOG=DEBUG`) and diff against CC's
  `--append-system-prompt` payload. Until that's done, the harness-shape
  attribution is unfalsifiable.

---

## Copilot Responses to Findings

Written 2026-04-27 immediately after reading RN-004, before any fix work.

| # | Finding | Severity | Response | Details |
|---|---|---|---|---|
| 1 | AGENTS.md primer never reaches the model | P0 | **accept → fix** | The smoketest "success" was a false positive. Writing AGENTS.md to the workspace does NOT auto-inject it into OpenHands' system context — `load_project_skills` looks for specific paths/filenames I misread. Fix: prepend `primer_text` to the task prompt (above `--- BEGIN SIMULATION SPECIFICATION ---`) so it lands in the first user message. Verify by post-run grep on `events.jsonl` for 5 distinctive primer strings (e.g. `GEOS Expert`, `# GEOS Primer`, `PRIMARY RESPONSIBILITY`, `two-file pattern`, `inputs/ directory`) — assertion failure aborts the run. Record `primer_in_context_verified: true/false` in `status.json`. Note placement differential vs CC (system-slot vs user-prefix) in metadata + XN-016. |
| 2 | OpenHands auto-injects keyword-matched public skills | P0 | **accept → fix** | Catastrophic confound — Sneddon got Linear API GraphQL injected for matching the substring "linear elastic". Fix: disable skill bootstrap. Approach: build the image with the public-skills cache pre-emptied + write-protected; also set `OPENHANDS_DISABLE_DEFAULT_SKILLS=1` (or whatever the v1.15 env var is — to be verified empirically) defensively. Re-smoketest and assert `activated_skills == []` in every event; assertion failure aborts. Record `activated_skills` list in `status.json` for every run for permanent audit trail. |
| 3 | `task.txt` in workspace is re-readable; CC's spec is not | P1 | **accept → fix** | After fix for finding #1, the primer + spec live in the user message. Switch from `-f /workspace/task.txt` to `--task "<inline>"` and drop `task.txt` from the workspace. Verify by `ls /workspace` not showing the file in event stream. |
| 4 | `prepare_task_workspace` does not wipe stale `inputs/*.xml` | P1 | **accept → fix** | Add `shutil.rmtree(task_dir, ignore_errors=True)` before `mkdir`. Trivial. CC has the same shape gap noted by reviewer; not in scope to fix CC. |
| 5 | `summarize_events` silently zeroes token counts | P2 | **accept → limitation + partial fix** | Already documented in XN-016 §"Bugs found + fixed" #4. Add explicit warning to `status.json` when `elapsed > 30s and (n_events == 0 or tokens_in == 0)`. Token-count cross-harness comparison already flagged as future work; not blocking the TreeSim comparison. |
| 6 | OpenHands version unpinned in `Dockerfile.openhands` | P3 | **accept → fix** | Pin to 1.15.0 (the smoketest version). Add `openhands --version` capture into `metadata.json`. |
| 7 | Tool-surface parity gap (task_tracker, finish, etc.) | P3 | **accept → limitation** | Tool surface differs between CC's no-plugin set and OpenHands' default set. Document explicitly in XN-016 + paper methods: "OpenHands ships built-in task-tracker and finish tools that CC does not expose; tool-surface confound is uncontrolled." Investigate whether OpenHands has a `--disable-tool` flag in v1.15; if yes, disable task_tracker for tighter parity. If no, accept and document. |
| 8 | OpenHands' built-in system prompt may contain task-relevant directives CC lacks | (unflagged, parting note) | **accept → fix (verification)** | Before campaign, dump the first system message OpenHands sends to LiteLLM (run smoketest with `LITELLM_LOG=DEBUG` or instrument the wrapper). Diff against CC's `--append-system-prompt` payload. Document any directives that materially shape agent behavior. If OpenHands' system prompt contains task-relevant directives CC lacks (e.g. "always plan first"), the cross-harness comparison must be framed as "harness package, including its built-in prompt" rather than "agent loop alone." |

**Gate decision: HALT 17-task campaign.** Findings #1, #2, #3, #4, #6, #8 must be fixed and re-smoketested before any further runs. Finding #5 + #7 documented as limitations, not blockers.

**Plan:**
1. Empty + write-protect the public-skills cache in `Dockerfile.openhands`.
2. Pin openhands to a specific version.
3. Switch driver to inline primer + inline task via `--task`, drop workspace `task.txt`.
4. Wipe task_dir on prepare.
5. Verify primer-in-context + zero-skill-activation by post-run grep; abort run on failure; record both in `status.json`.
6. Investigate OpenHands' default tool-disable flag and built-in system prompt content.
7. Re-smoketest 1 task. If green, re-invoke `/adversarial-review` on the patched runner before the 17-task campaign.

The smoketest "TreeSim=0.843" result is now invalidated as evidence of harness readiness — it was a primer-less, skill-contaminated run. Treat as a debugging trace, not as a baseline data point.


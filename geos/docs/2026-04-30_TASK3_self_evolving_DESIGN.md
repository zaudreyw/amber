# Task 3 design: Self-evolving agent

*2026-04-30 — design doc for Task 3 of overnight session.
Per `misc/apr30_overnight_instructions.md` §"Idea 2".*

## Goal

Test whether an agent that can rewrite its own plugin (memories +
skills + subagents) self-improves across the 17 v2 test tasks.

## Design decisions (committed early per overnight constraint)

### Init: BLANK plugin

Per overnight: "my hunch is that you can plot growth more easily if
you start from blank but that's just my bias". Agree.

The agent starts with:
- `plugin_evolving/v0/` containing only an absolute-min primer
  (`GEOS_PRIMER_absolute_min.md` — the 5-line "GEOS source at
  /geos_lib/, write XML to /workspace/inputs/")
- An empty `agents/` dir (no subagents)
- An empty `skills/` dir (no skills)
- An empty `memory/` dir (no cheatsheets)
- The xmllint hook + MCP tool + verify_outputs.py (these are
  hand-coded xmllint validation, not "skill" content the agent
  could create or improve — they're scaffolding the agent uses)

### Schedule: ONLINE periodic update every 6 tasks

Per overnight:
> after every 6 tasks: reflect on the previous 6 trajectories,
> make any self-updates to the custom plugin package; do the next
> 6 tasks with the updated plugin package

17 tasks → 3 update windows: tasks 1-6, 7-12, 13-17.

Sequence:
- v0 = blank (initial)
- run tasks 1-6 with v0 → reflect → produce v1 = v0 + agent edits
- run tasks 7-12 with v1 → reflect → produce v2
- run tasks 13-17 with v2 → reflect → produce v3 (final)

### Versioning

Each version is a separate filesystem snapshot:
`/data/shared/.../self_evolving_2026-04-30/plugin_v{N}/`

A `version_log.jsonl` at `/data/shared/.../self_evolving_2026-04-30/`
tracks (version, timestamp, parent_version, summary_of_edits).

Storing **on /data** (not /home) — heavy artifact policy.

## What the agent can edit

The agent can produce new files in 4 categories. Each goes into the
plugin's appropriate subdir.

| Category | Path | Format | What it is |
|---|---|---|---|
| Memory | `plugin_v{N}/memory/cheatsheet.md` | markdown | Free-form notes / lessons / patterns |
| Skills | `plugin_v{N}/skills/<name>.md` | YAML frontmatter + body | Procedural instructions invokable as `/<name>` |
| Subagents | `plugin_v{N}/agents/<name>.md` | YAML frontmatter (description, tools) + system prompt | Delegatable role |
| Primer extension | `plugin_v{N}/PRIMER.md` | markdown | Replaces or extends the absolute-min primer |

### Reference docs (for the agent's reflection step)

- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/agent-sdk/custom-tools

The reflection prompt will include enough excerpt of these docs that
the agent knows what file formats to produce.

## The reflection step

Between rounds, a separate "reflection" agent invocation runs:

**Inputs**:
- The 6 most recent trajectories' events.jsonl (or compacted summary)
- Their treesim scores against GT
- The current `plugin_v{N}` contents
- The 4-format menu of what's editable

**Tools available**:
- Read (current plugin contents, recent trajectories)
- Write (proposes new files in `plugin_v{N+1}/`)
- Bash (run a hygiene check on proposed memory)

**Output**: a new `plugin_v{N+1}/` directory.

**Prompt skeleton** (will refine in implementation):

> You are improving a Claude Code plugin that authors GEOS XML.
> Recent run results (6 tasks):
> ...
> Current plugin (`plugin_v{N}`):
> ...
> Reflect on what would have helped the agent author better XML.
> You may produce ANY of the following 4 file types in plugin_v{N+1}/:
> 1. memory/cheatsheet.md (free-form lessons; budget ≤2K tokens total)
> 2. skills/<name>.md (...)
> 3. agents/<name>.md (subagent definition; if you create one, the
>    next runs may invoke it via Agent(subagent_type=name))
> 4. PRIMER.md (replaces the system primer)
>
> Be conservative — only add content that addresses concrete failures
> or inefficiencies you observed. Output a list of files you'd write
> with their content.

The reflection agent uses DSv4-flash (same model). Cost per reflection
~$0.10. 3 reflection windows total.

## Comparison plan

| Cell | Description | Cells to compare |
|---|---|---|
| **SE-blank** | Self-evolving from blank, online periodic | vs C0 (vanilla, blank-ish) and C6 (human-best with xmllint) |
| **SE-self-prior** | Per-version comparison: does v3 > v2 > v1 > v0? | (internal, observed during run) |

The "growth" claim: SE_v3 should outperform SE_v0. The "good"
claim: SE_v3 should outperform C0 (or even C6).

## Implementation plan

### Component 1: Initial plugin v0

Manually create:
- `plugin_evolving/v0/PRIMER.md` (just the abs-min primer content)
- `plugin_evolving/v0/agents/` (empty)
- `plugin_evolving/v0/skills/` (empty)
- `plugin_evolving/v0/memory/` (empty)
- `plugin_evolving/v0/.claude-plugin/plugin.json` (minimal manifest;
  may need to declare empty subagents/skills lists)
- Copy xmllint hook + MCP into v0 (these are scaffolding, not
  agent-authored content)

### Component 2: Round runner

`scripts/self_evolving/run_round.py`:
- Args: `--plugin-version N --tasks TASK_LIST`
- For each task:
  - Run with `--plugin-dir plugin_evolving/v{N}/`, primer = `plugin_v{N}/PRIMER.md`
  - Same xmllint hook, no RAG, no other harness mods
- Output to `data/eval/self_evolving/round_{N}/`

### Component 3: Reflection driver

`scripts/self_evolving/reflect.py`:
- Args: `--from-version N --trajectories DIR --treesim-evals DIR`
- Constructs prompt with trajectory summaries + treesim scores
- Calls DSv4-flash via direct API
- Parses agent's file proposals from response
- Writes them to `plugin_evolving/v{N+1}/`
- Validates structure (skill files have frontmatter, etc.)
- Updates `version_log.jsonl`

### Component 4: Orchestrator

`scripts/self_evolving/run_full.sh`:
- For round in 0..2:
  - run_round on tasks [round*6 : (round+1)*6]
  - reflect from version round → version round+1
- run_round on tasks 12-16 with version 3
- Score all rounds
- Write summary

### Token / time budget

- 17 tasks × ~6 min = ~100 min total task time
- 3 reflections × ~1 min = ~3 min
- Wall: ~105 min (sequential per round, not parallel due to round dependency)
- Cost: 17 × $0.07 + 3 × $0.10 = ~$1.50

(Far cheaper than the rest of the campaign.)

## Validation

If self-evolving v3 ≥ v0 by ≥0.05pp on the late-round tasks, that's
positive growth. If v3 underperforms v0, the agent's edits are net
harmful (still useful negative result).

Note: tasks 13-17 are "test set" for v3, but v3 was created using
v2's reflection on tasks 1-12. Per-round comparisons need
"on-distribution" controls — we'll compare round-3-tasks (13-17)
under v3 vs v0 to isolate the version effect.

## Risk: agent generates broken files

The reflection prompt enforces the 4-format menu, but the agent
might still produce malformed content. Mitigation:
- Hygiene check after each reflection: parse YAML frontmatter, verify
  skill files have valid markdown, verify agent files have non-empty
  system prompt sections.
- If hygiene fails, retry reflection once. If still bad, freeze
  plugin at current version and continue (log the failure).

## Risk: agent corrupts existing plugin

The agent only writes to `plugin_v{N+1}/`. The previous version is
read-only (filesystem-immutable for that bash session — set chmod
on v{N} after creation).

## Honest limitations

- 3 reflection rounds is small; might not show convergence.
- Single seed per round (cost-bound). Within-round variance is
  unmeasured.
- "Skills" in CC are a richer mechanism than markdown; the agent
  may produce skills the runtime can't actually invoke. We accept
  this and look for any positive growth signal.
- The reflection agent shares the same backbone (DSv4-flash) as the
  task agent — there's no "wisdom transfer from a stronger model"
  in this setup.

## What this answers

- **Can the agent self-improve from a blank slate?** Compare v3 vs v0.
- **Does it converge or oscillate?** Compare v1, v2, v3 trajectories.
- **Which edit types help most?** Inspect what the agent wrote at each
  reflection step (memory? skills? subagents? primer?).
- **Does it match or beat human design?** Compare v3 to C6 (best
  hand-designed cell from Task 0).

## What this doesn't answer (out of scope)

- Cross-model self-evolution (would need different backbone for
  reflection)
- Online single-task updates (this is per-batch, not per-task)
- Catastrophic forgetting (only 3 rounds, no test of older tasks
  re-evaluated under newer versions)

## Time budget

- Component 1: 15 min
- Component 2: 30 min
- Component 3: 45 min (most complex — file parsing, hygiene)
- Component 4: 10 min
- Smoketest 1 round on 2 tasks: 15 min
- Full 3-round run: 105 min (background)
- Analysis + writeup: 30 min

Total: ~3h, mostly background time.

## Status

Design committed. Will begin implementation after Task 1 (MemP)
writeup is done and Task 2 (orchestrator P1 fix re-run) is launched
in background.

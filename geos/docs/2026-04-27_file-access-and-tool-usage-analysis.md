# 2026-04-27 — Cross-run file-access and tool-usage analysis

## TL;DR

Two analysis scripts now exist to characterize agent behavior across the full
data tree (`scripts/analysis/analyze_file_access.py` and
`scripts/analysis/analyze_tool_usage.py`). I ran them across 908 task runs in
18 agent_keys. Three findings stand out for the paper:

1. **The chromadb gap creates a behavioral asymmetry.** Vanilla CC, lacking
   RAG, falls back to filesystem search and reads non-sphinx `.rst` files
   that plugin agents almost never see (31 of 36 such reads come from
   `claude_code_no_plugin`, only 5 from any plugin variant).
2. **`xmllint` has been invoked 91 times across 87 task-runs in 15
   agent_keys** without us ever surfacing it. The agent already partially
   knows about it. Wiring it into a hook or tool will amplify a behavior
   already in the model prior, not introduce something foreign.
3. **The status.json `per_tool_counts` over-counts.** Stale plugin calls (e.g.
   on vanilla CC), `AskUserQuestion` (always errors), and `WebFetch` (network
   blocked) all inflate `total_tool_calls` and `plugin_tool_calls`. The
   analysis script computes `succeeded_count = attempted − errored` from
   events.jsonl as the source of truth for fair comparisons.

## Outputs

`scripts/analysis/out/file_access/`:
- `file_access_per_run.csv` — long, ~7.7k rows: one per (agent, run, task,
  file, tool surface).
- `file_access_per_task.csv` — wide per-task counts by category.
- `file_access_summary.csv` — per-(agent, run, model) rollup.
- `file_access_glob_grep.csv` — Glob/Grep patterns + paths.
- `file_access_summary.md` — narrative.

`scripts/analysis/out/tool_usage/`:
- `tool_usage_per_run.csv` — ~7.5k rows: per (agent, run, task, tool) with
  attempted, errored.
- `tool_usage_by_agent.csv` — long, with succeeded, error_rate.
- `tool_usage_by_agent_pivot_attempted.csv`,
  `tool_usage_by_agent_pivot_succeeded.csv` — wide, agents × tools.
- `tool_usage_discrepancies.csv` — 25 rows where status.json and events.jsonl
  disagree (small; events.jsonl is source of truth in our outputs).
- `tool_usage_summary.md` — narrative.

Both scripts accept `--agent-keys`, `--max-tasks-per-run`, `--out-dir`,
`--eval-root`. Run from the repo root or anywhere; defaults point to
`/home/matt/sci/repo3/data/eval`.

## Headline numbers

### Non-sphinx rst reads

21 distinct files, 36 reads total. Top 5:
1. `src/coreComponents/constitutive/docs/solid/DruckerPrager.rst` — 4 reads
   (3 vanilla, 1 gmem)
2. `src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst` — 4 (all vanilla)
3. `src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst` — 4 (all vanilla)
4. `src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst` — 3 (all vanilla)
5. `src/coreComponents/constitutive/docs/solid/SolidModels.rst` — 2 (1 vanilla, 1 gmem)

By agent variant: **31 of 36 (86%) come from `claude_code_no_plugin`**. The
plugin variants (`m1u`, `m4g`, `mem`, `placebo`, etc.) almost never wander.

This is the asymmetry: when RAG is available, the agent uses RAG and stays
inside whatever the indexer covered (in our case `src/docs/sphinx/` only).
When RAG is absent, the agent falls back to filesystem search and discovers
constitutive-model docs scattered under `src/coreComponents/*/docs/`. These
docs are exactly the ones that would help with the constitutive-law tasks
(DruckerPrager, ModifiedCamClay, ExtendedDruckerPrager) we evaluate on.

### `xmllint` invocations

91 invocations across 87 task-runs spanning 15 of 18 agent_keys.
Leaders: `claude_code_no_plugin` (31), `claude_code_repo3_plugin` (13).
Almost every plugin variant attempts xmllint at least once.

So the agent already knows the validator exists. The gain from baking it into
a hook isn't novelty — it's the consistent application that the agent
otherwise reaches for sporadically.

### Top-read XML examples (paper §"what the agent learns from")

| Rank | File | Reads |
|---|---|---:|
| 1 | `inputFiles/triaxialDriver/triaxialDriver_base.xml` | 141 |
| 2 | `inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml` | 103 |
| 3 | `inputFiles/solidMechanics/DruckerPragerWellbore_base.xml` | 66 |
| 4 | `inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml` | 53 |
| 5 | `inputFiles/poromechanics/PoroElastic_Mandel_base.xml` | 49 |
| 6 | `inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml` | 49 |
| 7 | `inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml` | 47 |
| 8 | `inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml` | 45 |
| 9 | `inputFiles/wellbore/ThermoPoroElasticWellbore_base.xml` | 43 |
| 10 | `inputFiles/poromechanics/PoroElasticWellbore_base.xml` | 41 |

Heavy concentration on `triaxialDriver/` and `solidMechanics/` — these are
the constitutive-law tasks. The fact that vanilla CC reads constitutive docs
that plugin variants miss is consistent with this.

### Per-agent tool-usage snapshot

| agent | n_tasks | attempted | errored | mean/task | err_rate |
|---|---:|---:|---:|---:|---:|
| `claude_code_no_plugin` | 46 | 6284 | 270 | 136.6 | 0.043 |
| `claude_code_repo3_plugin` | 17 | 3740 | 59 | 220.0 | 0.016 |
| `claude_code_repo3_plugin_gmemsilent` | 17 | 2571 | 28 | 151.2 | 0.011 |
| `claude_code_repo3_plugin_m_placebo` | 17 | 1538 | 23 | 90.5 | 0.015 |
| `claude_code_repo3_plugin_gmem` | 17 | 1327 | 46 | 78.1 | 0.035 |

Full 18-row table in `tool_usage_summary.md`. The headline is variance: even
within plugin variants, mean tool calls per task ranges from ~78 to ~220.
That's a 3× spread that probably reflects how aggressively each
prompt/cheatsheet pushes the agent to over- or under-explore.

### Other notable per-tool patterns

- `mcp__geos-rag__search_*`: error rate ~0.5% when actually present —
  reliable.
- `AskUserQuestion`: 100% errored (15/15). Runner doesn't support
  interactive prompts; agent emits them and they fail. We should either
  disable the tool or add a stub that no-ops.
- `WebFetch`: 70.8% errored (17/24). Network-blocked container.
- `claude_code_no_plugin` `mcp__geos-rag__search_navigator`: **49 attempted,
  100% errored.** This is the stale-plugin-call bug captured today (see
  `2026-04-27_vanilla-cc-stale-plugin-call-bug.md`).

## Implications for the paper

- The "plugin vs vanilla" comparison has a structural confound we hadn't
  named: **plugin variants are ABLE to find docs only inside whatever the
  indexer covered.** If the indexer is path-scoped (which it is — see
  `xmllint_validation.md`), the plugin variant has *less* effective doc
  surface than vanilla on tasks whose authoritative docs live outside the
  indexed tree. Some of the headline plugin-vs-vanilla deltas may be partly
  compensating for, partly fighting against, this asymmetry. Worth a section.
- The "what does the agent read?" tables (top-N rst, top-N xml) are
  paper-ready figures; we should produce them for the camera-ready.
- We can now measure: *given a fixed model and prompt, how does file-access
  pattern change with primer / cheatsheet / RAG ablations?* The data are
  already on disk; running `analyze_file_access.py` with `--agent-keys`
  filters to whichever subset answers a specific question.

## Pointers

- Scripts: `scripts/analysis/analyze_file_access.py`,
  `scripts/analysis/analyze_tool_usage.py`.
- Outputs: `scripts/analysis/out/`.
- Related findings: `xmllint_validation.md`,
  `2026-04-27_vanilla-cc-stale-plugin-call-bug.md`.
- Investigation transcript: this conversation, 2026-04-27.

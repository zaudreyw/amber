# Sub-agent orchestrator handoff (autonomous sleep cycle, 2026-04-27)

**TL;DR**: Built a working sub-agent orchestrator for GEOS XML authoring; uses Claude Code's built-in subagents distributed via plugin; smoketest validated the architecture on Mandel; 5-task DSv4-flash campaign launched, results pending in `data/eval/orchestrator_dsv4flash/orch_dsv4_5task_s1/`.

## What you should read first

1. **Architecture rationale**: `docs/2026-04-27_subagent-architecture-geos.md` — the pre-sleep design analysis.
2. **Implementation decision**: `.copilot/decisions/D-010_subagent-orchestrator.md` — what got built and why.
3. **Findings so far**: `docs/XN-017_subagent-orchestrator-results.md` — smoketest iteration story + (when scoring completes) the 5-task table.
4. **Working state**: `.copilot/checkpoint.md` — cycle-by-cycle progress.

## What got built

**`plugin_orchestrator/`** — new plugin alongside the existing `plugin/`. Self-contained:
- `.claude-plugin/plugin.json` — manifest with the geos-rag MCP server.
- `agents/{geos-mesh,geos-regions-constitutive,geos-solvers,geos-drivers,geos-events}.md` — 5 subagent definitions with YAML frontmatter (Claude Code's built-in subagent format).
- `primers/<segment>.md` — condensed Sphinx docs per segment.
- `schema_slices/*.xsd` — auto-extracted complexType slices from `data/GEOS/.../schema.xsd` via `scripts/extract_schema_slice.py`.
- `ORCHESTRATOR_SYSTEM.md` — the main thread's strict numbered workflow, appended to system prompt at runtime.
- `scripts/geos_rag_mcp.py`, `hooks/verify_outputs.py` — copies of the existing plugin's MCP server and Stop hook so this plugin is self-contained.

**`scripts/orchestrator/run_orchestrator_eval.py`** — standalone runner (parallel to `src/runner.cli`). Imports read-only utilities from `src/runner` for shared logic (filtered GEOS copy, blocklist, prompts) but does NOT modify any file under `src/runner/`. **Per your constraint, the existing OpenHands campaign and the standard runner are unaffected.**

Both plugins mount into the container — `plugin_orchestrator/` at `/plugins/orchestrator` (provides the agents/ directory loaded via `--plugin-dir`); `plugin/` at `/plugins/repo3` (provides the geos-rag MCP server via `--mcp-config`).

DSv4-flash direct: confirmed the Anthropic-compatible endpoint at `https://api.deepseek.com/anthropic`. Runner uses it by default with `ANTHROPIC_API_KEY=$DEEPSEEK_API_KEY` and `--model deepseek-v4-flash`. Fallback flags (`--model`, `--api-base`, `--api-key-env`) make it a one-line swap to OpenRouter for minimax-m2.7 or deepseek-v3.2.

## Toggleable

To run the orchestrator: `bash scripts/orchestrator/launch_5task.sh <run_name>` or `bash scripts/orchestrator/launch_full_17.sh <run_name>`.
To run the standard agent (existing path): `python -m src.runner.cli ...` exactly as before. **Nothing changed in the existing path.**

## Smoketest outcome

Three iterations needed before the model actually delegated:
1. **v1** (Sneddon, gentle prompt + Write enabled): orchestrator wrote XML directly via Write — zero subagent calls.
2. **v2** (Sneddon, Write disabled but free-form): orchestrator copied 6 bootstrap variants instead of one — zero subagent calls.
3. **v3** (Mandel, **strict numbered phases + anti-pattern hall of shame**): all 5 subagents spawned, 4 of 5 segments cleanly spliced. Container was killed (exit 143 SIGTERM) at ~933 s elapsed (well under 1800 s timeout) before the events-subagent finished — final XML missing `<Events>`. Likely transient (24+ docker containers visible at peak, possible OOM); did not reproduce in the smoketest run.

Generated XML quality on Mandel (when v3 reached the splice phase) was **canonical poromechanics**: `SinglePhasePoromechanics` composite with correct sub-solver cross-refs, `PorousElasticIsotropic` material composite, all 6 BC boxes, 11 FieldSpecifications with correct objectPath/fieldName/component, verbatim TableFunction values from spec. This is the kind of XML the prior monolithic agent occasionally fails on per XN-008.

## What's running now

`orch_dsv4_5task_s1` campaign (background `bx2gfikms`):
- Tasks: TutorialSneddon, ExampleMandel, TutorialPoroelasticity, AdvancedExampleDruckerPrager, buckleyLeverettProblem.
- 2 workers, 2400 s/task timeout.
- Started ~13:33 Z, expected wall ~40-50 min.

## When the campaign finishes

Run:
```bash
bash scripts/orchestrator/score_run.sh orch_dsv4_5task_s1
```

Then compare against the existing vanilla DSv4-flash baseline:
```bash
python -m scripts.orchestrator.compare_with_baseline \
    --orchestrator data/eval/results/orch_dsv4_5task_s1/orchestrator_dsv4flash/_summary.json \
    --baseline    data/eval/results/dsv4flash_direct_s1/claude_code_no_plugin/_summary.json \
    --baseline-label "vanilla DSv4-flash" \
    --orch-label    "orchestrator DSv4-flash" \
    --out           data/eval/results/orch_dsv4_5task_s1/comparison.md
```

Then optionally `python -m scripts.orchestrator.analyze_run --run-dir data/eval/orchestrator_dsv4flash/orch_dsv4_5task_s1` for token + tool-use breakdown.

If the 5-task results are encouraging, queue the full 17 with:
```bash
bash scripts/orchestrator/launch_full_17.sh orch_dsv4_full_s1
```

## Constraints honored

- **Did not modify** `src/runner/*`, `run/AGENTS.md`, `scripts/eval/*`, `data/eval/claude_code_*`, `data/eval/openhands*`, or `plugin/`.
- All new code goes to `plugin_orchestrator/`, `scripts/orchestrator/`, new `data/eval/orchestrator_dsv4flash/` subdirs.
- New design memo at `.copilot/decisions/D-010_*.md`. Research log appended to with LOG-2026-04-27-3, -4, -5.

## Open issues / things to watch

1. **Container kill at 933 s in v3.** Cause unknown. If 5-task campaign tasks also die mid-way (multiple exit-143 statuses), suspect OOM and reduce `--workers` from 2 to 1.
2. **Per-subagent runtime is long** (~5–10 min/subagent on DSv4-flash). Full 17-task at 2 workers projects to ~4-5 h.
3. **The Solvers schema slice is 86 KB** — heavy. If the solvers subagent over-loads context, consider splitting per physics family (SolidMechanics, SinglePhaseFlow, Poromechanics, …) as designed for v2.
4. **No adversarial review of orchestrator code yet** (deviation from `/adversarial-review` gate). Recommend running it before declaring results validated.

## What I did NOT do

- Did NOT launch the full 17-task campaign (deferred until 5-task validates).
- Did NOT score against E03 (plugin+ds-v3.2 via OR) — that's a different vector_db_dir + different model and would muddy the model-vs-orchestrator delta. The vanilla DSv4-flash baseline is the cleaner comparison.
- Did NOT iterate further on the v3 events failure — moved to 5-task to use sleep budget for results, not for smoketest tuning.
- Did NOT implement Phase-2/Phase-4 parallelism (MVP scope: 5 serial subagents).

---
id: D-010
title: Sub-agent orchestrator for GEOS XML authoring
date: 2026-04-27
status: implementing
dag_nodes: [I14, E25]
links:
  derived_from: [docs/2026-04-27_subagent-architecture-geos.md]
  related_to: [XN-001, XN-005, XN-008, XN-016]
---

# D-010 — Sub-agent orchestrator for GEOS XML authoring

## Decision

Build a parallel, toggleable orchestrator that decomposes GEOS XML authoring into per-segment Claude Code subagents (built-in subagent system, distributed via plugin). Test on the existing 17-task v2 set with DSv4-flash direct (Anthropic-format endpoint at `https://api.deepseek.com/anthropic`). Fall back to minimax-m2.7 via OpenRouter if DeepSeek runs out.

## Why

Three motivations from the user, ranked by expected payoff:

1. **Faithful documentation use (biggest expected win, but uncertain)**
   The current monolithic agent leans on examples and underuses the GEOS docs (XN-001, XN-008 trajectory analyses). A focused per-segment subagent that carries only its segment's primer + schema slice should *make* the model read the docs rather than skim past them. This is the qualitative argument; the experiment will say whether it shows up in TreeSim.
2. **Token efficiency / less context rot (most measurable)**
   Each subagent gets ~4–7k tokens of focused context vs. a monolithic agent's growing accumulation. Per-call input is much smaller, which is what context-rot studies say matters.
3. **Wall-clock latency (smallest)**
   The dependency graph forces 4–5 serial phases. Optimistic 1.3–1.8× speedup. Mostly free with the design.

## Architecture

The detailed segment dependency analysis is in `docs/2026-04-27_subagent-architecture-geos.md`. Summary:

- **9 segments** (Geometry folds into Mesh, NumericalMethods folds into Solvers).
- **6-phase pipeline**: bootstrap → mesh → (regions+constitutive parallel) → solvers → (functions+fieldspec+tasks+outputs parallel) → events → splice + xmllint.
- **Bootstrap from a similar example** dissolves cross-segment naming concerns. Subagents receive a frozen name registry and a "do not rename" contract.
- **Subagents return text, orchestrator splices.** No shared file writes; no merge queue needed.

### MVP scope (this build)

To ship a working prototype tonight rather than the full 9-segment design, the MVP collapses to **5 subagents in 5 serial phases**:

1. `geos-mesh` — produces `<Mesh>` + `<Geometry>`
2. `geos-regions-constitutive` — produces `<ElementRegions>` + `<Constitutive>` (combined because they're tightly coupled by `materialList`)
3. `geos-solvers` — produces `<Solvers>` + `<NumericalMethods>` + `<LinearSolverParameters>` (combined because solver and discretization are co-determined)
4. `geos-drivers` — produces `<Functions>` + `<FieldSpecifications>` + `<Tasks>` + `<Outputs>` (combined to keep MVP small; these can be split later for parallelism)
5. `geos-events` — produces `<Events>` (must be last; references all prior names)

The MVP loses Phase-2 and Phase-4 parallelism (motivation #3) but preserves motivations #1 and #2 — the per-call token savings and focused doc context still apply. Splitting can come in v2 once we know the architecture works.

### Component design

**Plugin** (`plugin_orchestrator/`):
- `.claude-plugin/plugin.json` — manifest. Same MCP server config as `plugin/` (geos-rag).
- `agents/<name>.md` — five subagent definitions, each with a focused system prompt, a curated doc primer (RST condensed by hand), the relevant schema slice, and 1–2 example excerpts.
- `scripts/geos_rag_mcp.py` — copied from `plugin/scripts/` (so the orchestrator plugin is self-contained).
- `scripts/extract_schema_slice.py` — utility to pull complexTypes from `schema.xsd` at primer-build time.
- `hooks/verify_outputs.py` — copied from `plugin/hooks/`. Same Stop-hook XML check.
- `ORCHESTRATOR_SYSTEM.md` — workflow primer that the runner appends to the system prompt for the main thread.

**Runner** (`scripts/orchestrator/run_orchestrator_eval.py`):
- Standalone Python script. **Does not modify `src/runner/*`** (constraint from concurrent OpenHands run).
- Imports read-only from `src/runner` for shared utilities (filtered GEOS copy, blocklist, prompt building).
- Defines its own per-task command builder that:
  - Mounts both `plugin_orchestrator/` (at `/plugins/orchestrator`) and `plugin/` (at `/plugins/repo3` — for the geos-rag MCP and Stop hook) into the container.
  - Passes `--plugin-dir /plugins/orchestrator` so subagents in `agents/` are loaded.
  - Sets `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, `ANTHROPIC_API_KEY=$DEEPSEEK_API_KEY`, `--model deepseek-v4-flash`.
  - Appends `ORCHESTRATOR_SYSTEM.md` via `--append-system-prompt` so the main thread knows the workflow.
- CLI parity with the existing harness: `--run`, `--include`, `--workers`, `--timeout`, `--ground-truth-dir`, etc.
- Result dirs: `data/eval/orchestrator_dsv4flash/<run_name>/<task>/` (new path — does not collide with existing `claude_code_*` dirs).

### Toggle

The user's existing `claude_code_repo3_plugin*` agents are unaffected — `plugin/` is untouched, `src/runner/` is untouched, the standard runner still works. To use the orchestrator, the user runs `scripts/orchestrator/run_orchestrator_eval.py`. To use the standard runner, `python -m src.runner.cli` as before.

### Model fallback chain

1. **Primary**: DSv4-flash direct (`https://api.deepseek.com/anthropic`, model `deepseek-v4-flash`).
2. **Fallback A**: minimax-m2.7 via OpenRouter (existing path) — set `--model minimax/minimax-m2.7` and revert `ANTHROPIC_BASE_URL` to OpenRouter.
3. **Fallback B**: deepseek-v3.2 via OpenRouter (matches XN-001/E03 baselines for paired comparison if needed).

The runner takes `--model` and `--api-base` flags to make this swap a one-command change.

## What won't be done in MVP

- No parallelism within phases (would require splitting `geos-regions-constitutive`, `geos-drivers`).
- No splice-failure auto-retry; if xmllint fails, the orchestrator gets one retry chance through its normal turn loop.
- No cross-segment edits by subagents (subagents return text, orchestrator splices — splicing is read-Edit on the working file).
- No new RAG index — the orchestrator and all subagents share the existing GEOS vector DB.

## Risk register

1. **DSv4-flash refuses to spawn subagents.** Some weaker models don't reliably use the Agent tool. Smoketest catches this. Mitigation: fall back to minimax-m2.7.
2. **Subagents flood the orchestrator's context with their full segment text.** Final results return to main; if each is large, this defeats the purpose. Mitigation: subagents instructed to return **only** the segment XML, no explanation.
3. **Bootstrap example mismatch.** If RAG retrieves a poorly-matched example, the name registry is wrong from the start. Mitigation: orchestrator validates that the bootstrap example structure resembles the task spec before spawning subagents.
4. **xmllint failure rate higher than monolithic.** The splicing pattern can produce structurally invalid XML if the orchestrator splices the wrong block. Mitigation: subagent contracts demand a single segment; xmllint validates after each splice.
5. **Cost/quota on DeepSeek API exhausts mid-run.** Mitigation: launch with a dry-run smoketest first; if it works, run full 17 tasks and watch for 402/429.

## Evaluation

- **Headline metric**: TreeSim mean over 17 tasks vs. existing E03 (plugin + ds via OpenRouter) baseline.
- **Secondary**: pass-rate at TreeSim ≥ 0.7; win/loss/tie count vs E03 paired-by-task.
- **Cost metric**: cumulative input tokens across all subagent invocations; per-task wall time.
- **Failure mode breakdown**: how many tasks fail at which phase (mesh / regions+constitutive / solvers / drivers / events / splice).
- **Comparison with prior baselines** in hub.md: A3 (RAG+SR plugin only), E03 (plugin+ds), M1-u (best memory variant 0.796).

If TreeSim ≥ E03 within noise (0.828 ± 0.05), call this validated. If significantly lower, diagnose: was it the model (DSv4-flash novelty), the splicing (XML structure breakage), or the per-segment context (insufficient docs)?

## Out-of-scope (deferred)

- The "free-edit subagent merge queue" idea from the user's original message — defer to v2 if needed.
- Per-physics solver subagents (SolidMechanics, SinglePhaseFlow, etc.) — defer; MVP uses a combined `geos-solvers`.
- An adversarial review of the orchestrator code before launch — given autonomous mode and time constraints, dispatch reviewer ONCE results are in, not before. Documented as a deviation from the standard `/adversarial-review` gate.

## Implementation order (cycle-by-cycle)

- Cycle 1: design memo (this), `plugin_orchestrator/` skeleton, `extract_schema_slice.py`.
- Cycle 2: per-segment primers + schema slices + agent .md files.
- Cycle 3: `ORCHESTRATOR_SYSTEM.md` and runner script.
- Cycle 4: smoketest TutorialSneddon. Iterate.
- Cycle 5: smoketest ExampleMandel. Iterate.
- Cycle 6: launch full 17-task run.
- Cycle 7+: analyze + write XN-017.

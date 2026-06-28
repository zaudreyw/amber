# Research Direction

## Title
Finding adaptations to the Claude Code harness that improve GEOS XML authoring

## Questions
- **RQ1 (method):** Does the current `repo3` plugin (custom RAG over GEOS docs) improve Claude Code's accuracy on GEOS XML authoring tasks, relative to vanilla CC on the same model?
- **RQ2 (method):** What adaptation beats vanilla CC? Candidates: GEOS-RAG plugin, primer variations, file-tree context injection, simpler flat-chunking RAG, memory system (user's strongest bet).
- **RQ3 (generalization):** Does the winning adaptation hold across models (deepseek-v3.2, minimax-m2.7, gemma-4-31b, Opus 4.6)?
- **RQ4 (deferred):** Do the same adaptations hold on the harder difficulty setting (non-inferable params withheld from the natural-language spec)?

## Context
The project went through three harness generations:
- `repo1` (initial_geos_agent) — custom agent with custom 3-DB RAG. Ran on vibes.
- `repo2` (geos_agent) — reimplemented in a modular embodied-agent framework.
- `repo3` (this repo) — pivoted to build ON TOP of Claude Code after discovering CC outperformed both custom harnesses on the easy task at model-parity.

The paper contribution rests on demonstrating that *some* adaptation on top of vanilla CC yields measurable improvement. If no adaptation wins on the easy task, the fallback is to generate a harder task setting (non-inferable params hidden) where domain adaptations have more room to help.

## Anchor
- `../docs/README.md`, `../docs/experiment_runner.md`, `../docs/evaluation.md`, `../docs/cc_run_comparison.md` — current runner + eval + plugin design.
- `../misc/geophys_todo.md` — the user's original brief (dated 2026-04-20) with the full set of considered interventions, constraints, and priorities.
- `../misc/ablation_findings.md` — the latest ablation report (`ablation_deepseek_v2` no-plugin baseline).
- `../plugin/` — the current plugin (geos-rag skill + GEOS RAG MCP server over ChromaDB).

## Initial Hypotheses
- **H1:** The current plugin (RAG v0) improves TreeSim over vanilla CC at model parity (apples-to-apples on deepseek-v3.2). Testable *immediately* by scoring the already-run `repo3_eval_run4`.
- **H2:** A frozen, pre-learned memory/cheatsheet that stores lessons from a held-out train subset is the single largest available improvement lever — it directly addresses the repeated-mistakes pattern visible in vanilla-CC trajectories.
- **H3:** Primer presence in the system prompt (vs workspace file) reduces timeout incidence on deepseek. Already softly supported by timeline notes in `ablation_findings.md`.
- **H4:** File-tree-in-context (precomputed tree of `/geos_lib` fed into the system prompt) reduces exploratory `ls`/`glob` tool calls and shortens wall time without hurting accuracy.

## Non-goals for this session
- Do NOT rewrite the runner or eval — they are stable.
- Do NOT touch the contamination logic — two-layer enforcement is working and well-audited.
- Do NOT regenerate the task set — stay on the canonical 36-task list unless an intervention is decided too expensive for full 36 runs (then use a smaller sub-subset).

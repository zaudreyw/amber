# Checkpoint — interactive autonomy + difficulty ramp (2026-05-04 ~11:40Z, COMPLETE)

## Status
**Overnight workshop-paper sprint complete.** Researcher returns to:
- 64 single-seed runs scored (8 tasks × 2 configs × 2 difficulties × 2 modes)
- Final report at `docs/2026-05-04_interactive-autonomy-results.md`
- Design doc + plan + status log: `docs/2026-05-03_interactive-autonomy-{design,plan,status}.md`

## Headline
- F0 vanilla / F4 AUTOCAMP-best on medium and hard relaxed specs
- TreeSim drops ~9–13 pp from the test-17 Easy anchor; F4 retains a
  small advantage over F0 (~+0.5–5 pp) at relaxed difficulty
- **The agent consulted the simulated supervisor 1 time across 32
  interactive runs.** Even when the channel was in its tool list and
  explicitly advertised in the system prompt, it preferred inference
  from on-disk GEOS examples on 31 of 32 trials.

| difficulty | mode | F0 | F4 |
|---|---|---:|---:|
| Easy (anchor) | A | 0.910 | 0.921 |
| Medium | A non-int | 0.776 | 0.829 |
| Medium | B int     | 0.884 | 0.875 |
| Hard | A non-int   | 0.828 | 0.835 |
| Hard | B int       | 0.710 | 0.840 |

Mode B F0 medium +10.7 pp over Mode A F0 medium is almost certainly a
plugin-loaded confound (F0_interactive needs plugin loaded for the
supervisor MCP, F0_noninteractive doesn't).

## Open follow-ups
1. Second seed for each cell to harden n=1 numbers (cost: ~$3, ~3 hr).
2. Variant prompt pushing the agent to ask more aggressively, to
   distinguish "agent prefers inference" from "system-prompt framing
   discouraged asking".
3. A no-confound Mode B F0 control (vanilla CC + supervisor without the
   plugin loader). Requires either splitting the supervisor MCP from
   the plugin pipeline or only comparing F4 vs F4_interactive.
4. Question-quality / tier-coverage analysis once n_calls > 1.

## Files
- `docs/2026-05-03_interactive-autonomy-design.md` — design doc
- `docs/2026-05-03_interactive-autonomy-plan.md` — execution plan
- `docs/2026-05-03_interactive-autonomy-status.md` — overnight log
- `docs/2026-05-04_interactive-autonomy-results.md` — morning report
- `scripts/relax_specs.py`, `scripts/_recheck_hygiene.py`
- `scripts/launch_interactive_autonomy.sh`, `scripts/score_interactive_autonomy.sh`,
  `scripts/analyze_interactive_autonomy.py`
- `plugin/scripts/supervisor_mcp.py`
- `data/eval/experiments_relaxed_{medium,hard}/` — 16 relaxed specs (LLM rewrites + hygiene metadata)
- `data/eval/interactive_autonomy_2026-05-03/` — 64 runs + per-task scores + `_results/aggregate.json`

## Code added to runner (non-disruptive)
- 4 new agent variants: `ia_{F0,F4}_{noninteractive,interactive}` in
  `src/runner/agents.py`
- `--supervisor-spec-dir` CLI flag in `src/runner/cli.py`
- `supervisor_enabled` flag through `orchestrator.py`,
  `claude_settings.py`, `docker_cmd.py`, `prompts/__init__.py`
- All AUTOCAMP cells, scoring, contamination, and main-battery results
  are unchanged.

# Interactive autonomy + difficulty ramp — execution plan

*2026-05-03, evening. Decisions confirmed. Operating overnight.*

## Decisions (locked)
1. Best config = **F4** (xmllint MCP + memory primer m1u, no Stop hook).
2. **8 tasks**: ExampleMandel, ExampleDPWellbore, ExampleEDPWellbore,
   ExampleIsothermalLeakyWell, ExampleThermalLeakyWell, TutorialPoroelasticity,
   TutorialSneddon, ExampleThermoporoelasticConsolidation.
3. Agent + supervisor model = **deepseek-v4-flash**.
4. Spec rewrite model = **deepseek-v4-pro** (smarter, knows physics/numerics).
5. **Skip** Easy anchor (use existing test-17 numbers).
6. **Single seed** to start (case-study scope).

## Run matrix
- Mode A (non-interactive): 8 × 2 difficulties × 2 configs × 1 seed = **32**
- Mode B (interactive):     8 × 2 difficulties × 2 configs × 1 seed = **32**
- Smoketest:                ~6 runs
- Total:                    ~70 runs at DSv4-flash. Budget ≪ $20.

## Execution order
1. relax_specs.py + run on 8 tasks → freeze artefacts
2. agent variants in src/runner/agents.py
3. Mode A smoketest (ExampleMandel @ Medium + Hard, F4)
4. Mode A full run (background)
5. Supervisor MCP server (build while Mode A runs)
6. Mode B smoketest (ExampleMandel @ Hard, F4_interactive)
7. Mode B full run (background)
8. Score + analyse + morning report

## Files written tonight
- `docs/2026-05-03_interactive-autonomy-design.md` — design doc (already)
- `docs/2026-05-03_interactive-autonomy-plan.md` — this file
- `scripts/relax_specs.py` — spec rewrite generator
- `data/eval/experiments_relaxed_{medium,hard}/<task>/instructions.txt`
- `data/eval/experiments_relaxed_{medium,hard}/<task>/_omitted.json` — hygiene record
- `plugin/mcp-servers/geos-supervisor/server.py`
- `src/runner/agents.py` — 4 new variants
- `scripts/launch_interactive_autonomy_modeA.sh`
- `scripts/launch_interactive_autonomy_modeB.sh`
- `scripts/score_interactive_autonomy.py`
- `docs/2026-05-04_interactive-autonomy-results.md` — morning report

## Live status
See `docs/2026-05-03_interactive-autonomy-status.md` for running updates.

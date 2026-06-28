# repo3 docs

Documentation for this version of the GEOS agent, which is built directly on
top of the Claude Code harness (custom system instructions + a Claude Code
plugin that ships a GEOS RAG MCP server).

## Quickstart

### One-time setup

```bash
# 1. Symlink the shared data volume into repo3/data/ and repo3/runs/
ln -s /data/shared/geophysics_agent_data/data             data
ln -s /data/shared/geophysics_agent_data/data/eval/runs   runs

# 2. Put .env at repo root with the API keys you need:
#    ANTHROPIC_AUTH_TOKEN=...   (repo3-plugin agent, uses OpenRouter Claude)
#    ANTHROPIC_API_KEY=...      (claude_code agent)
#    CURSOR_API_KEY=...         (cursor_composer2 agent)
#    OPENROUTER_API_KEY=...     (MCP server embeddings; falls back to ANTHROPIC_AUTH_TOKEN)

# 3. Build the eval container image
docker build -t geos-eval run/
```

### Run a suite end-to-end (recommended)

```bash
uv run python scripts/run_and_eval.py \
    --run experiment_run1 \
    --agents claude_code_repo3_plugin \
    --include ExampleEDPWellbore TutorialDeadOilEgg \
    --workers 2
```

This runs the agent in Docker, one workspace per task, then scores each
task's `inputs/*.xml` against ground truth. The orchestrator prints the
exact commands it invokes so either phase can be rerun standalone.

### Or run the two phases separately

```bash
# Phase 1: launch agents, capture outputs
uv run python scripts/run_experiment.py \
    --run experiment_run1 \
    --agents claude_code_repo3_plugin \
    --include ExampleEDPWellbore \
    --workers 2

# Phase 2: score an existing run
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/claude_code_repo3_plugin/experiment_run1 \
    --ground-truth-dir data/eval/experiments_gt \
    --results-dir      data/eval/results/experiment_run1/claude_code_repo3_plugin
```

### Where to look afterwards

```
data/eval/<agent>/<run>/<task>/
├── inputs/                 # agent-written XML (scored against GT)
├── status.json             # final run status; dashboard source
├── events.jsonl            # per-turn CC events (tool calls, text, usage)
├── cc_conversation.jsonl   # raw CC stream-json (claude_native only)
├── eval_metadata.json      # blocked files, paths, start time — audit trail
└── ...

data/eval/results/<run>/<agent>/
├── <task>_eval.json        # per-task score + per-section treesim
└── _summary.json           # aggregate across tasks
```

`overall_score` is `10 * treesim` (XMLTreeSim headline; see
[evaluation.md](evaluation.md) for the algorithm and what the diagnostic
fields mean). `status.json` is what the dashboard ingests.

### Just rescore an existing run (no relaunch)

```bash
uv run python scripts/run_and_eval.py \
    --run experiment_run1 --skip-run \
    --agents claude_code_repo3_plugin claude_code
```

### One-task sanity check

```bash
uv run python scripts/eval/judge_one.py \
    --gt  data/eval/experiments_gt/ExampleEDPWellbore/inputs \
    --gen data/eval/claude_code_repo3_plugin/experiment_run1/ExampleEDPWellbore/inputs
```

## Contents

- [experiment_runner.md](experiment_runner.md) — how
  `scripts/run_experiment.py` launches agents in Docker, plus the
  contamination-prevention pipeline (variant expansion, RST blocking,
  hardlink sandbox).
- [evaluation.md](evaluation.md) — how agent outputs are scored, centred
  on the `XMLTreeSim` metric, with diagnostic and agent-behaviour metrics
  on the side.
- [cc_run_comparison.md](cc_run_comparison.md) — how the CC-as-agent
  runs differ between `repo3` and the original `geos_agent` repository.

## Top-level layout

```
repo3/
├── docs/                   you are here
├── src/
│   ├── runner/             eval-harness package: orchestrator, docker_cmd,
│   │                       prompts, agents, contamination, dashboard, ...
│   │                       (was a 3500-line monolith in scripts/; refactored
│   │                       into modules 2026-04-27 — see XN-008 / git history)
│   └── eval/               evaluation library (XMLTreeSim, metrics, LLM judge)
├── scripts/
│   ├── run_experiment.py   CLI shim — imports runner.cli.main and runs it
│   ├── run_and_eval.py     CLI — runs experiments then scores them
│   ├── api_probe.py        CLI — quick latency probe for OpenRouter / OpenAI /
│   │                       DeepSeek / Anthropic, useful for triaging a hang
│   ├── analysis/           Cross-run analysis (file access, tool usage)
│   └── eval/               CLI wrappers around src.eval
├── run/                    runtime assets: AGENTS.md (system prompt) + Dockerfile
├── plugin/                 Claude Code plugin (skills + GEOS RAG MCP server)
├── data/                   (symlink) experiment inputs, GEOS source, vector DB
└── runs/                   (symlink) experiment outputs
```

`data/` and `runs/` are expected to be symlinks into a shared data volume
(previously `/data/shared/geophysics_agent_data/...`). The runner expects
`DATA_DIR = REPO_ROOT / "data"`.

## Modularity

Three peer concerns, intentionally decoupled:

- **`plugin/`** — the agent's customization surface (skills + RAG MCP).
- **`src/runner/`** (driven by `scripts/run_experiment.py`) — the harness.
  Builds per-task Docker workspaces, wires up MCP, streams the agent's
  events, writes `inputs/` + logs + `status.json`. Internal split: `cli`
  (argparse + main loop), `orchestrator` (per-task driver), `task`
  (single-attempt runner), `docker_cmd`/`claude_settings` (container +
  MCP wiring), `prompts` (system-prompt assembly + retry prompts),
  `agents` (the variant catalogue), `contamination` (block-list +
  hardlink sandbox), `tool_counts`/`events`/`cost` (event-stream
  parsing), `dashboard` (live-status web UI).
- **`src/eval/` + `scripts/eval/`** — post-hoc analysis. Reads task
  workspaces, scores XML, computes agent-behaviour metrics.

The runner never imports `src.eval`; the evaluator never imports
`runner`. Contamination is a runner concern (it shapes what the agent
sees) so it lives in `runner.contamination`. `scripts/run_and_eval.py`
chains them via subprocess, preserving the process boundary.

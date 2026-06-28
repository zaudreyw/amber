# Experiment runner (`scripts/run_experiment.py`)

## Purpose

Launch GEOS-XML-authoring tasks under multiple agents in parallel Docker
containers, capture per-task logs and outputs, and emit status JSON that a
dashboard / later-stage evaluator can read.

Layout:

- `scripts/run_experiment.py` — CLI shim (what you actually run). Just imports `runner.cli.main` and calls it.
- `src/runner/` — the runner package (`runner.cli`, `runner.agents`, `runner.orchestrator`, `runner.task`, `runner.docker_cmd`, `runner.prompts`, `runner.tool_counts`, `runner.events`, `runner.claude_settings`, `runner.cost`, `runner.process_mgr`, `runner.contamination`, `runner.dashboard.{snapshot,server}`).
- `src/runner/prompts/` — long prompt strings (`rag_instructions.txt`, `rag_vanilla.txt`, `memory_instructions.txt`, `pseudo_tool_retry.txt`, `no_outputs_retry.txt`, `real_tool_tail.txt`, `native_plugin_prefix.txt`) loaded at import time and combined by `runner.prompts.build_system_prompt`.
- `src/runner/dashboard/template.html` — the live-status dashboard HTML.
- `run/AGENTS.md` — agent system prompt (read by the script at startup).
- `run/Dockerfile` — image the runner invokes (`docker build -t geos-eval run/`).

Three runners are wired in (`AGENTS` dict in `src/runner/agents.py`):

| Key | Runner | Purpose |
|---|---|---|
| `claude_code` | `acpx` | Claude Code via the ACP protocol. |
| `claude_code_repo3_plugin` | `claude_native` | Claude Code invoked directly (`claude -p ...`) with the `repo3` plugin and RAG MCP server attached. |
| `cursor_composer2` | `acpx` | Cursor's `composer-2` via ACP. |

The `claude_native` path is the headline config for this repo: it drives CC
with the plugin-defined skills (`geos-rag`) and a local MCP server that
queries a per-task ChromaDB copy.

## High-level flow

For each (agent, task) pair `run_eval.py`:

1. **Prepare a sanitized GEOS copy** (see *Contamination* below). The copy
   lives under `data/eval/tmp_geos/` and is hardlinked from the real
   `data/GEOS/` source, minus any files that could leak the answer for this
   task.
2. **Prepare a per-task result dir** at
   `data/eval/<agent>/<run_name>/<task>/`.
3. **Build the system context** from `run/AGENTS.md` plus the GEOS primer.
   The primer is injected into the agent system prompt; `/workspace/GEOS_PRIMER.md`
   is intentionally not created.
4. **Build the task prompt** from the task's `instructions.txt`.
5. For `claude_native`:
   a. Copy the shared vector DB into the task dir (ChromaDB takes write
      locks even for reads, so a per-task copy is required for parallelism).
   b. Run an MCP preflight (`geos_rag_mcp.py --smoke`) to make sure the
      plugin's stdio server starts cleanly before we spend agent budget.
   c. Write an explicit `claude_mcp_config.json` with `EXCLUDED_*` env vars
      baked into the MCP server's env.
   d. Launch `claude -p --model <model> --plugin-dir /plugins/repo3
      --mcp-config ... --output-format stream-json` inside the container.
   e. Parse the streaming JSON live, maintaining `status.json`,
      `tool_calls.json`, `events.jsonl`.
6. For `acpx` agents: launch `acpx <agent> exec <prompt>` with the same
   contamination mounts; capture stdout/stderr; post-process the event
   stream into `status.json`.
7. Teardown: remove the per-task GEOS hardlink copy and vector-DB copy.

Parallelism is bounded by `--workers` (default 1) and task-level timeout is
`--timeout` (default 600 s).

## Output layout per task

```
data/eval/<agent>/<run_name>/<task>/
├── inputs/                  # agent-written XML (target location)
├── outputs/                 # agent-written simulation outputs (unused in eval mode)
├── acpx_output.json         # raw stdout from acpx (or CC stream-json dump)
├── cc_conversation.jsonl    # claude_native only — full CC event log
├── events.jsonl             # parsed event stream (per-turn records)
├── tool_calls.json          # aggregated tool-call counts
├── stderr.txt
├── exit_code.txt
├── status.json              # live heartbeat; final state on exit
├── eval_metadata.json       # task, blocked files, primer delivery, start time
├── mcp_preflight.json       # claude_native only — MCP smoke-test result
└── claude_mcp_config.json   # claude_native only — explicit MCP wiring
```

Downstream: `scripts/eval/batch_evaluate.py` reads `inputs/` for each task
against `data/eval/experiments_gt/<task>/inputs/` and writes per-task
`<task>_eval.json` alongside.

## Contamination prevention

The agent must never see the ground-truth XML for the task it is being
evaluated on, nor the tutorial/example RST that the task was mined from.
All contamination logic lives in `src/runner/contamination.py`; the
runner calls `get_blocked_files_for_task()` once per (agent, task) and
`create_filtered_geos_copy()` to materialise the sandboxed mount.

### The block list

`get_blocked_files_for_task(task_id, ground_truth_dir, geos_source_dir)`
returns two lists:

1. **`blocked_xml_filenames`** — every XML basename under
   `<ground_truth_dir>/<task_id>/`, **plus variant siblings** found in the
   GEOS source. Variant expansion strips suffixes like `_base`,
   `_benchmark`, `_smoke`, `_iterative`, `_direct`, `_base_iterative`,
   `_base_direct` to a stem, then blocks every other XML in the source
   tree that reduces to the same stem. So a task whose GT is
   `DeadOil_base.xml` + `DeadOil_benchmark.xml` also blocks any
   `DeadOil_smoke.xml`, `DeadOil_base_iterative.xml`, etc. lurking in
   `inputFiles/`. Stems shorter than 10 characters or in a generic-words
   set (`base`, `benchmark`, `input`, `problem`, `model`, `smoke`) are
   dropped to avoid accidental cross-task blocking.

2. **`blocked_rst_paths`** — at most one RST relative path, looked up in
   `example_pairs.jsonl` (defaults to
   `/data/shared/geophysics_agent_data/data/eval/example_pairs.jsonl`, or
   set `GEOS_EXAMPLE_PAIRS`). Each line maps an RST cross-reference label
   (`.. _foo:`) to an RST path under the GEOS source. If the task id
   matches a label, that RST path is added to the block list.

### Enforcement layer 1 — per-task filtered GEOS mount

`create_filtered_geos_copy` materialises a fresh
`data/eval/tmp_geos/geos_eval_<rand>/geos/` tree by `os.link()`-ing every
file in `data/GEOS/`, except those whose basename is in
`blocked_xml_filenames` or whose relative path is in
`blocked_rst_relpaths`. Hardlinks are instantaneous and use no extra disk
when both paths share a filesystem.

Hardlinks are deliberately preferred over symlinks here: a symlink in a
Docker bind-mount can point *outside* the sandbox, which defeats the
point. A hardlink has no target — it's a second inode reference, and the
blocked files are simply absent from the mount.

The copy is bind-mounted at `/geos_lib:ro` in the agent's container:

```python
blocked = get_blocked_files_for_task(
    task_name, ground_truth_dir, geos_source_dir=GEOS_LIB_DIR,
)
filtered_geos = create_filtered_geos_copy(
    GEOS_LIB_DIR,
    blocked_xml_basenames=blocked["blocked_xml_filenames"],
    blocked_rst_relpaths=blocked["blocked_rst_paths"],
    tmp_parent=TEMP_GEOS_PARENT,
)
```

`cleanup_filtered_geos_copy(filtered_geos)` removes the whole temp parent
when the task finishes.

### Enforcement layer 2 — RAG server blocklist

The GEOS RAG MCP server (`plugin/scripts/geos_rag_mcp.py`) reads two env
vars from the explicit MCP config:

- `EXCLUDED_GT_XML_FILENAMES` — JSON list of XML basenames (variant-expanded)
- `EXCLUDED_RST_PATHS` — JSON list of GEOS-relative RST paths

Chunks from excluded sources are dropped from search results before being
returned to the agent. This catches any pre-indexed chunks that would
otherwise echo ground-truth content back through the search tools even
though the underlying file is no longer on disk.

### Enforcement layer 3 — provenance in the audit trail

Every task dir contains an `eval_metadata.json` recording
`blocked_gt_xml_filenames`, `blocked_rst_relpaths`, the filtered GEOS
path, and the primer path. The dashboard surfaces this so a reviewer can
verify after the fact that the correct files were withheld.

### What is *not* blocked

- General GEOS documentation under `src/docs/sphinx/userGuide/` and
  similar reference material.
- Other tasks' ground-truth XMLs in the same suite — only *this* task's
  GT is withheld. Cross-task leakage is possible when tasks share
  physics (a multiphase task could peek at another multiphase example).
  Variant expansion does stem-based matching, not physics-topic matching,
  so this gap is real.
- RSTs for tasks absent from `example_pairs.jsonl`. Mapping coverage is
  an ongoing responsibility.

### Historical note

Prior to this refactor, `run/run_eval.py` had a local
`collect_ground_truth_xml_filenames` that returned *only* the exact GT
basenames, and `blocked_rst_relpaths` was hardcoded to `[]`. The runner
was therefore missing both variant expansion and RST blocking that the
earlier `geos_agent` harness had. The `src/runner/contamination.py` module
combines the old repo's block-list logic with this repo's hardlink
sandbox.

## Adding a new task

1. Drop `data/eval/experiments/<task>/instructions.txt`.
2. Drop the reference XML under
   `data/eval/experiments_gt/<task>/inputs/`.
3. (Optional) If the task is derived from a specific tutorial RST, add a
   mapping line to `example_pairs.jsonl` so the RST is blocked too.
4. Rerun `uv run python scripts/run_experiment.py --run <run_name> --include <task>`.

## Adding a new agent

Edit `src/runner/agents.py` and add a new key to the `AGENTS` dict with
`runner="acpx"` or `runner="claude_native"`, an `api_key_env`, and (for
native) `requires_rag` if it should block on MCP preflight. The
`plugin_enabled` flag controls whether the system prompt's GEOS RAG
instruction block (in `src/runner/prompts/rag_instructions.txt`) is
included or replaced with the vanilla-fallback variant
(`rag_vanilla.txt`). Docker image stays the same; add any new CLI
binaries in `run/Dockerfile`.

## Probing model/provider latency

`scripts/api_probe.py` is a small CLI for sending a tiny prompt to one or
more `<provider>:<model>` targets and reporting per-request latency,
output tokens, and any error class. Use it before launching a run when
the harness is hanging and you need to disambiguate "the model is slow"
from "the provider is rate-limiting us":

```bash
python scripts/api_probe.py \
    --target openrouter:minimax/minimax-m2.7 \
    --target openrouter:deepseek/deepseek-v4-flash \
    --target deepseek:deepseek-v4-flash \
    --runs 3
```

Supported providers: `openrouter`, `deepseek`, `openai`, `anthropic`. Keys
are read from `.env` (`OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`,
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN`).

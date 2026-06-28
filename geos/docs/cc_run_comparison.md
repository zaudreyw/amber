# Claude Code experiments: `repo3` vs `geos_agent`

Both repos run GEOS-XML authoring tasks with Claude Code as the agent.
They arrive at very different plumbing.

## TL;DR

|                         | `geos_agent/scripts/eval/run_cc_harness.py` | `repo3/scripts/run_experiment.py` (`claude_native`) |
|-------------------------|---------------------------------------------|-----------------------------------------------------|
| Execution model         | In-process Python + subprocess CC on host   | One Docker container per (agent, task)              |
| CC invocation           | Via `misanthropic-cc`'s `run_openrouter`    | Direct `claude -p` with stream-json                  |
| System prompt           | GEOS primer + cheatsheet concatenated inline into `--append-system-prompt-file` | `AGENTS.md` + GEOS primer injected via `--append-system-prompt`; task instructions passed as the user prompt |
| Tool / skill surface    | Default CC tools; no plugin                 | Default CC tools + explicit **repo3 GEOS RAG MCP server** |
| Knowledge retrieval     | Raw file browsing of sanitized GEOS copy    | RAG over per-task ChromaDB copy, plus file browsing |
| Contamination: variant expansion | ✅ Stem-based expansion (`Foo_base` → `Foo_benchmark`, `Foo_smoke`, …) | ✅ Ported into `src/runner/contamination.py` |
| Contamination: RST blocking | ✅ Via `example_pairs.jsonl` | ✅ Via `example_pairs.jsonl` (wired through `EXCLUDED_RST_PATHS`) |
| Contamination: enforcement | Symlink tree on host (followable)    | Hardlink tree mounted at `/geos_lib:ro` (safer: no follow-out) |
| RAG-index scrubbing     | N/A (no RAG index)                          | `EXCLUDED_GT_XML_FILENAMES` + `EXCLUDED_RST_PATHS` env vars passed to MCP server |
| Parallelism             | `ProcessPoolExecutor` in-process            | `ThreadPoolExecutor` + Docker containers            |
| Per-task workspace      | Host dir                                    | Host dir bind-mounted at `/workspace:rw`            |
| Evaluation              | Inline (`evaluate_directories` called in-process after agent exits) | Deferred — `scripts/eval/batch_evaluate.py` runs after the suite |
| Agents supported        | CC only                                     | `claude_code` (acpx), `claude_code_repo3_plugin` (native), `cursor_composer2` (acpx) |

## Differences in detail

### 1. Agent bootstrapping

**`geos_agent`** builds one long system prompt by concatenating:

- Hardcoded GEOS scaffolding paragraph
- Full text of `modules/profile/prompts/GEOS_PRIMER.md`
- Full text of `modules/profile/prompts/cheatsheet.md`
- All hardcoded GEOS paths rewritten to point at the sanitized copy

…and passes it via `--append-system-prompt-file`. The agent starts with
the primer already in context.

**`repo3`** injects `AGENTS.md` plus the GEOS primer through Claude Code's
system prompt path. The task workspace intentionally omits
`/workspace/GEOS_PRIMER.md`, so the agent cannot waste a turn trying to read
the primer or silently skip it.

### 2. Skills and MCP

`repo3` ships a Claude Code plugin at `plugin/`, but the native Claude eval
path wires the RAG server directly through `--mcp-config` instead of loading
the plugin's skill wrapper. This avoids provider-specific message-shape errors
from synthetic skill messages while keeping the same RAG tools available.

The plugin contributes:

- The `geos-rag` skill (retrieval instructions for the agent).
- An MCP server (`plugin/scripts/geos_rag_mcp.py`) exposing
  `search_navigator` / `search_schema` / `search_technical` tools backed by
  ChromaDB over GEOS RST docs + example XML.

`geos_agent` has no plugin — CC browses files with the default `Read` /
`Glob` / `Grep` / `Bash` tools. The RAG layer that `geos_agent`'s framework
agent uses (`modules/adapters/geos_tools`) is Python-only; CC never
benefited from it.

Practical consequences:

- **repo3 CC can do semantic search.** Cheaper than grepping blind; more
  likely to surface the "right" example even if the agent doesn't know its
  filename.
- **repo3 CC needs vector DB copies per task** (ChromaDB write-locks even
  on reads), adding a few seconds of setup per task.
- **repo3 CC needs an MCP preflight** — `geos_rag_mcp.py --smoke` runs
  once before the real invocation to surface missing deps or locked DBs
  before we burn agent budget.

### 3. Contamination

Both repos withhold the task's ground-truth XML, variant siblings in the
GEOS source, and the tutorial RST the task was derived from. The block
list is the same (variant-stem expansion + `example_pairs.jsonl`
lookup — repo3's `src/runner/contamination.py` is the ported logic).

Enforcement differs:

**`geos_agent`** (`contamination.make_sanitized_geos_copy`) builds a
symlink tree into `/tmp/...`, omitting the blocked files. Paths inside the
primer / cheatsheet are rewritten to point at this sanitized copy before
going into the system prompt. CC runs on the host with `--add-dir
<sanitized_geos>`.

**`repo3`** (`create_filtered_geos_copy`) builds a hardlink tree into
`data/eval/tmp_geos/`, omitting the blocked files, and bind-mounts it at
`/geos_lib:ro` inside the container. Additionally the MCP server drops
results from excluded sources at query time.

repo3's sandbox is a harder guarantee: symlinks in a bind-mount can be
followed out of the sandbox if a link target lies outside the mount,
while hardlinks have no target and blocked files are simply absent from
the tree. The second RAG layer also prevents index-baked leaks that the
filesystem sandbox alone wouldn't catch.

### 4. Evaluation is deferred in repo3

`geos_agent`'s `_run_single_cc_task` calls `evaluate_directories` in the
same process, right after CC exits, and stuffs the score into the task
result dict. A failure in the evaluator kills the task result.

`repo3`'s runner never imports `src.eval`. It writes the XML, captures
logs, and exits. Evaluation is a second pipeline stage
(`scripts/eval/batch_evaluate.py`), which means:

- Evaluators can change without rerunning experiments.
- A broken evaluator doesn't cost agent budget.
- Cross-agent comparisons are trivial: run the same evaluator over every
  agent's output directory.

### 5. Container vs host

`geos_agent` runs CC directly on the host. Fast, but:

- Every task inherits the host's Node/CC install.
- Per-task environment isolation is partial (cwd only).
- Concurrent tasks share the host's `~/.claude` config.

`repo3` uses a Docker container per task (`run/Dockerfile`: Ubuntu 24.04
+ Node 22 + CC + acpx + uv). Slower cold start, but:

- Reproducible agent environment across hosts.
- Per-task `HOME=/workspace/.claude_home` keeps config state isolated.
- Same image runs acpx agents (Claude via ACP, Cursor) too, so
  cross-agent comparisons share infra.

## When to pick which

Use the **`geos_agent` harness** when iterating on agent internals: fast
turnaround, in-process debugging, no Docker overhead, single agent.

Use the **`repo3` runner** for reported evaluations: every configuration
the agent sees is captured in the task dir (`eval_metadata.json`,
`claude_mcp_config.json`, `events.jsonl`); the filesystem sandbox is
tighter; and the same command scales across CC, CC-with-plugin, and
Cursor.

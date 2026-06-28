---
title: "Other Coding-Agent Harness — Candidate Survey & Baseline Selection"
date: 2026-04-27
author: research-copilot (other-coding-agent-baseline session)
related: [D-009 (planned), XN-016 (planned)]
status: draft (selection complete, implementation in progress)
---

# Other-Coding-Agent Baseline — Candidate Survey & Selection

## Why this baseline exists

Current paper baselines:
- **Vanilla CC** (`claude_code_no_plugin`) — Claude Code harness, no
  plugin, primer in system prompt. The "harness baseline."
- **Harness-less / direct prompt** (`scripts/harnessless_eval.py`) —
  base LLM, no agent loop. Same primer, single-shot or 1-shot ICL.
  The "no-harness baseline."

Missing: a **third, different agent harness** running the same task /
model / primer. Without it, a reviewer can correctly object that any
finding about CC adaptations is "single-harness." We want to test
whether adaptations on top of CC outperform a *different general-purpose
coding-agent harness* on the same model. This third point in the design
space disambiguates "CC-specific" wins from "harness-shape" wins.

## Selection criteria (priority order)

1. **Closest to vanilla CC in agent-loop shape** — file/edit/bash tools,
   ReAct-style turn loop, sandbox-style execution. So the comparison is
   "different harness, same problem" not "different paradigm, same
   problem."
2. **Easy OpenRouter wiring** — must accept `minimax/minimax-m2.7` over
   an OpenAI-compatible base URL. Model parity with all other runs.
3. **Actively maintained, citation-credible** — paper publishes in
   ~weeks; we don't want a repo that disappears. Prior academic use is
   a plus.
4. **Scriptable + trajectory-capturable** — needs a headless mode and
   a structured per-event log so we can compute token / tool-call
   metrics consistent with our other runs.

## Candidates considered

### A. OpenHands (All-Hands-AI/OpenHands, formerly OpenDevin)

- Repo: `github.com/All-Hands-AI/OpenHands` (`docs.openhands.dev`).
- Shape: explicit ReAct-style agent loop, ships file-editor / bash /
  browser tools, runs each session in a Docker "sandbox runtime"
  container. Closest analogue to CC of the three.
- LLM wiring: LiteLLM under the hood. OpenRouter is a first-class
  provider; model names like `openrouter/minimax/minimax-m2.7`.
  `LLM_API_KEY` + `LLM_BASE_URL` env vars (or `~/.openhands/settings.json`).
- Headless: `openhands --headless -t "<task>"` with `--json` for
  streaming JSONL events (tokens, tool calls, file ops). Always-approve
  is the default in headless mode — exactly what we need for batch eval.
- Workspace: `SANDBOX_VOLUMES=<host>:<container>:rw|ro`, multiple
  mounts allowed. Maps cleanly onto our existing `/workspace` (rw)
  + `/geos_lib` (ro filtered) pattern.
- Install: `uv tool install openhands --python 3.12` (binary), or
  Docker, or `curl install.openhands.dev/install.sh | sh`.
- Citations: prior academic use as the OpenDevin / OpenHands NeurIPS
  2024 paper; widely used as a SWE-bench harness.

### B. OpenCode — disambiguation needed

Two distinct projects share the name:
- `opencode-ai/opencode` — **archived 2025-09; redirects to
  `charmbracelet/crush`**. Citing an archived project would be a red
  flag. **Disqualified.**
- `sst/opencode` — actively maintained; SST team. Client/server split
  (Go backend + TUI frontend). Has `opencode run "<prompt>" --model
  <provider/model> --format json` for headless use; OpenRouter
  supported via models.dev provider list / custom JSON provider.
- Shape: general coding agent (build / plan agents + standard
  file/bash/edit tools). Comparable to CC.
- Concerns:
  - **Containerization**: not designed to run inside a sandbox
    container; we'd containerize it ourselves.
  - **Two-process architecture** (Go server + TUI client) is more
    moving parts inside our Docker pipeline than a single Python CLI.
  - **Less academic citation history** than OpenHands.

### C. Hermes-Agent (NousResearch)

- Repo: `NousResearch/hermes-agent`.
- Shape: positioned as a general-purpose **autonomous personal agent**
  with persistent SQLite memory + a "skill learning loop" + multi-
  platform gateways (Telegram/Discord/Slack/...). It *can* do coding-
  style tool calls, but it's a different paradigm.
- LLM wiring: `hermes model` switches providers; OpenRouter supported.
- Concerns:
  - **Persistent-memory and self-improving-skills** are confounds for
    our experiment — we want a stateless harness running 17
    independent tasks. Disabling those is possible but takes us off
    the paved path.
  - Not a SWE-bench-style coding harness — closer to an assistant
    framework. Comparison would be apples-to-oranges with CC.

> **Verification note.** Some of the literature-search agent's specifics
> (star counts, exact release versions) looked implausibly high and were
> not used as decision inputs. The selection rests on (a) the qualitative
> shape comparison above and (b) directly verified docs (OpenHands
> headless mode, OpenRouter integration, sandbox-volumes config — all
> fetched from `docs.openhands.dev` 2026-04-27).

## Decision: **OpenHands**

Reasoning, mapped to criteria:

1. **Shape**: closest to CC in trio. ReAct-style loop, file/bash tools,
   sandbox container. sst/opencode is close but client-server split is
   extra friction; Hermes is a different paradigm.
2. **OpenRouter**: LiteLLM-based, well-documented `openrouter/<model>`
   pattern. All three work; OpenHands is the most battle-tested.
3. **Maintenance / citability**: strongest academic-citation footprint
   (OpenDevin/OpenHands paper). Lowest "vanished by publication" risk.
4. **Scripting**: `--headless --json` streams JSONL events with token
   usage included; trivial to fan out across 17 tasks.

Tie-breaker: OpenHands' sandbox-runtime model maps onto our existing
container/volume pattern almost exactly (writable `/workspace` + RO
`/geos_lib`), so the harness-side plumbing is a near 1:1 port of the
vanilla-CC runner.

**Fallback** if OpenHands' Docker-in-Docker sandbox fights our
`/geos_lib` mount setup: pivot to `sst/opencode` and containerize it
ourselves. **Skip Hermes** in either case — wrong paradigm.

## Parity contract with vanilla CC

For the OpenHands baseline to be a fair "different harness, same
problem" comparison:

| Knob | Vanilla CC | OpenHands baseline | Same? |
|---|---|---|---|
| Model | `minimax/minimax-m2.7` via OpenRouter | `openrouter/minimax/minimax-m2.7` via LiteLLM | ✓ |
| Task set | 17 test tasks (`TEST_TASKS_17`) | Same 17 | ✓ |
| Domain primer | `run/AGENTS.md` (incl. `# GEOS Primer` block) appended to system prompt via `--append-system-prompt` | Same `run/AGENTS.md` content injected into OpenHands' system prompt slot (e.g. via `agent.system_prompt_filename` / leading instruction) | ✓ |
| Per-task spec | `BEGIN/END SIMULATION SPECIFICATION` wrapper around `instructions.txt` | Same wrapper | ✓ |
| Workspace | `/workspace/inputs/*.xml` | `/workspace/inputs/*.xml` | ✓ |
| Reference repo | `/geos_lib` filtered (decontaminated per task) | Same filtered copy | ✓ |
| Tools | CC native (`Read`, `Glob`, `Grep`, `Bash`, `Write`, `Edit`) — `Skill` and `AskUserQuestion` disallowed | OpenHands defaults (`str_replace_editor`, `bash`, `read_file`) — comparable shape, harness-native names | ≈ (best-effort harness-native) |
| Plugin / RAG | none (vanilla baseline) | none | ✓ |
| Memory / cheatsheet | none | none | ✓ |
| Timeout | 1200s (20 min) per task | 1200s | ✓ |
| Output layout | `data/eval/claude_code_no_plugin/<run>/<task>/inputs/*.xml` | `data/eval/openhands_no_plugin/<run>/<task>/inputs/*.xml` | ✓ (same shape, separate dir) |

Per the user's guidance — *"identical to vanilla CC, only the primer
is the domain adaptation in the prompt"* — we **do not port** the
vanilla-CC `rag_vanilla.txt` redirect note or the `real_tool_tail.txt`
pseudo-tool-call guard into the OpenHands prompt:
- `rag_vanilla.txt` is CC-specific (it explains where the primer
  lives in CC's mounting scheme).
- `real_tool_tail.txt` is a CC-specific defense against minimax
  emitting fake `<invoke>` blocks under CC's tool surface.
The OpenHands harness has its own analogues; we don't double-instruct.

> Document either inclusion in `D-009` if the smoketest shows
> minimax misbehaves under OpenHands' tool surface in the same way.

## Output layout (scorer-compatible)

```
data/eval/openhands_no_plugin/<run_name>/<task>/
  inputs/*.xml              ← scored by batch_evaluate.py
  events.jsonl              ← OpenHands --json stream
  metadata.json             ← {model, base_url, started, ended,
                                tokens_in, tokens_out, tool_call_counts}
  exit_code.txt
  stderr.txt
  status.json               ← {task, status, elapsed, ...} (CC-parity)
```

Scoring will re-use `scripts/eval/batch_evaluate.py` exactly as the CC
runs do — same GT dir, same XMLTreeSim metric.

## Non-goals for the first cut

- Per-task contamination filtering parity is **planned, not skipped**:
  we will reuse `runner.contamination.create_filtered_geos_copy` so
  the same blocklist applies. Documented in D-009.
- Trajectory-level apples-to-apples token accounting (LiteLLM event
  format vs CC's stream-json) needs a small adapter; deferred to
  XN-016 follow-up if first-pass scores are interesting.
- Multi-seed runs: do 1 seed first; promote to ≥3 if scores look
  competitive.

## Risks

| Risk | Mitigation |
|---|---|
| OpenHands' sandbox runtime is itself a Docker container — Docker-in-Docker may fight our existing `geos-eval` image | Run OpenHands on the host with `RUNTIME=docker` and mount `/geos_lib` (filtered) directly into the sandbox via `SANDBOX_VOLUMES`. If that fails, switch to OpenHands' "local" runtime and run the agent process directly on the host with strict `/workspace` confinement enforced via `WORKSPACE_BASE`. |
| OpenHands' default system prompt tells the agent to do CC-style scope-of-work and may compete with our domain primer | Keep our primer **after** OpenHands' built-in instructions. Document the order in `metadata.json` per-task. |
| OpenHands' tool name space differs from CC (`str_replace_editor` vs `Edit`) — minimax's pseudo-tool-call failure mode (XN-010) might re-surface differently | If smoketest shows pseudo-tool-call leakage, port `real_tool_tail.txt` into the OpenHands prompt and re-document. |
| `minimax/minimax-m2.7` not on OpenHands' UI provider list | Use the "custom model identifier" Advanced field — `openrouter/minimax/minimax-m2.7` is accepted by LiteLLM directly. |
| LiteLLM throws on a tool the agent emits but OpenHands doesn't expose | Smoketest catches this; first-pass uses default toolset only. |

## Citation note

When citing in the paper:
- OpenHands paper: Wang et al. "OpenDevin: An Open Platform for AI
  Software Developers as Generalist Agents." NeurIPS 2024 D&B.
- Repo: `https://github.com/All-Hands-AI/OpenHands` (rebranded from
  OpenDevin).

## Sources

- [OpenHands docs — headless mode](https://docs.openhands.dev/usage/how-to/headless-mode)
- [OpenHands docs — OpenRouter integration](https://docs.openhands.dev/usage/llms/openrouter)
- [OpenHands docs — CLI installation](https://docs.openhands.dev/openhands/usage/cli/installation)
- [OpenHands GitHub issue — SANDBOX_VOLUMES behavior](https://github.com/All-Hands-AI/OpenHands/issues/8323)
- `opencode-ai/opencode` archived → `charmbracelet/crush`
- `sst/opencode` — `https://opencode.ai/docs/cli/`
- `NousResearch/hermes-agent` — repo + docs

---
id: D-009
title: "Add OpenHands as a third-harness baseline (vanilla parity)"
date: 2026-04-27
dag_nodes: [I12]
links:
  related_to: [D-005, XN-013, XN-014]
  derived_from: ["docs/2026-04-27_other-coding-agent-harness-selection.md"]
status: in-progress
---

# D-009 — OpenHands as third-harness baseline

## Context

Paper currently has two harness rows for the GEOS XML task:
- Vanilla CC (`claude_code_no_plugin`)
- Harness-less / direct prompt (`scripts/harnessless_eval.py`)

A reviewer can correctly object that any "CC adaptations help" finding
is single-harness. We need a third, different *coding-agent harness*
running the same model + primer + 17 tasks so we can disambiguate
"CC-specific" wins from "harness-shape" wins.

## Decision

Add **OpenHands** (All-Hands-AI/OpenHands, formerly OpenDevin) as the
third harness baseline. Selection survey:
`docs/2026-04-27_other-coding-agent-harness-selection.md`.

Disambiguation summary:
- **OpenCode**: `opencode-ai/opencode` is archived (→ `charmbracelet/crush`).
  `sst/opencode` is alive but client-server architecture adds plumbing.
- **Hermes-Agent**: persistent-memory + skill-loop paradigm — confounds
  a stateless 17-task eval. Wrong shape.
- **OpenHands**: ReAct-style loop, file/bash/edit tools, Docker sandbox
  runtime, OpenRouter via LiteLLM, headless JSONL streaming. Closest
  shape to vanilla CC.

## Parity contract (must hold)

- Same 17 test tasks (`TEST_TASKS_17` from `scripts/harnessless_eval.py`).
- Same model: `openrouter/minimax/minimax-m2.7` via LiteLLM.
- Same domain primer: `run/AGENTS.md` (incl. `# GEOS Primer` block)
  injected into OpenHands' system-prompt slot. **Only domain
  adaptation in the prompt** — no port of `rag_vanilla.txt` or
  `real_tool_tail.txt` (those are CC-harness-specific).
- Same per-task spec wrapper: `BEGIN/END SIMULATION SPECIFICATION`.
- Same filtered `/geos_lib` (re-use `runner.contamination`).
- Same per-task workspace: `/workspace` writable, agent writes to
  `/workspace/inputs/*.xml`.
- Same timeout: 1200s.
- Same scorer: `scripts/eval/batch_evaluate.py`, same GT dir.

## Implementation plan

1. New script: `scripts/openhands_eval.py` (mirrors `harnessless_eval.py`
   in CLI shape — `--run-name`, `--workers`, `--score`, etc.).
2. New output dir: `data/eval/openhands_no_plugin/<run_name>/<task>/`
   — separate from CC outputs; no collision.
3. Per-task driver: invoke OpenHands headless via Docker (or `uv tool
   install openhands` if Docker-in-Docker proves brittle), capture
   `events.jsonl`, write `metadata.json` (model, base URL, started/
   ended, token totals, tool-call counts), write status / exit_code
   for parity with CC `status.json`.
4. Smoketest: 1 task end-to-end → verify XML lands in `inputs/` →
   run scorer → confirm a single TreeSim score.
5. Full run: 17 tasks × 1 seed.
6. Document in XN-016. Update hub State of Knowledge with the new
   baseline.

## Non-disruption guarantees (other CC session is running concurrently)

- **No edits** to `src/runner/*` — that's the CC runner; can't be
  broken.
- **No edits** to `run/AGENTS.md` — read-only consumption; CC depends
  on it.
- **No edits** to `scripts/harnessless_eval.py` — only re-import its
  `TEST_TASKS_17` constant.
- **No edits** to `scripts/eval/*` — re-use scorer as a library / via
  subprocess.
- **No new agent entry** in `src/runner/agents.py` — the OpenHands
  baseline is NOT a CC variant; it lives outside that runner.
- **New files only** under `scripts/openhands_eval.py`,
  `data/eval/openhands_no_plugin/`, and `docs/XN-016*`.
- **Filtered `/geos_lib` copies** are written under
  `TEMP_GEOS_PARENT` per existing convention; they're per-run and
  cleaned up. No shared mutable state with CC runs.

## Risks (full list in selection doc §Risks)

- Docker-in-Docker friction with OpenHands sandbox runtime → fall
  back to local runtime if needed.
- Tool-name surface differs from CC; minimax pseudo-tool-call leakage
  may re-surface → port `real_tool_tail.txt` if smoketest shows it.
- LLM provider validation in OpenHands UI may reject custom model
  name → use Advanced "custom model identifier" with
  `openrouter/minimax/minimax-m2.7`.

## Validation gate (before claiming any cross-harness finding)

- [ ] Smoketest produces parseable XML for ≥1 task.
- [ ] Full 17-task run completes with ≥80% non-error / non-timeout.
- [ ] Per-task `metadata.json` confirms model, base URL, primer
      content hash all match CC parity.
- [ ] Scorer output for OpenHands run lands in
      `data/eval/openhands_no_plugin_results/<run>/`.
- [ ] `/adversarial-review` on the runner before promoting any
      cross-harness comparison to hub.md State of Knowledge.

## Status

- 2026-04-27: Selection complete (this memo). Runner in progress.
- 2026-04-27 (later): RN-004 caught 2 P0 + 2 P1 + 1 P3. All P0/P1
  fixed and verified by smoketest #2 (`primer_in_context: true` with
  all 5 fingerprints, `activated_skills: []`, TreeSim 0.743).
- 2026-04-27 (later still): **Round-2 adversarial review skipped**
  per researcher direction. Rationale:
  - Round-1 P0/P1 fixes are verifiable in code + at runtime
    (in-build grep of patched `agent_store.py`; smoketest #2
    parity gates green on a real run).
  - The un-inspected residual that round-2 would have hit —
    OpenHands' built-in system-prompt template content vs CC's —
    is a real but soft confound. It does not falsify the
    cross-harness comparison; it shapes the framing
    ("OpenHands package vs CC package" rather than "agent loop
    only"). Documented as a limitation in `XN-016 §Limitations`.
    Future paper draft must use the package-vs-package framing.
  - Cost trade-off: skip ~10 min of review vs spend ~2 hr on
    the 17-task campaign that the deadline is biting on.
  - Mitigations if round-2 had been done are still on the table
    post-results: if anything in the 17-task pattern looks
    suspicious (e.g. one task scoring weirdly high while the
    primer is irrelevant), revisit OpenHands' built-in system
    prompt before drawing conclusions.
- 2026-04-27 (final): 17-task × 1-seed × 4-worker × 1200s timeout
  campaign launched as `oh_test17_s1`.

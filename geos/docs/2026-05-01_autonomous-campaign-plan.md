# Autonomous Campaign Plan — DSv4 ablation + cross-model

*Started 2026-05-01 evening. User went to sleep, asked me to figure
this out autonomously.*

## What the user asked for

1. Restructure the prompt into **2 primer variants**:
   1. Contract-only minimum.
   2. With method suggestions.
   No more granular than 2; user said "I'm not convinced more granularity
   is needed."
2. Test the 2 primers on Vanilla CC (DSv4-flash) — pick the better one.
3. Plan an ablation across 6 factors:
   - primer version (contract/method)
   - custom embedding search tools (RAG yes/no)
   - self-refine hook with XML presence (SR yes/no)
   - XML validation + xmllint stack (yes/no)
   - external memory: cheatsheet (yes/no)
   - self skill authorship (yes/no)
4. 3 seeds × 17 tasks on DSv4-flash for everything.
5. Then run a reduced version (only baseline + best DSv4 config) on
   3 other models: minimax/minimax-m2.7, google/gemma-4-31b-it,
   openai/gpt-oss-120b (high reasoning).
6. Analyze: quality (treesim), reliability (variance), token efficiency,
   wall-time efficiency, tool-call distribution, file-extension and
   subtree distribution.

## Decisions / scope cuts

The full naive design — 6 binary factors × 3 seeds × 17 tasks = 64 cells
× 51 runs = **3,264 task-runs** — is way too much for a sleep cycle
(8h budget). Cuts:

1. **Primer is fixed after Phase 1**. So Phase 2 is over the remaining
   5 factors, not 6.
2. **Self-skill authorship handled separately** as a single +1 cell
   (use the existing `plugin_evolving/v3/` artifact as the
   "self-evolved" treatment vs the best static config). Reason: it
   needs a multi-round runner, not a single-shot knob.
3. **Use a 2^(4-1) Resolution IV fractional factorial** for the 4
   continuous-knob factors {RAG, SR-hook, xmllint-stack, memory} = 8
   cells. Plus a baseline (all off) and the SE cell = **10 cells**.
4. **Phase 2 wall-time estimate**: 10 cells × 3 seeds × 17 tasks ≈ 510
   task-runs. At ~6min/run with 5 workers in parallel ≈ 10h. **Too
   long for sleep cycle.** Compromise:
   - Phase 2 runs first; cells launched as 1 run = (3 seeds × 17 tasks)
     so each cell runs as a batch, with ~5 workers per batch.
   - Phase 3 launches in parallel on a different endpoint (OpenRouter)
     once we have provisional best-DSv4-cell from inspecting partial
     scores after ~3h. Phase 3 doesn't compete for DeepSeek API
     bandwidth.
5. **Phase 3 reduction**: 3 other models × 2 configs × 3 seeds × 17 =
   306 runs. Runs on OpenRouter, parallel to Phase 2's tail.

## Cell design

### Phase 1 — primer screen (DSv4-flash, 1 seed, 17 tasks)

| Cell | Primer | Notes |
|---|---|---|
| P1.contract | `GEOS_PRIMER_contract.md` | minimal contract addendum |
| P1.method | `GEOS_PRIMER_method.md` | method recipe + XML skeleton + docs/inputFiles pointers |

Both run with `claude_code_no_plugin_minprimer` agent (no plugin) but
with new primer paths and reduced AGENTS.md.

### Phase 2 — DSv4 fractional factorial (3 seeds, 17 tasks per cell)

Factors to vary (post-Phase-1 primer fixed):
- **R**: RAG MCP loaded (`rag_enabled`)
- **S**: SR Stop hook (`stop_hook_enabled` — verify_outputs.py: parse-check + retry)
- **X**: xmllint stack — both the proactive MCP tool (`xmllint_mcp_enabled`) and the schema check on the Stop hook (`GEOS_HOOK_XMLLINT=1`)
- **M**: memory cheatsheet (`cheatsheet_path` = `memory_primer_dsv4_m1u.md`)

Resolution-IV 2^(4-1) design (8 cells) generators: D = ABC

| Cell | R | S | X | M | Description |
|---|---|---|---|---|---|
| F0 | - | - | - | - | baseline (just primer + AGENTS.md) |
| F1 | + | - | - | + | RAG + memory |
| F2 | - | + | - | + | SR + memory |
| F3 | + | + | - | - | RAG + SR |
| F4 | - | - | + | + | xmllint + memory |
| F5 | + | - | + | - | RAG + xmllint |
| F6 | - | + | + | - | SR + xmllint |
| F7 | + | + | + | + | everything |

Plus **+1 SE cell**: `SE` — use `plugin_evolving/v3/` (the most-evolved
agent-authored plugin) on top of Phase-1 primer.

Total: **9 cells × 3 seeds × 17 tasks = 459 task-runs**.

### Phase 3 — cross-model (3 seeds, 17 tasks)

Models (OpenRouter):
- `minimax/minimax-m2.7`
- `google/gemma-4-31b-it`
- `openai/gpt-oss-120b` (with reasoning_effort=high)

Configs:
- **baseline**: same as Phase 2 F0 cell (primer + AGENTS.md, nothing else)
- **best**: provisional pick from partial Phase 2 scores at the time
  Phase 3 launches (probably F6 = SR + xmllint or F7 = everything based
  on prior data)

Total: **3 models × 2 configs × 3 seeds × 17 tasks = 306 task-runs**.

## Output paths

- DSv4 ablation: `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/dsv4/`
- Cross-model: `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/xmodel/`
- Logs: `<root>/_logs/<run_name>.log`
- Scoring summaries: `<root>/_results/<run_name>/<agent>/_summary.json`
- Per-task: `<root>/<agent>/<run_name>/<task>/{events.jsonl,inputs/,tool_calls.json,eval_metadata.json}`

## Files I'm creating

- `plugin/GEOS_PRIMER_contract.md` — minimal contract primer
- `plugin/GEOS_PRIMER_method.md` — method primer
- `run/AGENTS.md` — reduced to pure harness contract (delete methodological prescriptions)
- `src/runner/agents.py` — add new agent variants for the campaign
- `scripts/launch_autocamp.sh` — orchestrates phases 1-3
- `scripts/score_autocamp.sh` — scores all output dirs
- `docs/2026-05-02_autonomous-campaign-results.md` — final analysis (written after data lands)

## Process commitments

- Save all per-cell metadata to results dir.
- Write progress notes back into this plan file as phases complete.
- If a phase blows up (e.g. endpoint outage on OpenRouter), document
  and continue with whatever phases are still working.
- Keep wall-time budget in mind: if Phase 2 isn't done by ~5h in,
  reduce Phase 3 to 2 seeds instead of 3.

## Status (live updates appended)

- **2026-05-01 21:00 UTC** — plan written. Starting Phase 0.

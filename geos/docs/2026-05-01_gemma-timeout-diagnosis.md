# Why gemma-4-31b-it keeps timing out on this benchmark

*Investigation 2026-05-01 evening, after gemma was DROPPED from the
autocamp Phase 3 cross-model run.*

## TL;DR

`google/gemma-4-31b-it` (and the smaller `gemma-4-26b-a4b-it`) on
OpenRouter generate output at **~1-4 minutes per tool call**,
depending on which provider OpenRouter routes to. GEOS XML authoring
tasks need 15-30+ tool calls per task, so each task needs **30-90
minutes** wall time — far above the 600s default timeout that caused
the original drop. The bottleneck is **model decoding throughput**,
not tool-execution time.

## Smoke test grid

All on `ExampleDPWellbore` with `autocamp_xmodel_baseline` (no plugin,
contract-only primer) via OpenRouter.

| model | timeout | wall elapsed | tool calls | XMLs written | provider(s) | score |
|---|---:|---:|---:|:-:|---|---:|
| `gemma-4-31b-it` | 600s | 600 (timeout) | 9 | none | DeepInfra | n/a |
| `gemma-4-26b-a4b-it` | 1800s | 1800 (timeout) | 8 | none | Ionstream | n/a |
| `gemma-4-31b-it` | 1800s | 1800 (timeout) | **15** | **3 (all 3)** | rotation: Novita/Together/Friendli | **0.958** |
| `gemma-4-31b-it:nitro` | 1200s | 1200 (timeout) | 5 | none | Novita only | n/a |

Comparators (same task, same primer, same harness):
- `deepseek-v4-flash`: ~280s elapsed, ~50 tool calls, score ~0.95
- `minimax/minimax-m2.7`: 284s elapsed, 24 tool calls, score 0.94
- `openai/gpt-oss-120b` (with stop hook): 96s, 7 tools, score 0.07

## Diagnosis

### What's slow

**Per-tool-call latency** — the time between one tool result coming
back and the next tool call being emitted. For deepseek/minimax this
is ~5-15s per turn. For gemma-4 it's **60-240s per turn** depending
on the OpenRouter provider routing.

The decoding bottleneck is on the model side. Tools execute in
milliseconds (Glob, Read, Grep are all local file ops); it's the
model emitting the next reasoning + tool-call sequence that takes
minutes.

### Why provider matters

OpenRouter routes the same `google/gemma-4-31b-it` model name to
different infrastructure providers (DeepInfra, Ionstream, Novita,
Together, Friendli, Parasail, Venice, Chutes). Each provider has
different deployment characteristics (GPU type, batching, queue
depth, etc.) which produce wildly different effective TPS for the
same model. The ~4× variance we see (1 min/tool on Novita+rotation
vs 4 min/tool on DeepInfra/Ionstream) is *all provider-side*.

The `:nitro` suffix is supposed to route to fastest provider, but in
this test it stuck on Novita-only and was *worse* than the
no-suffix variant which got rotation. OpenRouter's routing is
opaque.

### Why gemma-4 specifically

Gemma-4-31b is a 31B dense model. Its decoding TPS is fundamentally
slower than a 30B-equivalent MoE (like minimax-m2.7) at the same
batch size, because every token requires the full 31B forward pass.
On the providers OpenRouter routes to, this manifests as 5-15 t/s
output, which translates to 60-240s for a typical 1000-2000-token
tool-call response.

Compare to:
- `minimax/minimax-m2.7`: probably ~50 t/s on its OpenRouter
  provider, ~5-10s per tool-call response
- `deepseek-v4-flash` via DeepSeek's own Anthropic-compat endpoint:
  ~50-100 t/s, ~5-15s per tool-call response

### Quality is fine — when given enough time

The single gemma-4-31b smoke that managed to write all 3 XML files
(via the 1800s + provider-rotation path) **scored 0.958 on
ExampleDPWellbore**, which is competitive with deepseek-v4-flash
(0.95) and minimax-m2.7 (0.94) on the same task. So gemma can author
GEOS XML correctly; it just needs ~5-10× the wall time.

## What would make gemma viable

In rough order of effort:

1. **Vertex AI direct** (Google's own infrastructure). Likely 2-5×
   faster than OpenRouter routes since it's first-party and not
   queued. Requires switching auth path (the runner currently
   assumes Anthropic-compat OpenRouter).
2. **Local deployment on a GPU**. With vLLM on an H100, gemma-4-31b
   typically does 50-100 t/s, which would be comparable to
   deepseek-v4-flash. Requires owning/renting a GPU.
3. **Pin OpenRouter to fastest provider** via `provider.order`
   parameter (not exposed in current runner). Even with the fastest
   provider it would still be 30+ min per task; not a full fix but
   could halve the time.
4. **Accept long wall time and run smaller scope**: 1 cell × 1 seed
   × 17 tasks at ~60 min/task with workers=5 = 3.4h per cell. A
   single-cell smoke at this rate could fit in a few hours and would
   give us a meaningful gemma data point.

## Decision for the autocamp campaign

Drop gemma from Phase 3. Document this finding. If the user wants
gemma data later, the path is:
- (a) Vertex AI integration in the runner (engineering work)
- (b) Local deploy (infrastructure work)
- (c) Wait for OpenRouter to add a fast provider

The ~10× wall-time penalty makes gemma not worth the budget for an
ablation campaign. It's a viable model for individual debugging /
spot-checks but not for batch evaluation.

## Tested smoke artifacts

All under `/data/shared/.../eval/autocamp_2026-05-01/_smoke_gemma2/` :
- `smoke_xmodel_gemma` (original 600s, DeepInfra, fail)
- `smoke_gemma_26b` (1800s, Ionstream, fail)
- `smoke_gemma_31b_long` (1800s, rotation, **wrote XMLs, scored 0.958**)
- `smoke_gemma_31b_nitro` (1200s, Novita-only, fail)

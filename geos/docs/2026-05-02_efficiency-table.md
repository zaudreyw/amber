# Paper-ready efficiency table — Phase 2 (DSv4-flash, 17 tasks × 3 seeds)

*Generated 2026-05-02 from `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01`. Per-cell aggregates over all (seed × task) pairs (≤51 runs).*

## Quality + efficiency

| cell | n | quality | Δq | tools | Δtools | turns | wall (s) | tools-before-Write |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F0 | 51 | 0.910 ± 0.110 | 0.000 | 82 | 0 | 106 | 359 | 73 |
| F1 | 51 | 0.885 ± 0.099 | -0.025 | 35 | -47 | 61 | 279 | 28 |
| F2 | 51 | 0.919 ± 0.087 | +0.009 | 73 | -9 | 96 | 349 | 64 |
| F3 | 51 | 0.874 ± 0.138 | -0.036 | 34 | -47 | 60 | 274 | 27 |
| F4 | 51 | 0.921 ± 0.076 | +0.012 | 80 | -2 | 108 | 337 | 71 |
| F5 | 51 | 0.893 ± 0.138 | -0.017 | 37 | -44 | 66 | 257 | 29 |
| F6 | 51 | 0.917 ± 0.086 | +0.007 | 83 | +2 | 110 | 348 | 75 |
| F7 | 51 | 0.885 ± 0.106 | -0.024 | 35 | -47 | 62 | 274 | 27 |
| SE | 51 | 0.919 ± 0.082 | +0.010 | 69 | -13 | 94 | 321 | 60 |

## Smaller-model anchor: qwen3.6-27b (Phase 4, 1 seed × 17 tasks)

| cell | n | quality | tools | turns | wall (s) | tools-before-Write |
|---|---:|---:|---:|---:|---:|---:|
| qwen baseline (F0-eq) | 17 | 0.882 ± 0.162 | 72 | 119 | 630 | 64 |
| qwen best (F4-eq) | 17 | 0.902 ± 0.087 | 107 | 162 | 771 | 97 |

## Reading guide

- **n** = (seed, task) pairs observed (max 51 = 17 tasks × 3 seeds for DSv4; 17 for qwen 1-seed).
- **quality** = TreeSim mean ± std across runs (timeouts/failures excluded; see results doc for failures-as-0 numbers).
- **Δq, Δtools** = vs F0 baseline (no plugin, no Stop hook, no MCP, no memory).
- **tools-before-Write** = mean number of tool calls before the first Write tool. Lower = faster path to authoring.

F0 is the unaugmented DSv4-flash baseline. SE uses `plugin_evolving/v3` (DSv4-validated agent-authored plugin).
F0–F7 are the 2^(4-1) Resolution-IV factorial cells over {RAG, SR-hook, xmllint MCP, memory}.
Qwen baseline ≡ F0-equivalent on qwen3.6-27b. Qwen best ≡ F4-equivalent (xmllint MCP + plugin v3).

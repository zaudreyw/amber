# DSv4-flash migration

Date: 2026-04-27
Status: harness validated, single-seed campaign launched

## Why switch

- **Cost**: minimax/minimax-m2.7 is the most expensive model in our rotation
  via OpenRouter. DSv4-flash is roughly an order of magnitude cheaper per
  token *and* produces shorter completions (probe: 1116-1291 tokens for a
  250-word ask vs minimax's 2721-11437 tokens for the same prompt). For a
  17-task × 3-seed campaign the cost is ~$2.50 vs ~$30.
- **Speed**: DSv4-flash is **faster** than minimax on a per-call basis.
  Probe TPS:
  - `openrouter:minimax/minimax-m2.7` — ~40-50 TPS
  - `openrouter:deepseek/deepseek-v4-flash` — ~75 TPS
  - `deepseek:deepseek-v4-flash` — ~70 TPS (direct API, slightly tighter
    p99 latency)
- **Quality**: TBD on a multi-seed campaign. Single-task `ExampleMandel`
  spot check: DSv4-direct treesim 0.301; minimax m2.7 vanilla CC seed
  range 0.269 / 0.280 / 0.925 (mean 0.491, σ ≈ 0.37). DSv4 sits inside
  minimax's wide range.

## Why DeepSeek-direct, not OpenRouter

When we tried `openrouter:deepseek/deepseek-v4-flash` end-to-end the
harness was unusable: the 40-min `dsv4flash_smoke2` run accumulated **30
api_retry events with `error_status: 429 / error: rate_limit`**, eating
~25 of the 40 minutes. Sustained CC sessions on OpenRouter trip a
rate-limit threshold our minimax campaigns don't hit.

DeepSeek serves the same model on a separate quota at
`https://api.deepseek.com/anthropic`. They publish an Anthropic-compatible
endpoint specifically for Claude Code (see
<https://api-docs.deepseek.com/guides/coding_agents>). Switching is just
two env vars; no code changes are needed.

Smoketest result on `ExampleMandel` (vanilla CC):
| Path | Wallclock | Tool calls | api_retry | Output XMLs |
|---|---:|---:|---:|---:|
| OpenRouter (`dsv4flash_smoke2`)   | 40m timeout | 18 | **30 (all 429)** | none |
| DeepSeek-direct (`dsv4flash_direct_smoke`) | **5m 14s success** | 30 | **0** | 3/3 (full deck) |

Verdict: DeepSeek-direct is the only viable path for sustained CC use.

## How to use it

### Environment

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
```

`DEEPSEEK_API_KEY` is already in `.env`. The runner reads
`ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` from the host env and
forwards them into the Docker container — no changes to `runner/`.

### Model name

DeepSeek-direct expects bare `deepseek-v4-flash`, NOT
`deepseek/deepseek-v4-flash` (the OpenRouter prefix). Pass via
`--claude-model deepseek-v4-flash`.

### Example invocation

```bash
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic \
ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY" \
python3 scripts/run_experiment.py \
    --run dsv4flash_direct_s1 \
    --agents claude_code_no_plugin \
    --workers 6 \
    --timeout 1500 \
    --claude-model deepseek-v4-flash \
    --include <task list>
```

### Other models on DeepSeek-direct

| Model alias | Real model |
|---|---|
| `deepseek-v4-flash` | DSv4-flash (~75 TPS, cheap, our new default for vanilla) |
| `deepseek-v4-pro` | DSv4-pro (slower, more capable; not yet probed in our harness) |

DeepSeek's docs (`api-docs.deepseek.com/guides/coding_agents`) also
suggest setting `ANTHROPIC_DEFAULT_OPUS_MODEL` and
`ANTHROPIC_DEFAULT_SONNET_MODEL` for sub-agent dispatch, but our runner
only uses the model passed via `--claude-model` so that's not needed.

## Probing other providers

`scripts/api_probe.py` is the multi-provider latency probe. Use it to
sanity-check before launching a campaign:

```bash
python3 scripts/api_probe.py \
    --target deepseek:deepseek-v4-flash \
    --target openrouter:deepseek/deepseek-v4-flash \
    --target openrouter:minimax/minimax-m2.7 \
    --runs 3
```

Supported providers: `openrouter`, `deepseek`, `openai`, `anthropic`.
Keys auto-loaded from `.env`.

## Future code change (optional)

Right now the per-agent config in `src/runner/agents.py` doesn't carry an
`anthropic_base_url` field — routing is purely via env vars. If we want
to permanently anchor `claude_code_no_plugin` (or a new
`claude_code_no_plugin_dsv4`) to DeepSeek-direct, we should:

1. Add an `anthropic_base_url` field to the agent dict.
2. Have `runner.docker_cmd` set `ANTHROPIC_BASE_URL` in the docker env
   based on `agent.get("anthropic_base_url")` instead of (or with
   precedence over) the host env.

For now, env-var-based routing is simple and explicit at the launch
site. Wire the in-config version when we settle on DSv4 as the
permanent successor to minimax.

## Open questions

- **Quality at scale**: confirmed working on `ExampleMandel`; need
  17-task × multi-seed mean treesim to compare to minimax baseline.
  Campaign launched today (`dsv4flash_direct_s1`); decision after.
- **DSv4-pro**: untested in our harness. Slower & more accurate;
  worth a single-task probe + a small comparison if we need a stronger
  model than DSv4-flash for harder tasks.
- **DeepSeek rate limits**: we have a separate quota from OpenRouter,
  but we haven't stress-tested it yet at workers=6+ on 17 tasks. The
  current campaign will surface any throttling.

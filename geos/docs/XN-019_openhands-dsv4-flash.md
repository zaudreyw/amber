---
id: XN-019
title: "OpenHands on DSv4-flash — integration, vanilla vs adaptations, multi-seed"
date: 2026-04-28
dag_nodes: [I12]
links:
  derived_from: [XN-016, D-009]
  related_to: [XN-005, XN-013, XN-014, XN-015]
tags: [baseline, harness, openhands, dsv4, cross-harness, ablation]
status: in-progress
---

# XN-019 — OpenHands on DSv4-flash + adaptations

*Continues XN-016 (which was minimax-m2.7 only). Adds DSv4-flash
support to the OH harness and tests two conditions on it.*

## Why

XN-016 left two things open:

1. **Multi-seed DSv4-flash on vanilla OH** was attempted on
   2026-04-27 (`oh_dsv4or_smoke`) but timed out at 600s on the
   single Sneddon smoketest with 0 file writes. Documented as a
   blocker; deferred.
2. **Do our domain adaptations (RAG plugin, memory primer,
   self-refine hook) help on top of OH's strong baseline?** Never
   tested cross-harness with the same model.

Now that the CC pipeline has settled on **DSv4-flash + minimal primer**
as the SOTA stack (XN-015 / 2026-04-27 session summary; vanilla CC + minimal
primer = 0.671, vs full primer 0.640), the cross-harness comparison
should be on that same model+primer combo. Otherwise we're comparing
apples to oranges.

## DSv4-flash → OH integration (the hard part)

### What broke

OH 1.15.0 uses **LiteLLM** as the LLM layer. The natural routing
`LLM_MODEL=deepseek/deepseek-v4-flash` failed in three distinct ways:

1. **`security_risk` validation error.** OH's headless CLI installs
   `LLMSecurityAnalyzer()` which mandates a `security_risk` field on
   every tool call. DSv4-flash omits the field. OH raises after 2
   errors → conversation aborted.
2. **`reasoning_content` round-trip 400.** Once tool calls succeed, the
   next request fails with
   `litellm.BadRequestError: DeepseekException - "The reasoning_content
   in the thinking mode must be passed back to the API."` because OH's
   `model_features` only flags `deepseek/deepseek-reasoner` for
   `send_reasoning_content=True`, not `deepseek-v4-flash` (which also
   returns `reasoning_content`).
3. **`reasoning_effort=none` doesn't disable thinking.** Setting
   `LLM_REASONING_EFFORT=none` gets OH to omit the `thinking`
   parameter, but DeepSeek's `deepseek-v4-flash` defaults to
   thinking-on regardless. Even the legacy alias
   `deepseek-chat` (documented as "non-thinking mode of
   deepseek-v4-flash") still returns `reasoning_content`.

### The fix (three patches in `run/Dockerfile.openhands`)

1. **Sed-patch `openhands_cli/setup.py`** to skip the
   `set_security_analyzer(LLMSecurityAnalyzer())` line. With
   `security_analyzer=None` the SDK's
   `_extract_security_risk()` short-circuits to
   `SecurityRisk.UNKNOWN` instead of raising.
2. **Python-patch `model_features.py`** to add
   `deepseek/deepseek-v4-flash`, `deepseek/deepseek-chat`, and
   `deepseek/deepseek-v4-pro` to `SEND_REASONING_CONTENT_MODELS`.
   Now OH echoes prior `reasoning_content` on every request — DeepSeek
   stops complaining.
3. **At launch:** pass
   `LLM_LITELLM_EXTRA_BODY='{"thinking":{"type":"disabled"}}'` via
   `--llm-env` so DeepSeek never enables thinking on outgoing
   requests in the first place. This is the canonical knob from the
   DeepSeek API docs and removes the round-trip surface entirely.
   With this set, patch #2 becomes belt-and-braces (no
   `reasoning_content` is ever returned), but I leave it in so the
   image still works without the env var if someone wants thinking
   on later.

### Why not the simpler paths

- **Update LiteLLM**: OH 1.15.0 pins `litellm==1.83.14`. Newer LiteLLM
  may have changed the `deepseek/` provider transformations and
  `model_features` logic — but bumping LiteLLM under OH risks ABI
  breakage with the rest of the SDK. Three sed-style patches are
  smaller blast radius.
- **Use `deepseek-chat` instead of `deepseek-v4-flash`**: same
  underlying model, but verifying that *deepseek-v4-flash* itself works
  matters because that's what our CC SOTA runs on (per the migration
  doc). I want exact model parity, not "same model under a different
  alias."
- **Patch LiteLLM's deepseek provider to enforce reasoning_content
  preservation**: would need to maintain a downstream LiteLLM patch.
  Disabling thinking via the documented API knob is upstream-clean.

### Smoketest

`TutorialSneddon`, `deepseek/deepseek-v4-flash`,
`plugin/GEOS_PRIMER_minimal.md`,
`LLM_LITELLM_EXTRA_BODY='{"thinking":{"type":"disabled"}}'`:

- ✅ status `success`
- 7/7 expected XML files written (5.6 min wall)
- 31 FileEditor + 6 Terminal + 3 TaskTracker tool calls
- prompt_tokens 959K (cache_read 899K), completion 19.5K
- `accumulated_cost_usd = 0.0` — token cost summing isn't wired in
  LiteLLM for the `deepseek/` provider, so we have to reconstruct
  cost manually from `prompt_tokens × $0.14/M + cache_read × $0.0028/M
  + completion × $0.28/M` (DeepSeek's published pricing, 2026-04-28).

## Conditions tested

| Condition | Primer | RAG (MCP plugin) | Memory primer | Self-refine | Seeds |
|---|---|:---:|---|:---:|---|
| `oh_dsv4_vanilla_s{1,2}` | minimal | – | – | 0 | 2 |
| `oh_dsv4_adapt_s{1,2}`   | minimal | ✓ | M1-u | 2 | 2 |

The "adapt" condition stacks all three CC adaptations the OH harness
can host:

- **RAG**: same `geos-rag` MCP plugin (search_navigator,
  search_technical, search_schema). Mounts `plugin/` and the vector DB
  read-only and writes `/workspace/.openhands/mcp.json` so OH's MCP
  loader picks it up.
- **Memory primer**: `plugin/memory_primer_m1u.md` (the M1-u variant —
  ungated 1-shot memory primer that won the D-008 ablation on minimax).
  Prepended to the inline user message above the task spec, parallel to
  CC's `cheatsheet_path` plumbing.
- **Self-refine**: post-hoc retry loop in `scripts/openhands_eval.py`.
  After OH finishes, if `/workspace/inputs/` has 0 XMLs or any XML
  fails `xml.etree.ParseError`, re-invoke OH in the same workspace
  with a feedback `-t` describing the issue. Cap = 2 extra attempts.
  Mirrors `plugin/hooks/verify_outputs.py` which CC runs as a Stop
  hook. Note: no schema validation in this version (the CC plugin's
  `xmllint --schema` hook isn't ported yet).

Conditions that are **NOT** tested in this batch (deliberate scope cut):
- `xmllint --schema` Stop hook ported to OH.
- M-placebo / no-memory-primer ablation within the adapt stack.
- `--memory-primer plugin/memory_primer_m4u.md` (the gated M4-u variant).

## Run commands (verbatim)

Vanilla:
```bash
for SEED in 1 2; do
  python3 scripts/openhands_eval.py \
    --run-name "oh_dsv4_vanilla_s${SEED}" \
    --model deepseek/deepseek-v4-flash --base-url "" \
    --api-key-env DEEPSEEK_API_KEY \
    --primer-path plugin/GEOS_PRIMER_minimal.md \
    --tmp-geos-parent /data/shared/geophysics_agent_data/data/eval/tmp_geos_matt \
    --workers 4 --timeout 1800 \
    --llm-env 'LLM_LITELLM_EXTRA_BODY={"thinking":{"type":"disabled"}}'
done
```

Adapt:
```bash
for SEED in 1 2; do
  python3 scripts/openhands_eval.py \
    --run-name "oh_dsv4_adapt_s${SEED}" \
    --model deepseek/deepseek-v4-flash --base-url "" \
    --api-key-env DEEPSEEK_API_KEY \
    --primer-path plugin/GEOS_PRIMER_minimal.md \
    --plugin --memory-primer plugin/memory_primer_m1u.md \
    --self-refine 2 \
    --tmp-geos-parent /data/shared/geophysics_agent_data/data/eval/tmp_geos_matt \
    --workers 4 --timeout 1800 \
    --llm-env 'LLM_LITELLM_EXTRA_BODY={"thinking":{"type":"disabled"}}'
done
```

Scoring (failures-as-zero is the convention from prior XN- notes):
```bash
for d in oh_dsv4_vanilla_s1 oh_dsv4_vanilla_s2 oh_dsv4_adapt_s1 oh_dsv4_adapt_s2; do
  python3 scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/openhands_no_plugin/$d \
    --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
    --results-dir data/eval/results/$d/openhands_no_plugin
done
python3 scripts/oh_dsv4_compare.py
```

## Results

### Pre-campaign smoketest evidence

| Smoke | status | XMLs | wall (s) | tool calls | prompt tok | completion tok |
|---|---|---:|---:|---|---:|---:|
| Vanilla (`oh_dsv4_v5_smoke`)  | success | 7/7 | 337 | 31 FE + 6 Term + 3 TT | 959K | 19.5K |
| Adapt (`oh_dsv4_adapt_smoke`) | success | 7/7 | 379 | 34 FE + 9 Term + 4 TT + 3 MCP + 1 Task | 1.07M | 22.2K |

`oh_dsv4_adapt_smoke` MCP=3 confirms the geos-rag plugin engaged.

### 17-task headline (failures-as-zero, n=2 seeds)

| Condition | per-task mean | σ across 17 means | pass≥0.7 | $/seed |
|---|---:|---:|:---:|---:|
| OH vanilla (DSv4-flash, minimal primer) | **0.551** | 0.356 | 7/17 | $0.14 |
| OH adapt (RAG + M1-u memory + self-refine ≤2) | **0.598** | 0.335 | 8/17 | $0.16 |
| **Reference: CC vanilla DSv4-flash + minimal primer (3 seeds)** | **0.671** | 0.014 | 17/17 | n/a |

The CC reference is from `docs/2026-04-27_session_summary.md` Group A.

Two things stand out:

1. **Both OH conditions underperform the CC vanilla baseline by ~0.07-0.12pp** despite running the same model + same minimal primer.
2. **σ across the 17 task-means is ~25× larger for OH than for CC** (0.336 vs 0.014). This is dominated by *categorical* failures: in the OH runs, ~6-7 tasks per seed write zero XML files and score 0, while the rest score in the 0.7-1.0 range. CC essentially never has the zero-write failure mode.

### Adapt vs vanilla within OH (paired by task seed-mean)

| | adapt > vanilla | adapt = vanilla (|Δ|≤0.01) | adapt < vanilla |
|---|:---:|:---:|:---:|
| Tasks (n=17) | 9 | 4 | 4 |

**Mean Δ (adapt − vanilla) = +0.046 (σ across tasks 0.303)**

With n=2 seeds and σ that high, this is **not** statistically distinguishable from zero. The wins are concentrated where vanilla fails outright and adapt's self-refine recovers a useful XML (`AdvancedExampleDruckerPrager`, `AdvancedExampleViscoDruckerPrager`, `ExampleIsothermalLeakyWell`, `TutorialPoroelasticity`, `TutorialSneddon` — all +0.23 to +0.48). The losses are tasks where vanilla happened to hit a good seed in s1 or s2 and adapt didn't (`ExampleThermoporoelasticConsolidation` -0.47, `AdvancedExampleExtendedDruckerPrager` -0.50, `AdvancedExampleModifiedCamClay` -0.40). This is exactly the "high-σ binary outcomes" pattern visible in the raw σ.

| Task | vanilla mean | adapt mean | Δ |
|---|---:|---:|---:|
| AdvancedExampleCasedContactThermoElasticWellbore | 0.412 | 0.407 | -0.005 |
| AdvancedExampleDeviatedElasticWellbore | 0.888 | 0.910 | +0.022 |
| AdvancedExampleDruckerPrager | 0.000 | 0.388 | **+0.388** |
| AdvancedExampleExtendedDruckerPrager | 0.499 | 0.000 | **-0.499** |
| AdvancedExampleModifiedCamClay | 0.500 | 0.100 | **-0.400** |
| AdvancedExampleViscoDruckerPrager | 0.000 | 0.475 | **+0.475** |
| buckleyLeverettProblem | 0.000 | 0.000 | 0 |
| ExampleDPWellbore | 0.875 | 0.905 | +0.031 |
| ExampleEDPWellbore | 0.998 | 0.882 | -0.116 |
| ExampleIsothermalLeakyWell | 0.325 | 0.770 | **+0.445** |
| ExampleMandel | 0.370 | 0.624 | +0.254 |
| ExampleThermalLeakyWell | 0.868 | 0.891 | +0.022 |
| ExampleThermoporoelasticConsolidation | 0.885 | 0.416 | **-0.469** |
| kgdExperimentValidation | 0.932 | 0.930 | -0.002 |
| pknViscosityDominated | 0.998 | 0.997 | -0.001 |
| TutorialPoroelasticity | 0.399 | 0.811 | **+0.411** |
| TutorialSneddon | 0.425 | 0.659 | +0.234 |

### Self-refine effectiveness

- adapt_s1: self-refine fired on **9 of 17** tasks (53%); only 5 tasks ended with zero XMLs after retries.
- adapt_s2: self-refine fired on **7 of 17** tasks (41%); 4 tasks ended with zero XMLs.

So the loop does drive failures down (vanilla 6.5/17 → adapt 4.5/17 zero-XML on average) but ~25-50% of "needs refinement" tasks still don't recover. Inspection of `AdvancedExampleDruckerPrager` adapt_s1 (3 attempts, all "success" exit, all 0 XML): the agent reads workspace, calls `task_tracker`, and ends turn — even after explicit `"Write at least one well-formed GEOS input XML"` feedback. The model gets stuck in a "I'm done" pattern that re-prompting doesn't break.

### Cost (DeepSeek pricing 2026-04-28)

| Run | prompt tok | cache_read | completion | cost (USD) |
|---|---:|---:|---:|---:|
| oh_dsv4_vanilla_s1 | 7.18M | 6.71M | 168K | $0.133 |
| oh_dsv4_vanilla_s2 | 8.26M | 7.71M | 208K | $0.157 |
| oh_dsv4_adapt_s1   | 8.35M | 7.79M | 171K | $0.149 |
| oh_dsv4_adapt_s2   | 8.88M | 8.28M | 198K | $0.161 |

Each 17-task seed costs $0.13-$0.16, much cheaper than minimax-m2.7 (XN-016 reported ~$0.10/task on minimax for adapt; here it's ~$0.01/task). Self-refine adds only ~$0.02/seed (~14%).

## Mechanism: why OH-vanilla < CC-vanilla on the same model

Top suspects, in order of likely contribution:

1. **Thinking-mode parity gap.** OH runs DSv4-flash with
   `LLM_LITELLM_EXTRA_BODY={"thinking":{"type":"disabled"}}` (forced
   off to dodge the `reasoning_content` round-trip). CC runs DSv4-flash
   via `https://api.deepseek.com/anthropic` with thinking ON. The CC
   migration doc records `reasoning_tokens > 0` on every CC call.
   This is the *only* known knob that differs between OH and CC for
   the same model.
2. **Early-end-turn failure mode.** Without thinking actively driving
   planning, DSv4-flash on OH's headless loop terminates after
   exploration without writing XML on ~38-40% of tasks. CC has the
   `verify_outputs.py` Stop hook by default which forces re-prompt
   when `/workspace/inputs/` is empty. Our OH self-refine implements
   the same idea but only recovers ~half of those tasks (the model
   stays stuck even with explicit feedback).
3. **OH agent overhead in context.** OH's headless agent has scaffolding
   (TaskTrackerAction, security-risk wrapping at the schema level
   even when the analyzer is patched off, summary fields, project-skill
   hooks). The system prompt is ~7-8K tokens before our primer. CC's
   `claude_code_no_plugin` is leaner. This is hard to ablate without
   re-engineering OH.

## Proposed next steps (not in this batch)

- **Re-run with thinking ON** once we patch the `reasoning_content`
  round-trip end-to-end (LiteLLM upstream may have it fixed in a
  newer pin). This should close most of the 0.07-0.12pp gap to CC.
- Port the `xmllint --schema` Stop hook into the self-refine loop so
  schema-violating XMLs trigger a retry. Currently we only catch
  unparseable XML.
- Consider a **stronger feedback message** for self-refine that also
  attaches a short reminder of the spec: this might break the
  "I'm done" pattern.
- Re-run with **3 seeds** to bring σ down enough that the vanilla
  vs adapt delta (or its absence) is statistically interpretable.

## Limitations

1. **No xmllint Stop hook on OH.** Self-refine here only catches
   parse failure, not schema violations. CC's full SOTA stack uses
   xmllint --schema for ablation `claude_code_repo3_plugin_xmllint_all`;
   the OH adapt condition is one notch weaker than the CC SOTA stack.
2. **2 seeds, not 3.** Time budget. CC SOTA results in
   `2026-04-27_session_summary.md` use 3 seeds. With n=2 the σ estimate
   is noisier — interpret deltas with caution.
3. **Token cost not auto-summed.** LiteLLM's
   `accumulated_cost_usd` returns 0 for `deepseek/*` provider. We
   compute cost post-hoc from prompt/completion tokens × DeepSeek
   pricing.
4. **`reasoning_content` patch is image-baked.** If OH bumps to a newer
   version of `model_features.py`, the python patch in
   `Dockerfile.openhands` will break (it asserts the
   `deepseek-reasoner` needle is present). Scan `model_features.py`
   when bumping the OH pin.
5. **Thinking disabled.** We're running DSv4-flash with thinking off
   — this matches `deepseek-chat` semantics. The CC pipeline runs
   DSv4-flash via the Anthropic-compat endpoint with thinking ON. So
   the OH-vanilla vs CC-vanilla cross-harness comparison has a
   thinking-mode parity gap that **is not** visible in the
   `model=deepseek/deepseek-v4-flash` string. Document this clearly
   when reporting the cross-harness delta.

## Decisions

- Locked OH model name to `deepseek/deepseek-v4-flash` (with thinking
  off via `LLM_LITELLM_EXTRA_BODY`). Not `deepseek-chat`. The two are
  the same underlying model per DeepSeek docs but the explicit name
  matches the CC migration doc and is grep-able.
- Locked OH primer to `plugin/GEOS_PRIMER_minimal.md` for the
  cross-harness comparison. Matches the current CC SOTA stack.
- The three Dockerfile patches (model_features, security_analyzer,
  user/public skills) are now load-bearing for any DSv4 OH run —
  document and re-verify on every OH version bump.

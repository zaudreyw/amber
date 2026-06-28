# Session summary — 2026-04-27

A roughly day-long working session covering: harness bug discovery & fix,
codebase refactor, model migration (minimax → DSv4-flash), schema-validation
infrastructure (xmllint), several cross-cutting analyses, and seven new
agent variants. This doc cross-references the dated finding docs and is
intended as the single entry point for "what happened today."

## Quick links to artifacts produced

- `docs/2026-04-27_vanilla-cc-stale-plugin-call-bug.md` — the harness bug
- `docs/2026-04-27_dsv4_migration.md` — model migration design + smoketest evidence
- `docs/2026-04-27_4condition-file-tool-comparison.md` — file-access + tool-usage comparison across the 4 canonical conditions, with Bash analysis and the read-math breakdown the user asked about
- `docs/2026-04-27_file-access-and-tool-usage-analysis.md` — broader cross-run analysis
- `docs/xmllint_validation.md` — schema-validation investigation
- `docs/2026-04-27_xmllint-validation-summary.md` — index entry
- `scripts/api_probe.py` — multi-provider latency probe (OpenRouter / DeepSeek / OpenAI / Anthropic)
- `scripts/analysis/analyze_file_access.py`, `analyze_tool_usage.py`,
  `compare_4conditions.py` — cross-run analysis tooling
- `src/runner/` — refactor of the 3500-line run_experiment.py into 17 modules

## Threads, in approximate order

### 1. Vanilla-CC stale-plugin-call bug

**Symptom**: An earlier gemma-4-31b vanilla-CC smoketest looked like it had
plugin tools loaded — its `status.json` showed `plugin_tool_calls: 4` and
non-zero `mcp__geos-rag__*` counts.

**Root cause** (two real bugs):
1. `build_system_prompt` unconditionally appended a paragraph saying "Use
   the MCP tools mcp__geos-rag__search_*" regardless of `enable_plugin`.
   Vanilla CC saw a system prompt instructing it to call tools that were
   not loaded. Some models (gemma-4, deepseek-v3.2) bit and emitted
   phantom tool_use blocks; minimax m2.7 and qwen 3.5 ignored.
2. `per_tool_counts` increments on attempted tool calls, including ones
   that error with "No such tool available".

**Cross-model audit**: 0 stale calls in 52 minimax m2.7 task-runs, 100% in
gemma-4-31b (1/1 sampled), 94% in deepseek-v3.2 v2 era. The phenomenon was
model-specific.

**Fix**: thread `plugin_enabled` into `build_system_prompt` and gate the
RAG instruction paragraph behind it. When false, replace with a short
"use Read/Glob/Grep/Bash" fallback. The metrics-quality bug
(`per_tool_counts` over-counts) is acknowledged but not fixed in code;
the new `analyze_tool_usage.py` script computes
`succeeded_count = attempted - errored` from events.jsonl as the
source-of-truth column for fair comparisons.

Implication: prior `claude_code_no_plugin` baselines on minimax m2.7
were unaffected; ones on deepseek-v3.2 v2 / gemma-4 should be re-run if
those numbers ever appear in the paper.

### 2. xmllint validation investigation

**Premise**: A meaningful chunk of failures fall in the "F1 schema
hallucination" class (invented element/attribute names). The user
proposed wiring schema validation into the harness.

**Findings**:
- `xmllint --schema $GEOS_SCHEMA input.xml` works perfectly. Errors are
  highly actionable: bad element names get the *expected alternatives*
  listed; missing required attributes get the attribute name; bad
  attribute spellings get the offending attribute.
- The agent already invokes xmllint **91 times across 87 task-runs** in
  ~10% of all tasks without us prompting it explicitly — but the prompt
  buries the mention inside a "Validating Input Files" subsection, the
  schema path is not in the prompt at all, and only ~10% of tasks bite.
- The chromadb is path-scoped to `src/docs/sphinx/`. **87 GEOS rst files
  exist outside that path and are invisible to RAG**, including
  `InputXMLFiles.rst` (which documents xmllint usage). Vanilla CC reads
  these via Glob/Grep; plugin variants do not.

**Three integration paths implemented**:
1. **xmllint-aware primer** (`plugin/GEOS_PRIMER_xmllint.md`) — prominent
   "REQUIRED before declaring done" section with the absolute schema
   path and 3-bullet hint about reading xmllint errors. Activated via
   `--strip-baked-primer --geos-primer-path plugin/GEOS_PRIMER_xmllint.md`.
2. **MCP tool** (`plugin/scripts/xmllint_mcp.py`) — exposes
   `mcp__xmllint__validate_geos_xml(xml_path)`. Wired via the
   `xmllint_mcp_enabled: True` flag in the agent dict.
3. **Stop-hook xmllint check** in `plugin/hooks/verify_outputs.py` —
   gated on `GEOS_HOOK_XMLLINT=1`. After the existing parse check, runs
   `xmllint --schema` per file and blocks with formatted errors as
   feedback (capped at 8 errors/file × 4 files). Counts toward the
   existing retry budget.

The container `geos-eval` was rebuilt to add `libxml2-utils`. Verified
the hook end-to-end on a known-bad model output (`m4g_s2 /
pknViscosityDominated_base.xml`); the hook correctly blocks with
structured feedback identifying the hallucinated
`CompressibleSolidCappedPlatesPorosity` element and the missing
`defaultViscosity` attribute.

### 3. Refactor of `scripts/run_experiment.py`

Single 3500-line file → `src/runner/` package with 17 modules (largest
584 lines). Long prompt strings extracted to `src/runner/prompts/*.txt`;
dashboard HTML to `src/runner/dashboard/template.html`. The CLI shim at
`scripts/run_experiment.py` is now 16 lines.

Verified by:
- SHA-256 fingerprint of `build_system_prompt` output across 4 agents
  matches pre-refactor baseline byte-for-byte.
- `--help` byte-identical to baseline.
- `--dry-run` docker command lines for 3 agents identical to baseline
  (modulo timestamps).
- 16 module imports clean.

Followup merge: the leftover `src/runner/contamination.py` was absorbed
into the new package; the awkward `repo3_runner` working name was
renamed to `runner`.

### 4. Cross-run analyses

Two new analysis scripts run across all 908 completed task-runs:

**`scripts/analysis/analyze_file_access.py`** — categorizes Read /
Glob / Grep / Bash invocations per (agent, run, task), buckets file
paths into rst_sphinx / rst_nonsphinx / xml_input_files / xml_workspace
/ xsd_schema / python / other.

**`scripts/analysis/analyze_tool_usage.py`** — re-derives tool counts
from events.jsonl, splits attempted vs succeeded, flags discrepancies
with status.json (25 found out of 908 runs, all minor).

**Headline findings (4-condition comparison, minimax m2.7, 17-task test set)**:

| Condition | Tool calls/task | RST sphinx/task | RST non-sphinx/task | XML examples/task | xmllint/task |
|---|---:|---:|---:|---:|---:|
| CC (vanilla) | 37.1 | 1.55 | **0.55** | **8.1** | 0.06 |
| CC + RAG | 31.1 | 0.00 | 0.00 | 0.1 | 0.06 |
| CC + RAG + hook | 27.9 | 0.01 | 0.00 | 1.1 | 0.07 |
| CC + RAG + hook + memory (M1-u) | 23.9 | 0.02 | 0.00 | **2.4** | 0.08 |

Key observations:
- **Vanilla CC discovers non-sphinx rst files** that plugin variants miss.
  Plugin variants are anchored to whatever the indexer covered — the
  chromadb gap is a structural confound for the plugin-vs-vanilla
  comparison.
- **Memory primer doubles XML example reads** (1.1 → 2.4) because the
  primer names specific reference XMLs.
- **xmllint usage is harness-independent** at ~0.06-0.08/task; baking it
  in (hook or tool) amplifies an existing behavior.
- **Vanilla CC uses Bash for filesystem search** ~3× more than the
  dedicated Glob/Grep tools (find/ls 59% of Bash, grep/rg 26%). Total
  filesystem-search effort: ~15.5 calls/task vs 12.4 Reads/task — the
  agent's main activity is searching, not reading.

### 5. Model migration: minimax → DSv4-flash

DeepSeek released v4-pro and v4-flash. v4-flash is roughly an order of
magnitude cheaper than minimax m2.7 and benchmarked faster
(~75 TPS vs ~40-50).

**The smoketest stalemate**:
- DSv4-flash via OpenRouter — 40-min timeout, **30 OpenRouter
  rate_limit retries** ate ~25 minutes. The model itself is fast; the
  provider was throttling sustained CC sessions.
- Gemma-4-31b — 40-min timeout with 0 retries. Just genuinely slow
  per-turn (~4 min between assistant messages).

**Probe** (`scripts/api_probe.py`) confirmed simple-prompt latency:

| Target | Latency (mean) |
|---|---:|
| `deepseek:deepseek-v4-flash` (direct) | 0.97s |
| `openrouter:deepseek/deepseek-v4-flash` | 1.20s |
| `openrouter:minimax/minimax-m2.7` | 4.60s |

**The fix**: route through DeepSeek's Anthropic-compatible endpoint at
`https://api.deepseek.com/anthropic` with `DEEPSEEK_API_KEY`. Docs:
<https://api-docs.deepseek.com/guides/coding_agents>. No code changes —
just two env vars (`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`).

**Validation**:
- `dsv4flash_direct_smoke` (single-task) — 5m 14s success, 0 retries,
  treesim 0.301 (within minimax variance).
- `dsv4flash_direct_s1` (full 17-task) — **17/17 success, mean treesim
  0.647, 0 retries**. Beats best minimax seed (0.66 mm_noplug_run1)
  within rounding.

### 6. Minimal-primer ablation (botched test, then fixed)

Discovered that the prior `minprimer_run1` (April 20) was a NULL
ablation: AGENTS.md already contained `# GEOS Primer` baked in, and the
`build_system_prompt` guard suppressed any external primer when
AGENTS.md already had one. The minimal primer file was loaded but
discarded — system prompt was byte-identical to the regular condition.

**Fix**: added `--strip-baked-primer` flag that strips the `# GEOS
Primer` block out of AGENTS.md before injection. Then the file passed
via `--geos-primer-path` is actually inlined.

**Real ablation** (single seed, minimax m2.7, vanilla CC):
- Full primer baseline mean treesim (3 seeds): 0.558 (range 0.45-0.66)
- Minimal primer (1 seed): 0.625

Within seed variance — single-seed result is suggestive but not
conclusive. A 3-seed DSv4 follow-up was launched at session end to
disambiguate (see "Open campaigns" below).

The minimal primer is also vanilla-CC-friendly: created
`plugin/GEOS_PRIMER_minimal_vanilla.md` as a copy of the original
minimal primer with the `mcp__geos-rag__search_*` mention replaced by a
"Glob / Grep / Read against /geos_lib/inputFiles/" workflow step. This
prevents the same phantom-tool problem from recurring under the
ablation.

### 7. xmllint ablation cells

Two cells launched on top of CC + RAG + hook + minimax m2.7:

| Cell | Treatment | n_scored | Mean treesim |
|---|---|---:|---:|
| baseline (existing pac1_plug_hook) | none | varies | ~0.50 |
| primer-only (`xmllint_primer_mm_s1`) | xmllint primer + path | 17/17 | 0.556 |
| hook-only (`xmllint_hook_mm_s1`) | hook validates against schema | 17/17 | 0.567 |

Both treatments hit **17/17 completion** vs the baseline's typical
14-16/17 — the strongest signal: schema awareness pushes the agent to
finish authoring rather than ending with broken or absent XML. Single
seed; quality on scored tasks is statistically indistinguishable from
baseline at this n.

## New artifacts (code, configs, primers)

### Source code
- `src/runner/` — full eval-harness package (refactor)
- `scripts/api_probe.py` — multi-provider latency probe
- `scripts/analysis/analyze_file_access.py`
- `scripts/analysis/analyze_tool_usage.py`
- `scripts/analysis/compare_4conditions.py`
- `plugin/scripts/xmllint_mcp.py`
- `plugin/hooks/verify_outputs.py` (extended)
- `run/Dockerfile` (added `libxml2-utils`)

### Primers
- `plugin/GEOS_PRIMER_xmllint.md` — full primer + xmllint-aware section + absolute schema path
- `plugin/GEOS_PRIMER_minimal_vanilla.md` — vanilla-CC-compatible minimal primer

### CLI flags added
- `--strip-baked-primer` (in `runner.cli`) — drops the embedded primer
  out of AGENTS.md so `--geos-primer-path` actually takes effect.

### Agent variants registered (in `src/runner/agents.py`)
- `claude_code_no_plugin_minprimer`
- `claude_code_repo3_plugin_xmllint_primer`
- `claude_code_repo3_plugin_xmllint_hook`
- `claude_code_repo3_plugin_xmllint_all`

### Env vars (passed through to container)
- `GEOS_HOOK_XMLLINT` — enable hook schema validation
- `GEOS_HOOK_SCHEMA_PATH` — override schema path

## Headline result table (final)

Mean treesim ± std dev across seeds, 17-task test set, all 17 tasks scored
unless noted. n is seed count.

### Group A — Vanilla CC primer ablation (DSv4-flash, DeepSeek-direct)

| Condition | n | Mean | σ | Notes |
|---|---:|---:|---:|---|
| Vanilla CC + **full** primer | 3 | 0.640 | 0.008 | s1=0.647, s2=0.641, s3=0.632 (16/17 scored on s3 — disk-full incident clobbered 1 task) |
| Vanilla CC + **minimal** primer | 3 | **0.671** | 0.014 | s1=0.687, s2=0.666, s3=0.661 (17/17 each) |

**Minimal primer wins by +0.031.** Tight σ on both — high-confidence delta.
Surprising because minimal primer is ~38% the size of the full primer
(7868 vs 20807 chars in the assembled system prompt). Suggests the
bulky baked-in primer carries little information beyond what the agent
infers from RAG-via-Bash + the smaller primer's structural skeleton.

### Group B — "Best setup" stack (CC + RAG + hook + xmllint MCP tool + xmllint hook + minimal primer)

| Condition | n | Mean | σ | Notes |
|---|---:|---:|---:|---|
| Best setup, **minimax m2.7** | 1 | 0.622 | — | 17/17 |
| Best setup, **DSv4-flash** | 3 | 0.628 | 0.034 | s1=0.617, s2=0.666, s3=0.600 (17/17 each) |

### Group B' — Best setup + M1-u memory cheatsheet (everything stacked)

Adds the M1-u memory primer (the hero of the original D-008 ablation)
on top of the Group B stack. Same minimal base primer; agent variant
`claude_code_repo3_plugin_xmllint_all_m1u`.

| Condition | n | Mean | σ | Notes |
|---|---:|---:|---:|---|
| Best+M1-u, **minimax m2.7** | 1 | 0.581 | — | 17/17 |
| Best+M1-u, **DSv4-flash** | 3 | 0.617 | 0.012 | s1=0.617, s2=0.629, s3=0.606 (17/17 each) |

**Memory primer does not visibly help on DSv4-flash** (0.617 with memory
vs 0.628 without — within seed variance, σ ≈ 0.034 vs 0.012). It also
appears to slightly hurt on minimax single-seed (0.581 with memory vs
0.622 without), though n=1 makes that uncertain. The M1-u primer was
the hero of the D-008 ablation on minimax, but the gain appears not to
transfer to either model in the new harness. Possible explanations:

- The memory primer's content (named GEOS solver families, anti-pattern
  list) may be redundant with what DSv4 already infers from its better
  base prior.
- Or the minimax win was partly a "longer-prompt-helps" effect that
  doesn't show up in DSv4's training distribution.
- 3 seeds is enough to bound the effect at modest size; the 1.1pp gap
  is well inside one seed's variance.

Both Group B and Group B' STILL underperform vanilla DSv4 + minimal
primer (0.671). All Group B' DSv4 campaigns hit 17/17 completion (the
xmllint hook backstop continues to force well-formedness).

**Working conclusion**: on DSv4-flash, the simplest harness (vanilla
CC + minimal primer) outscores every plugin variant we've tested by
~4-5pp. The plugin's RAG / hook / memory stack was tuned to minimax;
its components don't compose to a net win on DSv4. The xmllint backstop
is universal value (100% completion across all conditions) but doesn't
raise quality.

### Group C — pre-session baselines (kept for cross-reference)

| Condition | Model | n | Mean | Notes |
|---|---|---:|---:|---|
| Vanilla CC + full primer | minimax m2.7 | 3 | 0.558 ± 0.087 | wide range 0.45-0.66 |
| Vanilla CC + minimal primer | minimax m2.7 | 1 | 0.625 | within minimax seed variance |
| Vanilla CC + full primer | DSv4-flash | 1 | 0.647 | (now the s1 entry of group A) |
| CC + RAG + hook | minimax m2.7 | 4 (existing) | ~0.50 | from prior data |
| CC + RAG + hook + xmllint primer | minimax m2.7 | 1 | 0.556 | 17/17 |
| CC + RAG + hook + xmllint hook | minimax m2.7 | 1 | 0.567 | 17/17 |
| CC + RAG + hook + memory (M1-u) | minimax m2.7 | 3 (existing) | varies | best of plugin variants |

### Take-aways

1. **DSv4-flash is the clear model winner** at ~10× lower cost, ~2×
   higher TPS than minimax m2.7 (when routed via DeepSeek-direct).
   Quality is comparable or better.
2. **The minimal primer is at least as good as the full primer**, with
   substantially less prompt text to process. Strong case to default to it.
3. **Schema validation backstop reliably forces completion** but does
   not raise quality on already-completing tasks. Treesim depends on
   correct semantic structure, not just well-formedness — xmllint
   catches the latter, not the former.
4. **The plugin stack underperforms vanilla** on DSv4-flash on this
   17-task set. The plugin's RAG and memory mechanisms were tuned to
   minimax behavior; on a different model they're not free wins. Worth
   re-running the full ablation matrix on DSv4 if we want to claim
   anything about the plugin's contribution under the new model.

## Disk hygiene incident & mitigation

Mid-session, the root filesystem hit 100% (`No space left on device`)
during the parallel best-setup launch. Cause: 293 GB of `.uv_cache`
directories accumulated across the eval tree — every per-task
workspace pulled chromadb + pydantic + grpcio + 100s of MB of
dependencies. Cleanup:

- Killed all running wrappers + docker containers
- `find /home/matt/sci/repo3/data/eval -maxdepth 4 -name .uv_cache -type d -delete` (regenerable on next launch)
- Re-launched best-setup campaigns with `--results-root-dir
  /data/matt/repo3_eval_results` so future writes target the 140 TB
  `/data` volume, not the root fs

Followup: consider auto-cleaning `.uv_cache` per task after success in
the runner, or sharing a single uv cache via `UV_CACHE_DIR` mount.

## Open work / followups (not done this session)

- [ ] Brian to confirm whether chromadb indexer is path-scoped (the
      data strongly suggests yes; 87 non-sphinx rst files unindexed).
      Re-index plan if confirmed.
- [ ] Decide whether to fix `per_tool_counts` to exclude
      `is_error: true` tool calls (currently the analysis script
      papers over this; the metric in `status.json` is contaminated).
- [ ] If we want a permanent home for DSv4-direct routing, add an
      `anthropic_base_url` field per agent (currently env-var-driven).
- [ ] Re-run any DSv4 / gemma-4 / deepseek-v3.2-v2 vanilla baselines
      that appear in the paper, with the post-fix harness.
- [ ] Consider the third xmllint cell (combined primer + hook + MCP
      tool) if the primer/hook ablation is inconclusive.

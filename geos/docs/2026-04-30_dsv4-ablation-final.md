# DSv4-flash ablation: build-up from empty harness to full stack

*2026-04-30 — final results. Six conditions × 3 seeds × 17 tasks v2 test set.
DSv4-flash via DeepSeek's Anthropic-compatible endpoint.*

## TL;DR

Build-up ablation: each cell adds one component. **C2 (minimal primer +
plugin loaded with empty MCP + SR-settings on, RAG OFF) wins at 0.913 ± 0.015**.

| Cell | Setup | Mean | σ | n |
|---|---|---:|---:|:-:|
| C1 (prior) | min primer (with workflow steps), no plugin | 0.671 | 0.014 | 3 |
| C0 | **true vanilla** — abs-min primer, no plugin | 0.865 | 0.067 | 3 |
| **C2** | **min primer + plugin loaded, RAG OFF, SR-settings** | **0.913** | **0.015** | 3 |
| C3 | min primer + RAG, no SR | 0.847 | 0.035 | 3 |
| C4 | min primer + RAG + SR | 0.874 | 0.005 | 3 |
| C5 | C2 + DSv4-distilled M1-u memory cheatsheet | **0.912** | 0.003 | 3 |

**Effect decomposition (paired per-task analyzer)**:
- **Strip workflow guidance from primer** (C1→C0): **+0.194** ← largest single component
- **Add SR/settings on top of vanilla** (C0→C2): **+0.049**
- **Add SR/settings on top of vanilla+RAG** (C3→C4): +0.027
- **Add RAG on top of vanilla** (C0→C3): −0.018
- **Add RAG on top of vanilla+SR** (C2→C4): **−0.039** (RAG hurts when SR present)
- **Add DSv4-distilled memory on top of best** (C2→C5): **−0.001** (no lift)

**Conclusion for DSv4-flash on this task**: the best harness is C2.
- The minimal primer with workflow guidance ("recommended workflow: 1. Glob, 2. Read, 3. Write...") *actively hurts* DSv4. Strip it.
- SR-settings on Stop hook helps reproducibility (tightens variance, +0.05 mean) — though the hook never actually fires (0 block decisions across all C2 tasks).
- RAG is consistently mildly harmful or neutral. The mechanism (RAG suppressing Glob/Grep) reproduces across multiple ablation pairs.
- Memory adds variance reduction (σ 0.015 → 0.003) but no mean lift — and adds 29% wall time. Not worth the cost.

## 1. Setup

**Test set**: 17 v2 tasks (canonical PAC-1 / D-008 set).
**Spec dir**: `/data/shared/geophysics_agent_data/data/eval/experiments_test36_template/`
**GT dir**: `/data/shared/geophysics_agent_data/data/eval/experiments_gt/`
**Model**: `deepseek-v4-flash` via `https://api.deepseek.com/anthropic`
**Concurrency**: 4 workers per (cond, seed) batch, 12-16 concurrent containers.
**Output dir**: `/data/shared/.../dsv4_ablation_2026-04-29/` (43 TB free).

**Cell definitions** (all use `--strip-baked-primer` to remove the AGENTS.md baked GEOS Primer):

| Cell | Primer | RAG MCP | SR Hook | Memory |
|---|---|:-:|:-:|:-:|
| C0 | `GEOS_PRIMER_absolute_min.md` (5 lines) | ✗ | ✗ | ✗ |
| C2 | `GEOS_PRIMER_minimal_vanilla.md` (34 lines) | ✗ | ✓ (settings written, never fires) | ✗ |
| C3 | `GEOS_PRIMER_minimal.md` | ✓ | ✗ | ✗ |
| C4 | `GEOS_PRIMER_minimal.md` | ✓ | ✓ | ✗ |
| C5 | `GEOS_PRIMER_minimal_vanilla.md` | ✗ | ✓ | DSv4-distilled M1-u |

**Caveat**: AGENTS.md retains 5KB of GEOS-specific guidance (workflow + base/benchmark file pattern + responsibility statement) after `--strip-baked-primer`. So C0 isn't "fully empty" — it's "AGENTS.md + just file paths in primer."

**Cost & wall** (real DSv4-flash, all conditions):
- 17 tasks × 3 seeds × 5 conditions + harvest = 273 task-runs
- Wall: ~3h ablation + ~30min harvest + ~25min C5 = **~4h**
- CC-reported cost: ~$0.85/task × 273 = **~$230 (anthropic-rate, not real)**
- Real DSv4 cost: ~$0.07/task × 273 = **~$19 (real)**

## 2. Surprising findings

### 2.1 The "minimal" primer was actively hurting

Going from C1's 34-line minimal primer (`GEOS_PRIMER_minimal_vanilla.md` —
includes "Recommended workflow: 1. Glob/Grep, 2. Read, 3. Write, 4. Read
back" + an XML skeleton) to C0's 5-line absolute-min primer (just file
locations) gives **+0.194 paired**. This is the biggest single effect in
the ablation.

Hypothesis (not yet directly tested): the workflow instructions
constrain DSv4 to a less-effective sequencing strategy than its
default. The XML skeleton in the minimal primer may also bias the
output structure incorrectly.

The prior `vanilla_dsv4_min` baseline (0.671) was thus not the floor of
DSv4's capability — it was the floor *under a counterproductive primer*.
DSv4 + AGENTS.md alone (with abs-min primer) lands at 0.865.

### 2.2 SR-settings provide a lift even when the hook never fires

C2 (no RAG, plugin loaded with empty MCP, `--settings` flag passed) beats
C0 (no plugin at all, no `--settings`) by **+0.049 paired**. Same primer,
same model, same docker invocation otherwise.

But: across 3 seeds × 17 tasks of C2, the verify_outputs.py Stop hook
returned **0 block decisions**. The agent never triggered a retry.

So the lift is *not* from the SR retry mechanism. Possible mechanisms:

1. **`--settings` flag flips internal CC behavior** (maybe Claude Code
   produces longer/different tool sequences when settings are present).
   Mandel: assistant turns went from 38 (C1) to 91 (C2) on the same task.
2. **`--mcp-config` flag** (even with empty `mcpServers`) changes
   Claude Code's runtime startup.
3. **Plugin-prefix in the user prompt** ("Do not call the Skill tool. Use
   the GEOS RAG MCP tools directly: ...") → the agent ignores the
   non-existent tools but the "Do not call Skill" instruction may be
   defending against some bad behavior.

Whichever mechanism — empirically, C2's σ=0.015 is much tighter than
C0's σ=0.067 (5× tighter). Adding `--settings` makes runs more
reproducible and slightly higher mean.

### 2.3 RAG is consistently mildly harmful on DSv4

The pattern from yesterday's reconciliation reproduces:

| Pair | Effect of adding RAG | Big-swing tasks |
|---|---:|---|
| C0 → C3 (no SR) | −0.018 | 4, 2 degradations |
| C2 → C4 (with SR) | **−0.039** | 3, **all 3 are degradations** |

In the C2→C4 pair, the analyzer reports "RAG replaces filesystem search"
in 3/3 big-swing tasks. The agent abandons Glob/Grep exploration of
`/geos_lib/inputFiles/` in favor of RAG queries that return prose
chunks. The latter strategy produces less structurally-complete XML.

**RAG is more harmful when SR is present.** Hypothesis: SR's invisible
constraint (settings flag → different agent behavior) interacts with
RAG's instruction to redirect search → the agent does fewer overall
file reads.

### 2.4 Memory doesn't help on top of the best harness

C5 = C2 + DSv4-distilled M1-u memory cheatsheet. Memory was distilled
via `gemini-3-flash-preview` from 18 train-task trajectories harvested
under C2 setup with `--extend-blocklist-with-test`.

C5: **0.912 ± 0.003** (3 seeds).
C2: 0.913 ± 0.015.

Paired Δ = **−0.001** — null. **N = 0 big-swing tasks**.

Two side observations:
- C5 has 5× tighter seed-to-seed variance than C2 (σ=0.003 vs 0.015) —
  reproducibility benefit, not a quality benefit.
- C5 costs +29% wall time (420s/task vs 326s/task) and +10% CC-reported
  cost. The agent reads/processes the cheatsheet but doesn't extract
  enough actionable signal to lift quality.

**Caveat for C5**: the M1-u distillation produces a primer with
plausible-sounding GEOS hallucinations (`SolidMechanicsLagrangianSSLE`,
`BiotLinearPoromechanics`, `FractureManager`) — known M1-u risk
without TreeSim grounding. The training-set trajectories were 18/18
"success" classified, so the distiller had no failure cases to mine
and instead over-generalized from successful XMLs.

This means: **either DSv4 doesn't need memory (it has enough prior on
GEOS XML), OR the M1-u-style cheatsheet is the wrong format for it.**
A cleaner test would be M1-g (grounded) memory, but with all-success
trajectories grounding has no signal to inject.

## 3. Per-task pattern (the smoking gun reproduces)

For C2→C4 (the canonical "does RAG help on DSv4?" test, both with SR),
all 3 big-swing tasks are degradations:

| Task | C2 | C4 | Δ |
|---|---:|---:|---:|
| ExampleMandel | 0.949 | 0.825 | **−0.124** |
| AdvancedExampleModifiedCamClay | 0.912 | 0.770 | **−0.142** |
| AdvancedExampleDruckerPrager | 0.962 | 0.798 | **−0.164** |

Tool-use diff on these tasks confirms: C4 makes 2-3× fewer Reads,
2-4 RAG queries replacing 4-10 Glob/Grep calls. The "fewer Reads under B"
pattern fires in 2/3.

## 4. Implications

### 4.1 For the paper / advisor narrative

- The plugin's RAG and memory components do not transfer from minimax to
  DSv4-flash. On DSv4, the simpler harness wins.
- The plugin's SR component (Stop hook + --settings flag) DOES transfer.
  +0.05pp lift, tighter variance.
- The biggest factor is the prompt design. Stripping the workflow
  guidance from the minimal primer was worth +0.19pp on DSv4.

### 4.2 For domain-adaptation engineering

The reverse-direction lesson from yesterday: when designing prompts for
a stronger base model, *less is more*. The structured workflow text
that helps weaker models actively constrains stronger ones.

A cross-model evaluation should report the same harness across all
models — not the harness optimized for each. We currently have:
- minimax-m2.7: best harness was probably full-primer + RAG + SR + M1-u memory
- DSv4-flash: best harness is C2 (minimal-primer + SR, no RAG, no memory)
- These are *different harnesses*. Comparing scores across them
  conflates harness optimization with model capability.

### 4.3 What's actually happening in C2

Best guess (n=2 trajectories sampled): the `--settings` flag's presence
shifts CC's runtime in some way that makes DSv4 take more thinking
turns + produce more output. The Stop hook itself never blocks. The
mechanism is some subtle interaction I haven't isolated.

Worth a follow-up experiment: C2-without-settings (just `--mcp-config`
with empty servers, no `--settings`) to isolate which CLI flag does
the work. Cheap to run.

## 5. Methodological wins from this campaign

- **Decoupled `rag_enabled` from `plugin_enabled`** in the runner. Lets
  us run plugin/hook without RAG. Was previously coupled.
- **Phase-1 ablation analyzer** (`scripts/analysis/ablation_analyzer.py`)
  produced clean per-pair markdown reports + JSON sidecars in seconds.
  Would have taken hours manually. Will be reused for every future
  ablation.
- **Per-task table + tool-use diff + treesim section diff + xmllint diff
  + cross-task pattern detection** — covers 80% of "what changed?"
  questions. The full LLM-driven trajectory reader (subagent 0.3) was
  not needed for any of the 5 cross-pair analyses on this campaign.
- **DSv4 cost was ~10% of CC's reported cost** (real $19 vs reported
  $230). CC computes cost using Anthropic-rate tables, not actual
  DSv4 pricing.

## 6. Open questions / followups

- **Is C2's lift over C0 from `--settings`, `--mcp-config`, or the
  plugin prefix in the user prompt?** Three components currently
  bundled. Could split with a quick C0+settings-only ablation (1 seed).
- **Does the "stripping workflow text helps" finding transfer to other
  models?** Re-test on minimax with the absolute-min primer.
- **What does an even-more-minimal AGENTS.md look like?** Currently
  AGENTS.md has 5KB of guidance. Stripping it would reveal the true
  capability floor of DSv4 + 5-line primer.
- **What's wrong with `vanilla_dsv4_min` (the prior C1 baseline at
  0.671)?** The same agent + same primer file scored 0.865 in C0 with
  abs-min primer. Confirmed not infrastructure regression because C2
  scored 0.913 in this campaign. The ~+0.19 from primer change
  reproduces but the magnitude is striking — worth re-examining
  whether the prior baseline was hit by something specific (model
  state, network conditions, retry behavior).

## 7. References

- Run dir: `/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/`
- Logs: `_logs/c{0,2,3,4,5}_dsv4_s{1,2,3}.log`
- Scored summaries: `_results/<run>/<agent>/_summary.json`
- DSv4 memory primer: `plugin/memory_primer_dsv4_m1u.md`
- DSv4 grounded reports: `misc/memory_artifacts/grounded_train_reports_dsv4.json`
- Per-pair analyses: `docs/ablation_*.md`
- Yesterday's reconciliation: `docs/2026-04-28_plugin-reconciliation-and-bottlenecks.md`
- Analyzer design: `docs/2026-04-29_ablation-analyzer-design.md`

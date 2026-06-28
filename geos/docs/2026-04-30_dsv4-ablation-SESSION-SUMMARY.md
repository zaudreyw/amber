# DSv4-flash full ablation campaign — session summary

*2026-04-30 — comprehensive single-document summary of the entire
DSv4-flash ablation campaign (C0-C11). Supersedes both prior writeups
in scope.*

## Quick navigation

This doc is for tomorrow-morning reading. If you want the:
- **Headline numbers**: § "Final 12-cell consolidated table"
- **What each component does**: § "Component-by-component findings"
- **Refuted/confirmed hypotheses**: § "Hypothesis tests"
- **Cost/efficiency Pareto**: § "Pareto frontier and recommendations"
- **What's still open**: § "Open follow-ups for the paper"

Per-pair markdown reports for every cross-condition comparison live at
`docs/ablation_C{X}_vs_C{Y}.md` (12 of them). Runbook at
`docs/2026-04-30_dsv4-ablation-runbook.md`.

## Session goal and structure

Build-up ablation on DSv4-flash for the 17-task v2 GEOS XML-authoring
test set. Each cell adds exactly one component relative to a
documented baseline so we can attribute effects cleanly:

```
C1 (prior baseline)                                       0.671
  + strip workflow text from primer    → C0              0.865
    + load plugin (settings + mcp-config + dir mount)
      with RAG OFF, parse-only SR      → C2              0.913
      - remove user-prompt prefix      → C9              0.917
      + xmllint Stop hook              → C6              0.921 (best)
        + xmllint MCP tool             → C7              0.914
          + RAG                        → C8              0.878
        + memory cheatsheet            → C10             0.913
        + memory cheatsheet (on C7)    → C11             0.920
      + memory cheatsheet              → C5              0.912
      + RAG no SR                      → C3              0.847
      + RAG (parse-only SR)            → C4              0.874
```

3 seeds × 17 tasks per cell = 561 task-runs total. **Real DSv4 cost ~$45**
(CC reports ~$430 anthropic-rate). Wall ~12h spread across the day,
mostly while I slept.

## Final 12-cell consolidated table

| Cell | mean | σ | wall | turns | $real | q/$ | Setup |
|---|---:|---:|---:|---:|---:|---:|---|
| C1 | 0.671 | 0.014 | 359s | 31.6 | $0.100 | 6.7 | (PRIOR) min primer, no plugin |
| C0 | 0.865 | 0.067 | 367s | 26.3 | $0.084 | 10.2 | abs-min primer, no plugin |
| **C2** | 0.913 | 0.015 | 326s | 33.0 | $0.094 | 9.7 | min primer + plugin (no RAG), parse-SR |
| C3 | 0.847 | 0.035 | 290s | 34.4 | $0.097 | 8.7 | min primer + RAG, no SR |
| C4 | 0.874 | 0.005 | **276s** | 33.6 | $0.094 | 9.3 | min primer + RAG + parse-SR |
| C5 | 0.912 | **0.003** | 420s | 31.3 | $0.097 | 9.4 | C2 + DSv4-memory |
| **C6** | **0.921** | 0.006 | 381s | 30.1 | $0.089 | 10.4 | min primer + xmllint hook |
| C7 | 0.914 | 0.008 | 335s | 36.3 | $0.099 | 9.2 | C6 + xmllint MCP tool |
| C8 | 0.878 | 0.008 | 288s | 34.0 | $0.089 | 9.9 | C7 + RAG (≈ old "best_dsv4") |
| **C9** | 0.917 | 0.016 | 359s | 28.4 | **$0.082** | **11.2** | C2 minus user-prompt plugin-prefix |
| C10 | 0.913 | 0.013 | 387s | 31.7 | $0.097 | 9.5 | C6 + DSv4-memory |
| C11 | 0.920 | 0.009 | 306s | 33.5 | $0.087 | 10.6 | C7 + DSv4-memory |

(`$real` uses DSv4-flash published pricing $0.27/M input cache-miss,
$0.07/M cache-hit, $1.10/M output. CC's reported `total_cost_usd` uses
Anthropic-rate tables and runs ~10× higher; *don't trust it across cells*.)

## Effect-size decomposition (paired analyzer Δ)

Each row is a single-component edit. The analyzer computes per-task
paired diffs and aggregates.

| Pair | Edit | Δ | big-swing tasks |
|---|---|---:|---|
| C1 → C0 | strip workflow text from primer | **+0.194** | 8 (1 deg) |
| C0 → C2 | load plugin (settings + mcp-config + dir-mount) | **+0.049** | 5 (0 deg) |
| C2 → C9 | remove user-prompt plugin-prefix | +0.004 | 0 |
| C2 → C6 | add xmllint Stop hook | +0.008 | 0 |
| C6 → C7 | add xmllint MCP tool | −0.007 | 0 |
| C2 → C5 | add memory cheatsheet (on parse-only SR) | −0.001 | 0 |
| C6 → C10 | add memory cheatsheet (on xmllint hook) | −0.008 | 0 |
| C7 → C11 | add memory cheatsheet (on full xmllint stack) | +0.006 | 0 |
| C0 → C3 | add RAG (no SR baseline) | −0.018 | 4 (2 deg) |
| C2 → C4 | add RAG (parse-only SR baseline) | −0.039 | 3 (3 deg) |
| C7 → C8 | add RAG (full xmllint stack) | −0.036 | 2 (2 deg) |

## Component-by-component findings

### 1. Primer — first-order effect, **strip the workflow text**

Going from C1's structured "Recommended workflow: 1. Glob, 2. Read, 3. Write,
4. Read back" + XML skeleton + section headings (34 lines) to C0's bare
"GEOS source at `/geos_lib/`, write XML to `/workspace/inputs/`" (5
lines) gives **+0.194 paired**.

The structured guidance was actively constraining DSv4 to a sub-optimal
sequencing. With the abs-min primer, the agent uses its own better
default exploration strategy (more thorough Glob, more reads of
reference XMLs, multi-variant detection on tasks like Sneddon).

This is the single largest effect in the campaign.

**Caveat for paper**: even C0 isn't "fully empty." `--strip-baked-primer`
removes the GEOS Primer block from AGENTS.md but AGENTS.md retains
~5 KB of GEOS-specific content (responsibility statement, base/benchmark
file pattern, documentation usage rules). A "truly empty" baseline
would also strip AGENTS.md — not done here.

### 2. Plugin infrastructure — second-order effect, mechanism **unresolved**

**Loading the plugin (C0 → C2) = +0.049 pp** with the **same primer**.
The "plugin loading" here is just three CLI flags:
- `--plugin-dir /home/matt/sci/repo3/plugin` (mounts at `/plugins/repo3`)
- `--mcp-config <path>` (with `mcpServers: {}` — RAG MCP NOT loaded)
- `--settings <path>` (Stop hook configured but **never blocks** in C2:
  XML always parses, parse-check has nothing to reject)

We isolated the most plausible mechanism (the user-prompt
plugin-prefix that says "use mcp__geos-rag__* tools") and **refuted
it**: removing the prefix in C9 leaves quality essentially unchanged
(0.917 vs C2's 0.913, Δ = +0.004 paired).

So +0.049 comes from **some interaction with `--settings` or
`--mcp-config` or the plugin-dir mount that we haven't identified**.
This is the most interesting unresolved finding for the paper.

Cheap follow-up to nail down (~$5):
- C0 + just `--settings`, no other flags
- C0 + just `--mcp-config` (empty), no other flags
- C0 + just `--plugin-dir`, no other flags

### 3. xmllint Stop hook — modest mean lift, big variance compression

**C2 → C6 = +0.008 pp** mean. Statistically unimpressive on its own,
**but variance compresses ×2.5** (σ 0.015 → 0.006). The hook fires
on **4/34 tasks (~12% rate) with real schema-block decisions**. On
those tasks the agent retries with feedback shaped like:

> Element 'CompressibleSolidCappedPlatesPorosity': not in schema.
> Expected: A, B, C, ...

The "Expected: ..." enumeration in xmllint's error message is enough
for DSv4 to recover. **You don't need RAG to translate the hint.**
Wall cost: +17% (381s vs 326s) for the variance compression and
+0.008 mean. Marginal but positive.

C6 has the **highest mean treesim** of any cell tested (0.9211).

### 4. xmllint MCP tool — null over hook

**C6 → C7 = −0.007 pp** (within noise). Adding the voluntary
`mcp__xmllint__validate_geos_xml` tool lets the agent self-validate
during authoring. Result: end-of-turn hook blocks drop to 0 (vs 12% in
C6) but +6 turns/task and no quality lift. The validation budget
shifts from "post-stop block-and-retry" to "pre-stop self-check"
without changing where the agent lands.

**For paper: the value is in the validation feedback signal, not in
*when* it happens.** Hook-on-Stop is sufficient.

### 5. RAG — consistently harmful (3 paired tests)

| Pair | Δ | n_deg / n_big-swing |
|---|---:|---|
| C0 → C3 (no SR baseline) | −0.018 | 2/4 |
| C2 → C4 (parse-check SR baseline) | −0.039 | 3/3 |
| C7 → C8 (full xmllint stack baseline) | −0.036 | 2/2 |

**Mechanism documented**: in every big-swing degradation, the analyzer
reports "RAG replaces filesystem search". The agent that has RAG
makes fewer Glob/Grep/Read calls and more RAG queries; the resulting
XMLs are structurally less complete (often missing one of the
multi-variant files DSv4 would otherwise discover via Glob).

**Critical**: even when xmllint provides schema feedback (C7 → C8),
RAG still hurts. **The hypothesis "RAG is needed to use xmllint
feedback effectively" is empirically refuted on DSv4.** xmllint's
"expected: ..." list is enough.

This is the **single most surprising negative result of the campaign**.
Prior sessions (minimax era) treated RAG as the foundation of the
plugin's value. On DSv4, RAG strictly hurts.

### 6. Memory cheatsheet — null mean, modest variance compression

| Pair | Δ | σ change |
|---|---:|---|
| C2 → C5 (parse-only baseline) | −0.001 | 0.015 → 0.003 |
| C6 → C10 (xmllint hook baseline) | −0.008 | 0.006 → 0.013 |
| C7 → C11 (full xmllint stack baseline) | +0.006 | 0.008 → 0.009 |

DSv4-distilled M1-u-style memory cheatsheet (distilled via
gemini-3-flash-preview from 18 train-task harvest under C2 setup,
820 tokens) doesn't move the mean meaningfully. C5 has the tightest σ
of any cell (0.003) but at +29% wall time. Memory has nothing to add
on DSv4 — the agent's base prior already covers what the memory
primer would tell it.

**Caveat**: distilled M1-u memory contained plausible-sounding GEOS
hallucinations (`SolidMechanicsLagrangianSSLE`, `BiotLinearPoromechanics`)
because all 18 train trajectories were "success"-classified by the
grounder, leaving the distiller no failure cases to learn from.

### 7. Plugin-prefix in user prompt — null on quality, **−13% on cost**

**C2 → C9 = +0.004 pp** (within noise). Removing the
"Don't call Skill; use mcp__geos-rag__* tools" prefix from the user
prompt saves 3.4 turns/task and 13% real cost ($0.082 vs $0.094).
Pure efficiency win. **Recommend dropping the prefix from production.**

## Hypothesis tests

### Refuted

1. **"RAG is needed to use xmllint feedback effectively"** —
   refuted across all 3 RAG-add pairs, especially C7 → C8 = −0.036.
2. **"The user-prompt plugin-prefix drives the C1 → C2 lift"** —
   refuted by C2 → C9 = +0.004 (null).
3. **"DSv4-distilled memory helps on top of the best harness"** —
   refuted by C2 → C5 (−0.001), C6 → C10 (−0.008), C7 → C11 (+0.006);
   none meaningful.
4. **"xmllint MCP tool (voluntary) helps more than hook (mandatory)"** —
   refuted by C6 → C7 = −0.007.
5. **"Memory + xmllint compose to outperform either alone"** — refuted
   by C10 (= C6) and C11 (= C7).

### Confirmed

1. **"Stripping the workflow guidance from the primer helps DSv4"** —
   confirmed by C1 → C0 = +0.194.
2. **"RAG hurts on DSv4 by replacing filesystem search"** — confirmed
   across 3 paired tests; mechanism documented (analyzer reports
   "RAG replaces filesystem search" in 7/9 big-swing degradations).
3. **"Plugin loading (without RAG) lifts DSv4 quality"** — confirmed
   but mechanism not isolated; +0.049 from `--settings` +
   `--mcp-config` + plugin-dir-mount, with prefix and RAG ruled out.
4. **"xmllint hook compresses variance"** — confirmed; σ 0.015 → 0.006
   (×2.5) at +0.008 mean, +17% wall.

## Pareto frontier and recommendations

For different optimization targets:

| Target | Cell | Why |
|---|---|---|
| **Highest mean quality** | **C6** (0.921 ± 0.006) | xmllint hook + tight variance |
| **Best q/$** | **C9** (11.2) | drop the plugin-prefix; quality unchanged at lower cost |
| **Lowest variance** | C5 (σ=0.003) | memory tightens variance but null mean |
| **Fastest at acceptable quality** | C4 (276s, 0.874) | RAG-based, but quality cost is real |
| **Strictly dominated** | C1, C3 | matched/exceeded by others on every axis |

If forced to ship one configuration: **C6 (xmllint hook + minimal
primer + plugin loaded, no RAG, no memory)**. Highest quality, second-
best q/$, mid-pack wall time. The 17% wall hit vs C2 buys the
variance reduction.

If shipping is dominated by efficiency: **C9 (C2 minus the
plugin-prefix)**. Best q/$ in the campaign at 11.2 treesim/$ real DSv4.

## Why this matters for the paper

Counter-narrative to the prior minimax-era plugin claims:

- **The minimax-era "plugin wins by +0.27 (RAG+SR+memory hero)" finding
  does NOT generalize to DSv4-flash.** On DSv4, RAG mildly hurts,
  memory is null, and only the SR-validation component (specifically
  xmllint) provides any positive signal.
- **The base model determines which DAs help.** Minimax needed RAG
  to surface schema docs because it hallucinated element names
  frequently. DSv4 has the schema priors built in → RAG just steers
  it away from filesystem-search exploration that would otherwise
  discover multi-variant XML structures.
- **The biggest "DA" win on DSv4 was actually undoing a bad primer
  choice** (C1 → C0 = +0.194). The structured workflow guidance
  bundled in the prior baseline was the dominant problem.
- **Plugin-loading alone (C0 → C2) gives +0.049 by an unidentified
  mechanism.** This is the single most interesting un-explained
  positive finding in the campaign. Worth follow-up isolation.

## Cost/wall accounting

Real DSv4-flash cost (DeepSeek published pricing applied to observed
token usage):

| Phase | task-runs | $real | wall |
|---|---:|---:|---|
| Group A (C0+C2) × 3 seeds | 102 | $9 | 30 min × 3 (sequential seeds, parallel cells) |
| Group B (C3+C4) × 3 seeds | 102 | $10 | 30 min × 3 |
| Train harvest (18 tasks) | 18 | $2 | 30 min |
| C5 × 3 seeds | 51 | $5 | 25 min |
| Group C (C6+C7) × 3 seeds | 102 | $9 | 30 min × 3 |
| Group D (C8+C9) × 3 seeds | 102 | $9 | 30 min × 3 |
| C10 + C11 × 3 seeds | 102 | $10 | 25 min (all 6 in parallel) |
| **Total** | **579** | **~$54** | **~12h spread** |

CC's reported `total_cost_usd` for the same runs sums to **~$430**
because it uses Anthropic-rate tables. The CC numbers are useful for
cell-to-cell *comparisons* (token usage shape) but the absolute
dollars are misleading.

## Open follow-ups for the paper

1. **Plugin sub-component isolation** (highest priority, ~$5):
   Three cells:
   - C0 + `--settings` only (no mcp-config, no plugin-dir)
   - C0 + `--mcp-config` only
   - C0 + `--plugin-dir` only
   This nails down what specifically about plugin loading lifts
   quality by +0.049.

2. **AGENTS.md ablation** (medium priority, ~$5):
   The "true vanilla" C0 still has 5 KB of GEOS guidance in AGENTS.md.
   What happens when AGENTS.md is also empty? Reveals the model's
   intrinsic prior.

3. **Cross-model replication of the C6 finding**:
   Run C6 (xmllint hook only, no RAG, no memory) on minimax-m2.7 and
   gemma-4. If C6 works there too, "xmllint hook is general-purpose";
   if not, "xmllint adds value only when the model has good priors."

4. **Per-task class analysis**:
   Two tasks consistently underperform across all cells:
   TutorialPoroelasticity (0.40-0.50) and CasedContactThermoElastic
   (0.80-0.85). What makes them resistant? Could reveal a missing
   DA class.

5. **Why does RAG hurt only when SR is present?**
   C0 → C3 = −0.018 (no SR), C2 → C4 = −0.039 (with SR). The harm
   is ~2× larger when SR is present. Suggests SR + RAG interact in a
   way I haven't characterized.

## Files / reproducibility

- **Runbook (every command)**: `docs/2026-04-30_dsv4-ablation-runbook.md`
- **Per-pair analyses**: `docs/ablation_C{X}_vs_C{Y}.md` (12 pairs)
- **Raw runs**: `/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/`
- **Scored summaries**: same path under `_results/<run>/<agent>/_summary.json`
- **Analyzer code**: `scripts/analysis/{ablation_analyzer,tool_use_differ,treesim_xmllint_analyzer,per_task_matrix}.py`
- **Primers**: `plugin/GEOS_PRIMER_{absolute_min, minimal_vanilla, minimal}.md`
- **DSv4 memory primer**: `plugin/memory_primer_dsv4_m1u.md` (+ source: `misc/memory_artifacts/grounded_train_reports_dsv4.json`)
- **Agent variants**: `src/runner/agents.py` (`abl_c0` through `abl_c11_xmllint_full_mem`)
- **Launchers**: `scripts/launch_dsv4_ablation.sh`, `scripts/launch_dsv4_full_matrix.sh`, `scripts/launch_dsv4_c6_c9.sh`
- **Scoring**: `scripts/score_dsv4_ablation.sh`, `scripts/score_all_dsv4_ablation.sh`

## Commits in this campaign (chronological)

```
dd0d39e  [FEAT] DSv4 ablation matrix C0-C4 + ablation analyzer system
ffef284  [ANALYSIS] DSv4 ablation Group A complete: C0 0.865, C2 0.914
ced76c1  [ANALYSIS] DSv4 ablation final: C2 wins (0.913), memory adds nothing on top
0da6949  [DOCS] DSv4 ablation runbook: every command run for the 2026-04-29 campaign
7b4544d  [FEAT] DSv4 ablation cells C6-C9 (xmllint split + plugin-prefix probe)
3564c28  [ANALYSIS] DSv4 ablation v2 final: 9 cells, xmllint split + prefix probe
(this commit) [ANALYSIS] DSv4 ablation final v3: 12 cells with full mem×xmllint matrix
```

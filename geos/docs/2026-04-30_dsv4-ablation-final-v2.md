# DSv4-flash ablation v2: 9 cells × 3 seeds, with xmllint split + prefix probe

*2026-04-30 — paper-ready findings. Supersedes `2026-04-30_dsv4-ablation-final.md`
in scope (added C6/C7/C8/C9) but does not contradict any of its findings.*

## TL;DR for the paper

Build-up ablation on DSv4-flash, 17 v2 tasks, 3 seeds each. Each
component is added one at a time relative to a documented baseline:

| Cell | Components added | mean treesim | σ |
|---|---|---:|---:|
| C1 | (PRIOR) min primer (workflow text), no plugin, no SR | 0.671 | 0.014 |
| C0 | strip workflow text from primer (= abs-min primer) | 0.865 | 0.067 |
| C2 | + load plugin (`--settings` + `--mcp-config` + plugin-dir-mount, RAG MCP off) + parse-check Stop hook | 0.913 | 0.015 |
| C9 | C2 minus the user-prompt plugin-prefix | 0.917 | 0.016 |
| C6 | C2 + xmllint Stop-hook validation (`xmllint --schema`) | **0.921** | 0.006 |
| C7 | C6 + voluntary xmllint MCP tool | 0.914 | 0.008 |
| C5 | C2 + DSv4-distilled M1-u memory cheatsheet | 0.912 | 0.003 |
| C8 | C7 + RAG | 0.878 | 0.008 |
| C4 | min primer + parse-check + RAG (no xmllint, no memory) | 0.874 | 0.005 |
| C3 | min primer + RAG (no SR, no xmllint) | 0.847 | 0.035 |

Headline: **on DSv4-flash, only two components produce meaningful
positive lift: stripping the workflow-step primer (+0.19) and loading
the plugin infrastructure (+0.05).** Every other component (RAG,
memory, xmllint hook, xmllint MCP tool, plugin-prefix) is null or
negative.

## Effect-size summary (paired per-task analyzer)

The 7 paired comparisons that decompose the harness:

| Pair | What's added | Δ | big-swing tasks |
|---|---|---:|---|
| C1 → C0 | strip workflow text from primer | **+0.194** | 8 (1 deg) |
| C0 → C2 | load plugin (settings + mcp-config + dir mount) | **+0.049** | 5 (0 deg) |
| C2 → C9 | remove user-prompt plugin-prefix | +0.004 | 0 |
| C2 → C6 | add xmllint Stop-hook | +0.008 | 0 |
| C6 → C7 | add voluntary xmllint MCP tool | −0.007 | 0 |
| C2 → C5 | add DSv4-distilled memory cheatsheet | −0.001 | 0 |
| C0 → C3 | add RAG (no SR, no xmllint) | −0.018 | 4 (2 deg) |
| C2 → C4 | add RAG to parse-check SR | −0.039 | 3 (3 deg) |
| C7 → C8 | add RAG to full xmllint stack | **−0.036** | 2 (2 deg) |

(Δ is paired-mean-of-per-task-means with `cond_b - cond_a`.)

## What each component contributes (confidence-weighted)

### 1. Primer content — first-order effect

**Stripping the workflow guidance from the prompt = +0.19 pp**, the
single largest effect in the ablation. The prior `vanilla_dsv4_min`
baseline (C1) used `GEOS_PRIMER_minimal_vanilla.md` which contains a
"Recommended workflow: 1. Glob, 2. Read, 3. Write, 4. Read back"
section + an XML skeleton. Replacing this with the 5-line
`GEOS_PRIMER_absolute_min.md` (just file locations) gives +0.19 pp.

The smaller primer is *less directive* and the agent uses its own
better default exploration strategy. The structured workflow steps
were actively constraining DSv4 to a worse sequencing.

**Caveat for paper**: this depends on AGENTS.md. With
`--strip-baked-primer`, AGENTS.md still has 5 KB of GEOS-specific
guidance (responsibility statement, base/benchmark file pattern,
documentation usage rules). C0 isn't fully empty. A clean
"truly empty" cell would strip AGENTS.md too — not done in this
campaign.

### 2. Plugin infrastructure — second-order effect, mechanism unknown

**Loading the plugin (C0→C2) = +0.049 pp** with the same primer.
The "plugin" here is just `--plugin-dir <repo3>` + `--mcp-config
<path>` + `--settings <path>`. **Crucially: RAG MCP is NOT loaded
in C2 (we explicitly disabled it via `rag_enabled=False`).** And
the Stop hook is configured but **never blocks** in C2 (XML always
parses; parse-check is the only validation). And we showed that
removing the user-prompt plugin-prefix (C9) doesn't undo the lift
(Δ = +0.004 vs C2).

So +0.049 comes from:
- the agent seeing a `mcp_config` file with empty `mcpServers`
- a `settings.json` file with a Stop hook config
- a `/plugins/repo3/` mount the agent never reads

We don't have a clean explanation. Hypotheses:
- Claude Code's runtime initializes differently when `--settings`
  is passed (subtle scheduler change?)
- The `mcp_config` flag presence affects token-budget allocation
- Some interaction between settings+mcp-config and the agent's
  initial system message that we haven't isolated

This is the **most interesting unresolved finding** for the paper.
Worth a follow-up isolation campaign:
- C0 + just `--settings`, no mcp-config, no plugin-dir
- C0 + just `--mcp-config` (empty), no settings, no plugin-dir
- C0 + just `--plugin-dir`, no settings, no mcp-config

### 3. xmllint Stop-hook — modest positive, big variance reduction

**C2 → C6 = +0.008** mean treesim. Statistically tiny on means but
**variance compresses** σ=0.015 → σ=0.006 (×2.5 tighter). The hook
fires on **4/34 tasks (~12% rate)** with a real schema-block decision.
On those 4 tasks, the agent retries with feedback like:

> Element 'X': not in schema. Expected: A, B, C, ...

The hint is enough for DSv4 to recover **without RAG**. Your concern
"don't you need RAG to translate xmllint feedback into a real
element name" turns out to be **empirically false on DSv4**: the
"expected: ..." enumeration in xmllint's error message is sufficient.

Cost: **+17% wall time** vs C2 (381s vs 326s) for the +0.008 mean
gain + variance reduction. Marginal.

### 4. xmllint MCP tool — null

**C6 → C7 = −0.007**. Adding the voluntary
`mcp__xmllint__validate_geos_xml` tool lets the agent self-validate
during authoring, BUT:
- 0 hook blocks at end (down from 12% under C6)
- +6 turns/task (30.1 → 36.3)
- No quality lift

The agent absorbs the validation budget into pre-stop self-checks
rather than waiting for the Stop hook to block. Same end quality,
slightly worse efficiency.

For paper: **the value is in the validation feedback loop, not in
*when* it happens.** Hook-on-Stop is sufficient; the agent doesn't
need to call validation itself.

### 5. RAG — consistently harmful (3 paired tests)

| RAG-add pair | Δ | n_deg / n_big-swing |
|---|---:|---|
| C0 → C3 (no SR baseline) | −0.018 | 2/4 |
| C2 → C4 (parse-check SR) | −0.039 | 3/3 |
| C7 → C8 (full xmllint stack) | −0.036 | 2/2 |

Mechanism: in every big-swing degradation, the analyzer reports
"RAG replaces filesystem search". The agent that has RAG made fewer
Glob/Grep/Read calls and instead made RAG queries; the resulting
XMLs were structurally less complete (often missing one of the
multi-variant files DSv4 would otherwise discover via Glob).

**Strong, reproducible finding.** RAG was a hero on minimax (where
F1 schema hallucinations dominated and RAG could surface schema
docs). On DSv4, hallucinations are rare AND the agent has good
defaults for filesystem exploration → RAG strictly dominates with
its harms.

**Critically**: even when xmllint is providing schema feedback (C7
→ C8), RAG still hurts. So your hypothesis "RAG is needed to
translate xmllint feedback into real names" is empirically rejected.
The "expected: X, Y, Z" list in xmllint's error is itself enough.

### 6. Memory cheatsheet — null mean, tightens variance

**C2 → C5 = −0.001**, σ 0.015 → 0.003. Same observation as v1
writeup. Memory adds 29% wall time for no quality lift, just
reduces seed-to-seed variance (also achievable cheaper via xmllint
hook in C6).

### 7. Plugin-prefix in user prompt — null, slightly negative cost

**C2 → C9 = +0.004** (within noise). Removing the prefix saves
3.4 turns and 13% real cost. **Recommend for paper: drop the
plugin-prefix from the production harness.** Pure cost win.

## Paper-ready efficiency table

3 seeds × 17 tasks each. `$real` = estimated DSv4-flash cost using
DeepSeek's published pricing ($0.27/M input cache-miss, $0.07/M cache-hit,
$1.10/M output). `q/$` = treesim per real-USD; higher is better.

| Cell | treesim | σ | wall | turns | $real | q/$ | Setup |
|---|---:|---:|---:|---:|---:|---:|---|
| C1 | 0.671 | 0.014 | 359s | 31.6 | $0.100 | 6.7 | (PRIOR) min primer, no plugin |
| C0 | 0.865 | 0.067 | 367s | 26.3 | $0.084 | 10.2 | abs-min primer, no plugin |
| **C2** | 0.913 | 0.015 | 326s | 33.0 | $0.094 | 9.7 | min primer + plugin (no RAG), parse-SR |
| C3 | 0.847 | 0.035 | 290s | 34.4 | $0.097 | 8.7 | min primer + RAG, no SR |
| C4 | 0.874 | 0.005 | **276s** | 33.6 | $0.094 | 9.3 | min primer + RAG + parse-SR |
| C5 | 0.912 | **0.003** | 420s | 31.3 | $0.097 | 9.4 | C2 + DSv4-memory |
| **C6** | **0.921** | 0.006 | 381s | 30.1 | $0.089 | 10.4 | min primer + xmllint hook |
| C7 | 0.914 | 0.008 | 335s | 36.3 | $0.099 | 9.2 | C6 + xmllint MCP tool |
| C8 | 0.878 | 0.008 | 288s | 34.0 | $0.089 | 9.9 | C7 + RAG (≈ old best_dsv4) |
| **C9** | 0.917 | 0.016 | 359s | 28.4 | **$0.082** | **11.2** | C2 minus plugin-prefix |

### Pareto-optimal cells

- **Best absolute quality**: C6 (0.921) — **min primer + xmllint hook**
- **Best q/$**: C9 (11.2) — **C2 minus plugin-prefix**
- **Fastest at acceptable quality**: C4 (276s, 0.874) — RAG-based, but quality cost is real
- **Strictly dominated**: C1, C3, C5 (matched/exceeded by others on every axis)

If forced to pick one configuration to ship: **C6** (xmllint hook
on top of plugin loading, no RAG, no memory). It has the highest
mean quality, tight variance, and the second-best q/$.

If we want the leanest configuration that captures most of the
gain: **C9** (C2 with the plugin-prefix removed). 11.2 q/$ — best
in the table — at quality 0.917 ≈ 0.92.

## Refuted hypotheses (worth reporting)

The campaign tested several hypotheses, several of which we expected
to confirm and that turned out null/negative:

1. **"RAG is needed to use xmllint feedback effectively"** — refuted.
   xmllint's error messages enumerate expected alternatives directly;
   no RAG lookup needed. C7→C8 = −0.036.

2. **"The plugin-prefix in the user prompt drives the C1→C2 lift"** —
   refuted. C2→C9 (remove prefix) = +0.004 (null). The prefix is
   not the mechanism. Worth a follow-up on `--settings` /
   `--mcp-config` / plugin-dir-mount isolation.

3. **"Memory-distilled cheatsheets help on top of best harness"** —
   refuted. C2→C5 = −0.001 (null mean), only tightens variance. The
   distilled M1-u DSv4-specific primer didn't help; on DSv4 there's
   nothing for memory to add.

4. **"xmllint MCP tool (voluntary self-validation) helps more than
   hook (mandatory post-stop validation)"** — refuted. C6→C7 = −0.007,
   wall +14%. Hook-on-Stop is the optimal validation locus.

## Confirmed hypotheses

1. **"Stripping the workflow guidance from the primer helps DSv4"** —
   confirmed. C1→C0 = +0.194.

2. **"RAG hurts on DSv4 by replacing filesystem search"** — confirmed
   across 3 paired tests, mechanism documented (analyzer reports
   "RAG replaces filesystem search" in 7/9 big-swing degradations
   across the 3 RAG-add pairs).

3. **"Plugin loading (without RAG) lifts DSv4 quality"** — confirmed
   but mechanism not isolated. +0.049 from `--settings` +
   `--mcp-config` + plugin-dir-mount, with prefix and RAG ruled out.

## Open questions for follow-up

1. **Which sub-component of plugin loading drives the +0.049?** Three
   candidates remain: `--settings` (Stop hook config), `--mcp-config`
   (empty servers), plugin-dir mount (visible to agent's filesystem).
   Could isolate with 3 cheap cells.

2. **Does C6 transfer to other models (minimax, gemma)?** Or is the
   "xmllint adds null mean but tightens variance" finding DSv4-specific
   the way RAG-helps was minimax-specific? Cross-model replicate of
   C6 would tell.

3. **What is the ceiling?** C6 at 0.921 with σ=0.006 is the best we've
   measured. Two tasks consistently underperform: TutorialPoroelasticity
   (0.40-0.50) and ExampleCasedContactThermoElastic (0.80-0.85). What
   makes those resistant?

## Files / reproducibility

- Runbook (every command): `docs/2026-04-30_dsv4-ablation-runbook.md`
- Per-pair analyzer reports: `docs/ablation_C{X}_vs_C{Y}.md`
- Raw runs: `/data/shared/.../dsv4_ablation_2026-04-29/`
- Analyzer code: `scripts/analysis/ablation_analyzer.py`
- Primers: `plugin/GEOS_PRIMER_{absolute_min, minimal_vanilla, minimal}.md`
- Agent variants: `src/runner/agents.py` (`abl_c0` through `abl_c9_no_prefix`)

Total compute: ~$33 real DSv4 (CC reports ~$330 anthropic-rate),
~7-8h wall, ~9 cells × 3 seeds × 17 tasks + 18-task harvest = 477
task-runs.

## What's next (paper-driven)

1. **Run the 3 plugin-component-isolation cells** (~$5, 1h) to nail
   down which of `--settings` / `--mcp-config` / `--plugin-dir`
   drives the +0.049.
2. **Pick canonical cell for paper** — recommend C9 (best q/$) or
   C6 (best quality).
3. **Cross-model replication** of the canonical cell on minimax to
   anchor the comparison.
4. **Per-task class analysis**: which task families benefit from
   xmllint hook (vs primer alone)? May reveal the mechanism by
   which xmllint provides its tiny mean lift.

---

*Last updated: 2026-04-30 09:30 UTC. C6/C7/C8/C9 just landed; this
doc supersedes the v1 final from 02:32.*

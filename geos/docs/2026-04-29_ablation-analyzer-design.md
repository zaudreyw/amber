# Ablation analyzer — agentic system design

*2026-04-29 — design doc for the multi-subagent system that automates
trajectory-level analysis of ablation pairs.*

## Goal

Given two ablation conditions A and B (e.g., C2 vs C3), produce a
report that:

1. **Top-line table**: per-task treesim-A, treesim-B, Δ, mean
   token usage, mean cost, mean wall time. Sorted by |Δ|.
2. **Big-swing list**: tasks where |Δ| > threshold (default 0.10pp,
   configurable). Default mode focuses on **degradations** (Δ < 0).
3. **Per-task root-cause** for each big-swing task:
   - Tool-use distribution diff (Reads, Globs, Greps, RAG calls,
     Bash subcommands)
   - Treesim component-wise diff: which sections / nodes lost the
     most points
   - xmllint diff: schema errors A introduces vs schema errors B
     introduces
   - Trajectory reading: extracted reasoning chain — what the agent
     was told vs what it decided vs why
4. **Cross-task patterns**: emergent recurring themes from the per-task
   analyses (e.g., "in 5/7 degradations, condition B used RAG instead
   of Glob/Read").

The system must be invocable repeatedly across new ablations without
re-prompting; the outputs should be diffable across ablation runs.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  AblationAnalyzer (subagent 1)                               │
│  Input:  cond_a_dir, cond_b_dir, threshold, focus            │
│  Output: docs/ablation_<a>_vs_<b>.md                         │
│                                                              │
│  Pipeline:                                                   │
│    1. Score-table.py            → per-task aggregates        │
│    2. Identify big-swing tasks  (|Δ| > threshold)            │
│    3. For each big-swing task:                               │
│         dispatch TrajectoryAnalyzer (subagent 0)             │
│    4. Aggregate per-task analyses → cross-task patterns      │
│    5. Render markdown report                                 │
└──────────────────────────────────────────────────────────────┘
                          ↓ dispatches
┌──────────────────────────────────────────────────────────────┐
│  TrajectoryAnalyzer (subagent 0)                             │
│  Input:  task_name, cond_a_dir/<task>, cond_b_dir/<task>     │
│  Output: per-task analysis dict  (returned to caller)        │
│                                                              │
│  Pipeline (subagents 0.1, 0.2, 0.3 run in parallel):         │
│                                                              │
│    0.1 ToolUseDiffer    → tool-distribution Δ table          │
│    0.2 TreesimAnalyzer  → component-wise score loss          │
│                          + xmllint output diff               │
│    0.3 TrajectoryReader → narrative analysis of why agent    │
│                          made each decision (LLM-driven)     │
│                                                              │
│  Aggregator combines into one analysis dict + bullets.       │
└──────────────────────────────────────────────────────────────┘
```

**Why split this way**: 0.1 and 0.2 are deterministic computation
(scripts), 0.3 is LLM-driven narrative. Running them as separate
subagents keeps each focused (small context, clear output schema)
and allows 0.1+0.2 to be implemented as plain scripts (cheap, fast)
while 0.3 invokes a Claude subagent with the full trajectory.

## Subagent specifications

### Subagent 1 — AblationAnalyzer (orchestrator)

**Type**: Python script that dispatches Claude subagent for 0.3 when needed,
runs 0.1/0.2 inline. Or alternatively, a Claude subagent that calls Bash
to run the scripts and Agent to dispatch 0.3 instances.

**Recommendation**: Pure Python orchestrator (`scripts/analysis/ablation_analyzer.py`) — deterministic, reproducible, cheap. Spawns Claude subagents only for the LLM-driven trajectory reading (subagent 0.3).

**Inputs**:
- `--cond-a` (path to results dir, e.g. `.../abl_c2_min_sr_no_rag/c2_dsv4_*`)
- `--cond-b` (same shape, the comparand)
- `--gt-dir` (path to GT — defaults to /data/shared/.../experiments_gt)
- `--threshold` (default 0.10 — minimum |Δ| to mark big-swing)
- `--focus` (default "degradations" — also "improvements" or "both")
- `--max-trajectory-analyses` (default 8 — cap LLM calls)
- `--out` (path to output markdown)

**Outputs**:
- `docs/ablation_<a>_vs_<b>.md`
- `<out>.json` (machine-readable companion)

**Steps**:
1. Load all per-task scores from each condition's `_eval.json` files.
   Average across seeds. Compute Δ = mean(B) − mean(A) per task.
2. Compute per-task token + cost + elapsed from each condition's
   `events.jsonl` last assistant message (final `total_cost_usd`,
   `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens`).
3. Identify big-swing tasks: `[t for t in tasks if abs(Δ[t]) >= threshold]`.
4. For each big-swing task, in parallel:
   - Run subagent 0.1 (`tool_use_differ`) inline — outputs dict
   - Run subagent 0.2 (`treesim_xmllint_analyzer`) inline — outputs dict
   - Dispatch subagent 0.3 (`trajectory_reader`) as Claude subagent —
     returns prose summary
5. Render markdown.

### Subagent 0.1 — ToolUseDiffer

**Type**: Pure Python (`scripts/analysis/tool_use_differ.py`).

**Inputs**: `task_dir_a`, `task_dir_b`.

**Outputs** (dict):
```python
{
  "tools_a": {"Read": 30, "Glob": 2, ...},
  "tools_b": {"Read": 6, "mcp__geos-rag__search_*": 6, ...},
  "delta":   {"Read": -24, "mcp__geos-rag__*": +6, ...},
  "bash_subcommands_a": {"find": 15, "grep": 8, ...},
  "bash_subcommands_b": {"xmllint": 3, ...},
  "reads_by_dir_a": {"inputFiles": 18, "src/docs/sphinx": 4, ...},
  "reads_by_dir_b": {"inputFiles": 4, ...},
  "summary_bullets": [
    "B made 4× fewer Read calls than A (6 vs 30)",
    "B never invoked Glob/Grep; A used Glob 2x, Grep 5x",
    "B replaced filesystem search with mcp__geos-rag__ (6 calls)",
  ],
}
```

Implementation: parse `events.jsonl` for tool_use events; categorize
Bash subcommands via regex on `command` arg; categorize Read paths
by prefix.

### Subagent 0.2 — TreesimXmllintAnalyzer

**Type**: Pure Python (`scripts/analysis/treesim_xmllint_analyzer.py`).

**Inputs**: `task_dir_a`, `task_dir_b`, `gt_task_dir`.

**Outputs** (dict):
```python
{
  "section_scores_a": {"Constitutive": 0.91, ...},
  "section_scores_b": {"Constitutive": 0.00, ...},
  "section_loss":     {"Constitutive": -0.91, ...},
  "tag_match_a":  ["Mesh","Constitutive",...],
  "tag_extra_a":  ["FunkyTag",...],
  "tag_missing_a":["Outputs",...],
  # same for b
  "node_loss_breakdown_a": [
    # walk treesim_detail recursively, collect nodes with score < 0.5,
    # ranked by (n_gt_children * (1 - score)) — i.e., points lost
    {"path": "Solvers/SolidMechanicsLagrangianFEM[lagsolve]", "score": 0.4,
     "lost_points": 1.8, "missing_attrs": ["targetRegions"], ...},
    ...
  ],
  "xmllint_a": [
    # xmllint --schema schema.xsd <each XML in inputs/>
    {"file": "Sneddon_base.xml", "errors": [
      "element 'CompressibleSolidCappedPlatesPorosity': not in schema; expected: ..."
    ]},
    ...
  ],
  "xmllint_b": [...],
  "summary_bullets": [
    "B's Solvers section dropped from 1.0 → 0.0 (entire block missing)",
    "B introduces 4 schema-hallucinated element names; A had 0",
  ],
}
```

Implementation: read `*_eval.json`, walk `treesim_detail` recursively
to identify worst-scoring nodes; run `xmllint --schema` on each XML
in `inputs/`; diff the results.

### Subagent 0.3 — TrajectoryReader

**Type**: Claude subagent (dispatched via `Agent(subagent_type=...)`).

**Inputs**: task name, condition A label + dir, condition B label + dir,
plus pre-computed 0.1+0.2 outputs as context.

**Subagent definition** (`.claude/agents/ablation-trajectory-reader.md`):
- Read both `events.jsonl` files (or filtered "assistant text only"
  versions for context efficiency).
- Read the diff outputs (0.1+0.2) as context.
- Identify decision points where A and B diverged:
  - File-discovery strategy choice
  - Element-name choice (any hallucinations?)
  - When did the agent decide a section was "done"?
- Return a 5-10 bullet narrative explaining the WHY of the score gap.

**Output** (string):
```markdown
## TutorialSneddon: why C4 (RAG+SR) lost 0.23 vs C2 (no RAG)

- **File discovery**: A used Glob (10 calls) → found 6 distinct
  `Sneddon_*_base.xml` reference files spanning 3 fracture-mechanic
  variants. B made 1 RAG call ("fracture mechanics geos"), got back
  prose chunks describing one variant, never explored
  `/geos_lib/inputFiles/` directly.
- **Variant decision**: A produced 6 XMLs (3 variants × {base,benchmark}).
  B produced only 2 (single variant). The GT layout B chose corresponds
  to lagrangianContact, but the GT requires all 3.
- **Element-name fidelity**: A copied element names verbatim from
  reference XMLs (no hallucinations). B inferred names from RAG prose
  and introduced `EmbeddedSurfaceMechanics` (not in schema; should be
  `EmbeddedSurfaces`).
- **Why this matters for the cross-task pattern**: this is the canonical
  "RAG suppresses Glob/Grep" failure mechanism described in 2026-04-28
  reconciliation doc.
```

The subagent's prompt template enforces this structure.

### Aggregation step in Subagent 1

Once per-task analyses are collected, the orchestrator extracts
recurring themes:
- Tool-use deltas that appear in ≥3 big-swing tasks
- Schema-hallucination patterns shared across tasks
- Section-loss patterns (e.g., "Solvers always tanks under condition B")
- File-count under-production (e.g., "B always produces 1 XML; A produces 3")

This is currently a hand-rolled Python aggregator. Could later be
upgraded to a Claude subagent reading all per-task summaries — keep
deterministic for now to avoid LLM noise in the cross-task synthesis.

## Output report format

```markdown
# Ablation: <cond_a> vs <cond_b>

*Generated 2026-XX-XX by ablation_analyzer.py*

## Summary
- mean treesim: A=0.671, B=0.628 (Δ=−0.043)
- mean cost: A=$0.42/task, B=$0.38/task
- mean wall: A=372s, B=310s
- big-swing tasks (|Δ| ≥ 0.10): N=4, of which 3 are degradations

## Per-task table
| task | A | B | Δ | tokens_A | tokens_B | cost_A | cost_B | walltime_A | walltime_B |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
...

## Degradations (sorted by |Δ|)

### TutorialSneddon: Δ = −0.233
**Tool-use** (subagent 0.1):
| tool | A | B | Δ |
|---|---:|---:|---:|
| Read | 30 | 6 | −24 |
| Glob | 10 | 0 | −10 |
| mcp__geos-rag__search_* | 0 | 6 | +6 |

**Treesim component-wise** (subagent 0.2):
| section | A | B | Δ |
|---|---:|---:|---:|
| Solvers | 1.00 | 0.20 | −0.80 |
...
**xmllint errors introduced by B**:
- `Sneddon_base.xml`: `EmbeddedSurfaceMechanics` not in schema (line 34)

**Trajectory reading** (subagent 0.3):
- File discovery: ...
- Variant decision: ...
...

### ExampleDPWellbore: Δ = ...
...

## Cross-task patterns
- In 3/4 degradations, condition B replaced Glob/Grep with RAG calls
- In 2/4, condition B produced fewer files than GT requires
- Schema-hallucination is non-monotone: B introduces fewer than A on
  pkn but more on Sneddon
```

## Implementation plan

Phase 1 (today, while ablation runs):
1. `scripts/analysis/tool_use_differ.py` — script for subagent 0.1
2. `scripts/analysis/treesim_xmllint_analyzer.py` — script for subagent 0.2
3. `scripts/analysis/score_table.py` — helper for subagent 1's score table
4. `scripts/analysis/ablation_analyzer.py` — orchestrator (subagent 1)
   - In Phase 1, skip the trajectory-reader (subagent 0.3); produce report
     with just 0.1+0.2 outputs.

Phase 2 (later):
5. `.claude/agents/ablation-trajectory-reader.md` — subagent 0.3 definition
6. Wire 0.3 dispatch into `ablation_analyzer.py`

The Phase 1 outputs are already very informative — the deterministic
analyses (tool-use, treesim breakdown, xmllint diff) typically tell
80% of the story. The trajectory reader is a nice-to-have for
narrative polish.

## Why this is worth building

Manually doing this for every ablation is the slow part. After the
DSv4 ablation matrix lands today we'll want to compare:
- C0 vs C1 (does *any* primer help?)
- C1 vs C2 (does SR hook help?)
- C1 vs C3 (does RAG alone help?)
- C2 vs C3 (RAG-vs-hook substitution)
- C3 vs C4 (does adding hook to RAG help?)
- C4 vs C5 (does memory add anything?)
- vanilla_dsv4_min (already-have C1) vs each new condition

That's 7+ pairwise analyses. Manual would take a day each. Scripted +
LLM-augmented should take 5 minutes each. The investment pays for
itself by the third ablation.

## Future extensions

- **Streaming mode**: as new seeds finish, recompute the table and
  flag if the rank-order of conditions changes (variance check).
- **Bottleneck-task triage**: for each big-swing task, automatically
  cluster the failure mode (F1 hallucination / F3 missing component /
  F4 spec under-spec) using the 0.2 outputs.
- **Domain-adaptation suggestion generator**: subagent 0.4 reads the
  cross-task pattern summary and proposes specific primer / skill /
  hook changes. (This is exactly the workflow we did manually for
  the 2026-04-28 reconciliation doc; codifying it as a subagent
  closes the loop.)

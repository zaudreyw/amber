# Evaluation

Evaluation lives in `src/eval/` (library) and `scripts/eval/` (CLI
entrypoints), separately from the experiment runner in `run/`. The runner
produces per-task workspaces with `inputs/*.xml`; evaluation scores those
against ground truth in `data/eval/experiments_gt/<task>/inputs/`.

All modules were ported from `geos_agent` without substantive changes —
see [cc_run_comparison.md](cc_run_comparison.md) for how the overall
pipeline differs.

## Modules

| Module | Role |
|---|---|
| `src/eval/judge_geos.py` | XMLTreeSim headline metric + legacy diagnostic dimensions |
| `src/eval/lxml_xml_eval.py` | Earlier weighted-dimension scorer (kept for backward compat / ablation) |
| `src/eval/agent_metrics.py` | Tool error rates + RAG retrieval accuracy from agent JSONL logs |
| `src/eval/llm_judge.py` | OpenAI/OpenRouter LLM-as-judge alternative |
| `src/eval/token_usage.py` | Aggregate billed tokens |

Contamination helpers (block-list + sanitized GEOS copy) live under
`src/runner/contamination.py`, not `src/eval/` — they're a runner concern,
not a scoring concern. See [experiment_runner.md](experiment_runner.md).

## CLI scripts

```bash
# Batch score all tasks in an experiment run against ground truth
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/claude_code/run1 \
    --ground-truth-dir data/eval/experiments_gt \
    --results-dir      data/eval/results/run1

# Ablate: use the older weighted-dimension metric instead of XMLTreeSim
uv run python scripts/eval/batch_evaluate.py ... --legacy

# One task only
uv run python scripts/eval/judge_one.py \
    --gt  data/eval/experiments_gt/ExampleEDPWellbore/inputs \
    --gen data/eval/claude_code/run1/ExampleEDPWellbore/inputs

# Tool-error + RAG-accuracy from CC conversation logs
uv run python scripts/eval/compute_agent_metrics.py \
    --logs-dir data/eval/claude_code/run1 \
    --output   data/eval/results/run1/agent_metrics.json

# Token totals across a run
uv run python scripts/eval/sum_billed_tokens.py data/eval/claude_code/run1

# LLM-as-judge (needs OPENROUTER_API_KEY)
uv run python scripts/eval/llm_judge.py --ground-truth gt.xml --generated gen.xml
```

## The headline metric: XMLTreeSim

Problem with the old weighted composite (`structural_completeness 0.15 +
element_type_match 0.35 + attribute_accuracy 0.35 + tag_coverage 0.15`):

- **Arbitrary weights** with no principled justification.
- **Correlated sub-metrics** (`structural_completeness` ~ `tag_coverage`).
- **`element_type_match`** used Jaccard of tag *sets*, so 5 GT
  `FieldSpecification`s vs 1 generated scored the same as 5 vs 5.
- **`attribute_accuracy`** only denominated over matched pairs, so it
  looked high when most elements were unmatched.

`XMLTreeSim` (`src/eval/judge_geos.py`) replaces the composite with a
single recursive tree-similarity score in [0, 1]; the final metric is the
root's score.

### Algorithm

```
TreeSim(gt_node, gen_node) -> float in [0, 1]:
  1. Match children of gt_node to children of gen_node using bipartite
     matching: group by tag, greedy by descending element similarity.
  2. For each GT child c_i:
       if matched to gen child g_j:
         attr = |matching attrs| / |union of attrs|
         child_score = attr                                 [leaf]
                     = alpha * attr + (1-alpha) * TreeSim(c_i, g_j)  [interior]
       else:
         child_score = 0
  3. matched_score = (1/N_gt) * sum(child_score)
     extra_penalty = beta * (N_extra / (N_gt + N_extra))
     return clamp(matched_score - extra_penalty, 0, 1)
```

Parameters (in `judge_geos.py`):

- `TREESIM_ALPHA = 0.3` — interior node: weight of own attrs vs subtree.
- `TREESIM_BETA  = 0.1` — penalty factor for extra (hallucinated) elements;
  missing elements are worse than hallucinated, so this is small.

### Why this is better

- **One grounded metric.** "Fraction of the GT tree correctly reproduced,
  weighted by depth." No hand-tuned dimension weights.
- **Respects tree structure.** Missing `<Solvers>` costs all its
  descendants. Getting `<Solvers>` right but missing one child param only
  penalises that subtree.
- **Handles multiplicity** via bipartite matching: 5 GT
  `FieldSpecification`s vs 1 generated → 4 contribute zero.
- **Sub-metrics fall out naturally.** Per-section TreeSim scores
  (`Solvers: 0.95`, `Mesh: 1.0`, `Events: 0.72`) are strictly more
  informative than the old composite.

### Reported output

`evaluate_directories(gt_dir, gen_dir)` returns:

```json
{
  "overall_score": 8.47,              // 10 * treesim
  "treesim": 0.847,
  "treesim_section_scores": {
    "Solvers": 0.95, "Mesh": 1.0, "Events": 0.72, ...
  },
  "dimension_scores": {               // legacy diagnostics only
    "structural_completeness": 1.0,
    "element_type_match": 0.82,
    "attribute_accuracy": 0.79,
    "tag_coverage": 0.90
  },
  "details": { ... },                 // TreeSim trace, up to max_depth=3
  "ordering_kendall_tau": 0.88        // diagnostic only
}
```

`overall_score` is `10 * treesim` so it stays on the 0–10 scale used by
existing plumbing (status.json, dashboards). Other numbers are not fed into
the headline — they exist so you can diagnose *why* a score is what it is.

### Multi-file / `<Included>` handling

Ground-truth and generated XML can span multiple files with `<Included>`
cross-references. `load_and_resolve_dir`:

1. Parses every XML in the directory.
2. Identifies entry files (not referenced by any other `<File>` tag).
3. Recursively inlines `<Included>` references.
4. Merges multiple entry files under a single `<Problem>` root.

Resolution happens *before* TreeSim, so scoring operates on the flattened
tree regardless of how the agent chose to split its files.

### Future: LLM-fuzzy matching

Currently the element-similarity function does exact tag + attribute
matching. When we relax the assumption that the user spells out every
required element, the clean extension point is
`compute_element_similarity`:

```python
def compute_element_similarity_fuzzy(gt, gen, llm_client=None):
    if gt.tag == gen.tag:
        return exact_attribute_similarity(gt, gen)      # fast path
    if llm_client:
        return llm_semantic_similarity(gt, gen, llm_client)  # slow path
    return 0.0
```

The tree traversal and bipartite matching stay put — only the leaf
similarity function changes. That's why matching and scoring are kept
cleanly separated in the current design.

## Agent-behaviour metrics

Independent of XML correctness:

- **Tool error rate** — fraction of tool calls that returned errors, per
  tool. Computed from `events.jsonl` or `cc_conversation.jsonl`.
- **RAG retrieval accuracy** — of the chunks returned by
  `search_navigator` / `search_schema` / `search_technical`, fraction
  whose source matches the expected RST for this task (requires
  `--source-path`).
- **Token usage and billed cost** — summed from per-turn usage blocks.

These are orthogonal to TreeSim: an agent can score 10/10 while wasting
tokens on tool errors, or vice versa. Report all three.

# LN-002: MemP — Procedural Memory for Agents (Fang et al. 2025)

*Notes from arxiv 2508.06433v4. Companion to `LN-001_memory-test-time-literature.md`.*

## Source

- **Paper**: https://arxiv.org/html/2508.06433v4
- **Repo**: https://github.com/zjunlp/MemP
- **Authors**: Runnan Fang, Yuan Liang, et al. (Zhejiang Univ + Alibaba)
- **Local copies**: `docs/literature/memp_2508.06433v4.{html,md}`,
  `misc/memp_external/MemP/`

## One-paragraph summary

MemP frames procedural memory (vs declarative/factual memory) as a
first-class object with three operations: **Build** (distill
trajectories into reusable workflows), **Retrieve** (cosine-similarity
match on new task), **Update** (add/delete/modify entries
post-execution). Unlike Dynamic Cheatsheet (single monolithic
primer) it stores **per-trajectory** entries and retrieves task-
relevant ones at test time. Tested on TravelPlanner + ALFWorld;
shows positive transfer + transfer from stronger model to weaker
model.

## Key claims

1. **Procedural memory boosts accuracy and cuts trial count.**
   On TravelPlanner with GPT-4o, no-memory = 71.93%, MemP-script =
   72.08% (small lift but clear step reduction).
2. **Procedural memory transfers from strong models to weaker ones.**
   Memory built by GPT-4o helps Qwen.
3. **Scaling memory retrieval improves agent performance.**
   Retrieving more entries (k > 1) helps until a saturation point.

## Three operations and design space

### Build

`build_policy ∈ {round, direct}`:
- **round**: multi-step "events" extraction (each trajectory step → JSON event)
- **direct**: single coherent workflow paragraph distilled from full trajectory

The repo has two prompt templates:
- `generate_workflow_from_trajectory_prompt`: full trajectory →
  natural-language workflow paragraph.
- `generate_events_from_trajectory_prompt`: full trajectory → JSON
  list of `{step, pre_state, action, entity, new_state}`.

For GEOS-XML our trajectories are short and the value-add is in
"how-to" prose, not per-step events. → use **direct** policy.

### Retrieve

`retrieve_policy ∈ {query, facts, random, ave_fact}`:
- **query**: cosine-sim between new task description and stored
  task descriptions; top-k retrieved.
- **facts**: cosine-sim against extracted facts (e.g., extracted
  destinations or attribute lists).
- **ave_fact**: average over fact embeddings.
- **random**: control.

Default + best in paper appears to be **query**. We'll use this.

### Update

`update_policy ∈ {add, delete, modify, ...}`:
- **Add**: incorporate new successful trajectories.
- **Delete (Del)**: remove memory entries whose actions failed.
- **Modify (Update)**: edit memory based on test-time feedback.

Update is the *online learning* mode. For our offline build we'll
skip update for now (and it overlaps with Task 3's self-evolving
agent anyway).

## Adaptation to GEOS XML authoring

Our setup vs MemP paper:
- **Task type**: structured XML authoring (vs travel planning + housework).
- **Action set**: standard CC tools (Read/Glob/Grep/Bash/Write) +
  optionally MCP tools. Not domain-specific verb set like the paper's
  `FlightSearch[...]`.
- **Train set**: 18 GEOS train tasks (`misc/memory_split.json["train"]`).
- **Test set**: 17 GEOS v2 test tasks.
- **Trajectories already harvested**: under
  `/data/shared/.../dsv4_ablation_2026-04-29/abl_c2_min_sr_no_rag/harvest_c2_dsv4_s1/`.
  Same C2 setup we ran. All 18 succeeded, mean treesim 0.895.

### Differences from M1-u (our existing memory, Dynamic-Cheatsheet-style)

| Property | M1-u (DC) | MemP |
|---|---|---|
| Granularity | One primer for all tasks | Per-trajectory entries |
| Retrieval | None (always inject) | Cosine sim on task desc |
| At test time, agent sees | All distilled content | Top-k relevant entries |
| Token cost per task | Constant (820 tok) | k × ~300-500 tok per entry |
| Anti-pattern surfacing | Aggregated rules | Per-task workflows |

**Hypothesis**: MemP wins where individual train tasks share
strong physics-class signal with test tasks (e.g., wellbore-train
→ wellbore-test). DC wins where the failure modes are diffuse
across tasks (the M1-u distill aggregates failure-mode patterns).

For GEOS XML: many task families are clearly clustered
(wellbore, fracture, poromechanics, tutorial-style) → MemP
retrieval should latch onto right train memory.

## Implementation plan for our pipeline

1. **Build (`scripts/memory/distiller_memp.py`)**:
   - For each of 18 train tasks: read instructions + harvested
     trajectory, prompt gemini-3-flash-preview with the workflow
     prompt (adapted for GEOS XML).
   - Compute embedding of task instructions using qwen3-embedding-8b
     (already in our infra).
   - Save library at `misc/memory_artifacts/memp_dsv4/library.json`:
     `[{task_id, query, query_embedding, workflow}]`.

2. **Retrieve + render (`scripts/memory/render_memp_per_task.py`)**:
   - For each of 17 test tasks: compute embedding of test task
     instructions.
   - Cosine-sim against all 18 train entries; take top-K.
   - Render per-task primer file `plugin/memp_per_task/<task>.md`
     containing the K retrieved workflows + brief intro text.

3. **Runner change (`src/runner/orchestrator.py`)**:
   - Add support for `cheatsheet_path_template` in agent dict.
     Substitute `{task}` with the actual task name at task-launch time.
   - This is a small change; existing per-task substitution patterns
     already exist for `result_dir`.

4. **Agent variant**:
   - `abl_cMP_dsv4_memp_top3`: same as C7 (xmllint hook + MCP tool +
     no RAG) but with per-task MemP retrieval as cheatsheet.
   - Compare to C7 (no memory baseline) and C11 (M1-u memory baseline).

5. **Run on 17 test tasks × 3 seeds**, score, run analyzer
   `C7 vs cMP_top3` and `C11 vs cMP_top3`.

6. **Decision**: pick best memory system (M1-u DC-style, MemP
   procedural with retrieval, or no memory).

## Key prompts (paper's)

The MemP repo prompt for "direct" build (workflow from trajectory),
adapted for GEOS XML, will look like:

> You are provided with a query and a trajectory taken to solve the
> query. The trajectory consists of multiple steps of thought, action,
> and observation. Your task is to generate a workflow based on
> critical steps to help solve similar GEOS XML authoring queries in
> the future. A critical step is one that has a significant impact on
> producing valid GEOS XML — actions in the set [Glob, Grep, Read,
> Bash, Write] whose outcome contributed positively. Write the
> workflow as a natural coherent paragraph...

Will use this template + GEOS-specific examples.

## Implementation choices we'll make explicit

- **K = 3** retrievals per test task (paper uses k=10 but on much
  larger task sets; with 18 train tasks, k=3 is more conservative
  and avoids dumping the whole library).
- **Embedding model**: qwen3-embedding-8b via OpenRouter (we
  already use this for M3 memory variant).
- **Build policy**: "direct" workflow distillation (vs "round"
  events). Our trajectories are short enough.
- **Retrieve policy**: "query" — task-description cosine match.
- **Update policy**: skip for offline build. Online update is
  Task 3's territory.

## Time budget

- Notes (done now): 30 min
- Build script: 30 min
- Render script + runner change: 30 min
- Run + analyze: 25 min wall + 10 min analysis
- Total: ~2h end-to-end.

---
id: LN-002
title: "Memory-for-agents survey (verified): Dynamic Cheatsheet, ACE, ReasoningBank, MemEvolve"
date: 2026-04-22
dag_nodes: [I06, I10]
links:
  related_to: [LN-001, XN-003, XN-009, XN-011, XN-014]
  supersedes: [memory_survey_2026-04-22_UNVERIFIED_superseded.md]
tags: [memory, dynamic-cheatsheet, ace, reasoningbank, memevolve, survey]
---

# Memory-for-Agents Survey — Verified (2026-04-22)

*Primary sources: full HTML/PDF of all four papers + local clones of all
four repos under `/home/matt/sci/repo3/misc/refs/`. Replaces the earlier
unverified survey (archived as `*_UNVERIFIED_superseded.md`) which was
synthesized from training-cutoff memory without web access.*

| Paper | URL | Local fetch |
|---|---|---|
| Dynamic Cheatsheet | arxiv 2504.07952v1 (Apr 2025) | `misc/refs/dynamic-cheatsheet.md` + `dynamic-cheatsheet/` |
| ACE | arxiv 2510.04618v3 (Oct 2025) | `misc/refs/ace.md` + `ace/` |
| ReasoningBank | arxiv 2509.25140v1 (Sep 2025) | `misc/refs/reasoningbank.md` + `reasoning-bank/` |
| MemEvolve | arxiv 2512.18746v1 (Dec 2025) | `misc/refs/memevolve.txt` + `MemEvolve/` |

---

## 1. Dynamic Cheatsheet (Suzgun, Yuksekgonul, Bianchi, Jurafsky, Zou — Apr 2025)

**Gist.** Endow a black-box LM with a persistent text "cheatsheet" that
accumulates reusable strategies, code snippets, and insights. Two
variants: **DC-Cu** (cumulative; curator rewrites memory after each
answer) and **DC-RS** (retrieval + synthesis; retrieves similar past
inputs first, then curates, then answers). Self-curated — no ground-truth
labels required.

**Memory form.** Single natural-language text artifact (the "cheatsheet").
Not an index of typed entries. In DC-RS, the cheatsheet is augmented by
top-k retrieved past input-output pairs at curation time.

**Retrieval.** DC-Cu: none. **DC-RS: embedding search** with OpenAI
`text-embedding-3-small`, k=3. Retrieved pairs inform the curator, not the
generator directly.

**Update dynamics.** Online. After generating $\tilde y_i$ for $x_i$, the
curator produces $M_{i+1} = \text{Cur}(M_i, x_i, \tilde y_i)$. Curator is
instructed to (i) extract generalizable insights, (ii) refine/remove
outdated entries, (iii) keep the memory compact. Both generator and
curator are typically the same LLM with different prompts.

**Agent count.** Single-agent. The "roles" (Gen, Cur, Retr) are prompts
run on one LM.

**Reported wins.** Claude 3.5 Sonnet: +27pp AIME 2024, +30pp AIME 2025 (DC-Cu).
GPT-4o: 10% → 99% Game of 24 (DC-RS). +9% GPQA-Diamond, +8% MMLU-Pro.

**Implementation complexity.** Low. Core is ~668 LOC
(`dynamic_cheatsheet/language_model.py`) plus prompts. Single model, single
text string, a few API calls per query. Embedding retrieval only in DC-RS.

**Repo:** https://github.com/suzgunmirac/dynamic-cheatsheet — local clone
at `misc/refs/dynamic-cheatsheet/`.

**Fit for our task.**
- Clean test of "does any memory help on top of RAG+SR" without
  engineering an embedding pipeline.
- DC-Cu's "growing monolithic text" maps naturally to a `primer.md`-style
  artifact appended to the system prompt — we already have a primer path.
- Training-time version: generate the cheatsheet from the 18 train
  trajectories offline, then inject as a frozen text block. No online
  curation at test time (matches your "no online updates — kills
  parallelism" constraint).
- DC-RS's `text-embedding-3-small` = OpenAI. For us: OpenRouter equivalent
  (see §5 below).

---

## 2. ACE — Agentic Context Engineering (Oct 2025)

**Gist.** Extends Dynamic Cheatsheet with three explicit roles and a
**structured itemized bullet** format. Explicitly targets two failure
modes of monolithic cheatsheet rewrites: "brevity bias" (curator
compresses detail away) and "context collapse" (iterative rewriting
degrades the context over time).

**Three roles.**
- **Generator:** produces reasoning trajectories on new queries, flags
  which bullets were useful vs misleading.
- **Reflector:** critiques trajectories, extracts lessons, can iterate
  multiple times per trace.
- **Curator:** integrates reflections into the bullet store via
  **incremental delta updates** (not monolithic rewrite). Non-LLM merge
  logic handles the actual store operations.

**Memory form.** Structured bullets with (1) metadata: unique ID +
helpful/harmful counters; (2) content: reusable strategy, domain concept,
or failure mode. Bullets are fine-grained — dedup by semantic embedding
in a "grow-and-refine" phase that runs proactively or lazily.

**Retrieval.** Fine-grained retrieval of relevant bullets at Generator
time. Paper doesn't pin down the retrieval mechanism but the dedup uses
semantic embeddings.

**Update dynamics.** Online. **Delta updates** — the Curator only adds
new bullets or bumps counters on existing ones; it does not rewrite the
whole context. This is the core engineering contribution over DC.

**Agent count.** Single agent orchestrating three roles.

**Reported wins.** +10.6% on agent benchmarks (AppWorld), +8.6% on
finance; up to +17.1% on AppWorld. Adapts without labeled supervision;
uses execution feedback.

**Implementation complexity.** Medium. ACE code: ~1240 LOC across
`llm.py`, `playbook_utils.py`, `logger.py`, `utils.py` + benchmark-
specific drivers. Conceptually more machinery than DC (three roles +
delta merge logic + dedup step).

**Repo:** https://github.com/kszhangus/ACE (hosted under different name
than user's guess "ace-agent/ace"; we cloned successfully from
`https://github.com/ace-agent/ace.git` which exists and resolves).

**Fit for our task.**
- Explicitly motivated by preserving detailed domain heuristics and
  common failure modes — which is *exactly* our F2 (wrong-version drift)
  and F4 (spec under-specification) problem from XN-014.
- Bullet-level format + helpful/harmful counters is a natural place to
  encode anti-patterns ("don't use `fluidNames`/`solidNames` — those are
  pre-v2 attributes").
- Cost to adapt to a frozen-memory setting is straightforward: do
  offline reflection on the 18 training trajectories to build the
  initial bullet set, disable online updates at test time.

---

## 3. ReasoningBank (Sep 2025)

**Gist.** Distill past trajectories into structured **memory items**
(title + description + content). Extracts items from **both successful
and failed** experiences — failures yield counterfactual signals and
guardrails, not just discarded data. Retrieve top-k relevant items at
each new task and inject into the agent's system instruction.

**Memory form.** Structured JSON items: `{title, description, content}`.
Multiple items per trajectory. Human-interpretable and machine-usable.

**Retrieval.** **Embedding-based similarity search**, top-k. Retrieved
items injected into system prompt.

**Update dynamics.** Online, closed-loop. (i) retrieve → (ii) act →
(iii) LLM-as-judge labels trajectory as success/failure → (iv) extract
memory items with per-label prompts → (v) simple-append consolidation.
Deliberately kept simple in the retrieve/consolidate steps to highlight
the contribution of the memory item design itself.

**Agent count.** Single-agent on task (the LLM-judge is a separate
prompt). Web browsing and SWE-bench eval.

**Reported wins.** Consistently outperforms raw-trajectory and
successful-only memory baselines on WebArena and SWE-bench. Plus MaTTS
(Memory-aware Test-Time Scaling) amplifies gains when you allocate more
rollouts per task.

**Implementation complexity.** Medium. ~1000 LOC across
`reasoning-bank/WebArena/` (6 files: run, induce_memory,
memory_management, induce_scaling, pipeline_memory, pipeline_scaling).

**Repo:** https://github.com/google-research/reasoning-bank — local clone
at `misc/refs/reasoning-bank/`.

**Fit for our task.**
- Directly addresses our F2/F4 — the failure-driven memory item design
  is what would store "Mandel task: do not copy `fluidNames` attribute
  from old examples."
- Closest architectural match to our existing `G-Memory-lite` (structured
  JSON, retrieve-by-query, inject-into-prompt). Difference: RB distills
  **strategies**, our index stores **pointers to reference XMLs**.
- Our 18 train trajectories (12 high TreeSim, 6 lower) provide a built-in
  success/failure split for RB-style extraction.
- Upgrade path from current impl: replace lexical token overlap with
  embeddings, replace "past-task summaries" with "extracted strategies
  and anti-patterns." That's a concrete, bounded change.

---

## 4. MemEvolve (OPPO AI + LV-NUS, Dec 2025)

**Gist.** Meta-evolutionary framework: treats the memory architecture
itself (not just its contents) as something to evolve, using agent task
performance as the fitness signal. Contribution is the **outer loop** —
the memory architecture evolves; the inner loop is the standard agent +
memory interaction.

**Modular design space (the paper's general framework).** Every memory
system decomposes into four components:
- **Encode (E):** raw experience → structured representation
- **Store (U):** commit representations to persistent memory
- **Retrieve (R):** context-aware recall
- **Manage (G):** consolidation, abstraction, selective forgetting

**EvolveLab: the 12 re-implemented methods (paper's Table 1, verbatim):**

| # | Method | Date | Mul. | Gran. | Online | Encode | Store | Retrieve | Manage |
|---|---|---|---|---|---|---|---|---|---|
| I | Voyager | 2023.5 | single | traj. | online | Traj. & Tips | Vector DB | Semantic Search | N/A |
| II | ExpeL | 2023.8 | single | traj. | online | Traj. & Insights | Vector DB | Contrastive Comparison | N/A |
| III | Generative Agents | 2023.10 | multi | traj. | online | Traj. & Insights | Vector DB | Semantic Search | N/A |
| IV | DILU | 2024.2 | single | traj. | online | Traj. | Vector DB | Semantic Search | N/A |
| V | AWM (Agent Workflow Memory) | 2024.9 | single | traj. | online+offline | Workflows | Vector DB | Semantic Search | N/A |
| VI | Mobile-E | 2025.1 | single | step | offline | Tips & Shortcuts | Vector DB | Semantic Search | N/A |
| VII | Cheatsheet (DC) | 2025.4 | single | traj. | online | Tips & Shortcuts | JSON | Semantic Search | N/A |
| VIII | SkillWeaver | 2025.4 | single | traj. | offline | APIs | Tool Library | Function Matching | Skill Pruning |
| **IX** | **G-Memory** | **2025.6** | **multi** | **traj.** | **online** | **Tips & Workflow** | **Graph** | **Graph/Semantic Search** | **Episodic Consolidation** |
| X | Agent-KB | 2025.7 | multi | step | offline | Tips & Workflow | Hybrid DB | Hybrid Search | Deduplication |
| XI | Memp | 2025.8 | single | step | online | Tips & Workflow | JSON | Semantic Search | Failure-driven Adjustment |
| XII | EvolveR | 2025.10 | single | step | online | Tips & Workflow | JSON | Contrastive Comparison | Update & Pruning |

*(Paper Table 1 convention: ♂ single-agent, ♂♂ multi-agent, step vs
traj. granularity, ® online / a offline.)*

**Memory form / retrieval / update / complexity.** The framework itself
is meta-level. Primary memory is whatever the current evolutionary
genotype selects; retrieval and update are whatever that genotype's (E,
U, R, G) implementations do. MemEvolve evolves these implementations via
a model-driven outer loop using agent performance as fitness.

**Reported wins.** Up to +17.06% over base agent on SmolAgent and
Flash-Searcher on GAIA, WebWalkerQA, TaskCraft, xBench-DS. Cross-task
and cross-LLM generalization.

**Implementation complexity.** Highest. The repo vendors the
Flash-Searcher agent and implements all 12 memory systems +
EvolveLab base class + MemEvolve outer-loop orchestration. Total ~9400
LOC in `Flash-Searcher-main/`, with 14 memory provider modules in
`EvolveLab/providers/`.

**Repo:** https://github.com/bingreeky/MemEvolve — local clone. The
`providers/` directory is a **goldmine**: it implements
`dynamic_cheatsheet_provider.py`, `expel_provider.py`,
`agent_workflow_memory_provider.py`, `memp_memory_provider.py`, etc. —
so if we want any of these 12 methods, we don't need to implement from
scratch, we can adapt a provider.

**Fit for our task.**
- The meta-evolution outer loop itself is overkill for a 2-week project
  (we don't have the evaluation budget to run an evolutionary search
  over memory architectures).
- **But EvolveLab as a library is extremely useful.** Each provider is
  50-300 LOC, implements a known method, and exposes the (E,U,R,G)
  interface. We can pick one — e.g., `dynamic_cheatsheet_provider.py` or
  `memp_memory_provider.py` — and drop it in, behind our MCP layer.

**Important: MemEvolve places G-Memory as row IX in the taxonomy —
multi-agent, graph-structured, online, episodic consolidation.** This is
the post-doc's point exactly: **G-Memory is designed for multi-agent
trajectory graphs.** For our single-agent frozen setting, the taxonomy
offers much simpler rows (Cheatsheet, DILU, Voyager, Memp) that are
already strictly simpler and more appropriate.

---

## 5. Summary table — complexity and fit for our task

Ranked by implementation simplicity (simplest → most complex). Task fit
is for: **single-agent, ~18 frozen training trajectories, test-time
static memory, XML-generation with strong external RAG, parallel eval
runs, no online memory updates desired.**

| Rank | Method | LOC (core) | Retrieval | Online? | Fit | Verdict |
|---|---|---|---|---|---|---|
| 1 | **DC-Cu (frozen)** | ~300-500 | none | offline distill | 🟢 High | Simplest clean test of "any memory help" |
| 2 | **Anti-pattern bullet list** (ACE-lite) | ~200-400 | none / simple | offline distill | 🟢 High | Directly targets F2/F4 from XN-014 |
| 3 | **DC-RS (frozen)** | ~600-800 | embedding | offline distill | 🟢 High | Adds retrieval benefit without online cost |
| 4 | **ReasoningBank (frozen)** | ~800-1000 | embedding | offline distill | 🟡 Med-High | Strongest semantic match for failure-distillation |
| 5 | **Our current G-Memory-lite** | 173 | lexical | offline, frozen | 🟡 Medium | Already implemented but lexical + never called |
| 6 | **Memp / EvolveR provider** (from EvolveLab) | ~300 | semantic | online by default | 🟡 Medium | Failure-driven management; needs adaptation for frozen |
| 7 | ACE full | 1240 | embedding dedup | online | 🔴 Low | Online updates conflict with parallel eval |
| 8 | ReasoningBank full online | ~1000 | embedding | online | 🔴 Low | Same |
| 9 | Repo2 G-Memory (full) | 1831 | embedding + graph | online | 🔴 Low | Built for multi-agent; overkill |
| 10 | MemEvolve (full) | ~9400 | varies | online + meta-evo | 🔴 Low | Meta-evo needs orders of magnitude more eval budget |

**Online methods can still be used in "frozen" mode** — just run the
memory construction step offline on the 18 train trajectories, freeze
the output, disable updates at test time. This works for any of
DC, ACE, ReasoningBank, or any EvolveLab provider. The honest framing is
that "online memory updates are the paper's contribution" for most of
these, but "offline distilled memory" is what our setup actually needs.

---

## 6. Retrieval: OpenRouter embeddings

User specified embeddings via OpenRouter (not OpenAI).

OpenRouter's embeddings endpoint: `https://openrouter.ai/api/v1/embeddings`
(per https://openrouter.ai/docs/api/reference/embeddings, same schema as
OpenAI's `POST /v1/embeddings` — `model`, `input`, returns `data[].embedding`).

Practical models available through OpenRouter for embeddings (as of
training cutoff; verify availability at request time):
- `text-embedding-3-small` / `text-embedding-3-large` (OpenAI via OR)
- `voyage-3` / `voyage-3-large` (Voyage via OR)
- `cohere/embed-v3`
- `jina-embeddings-v3`

For our 18-entry corpus, any of these is more than sufficient. The
budget cost is trivial: 18 entries × ~400 tokens/entry = ~7k tokens of
index-build cost, then ~400 tokens per eval query. At
text-embedding-3-small prices (~$0.02 / 1M tokens) this is ~$0.0001 per
full evaluation run.

---

## 7. Punchline

**Three concrete proposals, in order of what I'd test first:**

1. **DC-Cu (frozen)** — build a single cheatsheet text from the 18 train
   trajectories + the known failure patterns (F1–F4 from XN-014),
   inject it into the system prompt. No retrieval infrastructure. No
   online updates. ~1 day to implement, ~$5 to evaluate on 17 tasks with
   3 seeds. **Directly tests whether "any memory at all, simplest
   possible form, helps on top of RAG+SR."**

2. **ACE-lite anti-pattern bullets (frozen)** — same budget, but the
   cheatsheet has structured bullets (one per anti-pattern, tagged with
   physics-family), retrieved via simple tag-match or full-text. Tests
   whether **structured** memory helps where monolithic cheatsheet did
   not. Minimal engineering over (1).

3. **ReasoningBank-style, frozen, with OpenRouter embeddings** — our
   existing `G-Memory-lite` with two upgrades: (a) replace lexical
   retrieval with OpenRouter embeddings (jina-v3 or text-embedding-3-small);
   (b) add anti-pattern entries distilled from failed task trajectories.
   ~3-4 days work, ~$15 to evaluate. **Tests whether embedding +
   failure-distillation both matter together** (our existing lexical +
   success-only experiment was negative).

**What I would *not* recommend for this project:**
- Full ACE / ReasoningBank / MemEvolve online — online updates break
  parallelism per your explicit constraint.
- Full repo2 G-Memory port — multi-agent machinery unused in our
  single-agent setting; the post-doc's "overkill" concern is
  corroborated by MemEvolve's taxonomy (G-Memory sits in the
  most-complex row).

**Caveat I owe you:** Even with these three, there is **no guarantee any
of them beats RAG+SR alone.** RAG+SR already captures most of the
addressable surface (F1). Memory contributions on top of strong retrieval
+ self-refinement are empirically fragile across these papers — most of
their reported wins are over no-retrieval or weak-retrieval baselines.
If DC-Cu (the simplest) shows no gain on top of RAG+SR, the honest
framing is "we have no evidence memory is worth adding." That negative
result is itself a paper-worthy claim in our setting.

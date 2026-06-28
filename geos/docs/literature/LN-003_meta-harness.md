---
id: LN-003
title: "Meta-Harness: End-to-End Optimization of Model Harnesses (Lee et al., 2026)"
date: 2026-04-30
arxiv: 2603.28052v1
url: https://arxiv.org/abs/2603.28052v1
project_page: https://yoonholee.com/meta-harness/
artifact: https://github.com/stanford-iris-lab/meta-harness-tbench2-artifact
authors: Yoonho Lee, Roshen Nair, Qizheng Zhang, Kangwook Lee, Omar Khattab, Chelsea Finn
dag_nodes: []
links:
  related_to: [LN-002_memp, "self-evolving (Task 3, 2026-04-30)"]
  evidence_for: ["H4 (file-tree-in-context)"]
---

# LN-003: Meta-Harness — automated outer-loop search over LLM harness code

## Headline

Stanford/MIT/KRAFTON paper (30 Mar 2026) that **automates harness engineering**:
an outer-loop coding-agent proposer (Claude Code w/ Opus-4.6) iteratively
proposes new task-specific harnesses, evaluates them, and writes the source +
execution traces + scores into a filesystem the proposer reads on the next
iteration. Same loop spirit as our Task-3 self-evolving experiment, but at much
larger scale and with a sharper claim: *full filesystem access to prior code
and traces* is the ingredient that beats compressed-feedback text optimizers
(GEPA, OpenEvolve, ProTeGi, TextGrad, AlphaEvolve, TTT-Discover).

The paper is directly load-bearing for repo3 because:
1. The proposer they use **is Claude Code with Opus-4.6**. Same harness we're
   adapting; their results bound what's possible with self-modification.
2. Their TerminalBench-2 winner is essentially **environment-bootstrap injected
   into the initial prompt** — structurally identical to our H4 (file-tree
   injection) and the deepseek-v3.2 primer experiments. They validate that
   *purely additive context injected before the agent loop* is the safest
   high-leverage modification.
3. The text-classification harness family they discover (memory + retrieval +
   contrastive pairs) is essentially the design space we're already exploring
   for plugin RAG.
4. The MemP "skill = procedural memory" framing in LN-002 is the same idea
   used here for the proposer's own skill text.

## Core method (Section 3)

- **Outer loop**: at each iteration, a coding-agent proposer queries a
  filesystem `D` containing every prior candidate's `(source, scores, traces)`,
  proposes `k` new harnesses, each is evaluated and added back to `D`. Repeat
  for `N` iterations. Maintains a population + Pareto frontier; *no
  parent-selection rule* — proposer picks what to inspect.
- **Proposer**: Claude Code + Opus-4.6 with max reasoning, guided by a
  domain-specific *skill* (Anthropic agent-skill) that specifies directory
  layout, CLI tools, output format. Skill constrains *outputs and safety*, not
  diagnostic procedure.
- **Filesystem-as-feedback**: each candidate's directory typically holds
  source + scores + traces in JSON. Proposer reads via `grep`/`cat` rather
  than ingestion. In TerminalBench-2 a single eval can produce up to ~10M
  tokens; the filesystem is much larger than the proposer's context.
- **Validation**: malformed candidates rejected by a tiny interface test
  before the expensive eval (Appendix D).
- **Typical run**: ~60 harness evals over ~20 iterations, "a few hours"
  wall-clock.

## Three experiments

### 4.1 Online text classification — base model GPT-OSS-120B

- 3 datasets: LawBench (215 classes), Symptom2Disease (22), USPTO-50k (180).
- Init population: zero-shot, few-shot, ACE, MCE.
- 20 evolution iters × 2 candidates each = 40 candidates.
- **Result**: best discovered harness 48.6% avg vs ACE 40.9% (+7.7) using
  **4× fewer context tokens** (11.4K vs 50.8K). Beats MCE +8.6.
- **OOD generalization** (9 unseen datasets, Section C.1): 73.1% avg
  vs ACE 70.2%; best on 6/9. Naive few-shot hurts beyond N=32 in 7/9.
- **Interface ablation** (Table 3) — *the most important number in the
  paper*: scores-only median 34.6 / best 41.3; scores+summaries 34.9/38.7;
  full filesystem (raw traces) **median 50.0 / best 56.7**.
  Median-of-full > best-of-ablations. Summaries don't recover the lost signal
  and may *hurt* by dropping diagnostic detail.
- vs text optimizers (OpenEvolve, TTT-Discover): Meta-Harness matches
  their final accuracy in **0.1× the evals** and ends 10+ points higher.

### 4.2 Retrieval-augmented IMO-level math — GPT-OSS-20B as base

- 535K-problem deduplicated/decontaminated retrieval corpus (Section C.2);
  fuzzy-Jaccard threshold 0.8 vs eval splits.
- 250-problem search set (Olympiad + Omni-MATH hard); 40 iterations,
  109 candidates.
- Eval: 200 IMO-level problems on **5 held-out models** (GPT-OSS-20B,
  GPT-5.4-nano, GPT-5.4-mini, Gemini-3.1-Flash-Lite, Gemini-3-Flash).
- **Result**: discovered harness +4.7 pts avg over no-retrieval,
  +1.3 over BM25. Generalizes across 5 unseen models.
- Discovered structure (B.2): a **lexical router** assigns each query to
  one of {combinatorics, geometry, number-theory, default}, then runs a
  route-specific BM25 retrieval policy with route-specific dedup/rerank/K.
  Math-aware tokenizer that preserves LaTeX tokens. Combines two earlier
  successful lineages — proposer autonomously merged them.

### 4.3 Agentic coding (TerminalBench-2)

- 89 tasks, search and final eval on the same set (with manual
  contamination audit + regex audits for task-string leakage).
- Init from Terminus 2 and Terminus-KIRA.
- **Result on Opus 4.6**: 76.4% pass — beats Terminus-KIRA (74.7) and
  ranks #2 (ForgeCode 81.8% reportedly not reproducible).
- **Result on Haiku 4.5**: 37.6% — #1 among Haiku 4.5 agents (next-best
  Goose 35.5).
- **Discovered modification (B.3)**: just **environment bootstrapping**
  added on top of Terminus-KIRA. Before the agent loop, run one compound
  shell command; collect `pwd`, `/app` listing (truncated to 20 entries),
  language versions (python/gcc/g++/node/java/rust/go), package managers
  (pip, apt-get), available memory. Inject as `[Environment Snapshot]` in
  the initial prompt. 15-second timeout, fails silently. ~80 LOC on top of
  Terminus-KIRA.
- Per-task: gains on **7 of 89 tasks**, biggest on protein-assembly and
  path-tracing — tasks needing domain-specific tooling whose presence is
  not assumed (bioinfo, rendering, chess engines, crypto, CoreWars).

## Causal-reasoning trajectory (Appendix A.2) — important

The TerminalBench-2 search log shows the proposer doing more than random
mutation:

- Iter 1–2: bundles structural fix + new prompt template; **both regress**
  ~6 pp from 64.4% baseline.
- Iter 3: proposer **diagnoses the confound** — common factor across
  failures is the cleanup-heavy prompt rewrite, not the bugfixes. Reverts
  prompt and isolates the structural fixes. Still slightly under (-1.1pp)
  but loses much less.
- Iter 4–6: more direct fixes to the diagnosed state-machine bug; all
  regress. Proposer learns: prompt + completion-flow edits are high risk.
- Iter 7 (winning candidate): explicitly pivots strategy — *"All 6 prior
  iterations regressed because they modified the completion flow, prompt
  template, or observation processing. evo_env_bootstrap takes a different
  approach — purely additive."* Best result so far. **The proposer
  articulates *why* a purely additive change should be safer.**
- Iter 8: composes env-bootstrap with marker-stripping (orthogonal fixes).
- Iter 10: cross-run transfer — references a lesson from a separate run.

A.1 file-access stats: median **82 files read per iteration** (range
69–99). Split: 41% prior harness source, 40% execution traces, 6% scores,
13% other. *Non-Markovian access* — proposer routinely inspects far more
than the most recent parent.

## Discovered text-classification harness families (B.1)

Two endpoints from the Pareto frontier (full frontier in Table 9):

**Draft Verification** (low-context, 5.4K ctx, 40.1% avg): two short calls.
1. Retrieve 5 nearest labeled examples → make draft prediction `D`.
2. Re-retrieve conditioned on `D`: 5 *confirmers* (same label) + 5
   *challengers* (different labels) → ask model whether to maintain or
   revise. **Targeted counterexamples**, not generic neighbors.
3. Cold start: <5 examples → fall back to single-call few-shot.

**Label-Primed Query** (high-acc, 45.5K ctx, 48.6% avg): one larger call,
three blocks.
1. *Label primer* — list all valid labels up front.
2. *Coverage* — TF-IDF retrieves the most query-relevant example *per
   label*.
3. *Contrastive pairs* — pairs of highly similar examples with different
   labels (query-anchored partner selection), exposing local decision
   boundaries.

## Practical implementation tips (Appendix D)

These are the engineering lessons that actually generalize:

1. **Skill text is the strongest lever.** Iterate on the skill via 3–5
   short evolution runs *before* committing to a full run. After enough
   iterations, accumulated traces shape behavior more than the skill.
   Skill should constrain outputs and safety, *not* diagnosis procedure.
2. **Baseline + hard-for-baseline search set.** ~50–100 examples; small
   enough for ~50 full evals per run. Filter for what the baseline gets
   wrong — search has nothing to do if the baseline saturates.
3. **Log everything in queryable JSON.** Hierarchical, consistent
   filenames, regex-searchable.
4. **Small CLI for the experience store.** Pareto frontier, top-k,
   diff-pairs. Aligns with the read–write–execute workflow on which
   coding agents are trained. Saves proposer tokens on navigation.
5. **Lightweight pre-eval validation.** Tiny test that imports the
   module, instantiates the class, calls both methods. Reject malformed
   candidates in seconds.
6. **Run evals outside the proposer.** Separate harness scores
   candidates and writes results.

## Comparison framing (Section 2 + Appendix E)

Why prior text optimizers fall short (per-iter context budgets in
Table 1):
- **OpenEvolve / AlphaEvolve**: 4–22K tokens/step, scalar feedback
  + tournament selection over a fixed scaffold. Designed for stateless
  algorithm discovery, not stateful harnesses.
- **GEPA**: closest in feedback richness — provides rollout traces — but
  per-candidate (2–8K tokens/step) with a *fixed critique format*.
  Cannot reason across many candidates simultaneously.
- **ProTeGi, OPRO, TextGrad, Self-Refine**: even more compressed
  (~100–10K tokens/step), often single-candidate.
- Meta-Harness regime: up to ~10M tokens/eval, **3 orders of magnitude
  more** diagnostic context than any prior work in Table 1.
- DSPy / LangChain / LMQL: orchestration *frameworks* — they help
  humans specify multi-stage programs; Meta-Harness searches over the
  *implementation* of such programs.
- Memory-evolution lines (MemEvolve [56], Hu et al. ADAS [19], AFlow [57])
  — search over agent designs / memory; Meta-Harness's outer loop is
  deliberately more minimal (no fixed scaffold, no archive structure, no
  persistent memory mechanism — just filesystem + proposer).

## Relevance to repo3

| Their finding | Our angle |
|---|---|
| Env bootstrap = the discovered TerminalBench-2 win, +1.7 pp on Opus | Validates H4 (file-tree-in-context). The proposer chose this *after* 6 regressions on prompt/control-flow edits. Confirms that "purely additive context before the agent loop" is the dominant safe move. |
| Iter-1–7 trajectory: prompt-template edits and completion-flow changes regressed | Cautionary: our primer-variation experiments and orchestrator-variant work (Task 2, regressed) sit in the high-risk class; env-bootstrap-class interventions are the safer bet. |
| Skill text > iteration count for search quality | If we ever automate the harness search loop (extension of Task 3 self-evolving), invest in the skill text first. |
| Filesystem >> compressed feedback (50.0 median vs 41.3 best for scores-only) | Our self-evolving setup must preserve raw trajectories, not summaries. Memory cheatsheets (LN-002 MemP) lose signal compared to raw trace access. |
| Discovered harness generalizes across 5 held-out models (math) | Strengthens the cross-model transfer claim in our RQ3. If a discovered adaptation is "purely additive context", model-transfer is the expected case, not a surprise. |
| Per-task: env-bootstrap helps 7/89, biggest on tasks needing domain-specific tooling | Our 36-task GEOS set is *all* domain-specific tooling. The "bootstrap an environment snapshot" pattern is essentially what our pre-computed `/geos_lib` filetree tries to do. |
| Population init from existing baselines (zero/few-shot, ACE, MCE / Terminus-KIRA) | Our overnight Task 3 already did this — initialized from C0/C2/C6/C7. Their result that "proposer often starts from a strong prior harness, but emergent rather than hard-coded" matches our v3-from-C7 trajectory. |
| Run evals **outside** the proposer | Currently our self-evolving Task 3 does this — eval is in `experiment_runner`, agent only edits config. Confirms architectural choice. |
| Lightweight interface validation before expensive eval | Our XML-validation gate already serves this role. |

### Things that *don't* directly transfer

- We don't yet have anything like the 535K decontaminated retrieval corpus,
  and our 36-task eval is a benchmark, not the search-set/test-set split
  Meta-Harness uses. Their benchmark-as-discovery argument (§4.3) is
  *exactly* the position we're in for the GEOS task; their leakage
  audit (manual + regex for task-specific strings) is an audit pattern
  we should adopt before any self-evolving claim is published.
- They run ~60 evals × hours of wall-clock. Our budget is much smaller
  (Task 3 self-evolving did ~3 cycles in the overnight run). We're not
  in a position to claim "harness search" as the contribution; we're
  closer to demonstrating *one round* of agent-self-modification.

## Open questions / threats

1. **Reproducibility caveat for ForgeCode** is mentioned explicitly —
   public code couldn't reproduce the leaderboard score. Suggests harness
   leaderboards in this regime are fragile to undisclosed components. Same
   risk applies to anything we publish.
2. The text-classification gain (+7.7 vs ACE) compares the *best
   discovered harness picked by search-set perf* against a hand-designed
   baseline. The Pareto-frontier table (Table 9) shows the discovered
   variants form a smooth frontier; the +7.7 number is the highest-acc
   point. Selection on search-set is principled (no test peeking) but
   readers should look at the OOD numbers (+2.9 over next-best) for the
   honest generalization claim.
3. Per-task TerminalBench-2 gains: only **7 of 89 tasks** improve.
   Headline +1.7 pp comes from a thin slice. Need to verify the
   discovered improvement isn't overfit to the same 89-task set used as
   both search and eval. Authors do regex audit + manual inspection
   for task-name leakage; nothing stronger.
4. They never run a no-skill ablation, so the marginal contribution of
   the skill text vs the bare proposer is unmeasured (Appendix D claims
   skill-text matters most "in our experience" — qualitative).

## Citations to follow up

- [58] Zhang et al. ACE — Agentic Context Engineering (their main
  text-class baseline; reflective memory curation).
- [51] Ye et al. MCE — Meta Context Engineering via agentic skill
  evolution (closest method-wise; library of natural-language skills).
- [55] Recursive language models — adaptive external context access.
- [56] MemEvolve — meta-evolution of agent memory systems
  (related to our self-evolving subagent work).
- [49] Continual-learning agentic memory designs.
- [19] Hu et al. ADAS — automated design of agentic systems.
- [25] Lee et al. Feedback Descent — pairwise text optimization.
- [54] Learning to discover at test time (TTT-Discover).
- [24] Terminus-KIRA — the actual TerminalBench-2 baseline
  (https://github.com/krafton-ai/kira).

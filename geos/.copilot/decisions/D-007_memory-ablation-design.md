---
id: D-007
title: "Memory ablation: 5 frozen variants stacked on RAG+SR (SUPERSEDED by D-008)"
date: 2026-04-22
dag_nodes: [I06, I10, E23, E24]
links:
  derived_from: [XN-013, XN-014, LN-002]
  superseded_by: [D-008]
  related_to: [D-005, I05, I06, I10]
status: superseded
---

> **SUPERSEDED 2026-04-22.** RN-003 adversarial review identified 4 P1
> blockers (test-task GT filename leakage in memory_index.json, null-exposure
> M0 control, primer-size confound, n=2 A3 baseline). All fixes landed in
> D-008 which is the operative design. D-007 retained for decision history.

# D-007 — Memory ablation sprint

## Context

PAC-1 (D-005) established RAG+SR (A3) is the hero: +0.155 fa0 σ=0.017
over baseline. Memory (A5) added +0.110 on mean but did NOT stack
additively. Memory tool (`memory_mcp.py` lexical MCP) was **never called**
in any A4'/A5 run — the gain was pure tool-list-shape effect.

Advisor's post-doc flagged: (i) why is the task hard for vanilla CC, (ii)
why is our memory implementation using lexical overlap in 2026, (iii) is
G-Memory overkill for single-agent. User directed:
- Re-read actual papers (DC, ACE, ReasoningBank, MemEvolve — completed LN-002)
- Build proper memory systems, not the "hack job" lexical index
- Use OpenRouter for embeddings (OpenAI API unavailable)
- Target an ablation table so we can pick the winner and claim it as ours
- Keep memory FROZEN at test time (parallelism constraint)

XN-014 failure analysis found 4 modes: F1 schema hallucination (RAG
addresses), F2 wrong-version drift (RAG introduces), F3 missing
components, F4 spec under-specification. M0 memory addressed none of
these because (a) it was never called and (b) content was low-abstraction
task-specific dumps.

## Design principles

1. **All memory variants are FROZEN.** Built offline from training
   trajectories; no test-time updates. Preserves parallel eval.
2. **Content must be high-abstraction.** XN-009 anchoring lesson: retrieving
   "past task X's reference XMLs" biases toward wrong-physics matches.
   Distiller prompts enforce cross-task rules + explicit anti-patterns,
   no raw XML.
3. **Grounded distillation is a method contribution.** TreeSim's per-section
   and per-element feedback gives localized failure signal. Each grounded
   variant uses `trajectory_grounder.py` output alongside the raw trajectory.
4. **Train/test hygiene preserved.** Failure trajectories for anti-pattern
   distillation come from rerunning vanilla CC on the 18 TRAINING tasks
   (not test-set A1 failures).
5. **Two loci tested** with matched content:
   - **External injection**: distilled content prepended to system primer at run start
   - **In-run tool**: MCP server the agent can query mid-trajectory

## Matrix — 5 new conditions

All stacked on RAG+SR (same as A5 agent config minus memory impl).

| ID | Name | Content | Retrieval | Locus | Grounded | Distillation artifact |
|---|---|---|---|---|---|---|
| M0 | current lexical (control) | raw task summaries + refs | lexical | tool | n/a | `plugin/memory_index.json` |
| M1-u | DC-Cu primer (ungrounded) | LLM-self-judged cheatsheet | none (inject all) | external | ✗ | `misc/memory_artifacts/M1-u/cheatsheet.md` |
| M1-g | DC-Cu primer (grounded) | cheatsheet + TreeSim feedback | none | external | ✓ | `misc/memory_artifacts/M1-g/cheatsheet.md` |
| M3 | RB items, in-run tool | abstract `{title, description, content}` items | embedding top-k | tool (MCP) | ✓ | `misc/memory_artifacts/M3/items.json` |
| M4-u | RB items, external inject (ungrounded) | self-judged items | embedding top-k at run start | external | ✗ | `misc/memory_artifacts/M4-u/items.json` |
| M4-g | RB items, external inject (grounded) | items + TreeSim feedback | embedding top-k at run start | external | ✓ | `misc/memory_artifacts/M4-g/items.json` |

Total: 5 new × 3 seeds = 15 runs × ~$3.50 = ~$55 eval. Distillation ~$3
(4 passes × minimax-m2.7). Vanilla-CC training-set generation ~$8. Total
~$70.

M3 and M4-g share the SAME items.json artifact — only served differently
(MCP tool vs primer injection).

## What each comparison tests

- M0 → M1-g: does any form of abstract external memory help over the
  current lexical-tool-shape-only effect?
- M1-u → M1-g: does TreeSim grounding matter? **Attribution claim for
  the paper method contribution.**
- M4-u → M4-g: grounding attribution with matched content + retrieval.
- M1-g → M4-g: does selective retrieval (top-k via embedding) help over
  inject-all when content is abstract?
- M3 → M4-g: does external injection beat in-run tool-locus when content
  is fixed? (Addresses XN-009 "agent doesn't call the tool" + user's
  external-vs-tool design axis.)

## Abstraction guardrails in distiller prompt

Distiller instructions emphasize:
1. NO raw XML content. Element/attribute names only.
2. Prefer conditional rules over case examples. "When task mentions X,
   hierarchy is Y" over "Task Z used these files".
3. Explicit anti-patterns from failed trajectories: "Do NOT use X because
   it is hallucinated vocabulary; use Y instead."
4. Physics-family tags (`solver_family`: hydrofracture | triaxial |
   poromechanics | thermal | contact) for retrieval filtering.
5. `abstraction_level` field per item: high=cross-task rule, med=family-
   wide rule, low=task-specific.

## Train/test hygiene

- Success-side items: distilled from 18 training trajectories in
  `repo3_eval_run4` (already successful; final_treesim available).
- Failure-side items (anti-patterns): distilled from NEW vanilla-CC runs
  on the 18 training tasks (`vanilla_cc_train_s1` — to launch). This
  preserves strict train/test hygiene — no test-set data in memory.

## Success criteria / decision gate

Claim "memory helps on top of RAG+SR" requires:
- Best memory variant mean fa0 TreeSim ≥ A3 (0.653) + 0.05 at n=3 seeds
- AND std ≤ 0.05 (at least as reliable as A3's 0.017; much better than
  A5's 0.252)

Claim "grounded distillation is a method contribution" requires:
- (M1-g - M1-u) ≥ +0.04 OR (M4-g - M4-u) ≥ +0.04 on mean fa0
- AND the grounded version std ≤ ungrounded std

If all 5 memory variants fail the first gate, the honest story is
"external memory of any form does not stack with RAG+SR on this task;
RAG+SR is sufficient." That is paper-worthy as a negative result; we
do not silently descope.

## Paper table plan (agreed with user)

- Table 1: harness comparison (our harness vs vanilla CC vs competitors — TBD)
- Table 2: component ablation (RAG × SR × Memory, subset of 2×2×2)
- Table 3: **memory-variant ablation** (this sprint: M0 vs M1-u/g vs M3 vs M4-u/g)
- Table 4: no-agent baseline (base model direct / ICL)
- Table 5: difficulty (easy / hard-mode, tentative)

## Cost / timeline budget

Target 2 days total:
- Day 1: `trajectory_grounder.py` + `distiller.py` + vanilla-CC training
  runs + distillations + M3/M4 infra (embedding MCP + primer injection)
- Day 2: smoketests + 3-seed multi-condition eval + analysis + XN-015
  results note

LLM distillation uses minimax-m2.7 via OpenRouter. Cost: ~$0.60/pass ×
4 passes = $2.40. Escalation path: if minimax-distilled memory looks
plausibly broken (e.g., still produces raw-XML content despite
guardrails), rerun on gemini-2.5-flash (~$0.15/pass) or sonnet-4.6
(~$4/pass). Budget ceiling $50 for distillation before pausing.

## Open risks

1. **Distiller LLM drifts to low abstraction.** Guardrail: examine first
   artifact against a checklist before running all 4 passes. If failing,
   prompt-iterate with hand-written exemplars.
2. **Embedding retrieval surfaces wrong physics (M3 anchoring).** M3 is
   expected to underperform M4 per XN-009 — that's the design.
3. **Grounded feedback tokens blow up context.** TreeSim per-element
   detail can be large; grounder caps at top-20 unmatched/hallucinated
   per task and summarizes the rest.
4. **Smoketest per condition.** Required before full 3-seed run. Budget
   one smoketest per condition before committing the seeds.

## References

- XN-013 (PAC-1 Phase A design), XN-014 (failure analysis)
- LN-002 (memory survey, verified)
- D-005 (PAC-1 ablation campaign)
- Papers: `misc/refs/dynamic-cheatsheet.md`, `misc/refs/ace.md`,
  `misc/refs/reasoningbank.md`, `misc/refs/memevolve.txt`
- Repos: `misc/refs/{dynamic-cheatsheet, ace, reasoning-bank, MemEvolve}/`

---
id: D-008
title: "Memory ablation V2: hygiene-fixed design after RN-003 adversarial review"
date: 2026-04-22
dag_nodes: [I06, I10, E23, E24]
links:
  derived_from: [D-007, RN-003]
  supersedes: [D-007]
  related_to: [D-005, XN-013, XN-014, LN-002]
---

# D-008 — Memory ablation design V2 (post-adversarial review)

## Why V2

D-007 was reviewed in RN-003 at the implementation gate. Four P1 blockers:

1. **Test-task GT filename leakage** through `memory_index.json`. 13 of 17
   test tasks had blocked GT basenames surfaceable via the memory channel.
2. **M0-as-control is null** — A5 had 0 `memory_lookup` calls, so M0
   delivered zero bytes of memory content. Comparing M1/M4 (always-fire
   primer) against M0 confounds "any content at all" with "distilled
   content specifically."
3. **Primer-size / token-count confound** between grounded and ungrounded
   variants — uncontrolled; any M1-g ≥ M1-u lift could be pure size.
4. **A3 baseline n=2** makes the 3-seed pass/fail gate asymmetric and
   ~18% powered at the target effect size.

Plus P2/P3 findings on tool-list-shape, vanilla-CC-train hygiene, M3
silent degrade, and a meta-finding on self-distillation coupling (distiller
== evaluator model). All accepted as fixes in RN-003's Responses table.

**D-008 replaces D-007 as the operative design.** D-007 stays in the
decision trail for history.

## Design changes from D-007

### 1. Hygiene — non-negotiable gate

A new script `scripts/memory/hygiene_audit.py` is the single gate every
memory artifact must pass before being used in an eval run.

Checks:
- Regex `\b[a-z0-9_]+\.xml\b` on every artifact file — fail on any match.
- Basename blocklist: load the union of `blocked_gt_xml_filenames` across
  all 17 test tasks (from existing `eval_metadata.json` files). Case-
  insensitive substring match on every artifact field. Fail on match.
- Applied PRE-distillation to distiller inputs (trajectory text,
  `productive_rag_queries`, `reference_xmls`) AND POST-distillation to
  output artifacts.
- Audit result written to `misc/memory_artifacts/<variant>/hygiene_audit.json`.

`memory_index.json` is rebuilt with `reference_xmls` and
`productive_rag_queries` stripped. Only `task_id`, `solver_family`,
`section_strengths`, and an abstracted `instructions_excerpt` (sanitized,
no file basenames) remain. The new index replaces the old one at
`plugin/memory_index.json` — the old one is archived to
`plugin/memory_index_v1_LEAKY.json.bak` with a README warning.

### 2. Matrix — conditions revised

All stacked on RAG+SR. All distilled offline with **gemini-2.5-flash** via
OpenRouter (NOT minimax, to break self-distillation coupling). All frozen
at test time.

| ID | Name | Content | Retrieval | Locus | Grounded | Why |
|---|---|---|---|---|---|---|
| A3+ | RAG+SR baseline (n=3) | — | — | — | — | Primary comparator. Launch A3 seed 3 to reach n=3. |
| M-placebo | Placebo primer | Generic GEOS schema/glossary text, not trajectory-derived, token-matched to M1 artifacts | none | external | ✗ | Placebo control — if M1/M4 − M-placebo ≈ 0, the lift is primer-shape |
| M1-u | DC-Cu primer (ungrounded) | Self-judged cheatsheet from 18 train trajectories | none | external | ✗ | Claim B attribution pair — ungrounded |
| M1-g | DC-Cu primer (grounded) | Cheatsheet + TreeSim feedback | none | external | ✓ | Claim B attribution pair — grounded |
| M4-u | RB items, external inject (ungrounded) | Self-judged items | embedding top-k at run start | external | ✗ | Attribution pair with M4-g |
| M4-g | RB items, external inject (grounded) | Items + TreeSim feedback | embedding top-k at run start | external | ✓ | Hero run |
| M3-g | RB items via MCP tool (limitation-flagged) | same as M4-g | embedding top-k in-run | tool (MCP) | ✓ | Locus comparison (weakened — tool-list confound explicitly acknowledged) |

Total: 7 new conditions × 3 seeds = 21 runs × ~$3.50 = ~$75 eval.
Distillation ~$0.60 (gemini-flash). Vanilla-CC-train ~$8. Total ~$85.

M0 (current lexical MCP) is **demoted** — no longer a control, not
included in the new matrix. Referenced in the background for context.

M-placebo's content must be:
- Token-matched to M1 artifacts' token count (± 10%)
- Derived from public GEOS docs (GEOS_PRIMER.md style), NOT from any
  trajectory or task-specific source
- Contain no task names, no past-task XML filenames, no `solver_family`
  tags
- Written once, used for all 3 seeds

### 3. Statistical analysis — paired per-task

Replace mean±std pass/fail with paired-per-task analysis:

- For each condition vs A3, compute per-task paired delta (same 17 tasks).
- Report: mean_delta, median_delta, Wilcoxon signed-rank p-value, #wins /
  #losses / #ties.
- Decision gate for **Claim A (outcome)**:
  - mean delta vs A3 ≥ +0.05
  - Wilcoxon p ≤ 0.10
  - std ≤ max(A3 std, 0.08)
- Decision gate for **Claim B (attribution)**:
  - (grounded − ungrounded) mean delta ≥ +0.04 OR Wilcoxon p ≤ 0.10
  - grounded std ≤ ungrounded std
  - token count difference ≤ 10% between grounded and ungrounded artifacts

### 4. Token-budget parity (preregistered)

Distiller enforces hard token budgets:
- DC-Cu primer artifact: 1500 tokens ± 10% (both M1-u and M1-g)
- RB items JSON: 5 items × ~200 tokens each = 1000 tokens ± 10% (M4-u and M4-g share this)
- Tokenizer: `tiktoken` with `cl100k_base` encoder for model-agnostic count
- If the grounded artifact exceeds budget, it is re-distilled with a stricter prompt until within budget
- Token counts logged to each artifact's `hygiene_audit.json`

Preregistered: **Claim B is rejected if `|tokens(M1-g) − tokens(M1-u)| / tokens(M1-u) > 0.10`**, regardless of fa0 results.

### 5. Vanilla-CC-on-training-tasks run

For failure-trajectory harvesting:
- Agent: `claude_code_no_plugin` (vanilla CC)
- Tasks: 18 training tasks from `misc/memory_split.json`
- Extended blocklist: run with `--extend-blocklist-with-test` flag (new
  `run_experiment.py` flag) that unions the standard per-task blocklist
  with the union of test-task blocked_gt_xml_filenames
- Seeds: 1 (we only need failure instances, not variance)
- Output: `data/eval/claude_code_no_plugin/vanilla_cc_train_s1/`
- Audit: after runs complete, grep every `Read` tool-call input path in
  `events.jsonl` against the test-task blocklist — fail the harvest if
  any leak detected

### 6. Distillation model

**Primary:** gemini-2.5-flash via OpenRouter.
- Breaks self-distillation coupling (eval is minimax-m2.7)
- Cheaper: ~$0.15/pass × 4 passes = $0.60
- If gemini-flash produces broken artifacts (fails abstraction guardrail
  or hygiene audit), escalate to sonnet-4.6 (~$4/pass)

**Minimax comparison run (optional):** after the gemini-distilled matrix,
if headline result is positive, re-distill with minimax for one condition
to confirm the result isn't gemini-distillation-specific. Budget: $0.60.

### 7. M3 embedding MCP — hard-error behavior

`plugin/scripts/memory_mcp_embed.py` (new file):
- Startup: reads `OPENROUTER_API_KEY`. If missing, `sys.exit(1)` with
  stderr message. No fallback to OpenAI, no fallback to lexical.
- Preflight: on `app.run()` startup, makes one test embedding call. If
  non-200, stderr error + `sys.exit(1)`.
- Per-query: if embedding call fails, returns a tool error the agent
  sees (not an empty-result silent degrade). Failed calls logged to
  stderr.
- No TreeSim post-multiplication in scoring — pure cosine.

### 8. Tool-list-shape confound — acknowledged limitation

Claim C (locus) is explicitly weakened in the paper:
> "We compare external-injection (M4-g) against tool-locus (M3-g) with
> matched distilled content. The conditions differ in (a) content
> delivery locus AND (b) presence of a memory MCP tool in the tool list.
> Prior work (XN-010) showed tool-list-shape alone can move fa0 by
> +0.05–0.10. We report the comparison but do not attribute a clean
> locus effect."

Claim A (outcome) and Claim B (attribution) are NOT affected — both pairs
(M1-u vs M1-g, M4-u vs M4-g) have matched tool lists within the pair.

## Sprint sequence (ordered; items in the same step can be parallel)

1. **Prep**
   - Write `scripts/memory/hygiene_audit.py`
   - Rebuild `memory_index.json` (strip basenames) and archive old as
     `.bak`
   - Launch A3 seed 3 in background (~25 min)
   - Launch vanilla-CC-train-s1 in background (~60 min)
2. **Grounder + distiller**
   - Write `scripts/memory/trajectory_grounder.py`
   - Write `scripts/memory/distiller.py` (gemini-2.5-flash, token budget)
   - Test distiller end-to-end on 2 training tasks to verify abstraction guardrail
3. **Artifact build**
   - Distill M1-u, M1-g, M4-u, M4-g (in parallel)
   - Run hygiene_audit on each — FAIL the pipeline if any audit fails
   - Manually inspect first artifact for abstraction quality
4. **Infra**
   - Write `plugin/scripts/memory_mcp_embed.py` (M3-g MCP, hard-error)
   - Extend `run_experiment.py` with 7 new agent keys (memory variants)
   - Write `M-placebo` primer file (token-matched generic GEOS content)
   - Build embedding index for M3-g items
5. **Smoketest**
   - 1 seed × 1 task per new condition; verify no crashes, hygiene
     respected in the actual run
6. **Full matrix**
   - Launch 7 new conditions × 3 seeds = 21 runs
   - Watch for hygiene violations in live events.jsonl streams
7. **Analysis**
   - Score all runs; compute paired-per-task deltas vs A3
   - Write `docs/XN-015_memory-ablation-results.md` with Claim A/B/C
     dispositions and limitations
8. **Adversarial review round 2**
   - Before declaring results validated: dispatch /adversarial-review
     with focus text on the results + hygiene audit artifacts

## Open risks after V2

1. **Distillation quality with gemini-flash.** First artifact inspected
   manually; if abstraction is low, prompt-iterate or escalate to sonnet.
2. **Token budget too tight for grounded variant.** Grounded feedback
   can balloon; if budget forces dropping content, the "grounding" signal
   may not fit. Fall-back: raise budget to 2000 tokens and re-match
   ungrounded.
3. **M-placebo construction:** generic GEOS primer text exists but the
   token-match may require trimming/padding. Artifact reviewed before
   launch.
4. **Sequential eval time.** 21 runs × ~30 min each = 10.5h if serial;
   with 2 parallel conditions on OpenRouter, ~5-6h. Acceptable inside
   12h sleep window.

## References

- RN-003 adversarial review (all findings + responses)
- D-007 (superseded)
- D-005 (PAC-1 baseline campaign)
- XN-014 (failure analysis feeding memory content design)
- LN-002 (memory paper survey, verified)

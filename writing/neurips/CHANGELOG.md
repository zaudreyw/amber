# Paper changelog — `neurips_2026.tex`

Tracks substantive edits to the NeurIPS submission draft. Append-only; newest entry at top. Each entry: date, who, what changed, why.

---

## 2026-05-04 — abstract tightening: cut implementation detail to body

**Author**: research-copilot, same session.

**Goal**: reduce abstract from ~330 words to ~280 by moving implementation detail to the body. The abstract should carry headline framing and headline numbers; the *what* of the consultation tool, the *how* of the human-baseline-vs-agent comparison, and the prompt-framing invariance result all belong in the body.

### Edits

- **Three-axis sentences compressed.** Reliability / Quality / Efficiency each became a single short sentence. The "SIGA reduces across-seed variability... by preventing the agent from producing unparseable or empty decks" phrasing was tightened to "${\sim}40{\times}$ lower across-seed variance, by preventing unparseable or empty decks on a hard tail of compound multi-physics tasks." Saves ~25 words across the three axes.
- **Cut the `consult_supervisor` implementation detail.** "Backed by a separate LLM instance with access to the original full brief, simulating a domain expert" → "an explicit human-consultation tool". The handler-LLM detail belongs in §6.7 / App.~G; the abstract just needs the *finding* (3% rate, on-disk library as substitute). Saves ~22 words.
- **Cut the prompt-framing invariance hedge.** "Regardless of prompt framing" was load-bearing in §6.7 (the V0/V1 invariance is the diagnostic for "framing isn't the binding constraint"), but in the abstract the headline result is the rate itself; the framing-robustness detail can sit in the body. Saves ~5 words.
- **Cut the human-baseline file-count and browser-history detail.** "Complete only the first of two required files" and "browser histories show dozens of documentation visits" were doing two different jobs (time + quality contrast, file-usage strategy contrast). The strategy contrast is in §6.8; the abstract keeps "more than $8\times$ as long ... at lower quality." Saves ~30 words.
- **Tightened "we additionally contribute a behavioural finding"** to "we further characterise coding-agent behaviour" — same role in the abstract structure (additional contribution, not derivative measurement) but two words shorter.
- **Cut "SIGA components and a self-evolved monolithic variant"** — the reader does not need to know in the abstract that we evaluated 11+ cells. Just say "Resolution-IV factorial" and let the body explain. Saves ~9 words.
- **Cut "as a case study"** from the GEOS instantiation sentence — already implicit. Saves ~5 words.
- **Replaced "manually-designed configuration" with "hand-designed cell"** — terser and matches the body's "cell" language.
- **Replaced "SIGA-equipped agent" with "SIGA agent"** — same meaning, fewer words.
- **Replaced "(XML decks, input scripts, namelists)" parenthetical with em-dashed apposition** — same content, slightly tighter rhythm. (Optional cosmetic change; can revert.)

### What stayed (load-bearing)

- DSL framing in the opening (Brian's previous question made clear this framing actually clarifies the bottleneck).
- "Bespoke package of skills, tools, and workflow-altering control flow" SIGA description (user's hand-edit).
- Three explicit benefit axes with bolded labels (positive-results-forward structure).
- Self-evolved variant as automatic-discovery teaser.
- Human baseline 8× contrast as visceral hook.
- Autonomy-as-contribution framing.
- Closing recommendations.

### Build status

`pdflatex` succeeds. Page count drops to **27** (was 28); page 1 now shows ~7 lines of intro after the abstract (was ~3). Total bytes: 370,695.

---

## 2026-05-04 — abstract: surface the self-evolved variant as automatic-discovery teaser

**Author**: research-copilot, same session.

**Goal**: respond to user's instinct that self-evolving / self-creating agent harnesses are methodologically more interesting than manual factorial design and worth surfacing in the abstract — without overclaiming.

### Changes (abstract only)

- Expanded the **Efficiency** bullet to make explicit that the self-evolved monolithic variant is *not* hand-designed: "adapter contents iteratively rewritten by an offline pipeline rather than designed by hand." Closing clause: "a preliminary signal that automatic SIGA discovery is a tractable follow-up to the manual design space we explore here." This positions the SE result as both an efficiency point and a methodological teaser pointing at Paper 2.
- **Honest framing kept**: the variant is described as "iteratively rewritten by an offline pipeline" — not as full self-evolution, not as Meta-Harness-style online search, not as a method we propose. The phrasing "preliminary signal" / "tractable follow-up" hedges against reviewers who would otherwise ask "where's the comparison to automatic harness search?"
- Did not promote SE to a fourth axis (Reliability / Quality / Efficiency stays clean three-axis); did not claim "self-evolving adapter" as a method name; did not introduce Paper 2 explicitly. The teaser is one clause; reviewers can read further if interested.

### Build status

`pdflatex` succeeds, 28 pages, 371,682 bytes. Intro starts on page 1.

---

## 2026-05-04 — abstract reordering: lead with positive results

**Author**: research-copilot, same session.

**Goal**: respond to user feedback that the bottom half of the abstract had bad flow and led with negative framing ("not improving over noise"). Use-inspired submissions in particular benefit from a positive-results-forward abstract.

### Changes (abstract only)

- **Replaced the "no improvement on val / cluster within seed noise" lead** with a three-axis positive frame: **Reliability** (~40× variance reduction), **Quality** (+7 pp on the hard tail of held-out-eval, vanilla → best SIGA), **Efficiency** (SE matches the best factorial cell at ~16% fewer tool calls than vanilla CC). The val-vs-held-out-eval hedge is retained in the body of the paper but is no longer the abstract's headline.
- **Reordered the bottom half** to: factorial benefits → autonomy contribution → human baseline → recommendations. The autonomy probe is now framed as "we additionally contribute a behavioural finding about how a coding-agent harness handles deliberately under-specified briefs" rather than as a passive companion study; the human baseline lands as the punchy concrete contrast right before the close.
- **Numbers cited** (verified against `docs/2026-05-02_efficiency-table.md` and `tab:main-results`):
  - 40× variance reduction: held-out-eval Vanilla σ=0.081 → S+X best σ=0.002 (40× ≈ ratio).
  - 7 pp quality lift on hard tail: held-out-eval Vanilla 0.720 → SE 0.789 (Δ = +0.069 ≈ 7 pp).
  - 16% tool-call reduction: F0 (vanilla) 82 tools/task → SE 69 tools/task (Δ = -13, ≈ -16%).
  - 8× human-baseline wall-clock: agent ~5 min vs P1 48.2 min, P2 46.7 min on `buckleyLeverettProblem`.
  - 3% consultation rate: 1/32 in V0, 1/32 in V1.

### Build status

`pdflatex` succeeds, 28 pages, 371,451 bytes. Intro starts on page 1.

### Open items

- Body of the paper still has paragraphs phrased as "cells cluster within seed noise on val" — that's accurate and worth keeping in §6.1, but consider whether the *headline* paragraph of §6 should mirror the abstract's three-axis frame for consistency.
- Consider adding a one-sentence "regime-dependent" hedge somewhere in §6 to acknowledge that the abstract's positive numbers are held-out-eval; on val the same components are within noise. (Currently this is in §6.1 paragraph "On val, adapter wins are within seed noise" — fine, but a reader skimming results-only might miss the contrast.)

---

## 2026-05-04 — SIGA naming + abstract clarity pass (pre-submission)

**Author**: research-copilot, same session. Drives toward the abstract-submission deadline (a few hours out).

**Goal**: respond to (a) advisor's request to keep "Grounding" in the method name; (b) Brian's four pieces of feedback on the abstract (clarity of "design-space cells cluster within seed noise", what "catastrophic failure" and "compared to what" mean, what the consultation channel actually is, and what "failure categories that survive the vanilla→best transition" means); (c) the user's hand-revised abstract draft; (d) the new submission type ("Use-inspired"; main contribution is in framing/designing approaches for a real-world application).

### Changes

- **Method name renamed**: SIA → **SIGA** (Simulator-Interface Grounding Adapter). Hyphenated as "Simulator-Interface" so "Interface" parses as modifying "Simulator", not "Grounding". Title updated. All in-text mentions, contributions list, captions, and tables propagated. Rationale lives at `docs/2026-05-04_siga-vs-sia-naming.md` (three load-bearing arguments: "grounding" is established ML terminology that names exactly what we do; "Adapter" alone collides badly with parameter-efficient adapter literature like LoRA; the grounding framing aligns with the use-inspired submission type's framing/design contribution).
- **Abstract** rewritten as a single paragraph (~285 words). Specific clarity edits in response to Brian's feedback:
  - *Brian: "design-space cells cluster within seed noise" — what does this imply?* Now explicit: "no component combination improves over vanilla Claude Code by more than across-seed noise" (on the validation split, on tasks the bare harness already handles competently).
  - *Brian: "reduce standard deviation ~40× by preventing catastrophic failure" — compared to what? what is catastrophic failure?* Now reads "reduce across-seed variability by ${\sim}40\times$ relative to the vanilla baseline by preventing the agent from producing unparseable or empty decks on a hard tail of compound multi-physics tasks" — concrete on the comparison baseline (vanilla CC) and on the failure mode (unparseable / empty decks).
  - *Brian: "human consultation channel is exposed as a tool" — what is this?* Now describes the implementation: "We expose a `consult_supervisor` tool whose handler is a separate LLM instance with access to the original full brief, simulating a domain expert."
  - *Brian: "failure categories that survive the vanilla→best transition" — failure is what we want?* Reworded: "failure modes that remain unresolved even under our best configuration." Reads as a normal English sentence; no inversion.
  - Kept the user's hand-edited bones: the DSL framing opening, "bespoke package of skills, tools, and workflow-altering control flow", "more than $8\times$ as long" human-baseline phrasing, "case study" framing.
  - Trimmed: the "the only main effect that clears noise on the validation split is generic retrieval, and it is *negative*" sentence (kept in intro and Results; removed from abstract for length and to avoid double-loading the "no improvement on val" point).

### Build status

`pdflatex` succeeds, 28 pages, 371,199 bytes. Abstract no longer fills page 1; introduction begins on page 1.

### Open items

- The full method section still uses the older "four-component recipe" language. The abstract now describes SIGA more openly as "a bespoke package of skills, tools, and workflow-altering control flow that grounds the agent's outputs in the simulator's documentation, schema, and example library." For the full-paper submission a few days out, consider unifying: either (a) lean into the four-component recipe consistently, or (b) lean into the broader "skills, tools, control flow" framing and present the four components as one possible structuring of the recipe.
- The acronym SIGA is used a few times in figures and tables that may need their captions updated for camera-ready (some still say "SIA" as a leftover token in non-search-replaceable contexts? — verified clean by `grep "SIA\b" neurips_2026.tex` returning empty).
- Title still says "Adapters" (plural). For a single-system case study some reviewers may prefer "Adapter" (singular). Defer the call to the user.

---

## 2026-05-04 — split-rename + Table 1 compaction + abstract compression

**Author**: research-copilot, same session.

**Goal**: respond to three pieces of feedback from the user.

### Changes

- **Split renames**:
  - `test-17` → `val` (validation / cell-selection split). Internal name retired.
  - `Held-out-10` / `held-out-10` → `held-out-eval` (held-out evaluation split, never tuned against). Internal name retired.
  - Sample sizes are not in the split names anymore. Descriptive text in §5.1 still mentions "17 tasks" / "10 tasks" once when introducing each split, but they are no longer carried as suffixes throughout.
  - All in-text references, table captions, table column headers, paragraph headings, subsection headings, and appendix references propagated.
- **Table 1 layout**: collapsed the four `score` / `$\sigma$` columns into two `mean ± std` columns, dropping the table from 7 columns to 5. The TreeSim score and its standard deviation now appear as `0.910 ± 0.024` (etc.) within a single cell. Caption updated to explain the `±` convention. The table no longer extends past the right margin (verified via `pdftotext -layout` --- all rows render within the printable width).
- **Abstract** rewritten as a single paragraph and compressed by ~40%: kept the DSL framing, the SIA recipe, the three findings (factorial reliability story, autonomy-companion 3% rate, human-baseline contrast), and the closing recommendations. Cut: the explicit "two harder regimes" lead-in, the bolded numbered-list structure, and several adjective-heavy clauses. The abstract now ends mid-page-1 and the introduction begins on page 1 (verified via `pdftotext -f 1 -l 1`); previously the abstract filled the entire first page.
- **Build**: `pdflatex` succeeds, 28 pages, 371,176 bytes.

### Numbers / files NOT changed

All tabular numbers, footnotes, figure references, and appendix content unchanged from the previous pass; this is a presentation-only edit.

---

## 2026-05-04 — workshop-alignment + human-baseline pass

**Author**: research-copilot (Matt's session, pre-advisor meeting)

**Goal**: re-align abstract / intro / background with (a) the advisor's ChatGPT framing (`misc/lianhui_gpt_convo.md`) — already locked into `docs/2026-05-02_neurips-paper-plan.md` as the SIA contract — and (b) the ICML AI4Science workshop call (`https://ai4sciencecommunity.github.io/icml26/call`), which favours empirical study of design choices in scientific-software contexts. The user wants to argue at the upcoming advisor meeting that this paper is better suited for the workshop than the main conference, so up-weight the autonomy companion and the human-baseline calibration; down-weight bench-size disclosures and metric jargon in the abstract.

### Changes

- **Title** (line 34): dropped "Grounding" per prior naming decision (`misc/lianhui_gpt_convo.md` → user pushback → SIA compromise locked in NeurIPS plan §1). New title: *"Simulator Interface Adapters for Scientific Simulation Setup: A Geophysics Case Study"*.
- **Abstract** (rewritten, ~one paragraph + three numbered findings): leads with the DSL framing of simulator interfaces; loose paraphrase of the dozens-of-simulations scale (no \todo cite to the expert correspondence — paraphrased rather than quoted); introduces SIA as the four-component recipe; explicitly flags the autonomy companion ("when the user specifies less") and the human-baseline contrast as headline regimes; promotes the autonomy result and human-baseline result to numbered findings alongside the design-space result. Removes literal "17-task / 10-task" set sizes, "test-17" / "Held-out-10" labels, and the "fa0" suffix on TreeSim. Keeps the 40× variance-reduction headline and the negative-RAG headline.
- **Intro** (rewritten, four paragraphs):
  - §1 ¶1: scientific agents → DSL framing of executable interfaces. Same gap claim about subsurface simulation.
  - §1 ¶2: drops the literal advisor-correspondence quote and \todo. Loose paraphrase: "a representative subsurface investigation can demand dozens of decks across geological realizations." Adds DSL-bottleneck framing and TreeSim 0.333 floor.
  - §1 ¶3: now explicitly *empirical study of design choices*; introduces SIA recipe in plain language; collapses the Vanilla-vs-best headline.
  - **New §1 ¶4 (Two regimes that test the agent's autonomy)**: explicitly promotes the spec-relaxation/human-channel companion AND the human baseline, both as autonomy probes. This is the workshop hook.
  - **Contributions list**: rewritten to lead with the benchmark, factorial, autonomy companion, human baseline, design recommendations. Negative-results paragraph kept.
  - The old "Headline" \paragraph (the 17-task / 10-task spread block) is removed; that material now lives in the Results section unchanged.
- **Background § 3** (line 96): retitled "GEOS as a domain-specific simulator language". One-paragraph rewrite frames XML decks as DSL programs — elements = simulator classes, attributes = constructor params, nesting = composition, sequencing = `Events` block. Cross-section constraints elaborated. Authoring-difficulty list refactored to map directly to the DSL framing.
- **Metric § 4.2**: dropped "fa0" from the metric name. Sub-section retitled "Metric: TreeSim". Failures-as-zero detail kept inline in the same paragraph but no longer carried as a metric suffix.
- **fa0 → TreeSim search-and-replace**: throughout main text + table captions + harness-less floor result. Appendix table caption for the harness-less per-task table: "fa0 mean (17)" → "TreeSim mean (17, failures-as-zero)". Old `app:bench` paragraph mention of `fa0`-sorted training-run scores rewritten to use TreeSim.
- **New § 6.8 — Human baseline subsection**: inserted between the Autonomy companion (§6.7) and the Analysis section (§7). Reports:
  - Two PhD-level volunteers (P1, P2) on `buckleyLeverettProblem`, 1-hour timeslot each.
  - Both ran out of time on file 1 of 2; file-level TreeSim 0.812 (P1, 48.2 min) and 0.781 (P2, 46.7 min); deck-level TreeSim 0.540 / 0.527 because file 2 was missing.
  - New `tab:human-baseline` four-row table with the agent's vanilla CC and SIA cells for comparison.
  - Browser-history paragraph: P1 made 29 visits (20 on GEOS Sphinx docs); P2 made 73 (54 on Sphinx). No LLM chatbots. Both visited the unblocked DBC sibling deck on GitHub.
  - Agent-side counterpart paragraph: ~14 unique files / ~7 Greps / ~5 Globs per vanilla CC run on the same task; plugin variants drop to ~4 unique files + ~2 retrieval calls.
  - Closing "what this contrast says" paragraph: humans navigate prose explanations, agent navigates executable examples — two different DSL-translation strategies for the same task.
- **New Appendix L — Human baseline protocol + browser breakdown**: protocol details, per-domain navigation breakdown (`tab:human-browser`), top GEOS pages visited, agent-side counterpart, caveats.

### Numbers added / changed

| Item | Old | New | Source |
|---|---|---|---|
| Headline metric name | TreeSim-fa0 | TreeSim (failures-as-zero noted inline) | author preference |
| Title | "...via Simulator-Interface Grounding..." | "Simulator Interface Adapters for..." | NeurIPS plan §1, prior naming decision |
| Human baseline P1 file-level TreeSim | n/a | 0.812 | `scripts/score_human_baseline.py` |
| Human baseline P2 file-level TreeSim | n/a | 0.781 | `scripts/score_human_baseline.py` |
| Human baseline P1 deck-level TreeSim | n/a | 0.540 | `scripts/score_human_baseline.py` |
| Human baseline P2 deck-level TreeSim | n/a | 0.527 | `scripts/score_human_baseline.py` |
| P1 wall (min) | n/a | 48.2 | `data/human_baseline/human_baseline_notes.md` (Liam: 48:14) |
| P2 wall (min) | n/a | 46.7 | `data/human_baseline/human_baseline_notes.md` (Sahchit: 46:39) |
| P1 browser visits / GEOS-docs share | n/a | 29 / 20 | `scripts/analyze_human_browser_history.py` |
| P2 browser visits / GEOS-docs share | n/a | 73 / 54 | `scripts/analyze_human_browser_history.py` |
| Vanilla CC unique files / Greps / Globs on `buckleyLeverettProblem` | scattered | ${\approx}\,14$ / ${\approx}\,7$ / ${\approx}\,5$ (n=7 runs) | `scripts/analysis/out/file_access/file_access_per_task.csv` |

### Numbers NOT changed

- All Resolution-IV factorial cells (Table 1, Table 2, Table 3) — verified intact.
- Bottleneck-analysis category counts (Table 5) — verified intact.
- Cross-model + cross-harness panel (Table 6) — verified intact.
- Per-task Held-out-10 table (Table 4) — verified intact.
- Autonomy companion numbers (3% consultation rate, 64 trials, etc.) — verified intact.
- Harness-less floor TreeSim 0.333 — kept; only the metric suffix changed (fa0 → just TreeSim with failures-as-zero noted).

### Open items the author should still review

- The wall-clock estimate "${\approx}\,5$ minutes" for the agent on `buckleyLeverettProblem` is an extrapolation from `tab:efficiency` (per-task wall: vanilla 359 s on test-17 mean ≈ 6 min; the buckleyLeverett task is on the easier end so 5 min is plausible). Replace with the exact per-task wall time when convenient.
- The SIA cell row in `tab:human-baseline` says "${\geq}\,0.90$" for X+M on `buckleyLeverettProblem` — verify against per-task results for X+M before camera-ready (or at least flag as estimated upper bound).
- The new Background section frames XML decks as DSL programs; consider whether Method §4 should also pick up "interface vocabulary" wording more aggressively (currently it still talks about "MCP shapes" and "hook code paths" — fine, but a reviewer skimming for the DSL angle won't see it sustained).
- Consider whether the autonomy-companion subsection (§6.7) should also be promoted to its own section (§7) for the workshop framing. Currently it's a Results subsection; arguably it's Method+Results combined and would benefit from a dedicated heading. Left as-is in this pass.

### Build status

`pdflatex -interaction=nonstopmode -halt-on-error neurips_2026.tex` succeeds. Output: 28 pages, 371,666 bytes. The pre-existing pdfTeX warnings about `subsection.K.1` / `K.2` references (from `checklist.tex`) remain; not introduced by this pass.

---

*(future entries above this line)*

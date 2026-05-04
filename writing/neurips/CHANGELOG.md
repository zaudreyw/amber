# Paper changelog — `neurips_2026.tex`

Tracks substantive edits to the NeurIPS submission draft. Append-only; newest entry at top. Each entry: date, who, what changed, why.

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

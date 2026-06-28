# Jun 8 changelist — `jun8_v1.tex` (and arXiv copy `arxiv_v1.tex`)

Changes from `jun7_v0.tex` → `jun8_v1.tex`, plus creation of the arXiv preprint build `arxiv_v1.tex`.

`jun8_v1.tex` compiles clean (`pdflatex` + `bibtex`, exit 0, 0 undefined refs).

---

## Edits to `jun8_v1.tex`

### 1. Author block — de-anonymized
- **Before:** `Anonymous Authors`.
- **After:** Matthew Ho, Brian Liu, Jixuan Chen, Audrey Wang, Lianhui Qin (all UC San Diego), laid out with `\And`.
- Note: the NeurIPS template is still loaded without `[preprint]`, so in the submission build these names remain hidden behind the anonymous block; they render in the arXiv build (see §arXiv below).

### 2. Abstract (active/second paragraph) — concrete numbers + tighter claims
Rewritten to lead with headline numbers instead of qualitative phrasing.
- "We primarily **study** GEOS…" → "We primarily **evaluate SIGA on** GEOS…".
- Human-baseline sentence now states the numbers inline: "SIGA produces a complete GEOS deck in about five minutes with TreeSim above 0.90, matching the quality of an extended-budget human expert who required about three hours, a roughly ~36× wall-clock speedup."
- Held-out sentence now gives the TreeSim deltas: "grounding raises TreeSim from 0.720 to 0.789, a roughly 10% relative gain over the bare agent, and can reduce the [across-seed] standard deviation by 16×."
- Self-evolution sentence: "We further show that a self-evolution mechanism (in which the agent edits its own harness)…" → "Self-evolution further improves SIGA by rewriting adapter contents from prior trajectories, yielding the best held-out GEOS performance and outperforming the strongest hand-designed configuration."
- Transfer sentence: "Finally, we additionally explore generalization on two more simulators…" → "Transfers to OpenFOAM and LAMMPS show that the dominant mechanism shifts by interface: validation matters most when structural completeness is the bottleneck, while memory and retrieval matter most when domain correctness is the bottleneck."
- Closing sentence tightened to "lightweight, self-improvable grounding layers can turn general coding agents into practical operators of scientific software."

### 3. Related work — self-evolving-agents paragraph reworded
- Old sentence ("Our self-evolved variant … is fundamentally similar to these methods…") commented out and replaced with a tighter pair: "adopts this reflect-and-rewrite paradigm: the agent revises its own plugin, the adapter, based on prior trajectories. Our focus is different: we study whether such self-revision helps on a task whose bottleneck is domain knowledge and procedural guidance rather than general programming competence."
- Now explicitly connects to Buffer of Thoughts (`yang2024bot`) and forward-references the discussion (`\S\ref{sec:discussion}`).

### 4. NeurIPS checklist input — disabled
- `\newpage \input{checklist.tex}` → commented out (`% \input{checklist.tex}`).

---

## arXiv preprint build — `arxiv_v1.tex`

New file: a copy of `jun8_v1.tex` set up for arXiv. Full recipe in `ARXIV_INSTRUCTIONS.md`. Summary of what differs from `jun8_v1.tex`:

### A. Preprint style option
- `\usepackage{neurips_2026}` → `\usepackage[preprint]{neurips_2026}`.
- This single option reveals the author block, removes submission line numbers, un-hides `\ack`, and changes the page-1 notice from "Submitted to … NeurIPS … Do not distribute." to **"Preprint."** No manual hunting for "neurips" strings is needed.

### B. Authors
- Real author block (same five UCSD authors as `jun8_v1.tex`) placed in the now-visible `\author{}`.

### C. Acknowledgments
- Added a commented-out `\begin{ack} … \end{ack}` template (allowed in preprint mode) for later fill-in.

### D. Content fixes also applied here (SHOULD be back-ported to Overleaf / `jun8_v1.tex`)
These are genuine source bugs, not arXiv-specific:
1. **Broken cross-reference.** The "Hard-tail rescue" paragraph cited `App.~\ref{app:per-task}`, but that label is commented out, so it rendered as `App.~??`. Repointed to `Table~\ref{tab:per-task-icl10}`.
2. **Abstract typo.** `10\% \ relative` had a stray `\ ` (double space) — removed.
3. **Abstract wording.** `roughly $\sim 36\times$` (redundant "roughly"+"~") → `roughly $36\times$`; "reduce the standard deviation across the seed" → "reduce the across-seed standard deviation."

Build verified: 31 pages, 0 undefined references, "Preprint." notice present, authors render.

### Still TODO before posting
- Fill in / restore acknowledgments if desired.
- Back-port fixes D.1–D.3 into the Overleaf source so they don't reappear on the next re-copy.

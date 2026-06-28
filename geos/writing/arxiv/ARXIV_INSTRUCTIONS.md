# arXiv build instructions for the SIGA paper

This is the recipe to turn the Overleaf/NeurIPS source (`jun8_v1.tex`) into the
arXiv preprint (`arxiv_v1.tex`). The whole conversion is **3 mechanical edits**,
because the `neurips_2026.sty` `[preprint]` option does most of the work for you.

## The good news: you do NOT have to hunt for "neurips" strings

The only literal "NeurIPS / anonymous / submission" text that renders in the PDF
is the author block. The page-bottom notice, the line numbers, and the
"Submitted to … Do not distribute" banner are all driven by the *single* style
option below — flipping it to `[preprint]` automatically:

- reveals the real author block (instead of "Anonymous Author(s)")
- removes the submission line numbers
- changes the bottom-of-page-1 notice to **"Preprint."**
- un-hides the `\ack` (acknowledgments) environment

So when the Overleaf version changes, you only re-apply the 3 edits below.

---

## The 3 edits (apply these to a fresh copy of the latest Overleaf `.tex`)

### 1. Turn on preprint mode  (line ~7)
```diff
- \usepackage{neurips_2026}
+ \usepackage[preprint]{neurips_2026}
```

### 2. Fill in the author block  (the `\author{...}` near line ~80)
Replace the `Anonymous Authors` block with real authors. `\And` puts authors
side-by-side; `\AND` starts a new row:
```latex
\author{%
  Jane Doe\thanks{Corresponding author: \texttt{jane@uni.edu}} \\
  Dept. of X, University \\
  City, Country \\
  \texttt{jane@uni.edu} \\
  \And
  John Roe \\
  Dept. of Y, University \\
  \texttt{john@uni.edu} \\
}
```

### 3. (Optional) Restore acknowledgments  (just before the bibliography, line ~514)
Preprint mode allows acks. Uncomment and fill:
```latex
\begin{ack}
We thank ... . This work was supported by ... .
\end{ack}
```

That's it. Everything else (footer text, line-number removal) is automatic.

---

## Files arXiv needs in the upload

Put these in the upload tarball (all already in this folder):

- `arxiv_v1.tex`  (the main file — rename to whatever you like)
- `neurips_2026.sty`
- `references.bib`  **and** `arxiv_v1.bbl`  (include the `.bbl`; arXiv is happier
  when the compiled bibliography ships with the source)
- `assets/`  — needed images/inputs:
  `siga_f1_jun5.png`, `siga_f2.png`, `buckleyLeverett_base.xml`,
  `buckleyLeverett_benchmark.xml`, `trajectory_buckleyleverett_xm.txt`

Build command (what I ran, verified clean — 31 pages, 0 undefined refs):
```bash
pdflatex arxiv_v1 && bibtex arxiv_v1 && pdflatex arxiv_v1 && pdflatex arxiv_v1
```

---

## Content fixes I also applied to arxiv_v1.tex — PLEASE also fix these in Overleaf

These are real source bugs (not arXiv-specific). I fixed them in `arxiv_v1.tex`,
but they live in the Overleaf source too and will come back on every re-copy
unless you also fix them upstream:

1. **Broken cross-reference.** The Results section (the "Hard-tail rescue"
   paragraph, ~line 371) cited `App.~\ref{app:per-task}`, but that label is
   commented out (lines ~573–574), so it rendered as `App.~??`. I repointed it to
   the per-task table:
   `App.~\ref{app:per-task}` → `Table~\ref{tab:per-task-icl10}`.

2. **Abstract typo.** `a roughly 10\% \ relative gain` had a stray `\ ` (produces
   a double space). Removed it.

3. **Abstract redundancy / wording.** `a roughly $\sim 36\times$` had both
   "roughly" and "$\sim$" → changed to `a roughly $36\times$`. Also reworded
   "reduce the standard deviation across the seed by $16\times$" →
   "reduce the across-seed standard deviation by $16\times$".

## Minor things to look at (left as-is, your call)

- The abstract has two versions; the first (longer) one is commented out and the
  second is active. Confirm that's intentional.
- `tab:bottleneck` caption says held-out-eval `n=29–30` while the column header
  says `n=30`. Cosmetic.
- Stale vim swap file `.references.bib.swp` is sitting in this folder — safe to
  delete (`rm .references.bib.swp`) if no editor has `references.bib` open.

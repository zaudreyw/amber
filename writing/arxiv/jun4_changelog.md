# Changelog — Jun 4, 2026

Edits to `siga_jun3.tex` (and `references.bib`) following Lianhui's abstract/intro
rewrite. Two goals: (1) repopulate the citations the rewrite dropped, and
(2) foreground the human-baseline speedup and the headline improvement numbers.

## 1. Citations restored into the Introduction

Lianhui's rewritten intro had a `\lianhui{add more existing work and the gap back
and add citations}` placeholder. I refolded the related-work citations and the
two-gap framing from the previous version (`neurips_2026.tex`) into the new prose:

- **Scientific-agent systems** now cited by domain:
  chemistry (`bran2024chemcrow`, `boiko2023coscientist`),
  molecular dynamics (`shi2026mdagent2`, `zhao2026polyjarvis`, `guilbert2025dynamate`),
  CFD (`chen2024metaopenfoam`, `yue2025foamagent`, `pandey2025openfoamgpt`),
  finite-element/multiphysics (`zhan2025mooseagent`, `mcpsim2026`, `ni2024mechagents`),
  reservoir simulation (`moyner2026jutulgpt`).
- **The two gaps** are back, in the rewrite's voice:
  - *Application-wise* — no GEOS-specific agent; geoscience LMs do knowledge/QA
    (`deng2023k2`, `lin2024geogalactica`); closest geoscience agents target narrower
    families (`bekele2025geosim`, `li2025seismologyagent`, `moyner2026jutulgpt`).
  - *Method-wise* — most systems rebuild the agent loop from scratch rather than
    adapting an engineered coding harness (`wang2024openhands`).
- Kept Lianhui's new sentences ("We study a different design point…") intact;
  citations were woven around them, not over them.
- Removed the `\lianhui{}` placeholder.

## 2. Headline improvements foregrounded (Abstract + Intro contributions paragraph)

Lianhui flagged the human-baseline result as the most eye-catching, and asked for
the main improvements (% quality, time vs. vanilla, reliability) to be highlighted.
Removed the `\lianhui{7% performance, 10% speed up, self-evolution}` placeholder and
baked the actual numbers in.

**Human-baseline speedup — intro kept lean (per Lianhui, Jun 4):**
- Intro + abstract now state only the punchline: the extended-budget domain expert
  (new to GEOS) reached a complete deck (deck-level TreeSim 0.931) only after ~180 min,
  vs. SIGA at ≥0.90 in ~5 min → **~36× speedup**.
- Dropped from the intro (kept for §RQ3 / Discussion, where they already live): the
  two 1 h participants timing out at ~48 min (deck-level ~0.53), and the GEOS-developer
  ~30 min / **~6×** simulator-expert estimate. Rationale: the intro should land the
  headline, not the full human-baseline table.
- The ~6× simulator-expert figure was also removed from the abstract for consistency
  (abstract now carries 36× only). Easy to restore if you want both in the abstract.

**Main improvement numbers now in both abstract and intro:**
- Quality: held-out-eval mean TreeSim **0.720 → 0.789**, ≈ **+7 points / ~10% relative**.
- Quality vs. vanilla on the representative task: deck-level **0.751 (vanilla) → ≥0.90**.
- Reliability: across-seed std **0.081 → 0.005**, ~**order-of-magnitude** reduction.
- Efficiency: **no added wall-clock cost** over the bare agent (per the Efficiency
  paragraph / matched-runtime result) — deliberately did *not* claim SIGA is faster
  than vanilla, since the paper's own claim is "no overhead."
- Self-evolution: noted that the best held-out configuration is found automatically.

All numbers cross-checked against the Results section and Tables 1–2 of `siga_jun3.tex`:
- held-out 0.720→0.789 (+0.069): Table 1 (Vanilla / SE rows).
- σ 0.081→0.005: §RQ1 "Hard-tail rescue" + Table 1.
- 0.931 @ ~180 min, ≥0.90 @ ~5 min, vanilla 0.751 @ ~7 min, ~30 min dev estimate:
  Table 2 (human baseline) + §RQ3.

## 3. Citation/bibliography hygiene (surfaced by the restored citations)

These were pre-existing `references.bib` defects that became *live* once the restored
intro citations pulled the affected entries into the bibliography:

- **Undefined citation key:** Related Work cited `chen2025scienceagentbench`, but the
  bib key is `chen2024scienceagentbench`. Fixed the cite to match (arXiv 2410.05080 is
  Oct 2024, so 2024 is correct).
- **Duplicate `chen2024scienceagentbench` entry:** the bib had two entries with the
  same key (one `year=2024`, one `year=2025`). Removed the `year=2025` copy.
- **Unescaped `&` in two titles** (`shi2026mdagent2`, `rein2023gpqa`: "Q&A"): caused a
  `Misplaced alignment tab character &` compile error once `shi2026mdagent2` entered the
  bibliography via the restored MD citation. Escaped to `Q\&A`.
- **Three commented-out bib entries that BibTeX still parsed** (`% @article{...}` —
  `%` is not a BibTeX comment): `li2025seismologyagent`, `foamagent2025`,
  `moyner2026jutulgpt`. Each duplicated a real entry below it, producing "Repeated entry"
  errors (and BibTeX silently keeping the wrong/placeholder version). Deleted the three
  commented blocks; kept the real entries.

After these fixes: **BibTeX exits 0 with no errors/repeated entries; no undefined
citations; no LaTeX `!` errors.** (Validated with a draft-mode compile — figure assets
were stubbed since `assets/geos_fig1_v3(1).png` is not yet on disk; see below.)

## Not changed — flagged for your decision

- **Missing figure asset:** `\includegraphics` on intro Fig. 1 points to
  `assets/geos_fig1_v3(1).png`, which is not in `assets/` (only `siga_fig1.png` and
  `geos_fig2_v0.png` are present). A real (non-draft) build fails on this. Either drop
  the file in, or repoint the path.
- **Broken `\ref{subsec:cross-cutting}`** in `checklist.tex` (line 221, NeurIPS LLM-usage
  item): that label no longer exists — the cross-model panel content moved to
  `App.~\ref{app:cross-model-detail}` (already cited in the same sentence). Renders as
  "??". Left the checklist untouched; likely fix is to drop the `\S\ref{subsec:cross-cutting}, `
  fragment. Your call.

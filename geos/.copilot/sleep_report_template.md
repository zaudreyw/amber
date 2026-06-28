# Sleep Report (template — fill in when phases complete)

**Duration:** 2026-05-01 12:36 UTC → ___
**Cycles completed:** ___
**Exit reason:** [success | time | cycles | plateau | errors | stuck]

## What was accomplished

### Phase 0 — Infrastructure refactor
- Reduced `run/AGENTS.md` post-strip section from 5.4KB → 1.6KB
  (pure harness contract; methodology removed).
- Created `plugin/GEOS_PRIMER_contract.md` (5 lines) and
  `plugin/GEOS_PRIMER_method.md` (79 lines).
- Added 13 `autocamp_*` agent variants to `src/runner/agents.py`.
- Wrote phase launchers, scoring, and analyzer scripts.

### Phase 1 — primer screen (1 seed × 17 tasks, DSv4-flash)
- Contract primer: ___ / 17 success, mean treesim ___
- Method primer: ___ / 17 success, mean treesim ___
- Winner: **___**
- Δ between primers: ___ pp

### Phase 2 — DSv4 fractional factorial (3 seeds × 17 tasks × 9 cells)
- Best cell: ___ at ___ ± ___
- Main effects:
  - R (RAG): ___ pp
  - S (SR-hook): ___ pp
  - X (xmllint MCP): ___ pp
  - M (memory): ___ pp
- SE (self-evolved plugin v3): ___ at ___ ± ___ (vs F6 baseline)

### Phase 3 — cross-model
- minimax-m2.7 baseline: ___, best: ___
- gpt-oss-120b baseline: ___, best: ___ (low; model has weak tool-use loop)
- **Gemma was DROPPED** in preflight (timeout, no outputs)

## Key findings

1. The AGENTS.md split alone produced a substantial improvement
   (~+___ pp over the prior best C2 result of 0.913).
2. The contract-only primer is sufficient for ___; the method primer
   adds ___ pp.
3. The dominant Phase 2 factor was ___.
4. Cross-model: minimax tracks ___; gpt-oss-120b is too weak for this
   benchmark.

## Blockers

(if any)

## What remains

- Re-run Phase 2 winner with longer trajectories?
- Validate Phase 1 winner with 3 seeds (currently 1 seed)?
- Test gemma with different OpenRouter route or local deployment?

## Recommended next steps

(for the human)

# Wakeup briefing — autocamp 2026-05-01

When you wake, run:

```
bash /home/matt/sci/repo3/scripts/autocamp_status.sh
cat /home/matt/sci/repo3/.copilot/checkpoint.md
```

Most-likely-current state will be one of:

**A. All phases complete** — the analysis doc at
`docs/2026-05-02_autonomous-campaign-results.md` is filled in with
metrics. Read that for the headline. The plan doc is at
`docs/2026-05-01_autonomous-campaign-plan.md`.

**B. Some phases still running** — the status script will show which.
Logs at `/data/shared/.../eval/autocamp_2026-05-01/_logs/`. If a phase
crashed mid-run, the per-cell logs will tell you why. Re-launching is
idempotent (existing dirs are left alone, but the script will not
auto-skip). Manually delete the failed dir if needed.

**C. Phase 1 produced an unclear winner** — both primers within seed
variance. `scripts/decide_phase1_winner.py` defaults to `method` in
ties. I'll use that. See `docs/2026-05-02_autonomous-campaign-results.md`
for the per-task breakdown.

## Key files

- `docs/2026-05-01_autonomous-campaign-plan.md` — what I planned and why
- `docs/2026-05-02_autonomous-campaign-results.md` — what actually happened
- `run/AGENTS.md` — the new minimal harness contract (1.6KB post-strip)
- `plugin/GEOS_PRIMER_contract.md` (5 lines) — minimum primer
- `plugin/GEOS_PRIMER_method.md` (79 lines) — method primer
- `src/runner/agents.py` — added `autocamp_*` agent variants

## What was NOT done

- I didn't ablate AGENTS.md content separately (the user said "I'm not
  convinced more granularity is needed"). The contract sits inside
  AGENTS.md (post-strip) and is shared by all cells.
- The SE (self-skill-authorship) cell uses
  `plugin_evolving/v3/` (the DSv4-validated plugin from the
  2026-04-30 Task 3 work). This is a single-shot test of "is the
  agent-authored plugin good?" — not a multi-round self-evolution run.
- gpt-oss-120b reasoning_effort=high is set via env var, but the
  Claude Code runner doesn't have a verified pass-through. If the
  scores look weak it may be because reasoning effort wasn't applied
  end-to-end. Documented in the results doc.
- **GEMMA WAS DROPPED FROM PHASE 3.** Preflight: `google/gemma-4-31b-it`
  via OpenRouter timed out at 600s with 9 tool calls and zero XML
  files written. At <1 tool/min there is no plausible timeout that
  fits 17-task evaluations in a sleep cycle. Also tested with
  agent autocamp_xmodel_baseline + method primer — same setup as the
  other models, so this is a model-route capability finding, not an
  infra bug. The phase3 launcher has gemma cells commented out;
  results doc documents this.

## Decisions log

`.copilot/decisions/D-autocamp-2026-05-01.md` — the 7 design
decisions I made during the campaign (AGENTS split, 2-primer choice,
factorial design, SE single-shot vs multi-round, preflight smokes,
parallel Phase 2/3, gpt-oss reasoning-effort caveat, gemma drop).

## Verification protocol

Before treating any number as final:

1. Cross-check headline scores against raw `_summary.json` files.
2. Best-vs-mean gap: if `max_seed_score - mean > 3pp`, report mean and
   flag seed-dependence.
3. n_params equivalent: model name pinned per-cell.
4. Decontamination: confirm `blocked_gt_xml_filenames` and
   `blocked_rst_relpaths` populated for every (task, run).

# Handoff for Task 3: Self-evolving agent

*Reload `misc/apr30_overnight_instructions.md` if context is fresh.*

## Where we are

- Task 0 (DSv4 ablation): DONE
- Task 1 (MemP): DONE — both M1-u and MemP null over no-memory on DSv4. Doc: `docs/2026-04-30_TASK1_memp.md`
- Task 2 (orchestrator P1-fixed): RUNNING in background — `data/eval/orchestrator_dsv4flash/orch_dsv4_postfix_s{1,2,3}/`
- Task 3 (self-evolving agent): RUNNING in background — `/data/shared/.../self_evolving_2026-04-30/abl_se_round/`

## Task 3 mechanics already deployed

Design doc: `docs/2026-04-30_TASK3_self_evolving_DESIGN.md`

The full evolution pipeline launched via `bash scripts/self_evolving/run_full_evolution.sh`:
- Round 0 (6 tasks) on plugin v0 (blank scaffolding) → reflect → v1
- Round 1 (6 tasks) on v1 → reflect → v2
- Round 2 (5 tasks) on v2 → reflect → v3
- Round 3 (re-runs round 0's 6 tasks with v3) for v3-vs-v0 head-to-head

Plugin versions stored at `plugin_evolving/v{0,1,2,3}/` with each agent
edit producing a new versioned snapshot.

## What to do when SE finishes

1. Score all 4 rounds (`bash scripts/score_dsv4_ablation.sh ...` won't
   work for these; use `batch_evaluate.py` directly):
   ```
   ROOT=/data/shared/geophysics_agent_data/data/eval/self_evolving_2026-04-30
   for r in 0 1 2 3; do
     mkdir -p $ROOT/_results/se_round${r}_s1/abl_se_round
     uv run python scripts/eval/batch_evaluate.py \
       --experiments-dir $ROOT/abl_se_round/se_round${r}_s1 \
       --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
       --results-dir $ROOT/_results/se_round${r}_s1/abl_se_round \
       --output $ROOT/_results/se_round${r}_s1/abl_se_round/_summary.json
   done
   ```

2. Run analyzer:
   ```
   python3 scripts/self_evolving/analyze_evolution.py
   ```

3. Inspect what the agent authored across versions:
   ```
   ls -la plugin_evolving/v{0,1,2,3}/{PRIMER.md,memory/,skills/,agents/}
   cat .copilot/.../version_log.jsonl
   ```

4. Write big writeup `docs/2026-04-30_TASK3_self_evolving.md`:
   - Round-by-round mean treesim (v0/v1/v2/v3 on their respective tasks)
   - v3 vs v0 head-to-head (same 6 round-0 tasks)
   - v3 vs C6 (best human-designed)
   - Per-version: what files did the agent author?
   - Did self-improvement happen?

5. Cycle++ in status.md.

## Stopping conditions

Once SE done, increment Cycle to 3 (Task 0 was Cycle 0; tasks 1,2,3 each cycle).
After that, write master summary `docs/2026-04-30_OVERNIGHT_SUMMARY.md` (skeleton already exists), set `Researcher: present`.

## Cost tracking

So far real DSv4 spend: ~$15 across overnight (cMP + orch + SE).
Wall remaining: orch ~2-3h, SE ~1.5h — both already running.

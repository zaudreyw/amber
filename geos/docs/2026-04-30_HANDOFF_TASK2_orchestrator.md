# Handoff for Task 2: Multi-agent orchestrator refresh

*Reload `misc/apr30_overnight_instructions.md` if context is fresh.*

## Where we just stopped (Task 1 = MemP)

MemP (procedural memory with cosine retrieval) implemented and tested.
Big writeup at `docs/2026-04-30_TASK1_memp.md`.

Headline: TBD (cMPa + cMPb × 3 seeds run, compared to C5/C7/C11/C2/C6 baselines).
The "best memory" decision will be either M1-u (DC-style) or MemP per-task,
or skip memory entirely on DSv4.

## Task 2 setup (ready to fire)

P1 blockers from RN-005 are FIXED in `scripts/orchestrator/run_orchestrator_eval.py`:
- P1A: cross-test-task GT leakage — wired union_xml + union_rst from
  `misc/memory_artifacts/test_blocklist.json` into per-task blocklist.
- P1B: `--disallowedTools` is now comma-joined (`Skill,AskUserQuestion,Write`)
  instead of multi-flag.
- P1C: `analyze_17task.py:tally_jsonl_usage` dedups by `message.id` before summing.
- P3: `status.json` now records `started`/`ended` ISO timestamps.

Launcher ready: `scripts/orchestrator/launch_3seed_postfix.sh`. Runs 3 seeds
(orch_dsv4_postfix_s{1,2,3}) in parallel, workers=3 each = ~12 effective
task-batches concurrent. Wall ~2-3h.

## Decision: keep RAG ON for orchestrator

The DSv4 ablation found RAG hurts on single-agent. But the orchestrator's
subagents need to find right examples per stage, and RAG was load-bearing in
the prior preliminary +0.204 result. Re-running with RAG ON cleanly tests
"do P1 fixes preserve the +0.204?" without confounding with a RAG-removal
change. If we have time after, also run a no-RAG variant to compare.

## To do

1. **Smoketest** the P1-fixed orchestrator on a single task (e.g. Sneddon)
   to verify Write doesn't fire and union_xml is blocked. ~10 min wall.
2. **Launch full 3-seed run**:
   ```
   bash scripts/orchestrator/launch_3seed_postfix.sh > /tmp/orch_postfix_master.log 2>&1 &
   ```
   ~2-3h wall.
3. **Score** all 3 seeds via existing `scripts/orchestrator/score_run.sh`.
4. **Cross-implementation analysis** via existing `scripts/orchestrator/analyze_17task.py`
   (now with P1C fix). Output paired delta vs vanilla DSv4 (use C2 or C6
   from Task 0 as the "vanilla" baseline). Also vs orchestrator-prior
   (the preliminary 0.851 single-seed) to measure how much P1 fixes shift it.
5. **Write up** `docs/2026-04-30_TASK2_orchestrator.md`:
   - 3-seed table: orchestrator vs single-agent (best of Task 0)
   - Effect of each P1 fix (qualitative if not separately ablated)
   - Per-task pattern: which tasks does the orchestrator still win/lose on
   - Efficiency comparison: wall, tokens, real cost
6. **Increment Cycle to 2 in status.md.**
7. **Write small handoff** `docs/2026-04-30_HANDOFF_TASK3_self_evolving.md`.

## Key files

- `scripts/orchestrator/run_orchestrator_eval.py` (P1-fixed; commit 22ea72d)
- `scripts/orchestrator/analyze_17task.py` (P1C-fixed; same commit)
- `scripts/orchestrator/launch_3seed_postfix.sh` (3-seed wrapper)
- `plugin_orchestrator/` — the orchestrator plugin (5 subagents + primers + schema slices)
- `docs/2026-04-30_subagent-orchestrator-handoff.md` — original handoff with full design
- `.copilot/reviews/RN-005_adversarial_orchestrator-17task.md` — P1 details

## Reference: prior preliminary numbers (XN-018)

| condition | mean treesim | n |
|---|---:|---:|
| orchestrator-DSv4flash (preliminary) | 0.851 | 1 |
| openhands-minimax | 0.863 | 1 |
| DSv4flash+min-primer (vanilla) | 0.666 | 1 |
| C6 (Task 0 winner) | 0.921 | 3 |

If post-fix orchestrator is in [0.85, 0.92] across 3 seeds with low σ,
the architecture has merit but doesn't beat a single-agent xmllint setup.
If <0.85, the prior was overstated; if >0.92, multi-agent is the
new winner.

## Time budget

- Smoketest: 10 min
- 3-seed run: 2-3h (wall)
- Score + analyze + writeup: 30 min
- **Total**: ~3-4h

## Stopping rules (still active)

- max_hours: 6 (target 17:08Z)
- After Task 2 done, immediately Task 3 (self-evolving).
- Task 3 is largely pre-built; just needs results from full SE run.

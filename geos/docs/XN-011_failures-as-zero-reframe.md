# XN-011 — Including scoring failures in the average score

**Date:** 2026-04-21
**Status:** metric fix applied; numbers re-reported for E16/E17/E18

## Change

`scripts/eval/batch_evaluate.py` now reports both the scored-only mean
(previous default) and the failures-as-zero mean (tasks that failed to produce
scorable XML contribute 0). The per-task summary JSON written with `--output`
contains a new `summary` block with both views for `overall_score` and
`treesim`.

## Why

The previous mean excluded tasks where the agent produced no parseable XML,
which implicitly rewards runs with more failures (their surviving tasks skew
easier). Failures-as-zero is the fairer framing for a paper claim because it
treats the failure mode as part of the system's behavior — exactly what the
stop-hook retry is supposed to reduce.

## Re-reported E16 / E17 / E18 (v2 + minimax, 17-task subset)

| Run | Scored / Total | Scored-only TreeSim | Failures-as-0 TreeSim |
|---|---:|---:|---:|
| E16 no-plug + mm + v2                 | 15/17 | 0.564 | **0.497** |
| E17 plug + mm + v2 (seed 2)           | 13/17 | 0.575 | **0.440** |
| E18 plug + mm + v2 + G-memory-lite    | 17/17 | 0.725 | **0.725** |

### What changes under the new framing

- **Plug vs no-plug on v2+mm**: scored-only was +0.011 (plug slightly higher). Failures-as-zero is **-0.057** (plug now *worse*). The swing is driven by plug having 4 failures vs no-plug's 2. Finding 1 of SESSION_MAP (plugin's +0.011 "tie") becomes "plugin loses on this seed once failures are counted" — consistent with the variance story (plugin's rescue mechanism is high-variance; this seed landed on the bad side).
- **Memory vs plain plug**: scored-only +0.150. Failures-as-zero **+0.285** — nearly double. G-memory-lite's zero-failure rate is a large part of its gain, not a small part.
- **Memory vs no-plug**: scored-only +0.161. Failures-as-zero **+0.228**.

The memory win is *more* convincing under the fair framing; the plain plugin
win is *less* convincing. Both directions are consistent with what we already
believed (plugin has a high-variance rescue mechanism; memory eliminates one
failure mode), just sharper.

## Note on comparison script parity

`misc/compare_runs_per_task.py` already reports both means in its summary (per
SESSION_MAP §4 issue 3). This change brings `batch_evaluate.py` in line with
that so that rescoring a run produces both numbers directly, rather than
requiring a second pass through the per-task compare script.

## Re-run command (reproduces the numbers above)

```bash
cd /home/matt/sci/repo3

for run in \
    data/eval/claude_code_no_plugin/noplug_mm_v2 \
    data/eval/claude_code_repo3_plugin/plug_mm_v2_seed2 \
    data/eval/claude_code_repo3_plugin_gmemsilent/gmemsilent_mm_v2; do
  echo "=== $run ==="
  uv run python scripts/eval/batch_evaluate.py \
      --experiments-dir "$run" \
      --ground-truth-dir /data/shared/geophysics_agent_data/data/eval/experiments_gt \
      2>&1 | grep -E "Scored-only|Failures-as|succeeded"
done
```

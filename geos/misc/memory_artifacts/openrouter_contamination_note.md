# OpenRouter API Contamination — 3 seeds affected

*Written 2026-04-22 after running diagnostic on D-008 matrix results.*

## Summary

Three of the 18 memory-ablation seeds failed due to OpenRouter billing
or weekly-quota issues, not due to the memory-design variables being
tested. These seeds must be excluded from the analysis or they will
contaminate the interpretation.

| Condition | Seed | Reported fa0 | Cause | Task-level impact |
|---|:-:|---:|---|---|
| **M4-u** | s3 | 0.153 | HTTP 402 `Insufficient credits` | 13/17 tasks hit the 402 error; 4 tasks completed normally |
| **M3-g** | s2 | 0.000 | HTTP 403 `Key limit exceeded (weekly limit)` | 17/17 tasks hit the 403 error; 0 successful tool calls |
| **M3-g** | s3 | 0.000 | HTTP 403 `Key limit exceeded (weekly limit)` | 17/17 tasks hit the 403 error |

All other 15 seeds (A3 s1-s3, placebo s1-s3, M1-u s1-s3, M1-g s1-s3,
M4-g s1-s3, M3-g s1, M4-u s1-s2) completed without API errors.

## Detection

The 402 and 403 errors land in the `latest_agent_response` field of the
per-task `status.json`. For M4-u s3, the diagnostic script found 13 out
of 17 tasks with:

> `API Error: 402 {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402}}`

For M3-g s2 and s3, all 17 tasks per seed had:

> `Failed to authenticate. API Error: 403 {"error":{"message":"Key limit exceeded (weekly limit). Manage it using https://openrouter.ai/settings/keys","code":403}}`

## Impact on reported findings

**Before correction (contaminated):**
- M4-u mean 0.537 ± 0.333 (N=3, includes s3 at 0.153)
- M3-g mean 0.094 ± 0.162 (N=3, includes two 0.000 seeds)

**After exclusion (corrected):**
- M4-u mean 0.729 ± 0.024 (N=2 valid)
- M3-g mean 0.281 (N=1 valid)

**Note the reframing:**
- Previously reported: "M4-u is unstable (σ=0.333)". **This was wrong.**
  M4-u is stable at n=2; the high-variance impression came from including
  one credit-exhausted seed.
- Previously reported: "M3-g tool-locus is weak (mean 0.094)". **Partly misleading.**
  M3-g is effectively untestable — the one valid seed (0.281) had 0 memory
  tool calls, so we cannot distinguish "memory tool is bad" from "agent
  didn't use it."

M4-g is NOT affected: all 3 M4-g seeds completed cleanly. M4-g's
instability (seeds at 0.814, 0.313, 0.280) is a real format-level finding.

## How to detect this in the future

Use `scripts/memory/check_api_contamination.py` (see below — to write).
Or manually:

```bash
# Find seeds with API errors
grep -l "402\|403\|Insufficient credits\|Key limit" \
  /home/matt/sci/repo3/data/eval/*/*/*/status.json | sort -u

# For any suspicious seed (low score, fast elapsed):
python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
resp = d.get('latest_agent_response','')
if 'API Error' in resp:
    print(f'API error in {sys.argv[1]}: {resp[-200:]}')"  <status.json path>
```

A task with:
- elapsed < 30s AND
- tool_count == 0 AND
- exit_code != 0

is almost certainly an API-error abort, not a memory-variable failure.

## Mitigation for future runs

1. **Before launching multi-hour batches**, check OpenRouter dashboard:
   - Credit balance (402 prevention)
   - Weekly key limit status (403 prevention)
2. **Sequence high-value conditions first** (e.g. hero run seeds before
   ablation seeds), so if budget is hit the most important data is safe.
3. **Consider splitting the launch** into two halves with ~hour gap,
   to avoid all seeds of a single condition hitting the same quota window.
4. **Emit an explicit warning** when the wrapper log sees an API error —
   stop the matrix and notify the user, don't continue silently.
5. **Re-run excluded seeds** when the quota resets. For M3-g specifically,
   the 403 is a weekly limit; may need to wait up to 7 days or increase
   key quota.

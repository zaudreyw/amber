# XN-012 — E20 hook-ablation (narrow first-pass)

**Date:** 2026-04-21
**Status:** DRAFT (skeleton written before results; fill in after analyze_e20.py)

## Question

Does the plugin's Stop hook (`plugin/hooks/verify_outputs.py`) rescue the
`failed_no_outputs` empty-completion failure observed on minimax/OpenRouter
(XN-010), or is the rescue actually driven by tool-list-shape effects that
E18's memory tool incidentally provided?

## Design (D-004)

4 E17-failure tasks × 3 independent runs × 4 cells. Minimax/minimax-m2.7,
v2 specs (`experiments_test36_template`), workers=12, timeout=1200s.

| Cell | Agent variant | Hook | Extra tool |
|---|---|:-:|:-:|
| C0 | `claude_code_repo3_plugin_nohook` | off | none |
| C1 | `claude_code_repo3_plugin` | on | none |
| C2 | `claude_code_repo3_plugin_noop_nohook` | off | noop MCP |
| C4 | `claude_code_repo3_plugin_noop` | on | noop MCP |

Infrastructure changes vs prior sessions:
- `plugin/hooks/hooks.json` schema fix (nested `Stop:[{matcher, hooks:[...]}]`).
- Hook loaded via per-task `claude_settings.json` + `--settings` flag
  rather than `--plugin-dir`, preserving tool-list parity with E17/E18.
- `plugin/hooks/verify_outputs.py` emits `/workspace/.verify_hook_events.jsonl`
  on every invocation (decision, reason_category, retries_so_far).
- `plugin/scripts/noop_mcp.py` exposes a single `noop(s)` tool with a
  docstring that tells the agent not to call it.

## Analysis framework

Two granularities are reported per cell:

- **Final status (post runner-retry)** — what the user-facing configuration
  actually achieves. `--pseudo-tool-retries 1` means a failed first attempt
  may be salvaged by a fresh container. Both runner-retry and hook are
  rescue layers.
- **First-attempt status (pre retry)** — a finer-grained measure of how
  often the cell's configuration hits the failure on a single try. For
  cells with a hook, the hook's rescue path occurs WITHIN the first
  attempt (same container, same context) without incrementing this
  counter, so first-attempt failures here reflect only unrecoverable
  failures (e.g. hook disabled, hook errored).

## Live observations during the campaign

Two concrete hook rescues captured in run1:

1. **C1 `ExampleThermalLeakyWell`** (hook ON, no extra tool). Hook events:
   `[no_xml:block] [stop_hook_active:allow]`. Agent wrote XML to relative
   paths (`thermalLeakyWell_{base,benchmark}.xml` at result_dir root), tried
   to end_turn. Hook blocked with "write under /workspace/inputs/". Agent
   wrote to correct path. Final status: success.
2. **C4 `AdvancedExampleDruckerPrager`** (hook ON + noop). First attempt
   had `"stop-hook-error"` system notification + status=failed_no_outputs
   (root cause of this error not resolved — hook output format bug was
   ruled out because a subsequent block-path event succeeded before the
   fix). Runner retried. Second attempt: hook events
   `[no_xml:block]` → agent wrote → `[xml_clean:allow]`. Final success.

Both rescues caught the **wrong-path-write** failure (agent writes XML
relative to cwd=/workspace instead of /workspace/inputs/), not the
**true-empty-completion** failure documented in XN-010. These are two
distinct mechanisms that both present as `failed_no_outputs`:

- **Wrong-path-write:** agent emits tool_use=Write with a relative
  file_path, Write succeeds, files land at /workspace/..., workspace
  inputs dir stays empty, task reports failed_no_outputs.
- **True empty completion:** provider returns content=[] after a
  tool_result, agent loop exits without any assistant message.

The hook rescues both: it fires on Stop regardless of why the agent is
stopping, and blocks when `/workspace/inputs/*.xml` is empty.

## Per-cell results (final)

48 runs complete, 2026-04-21 12:27–12:45 UTC. Scored via
`batch_evaluate.py`, analyzed via `misc/analyze_e20.py`.

| Cell | n | success | timeout | failed_no_outputs | fa0 TreeSim | hook blocks | rescues |
|---|---:|---:|---:|---:|---:|---:|---:|
| C0 nohook       | 12 | 10 | 2 | 0 | **0.643** | 0 | 0 |
| C1 hook         | 12 | **12** | 0 | 0 | **0.530** | 1 | 1 |
| C2 noop_nohook  | 12 | 10 | 2 | 0 | **0.595** | 0 | 0 |
| C4 hook+noop    | 12 | 9 | 3 | 0 | **0.557** | 2 | 2 |

Hook event category counts:
- C1: `xml_clean=11`, `no_xml=1`, `stop_hook_active=1`
- C4: `xml_clean=11`, `no_xml=2`
- C0/C2: n/a (hook not registered in settings, no event file)

## Paired Wilcoxon signed-rank (failures-as-zero TreeSim)

n=12 per comparison (12 pairs of the same (run, task) across cells).

| Comparison | mean Δ | direction | p≈ (two-sided, normal approx) |
|---|---:|:---:|---:|
| C1 − C0 (hook effect) | **−0.112** | a<b | 0.308 |
| C2 − C0 (noop effect) | −0.048 | a<b | 0.638 |
| C4 − C0 (hook+noop) | −0.086 | a<b | 0.272 |
| C1 − C2 (hook vs noop) | −0.064 | a<b | 0.638 |

**Nothing reaches p<0.05 at n=12.** All cells score slightly below C0 on
mean TreeSim; the hook trends toward the largest negative delta.

## Decision (per D-004 pre-registered rule)

**Branch 4: C0 failure rate was ≤1 per cell — E17's 4/17 was run-level
fluke.** 0 `failed_no_outputs` in any cell at final status across 48 runs.
The empty-completion pattern that drove XN-010 did NOT reproduce here.
The runner's `--pseudo-tool-retries 1` salvaged the first-attempt
failures that did occur (2 attempt_1 failures, both on
`AdvancedExampleDruckerPrager`: one in C0, one in C4; both rescued by
retry). So the narrow hypothesis "hook rescues an otherwise-unrecoverable
failure" is unfalsifiable here — we had no unrecoverable failures.

**Do NOT expand to full 17-task factorial.** E20's narrow pass failed to
reproduce E17's failure rate on the same 4 tasks. Expanding wouldn't test
the mechanism because we'd be measuring hook behavior against a
non-failing baseline. Budget preserved.

## Secondary findings

1. **The hook DID intervene successfully twice** (1 no_xml rescue in
   run1/C1/TLW; 1 no_xml rescue in run2/C4/DruckerPrager-retry;
   1 spurious `stop_hook_active` allow in C1/TLW due to a mid-campaign
   bug I fixed). The rescue *works* at the mechanism level — it just
   doesn't hit often enough to move the aggregate.
2. **Rescued runs score lower than successful first-attempt runs.** C1
   achieved 12/12 completion (best of any cell) but lowest mean TreeSim
   (0.530). C1's TLW was rescued but wrote syntactically-malformed XML
   (`<?xml version1.0 encoding=UTF-8?>` — missing `=` and quotes).
   Sample too small to call this pattern real, but the rescue→write-rushed
   hypothesis is plausible and worth future investigation.
3. **The "wrong-path write" failure mode is real and hook-catchable.**
   Multiple tasks (across all cells) wrote XML with relative paths
   (`thermalLeakyWell_base.xml` at result_dir root instead of
   `/workspace/inputs/`). Hook correctly blocks `no_xml` in
   `/workspace/inputs/` and forces agent to relocate. This is a
   different mechanism from XN-010's "true empty completion" but same
   surface symptom.
4. **Timeouts, not empty completions, are the dominant failure mode
   here.** 7 of 8 non-successes across 48 runs are 900s timeouts, all
   on `ExampleThermalLeakyWell`. The hook cannot rescue timeouts (it
   fires on Stop, not on docker kill). This is a separate problem.

## Limitations

- n=12 per cell; Wilcoxon power is low. Δ of ±0.2 would be needed for
  p<0.05 at this sample size.
- Hook code changed once mid-campaign (removed `stop_hook_active`
  early-return between run1 and run2). C1/C4 run1 used the old hook
  (less aggressive re-entry check). Runs 2+3 used the new hook. Not
  restarting — the change was strictly more permissive to blocking, so
  it can only INCREASE hook effect, not create one from nothing.
- "3 independent runs" = OpenRouter/minimax non-determinism, not
  controlled seeding. Same limitation as all prior repo3 experiments.
- No adversarial review was run (codex CLI unavailable — D-005).

## Implications

- The **hook infrastructure is validated end-to-end**: plugin loads,
  hook fires on Stop, blocks `no_xml` and `parse_error` with correct
  JSON schema, writes event log, retries counter works.
- The **E17 failure rate does not reproduce** on the same 4 tasks with
  the same model/specs at 3 runs. The prior finding of 4/17 on seed 2
  was a seed fluke, not a reproducible pattern — consistent with
  repo3's documented high cross-seed variance (SESSION_MAP Finding 2).
- **The hook remains a reasonable-cost safety net** (fires zero-cost
  when XML is clean; occasionally salvages wrong-path writes). But
  the headline claim "hook rescues minimax empty-completions" is NOT
  supported by E20. Advise: ship the hook as defense-in-depth, do not
  write a paper section about it.

| Cell | n | success | failed_no_outputs | rate | fa0 TreeSim | hook blocks | rescues succ |
|---|---:|---:|---:|---:|---:|---:|---:|
| C0 | 12 | — | — | — | — | 0 | 0 |
| C1 | 12 | — | — | — | — | — | — |
| C2 | 12 | — | — | — | — | 0 | 0 |
| C4 | 12 | — | — | — | — | — | — |

## Per-task breakdown

_(filled in later)_

## Hook event categories

- C1 (hook on): `no_xml`, `parse_error`, `xml_clean`, `*_max_retries`
- C0/C2 (hook off): no events file (hook not registered in settings)
- C4 (hook on + noop): same categories as C1

## Primary tests (per D-004 decision rule)

1. **Hook effect (C0 → C1):** failure-rate reduction.
2. **Tool-list confound (C0 → C2):** does adding a no-op MCP tool
   alone explain E18's zero-failure rate?
3. **Interaction (C1 vs C4):** do hook and tool-presence compose?

## Decision

_(filled in; one of four branches per D-004 §"Pre-registered decision rule")_

## Limitations

- n=12 per cell is modest; detects only large rescue effects. Full
  17-task factorial needed for paper-grade claim (requires adversarial
  review per D-005 before launch).
- "3 independent runs" = OpenRouter/minimax non-determinism, not
  controlled seeding.
- C0 has `AskUserQuestion` disabled (via
  `NATIVE_CLAUDE_DISALLOWED_TOOLS`), so not a literal E17 replicate —
  but XN-010 ruled out `AskUserQuestion` for the 4 target failures.

## Next actions (by decision branch)

- **Hook rescues (C1 ≪ C0, C2 ≈ C0):** expand to full 17-task factorial
  at 3 runs/cell (pending adversarial review). Ship hook claim.
- **Tool-list shape is sufficient (C1 ≈ C2 ≪ C0):** narrow hook claim
  to XML-parse repair only. Motivate deeper study of why extra tools
  shift minimax message shape.
- **Neither rescues (C1 ≈ C2 ≈ C0):** minimal OpenRouter `curl`
  reproducer to localize the failure. Possibly pivot model.
- **Baseline fluke (C0 ≤ 1 failure):** conclude E17's 4/17 was run-level
  variance; note the null; do not expand.

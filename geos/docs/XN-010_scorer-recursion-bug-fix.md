---
id: XN-010
source: code-fix
title: Scorer RecursionError — cyclic <Included> resolution crash in judge_geos
dag_nodes: [E16, E17, E05, E06, E09, E02, E03]
created: 2026-04-21
---

## TL;DR

`scripts/eval/batch_evaluate.py` was silently dropping tasks in every run that contained cyclic or self-referential `<Included>` tags because `src/eval/judge_geos._resolve_included` recursed without a cycle guard. The session-map guess that "some XML files are deeply nested" was wrong — max XML depth in agent output is 3 and ~50 nodes. The recursion was on the file-include graph, not the XML tree. Fixed by passing an ancestor set of currently-expanding paths and skipping candidates already in it. Rescoring the fix recovered **8 previously-dropped tasks across 6 runs** (E02, E03, E05, E06, E09, E16).

## Root cause

`_resolve_included(root, base_dir)` walked every `<Included><File name=.../>` descendant, parsed the referenced file, and recursed to expand its includes. It had no memory of which files it was already in the middle of expanding. When the agent's output contained either

- **self-reference**: `base.xml` includes `base.xml` (e.g. E16/ExampleThermoporoelasticConsolidation), or
- **mutual cycle**: `base.xml` includes `benchmark.xml`, `benchmark.xml` includes `base.xml` (e.g. E16/AdvancedExampleDeviatedElasticWellbore),

the recursion went until Python's default limit (~1000). The traceback ended inside `pathlib.Path.resolve()` because each cycle step also allocated several stack frames to normalize the candidate path — so the crash surfaced as `RecursionError: maximum recursion depth exceeded` rather than anything naming the include graph.

`evaluate_one` in `batch_evaluate.py` catches the exception, records `status=error`, and (critically) **does not write a `<task>_eval.json`**. The aggregate mean is computed only over scored files, so dropped tasks silently disappear from reported statistics. Failed tasks were only visible as stdout during the scoring run — not persisted anywhere for later inspection. This is how tasks went missing unnoticed.

## What the malformed XML actually looked like

The ground truth uses a clean tree (`base.xml` is a leaf; `benchmark.xml` and `smoke.xml` each include `base.xml`). The agent sometimes inverted or duplicated this, e.g. hallucinating an `<Included>` block in `base.xml` that pulls in the benchmark/smoke files. It is an agent-output quality bug, but the scorer must not crash on malformed-but-parseable XML; it should score what it can.

## Fix (`src/eval/judge_geos.py`)

1. Threaded an `_ancestors: Set[Path]` parameter through `_resolve_included`. Each recursive call passes `_ancestors | {candidate}` (ancestor-chain semantics — not a global visited set, so a file referenced twice from independent branches still resolves both times). If `candidate in _ancestors`, the include is skipped silently.
2. The three call sites (`load_and_resolve_dir` single-entry, `load_and_resolve_dir` multi-entry merge loop, `load_and_resolve_file`) now seed the ancestor set with the originating file's resolved path so a top-level file cannot include itself.
3. Wrapped the inner `ET.parse(candidate)` inside `_resolve_included` in `try: ... except ET.ParseError: continue`. The top-level parse in `load_and_resolve_dir` was already tolerant of per-file parse errors; the inner re-parse on include resolution was not. This also salvaged one ParseError case (E16/ModifiedCamClay) where the malformed XML was only reachable via an include.

## Rescoring results

Script: `misc/rescore_missing.sh` — finds tasks present in each experiment dir but missing a `*_eval.json` in the results dir, and re-runs `batch_evaluate.py` on just those tasks. Ran it after the fix landed. Tasks recovered:

| Run | Task | New treesim |
|---|---|---:|
| E02 (repo3_eval_run2) | AdvancedExampleDeviatedPoroElasticWellbore | 0.816 |
| E03 (repo3_eval_run4) | ExampleSPE11b | 0.130 |
| E05 (memshort_run1) | TutorialSneddon | 0.358 |
| E06 (mm_noplug_run1) | ExampleThermalLeakyWell | 0.193 |
| E09 (memws_run1) | AdvancedExampleViscoDruckerPrager | 0.141 |
| E16 (noplug_mm_v2) | AdvancedExampleDeviatedElasticWellbore | 0.651 |
| E16 (noplug_mm_v2) | AdvancedExampleModifiedCamClay | 0.141 |
| E16 (noplug_mm_v2) | ExampleThermoporoelasticConsolidation | 0.869 |

Updated aggregate means (affected runs only):

| Run | Old n/total | Old mean | New n/total | New mean |
|---|---:|---:|---:|---:|
| E02 repo3_eval_run2 | 33/36 | 0.809 | 34/36 | 0.809 |
| E03 repo3_eval_run4 | 35/36 | 0.828 | 36/36 | 0.809 |
| E05 memshort_run1 | 13/17 | 0.561 | 15/17 | 0.548 |
| E06 mm_noplug_run1 | 15/17 | 0.694 | 16/17 | 0.662 |
| E09 memws_run1 | 15/17 | 0.622 | 16/17 | 0.592 |
| E16 noplug_mm_v2 | 12/17 | 0.566 | 15/17 | 0.564 |

Net effect on headline: E03's mean dropped 0.019 (previously excluded SPE11b, which scored poorly — partial XML). Other runs moved ≤0.032. None of the qualitative findings in the session map change.

## Regression check

Re-scored four non-cyclic tasks (ExampleMandel, AdvancedExampleDruckerPrager, TutorialSneddon, AdvancedExampleCasedContactThermoElasticWellbore) from E16 against their stored `_eval.json`. TreeSim scores match byte-for-byte. The cycle guard is a pure no-op when no cycle exists.

## Lessons / guardrails

- **Scorer must not crash on syntactically-parseable-but-semantically-malformed agent output.** Skip, don't raise. A scorer error silently shrinks the reported N; the honest behavior is to score degraded XML and let the score reflect it.
- **Silent drops in aggregate metrics are dangerous.** `batch_evaluate.py` only persists successes. Failure lists live in stdout, which means re-running an analysis months later gives no trail of which tasks were excluded and why. Fix candidates for later: (a) also write a `_eval_error.json` for failures, (b) include a `failed` block in the aggregate output JSON that has per-task `error` strings.
- **When diagnosing a RecursionError, do not assume it's the tree walker.** The traceback tells you where the recursion is. In this case the tree walker is iterative, and the infinite recursion was on the file include graph. Look at the actual frames before guessing.
- **Cycle-guard callers with the originating file.** An ancestor-chain that only populates on the first include lets a top-level file include itself. Seed it from the caller.

## Files changed

- `src/eval/judge_geos.py` — `_resolve_included` + three call sites
- `misc/rescore_missing.sh` — utility to rescore dropped tasks (left in place for future scorer fixes)
- `docs/XN-010_scorer-recursion-bug-fix.md` — this note

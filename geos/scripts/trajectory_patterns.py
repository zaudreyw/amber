#!/usr/bin/env python3
"""Cross-cell trajectory pattern mining for v4 plugin design.

Analyzes trajectories from F0 (baseline), F2, F4, F6, SE (top performers)
to extract:

  1. PER-TASK CANONICAL FILES: for each task, the files read in the final
     ~10 turns before first Write across successful runs. These are the
     files the agent actually NEEDED to find. Candidate for a
     task→canonical-files lookup.

  2. WASTED EXPLORATION: per (task, cell), files read by F0 that no
     efficient cell read. These are reads that didn't help.

  3. DEAD GREP/GLOB PATTERNS: patterns that returned 0 results or
     whose results were never followed up with a Read. Candidate
     "don't-do-this" warnings for the primer.

  4. RECURRING SUCCESSFUL PATTERNS: Grep/Glob queries used across
     multiple tasks that consistently led to a useful Read.

  5. CONSTITUTIVE-NAME → HEADER mapping: for each Read of a .hpp file,
     find the Grep/Glob that led to it. Build a name→file lookup.

Output: JSON at .../_analysis/F0_F2_F4_F6_SE_patterns.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(
    "/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/dsv4"
)
RES_ROOT = Path(
    "/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_results"
)

CELLS = ["F0", "F2", "F4", "F6", "SE"]
SEEDS = ["s1", "s2", "s3"]
TASKS = [
    "AdvancedExampleCasedContactThermoElasticWellbore",
    "AdvancedExampleDeviatedElasticWellbore",
    "AdvancedExampleDruckerPrager",
    "AdvancedExampleExtendedDruckerPrager",
    "AdvancedExampleModifiedCamClay",
    "AdvancedExampleViscoDruckerPrager",
    "buckleyLeverettProblem",
    "ExampleDPWellbore",
    "ExampleEDPWellbore",
    "ExampleIsothermalLeakyWell",
    "ExampleMandel",
    "ExampleThermalLeakyWell",
    "ExampleThermoporoelasticConsolidation",
    "kgdExperimentValidation",
    "pknViscosityDominated",
    "TutorialPoroelasticity",
    "TutorialSneddon",
]


def load_calls(events_path: Path) -> list[dict]:
    """Return ordered list of {tool, input, idx} for one trajectory."""
    calls = []
    if not events_path.exists():
        return calls
    for line in events_path.open():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") != "assistant":
            continue
        msg = e.get("message", {}) or {}
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            calls.append(
                {
                    "tool": c.get("name", ""),
                    "input": c.get("input", {}) or {},
                    "idx": len(calls),
                }
            )
    return calls


def task_score(cell: str, seed: str, task: str) -> float | None:
    """Per-task treesim score for one (cell, seed)."""
    sf = RES_ROOT / f"autocamp_{cell}_{seed}" / f"autocamp_{cell}" / "_summary.json"
    if not sf.exists():
        return None
    try:
        d = json.loads(sf.read_text())
        for r in d.get("results", []):
            if r.get("experiment") == task:
                return r.get("treesim")
    except Exception:
        pass
    return None


def first_write_idx(calls: list[dict]) -> int | None:
    for c in calls:
        if c["tool"] == "Write":
            return c["idx"]
    return None


def files_read_in_window(calls: list[dict], start: int, end: int) -> list[str]:
    """Read file_paths in calls[start:end]."""
    out = []
    for c in calls[start:end]:
        if c["tool"] == "Read":
            fp = c["input"].get("file_path", "")
            if fp:
                out.append(fp)
    return out


def search_calls_followed_up(calls: list[dict]) -> tuple[list[dict], list[dict]]:
    """Classify each Glob/Grep call as 'followed up' or 'dead'.

    A search call is 'followed up' if any of its returned paths
    (we don't have results in events.jsonl directly, so we use a proxy:
    the agent makes a Read within the next 5 calls).

    Returns (followed_up, dead).
    """
    followed_up = []
    dead = []
    for i, c in enumerate(calls):
        if c["tool"] not in ("Glob", "Grep"):
            continue
        # Look at next 5 calls. If any is Read, count as followed up.
        followup_window = calls[i + 1 : i + 6]
        had_read = any(c2["tool"] == "Read" for c2 in followup_window)
        if had_read:
            followed_up.append(c)
        else:
            dead.append(c)
    return followed_up, dead


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(
            "/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/patterns.json"
        ),
    )
    ap.add_argument(
        "--canonical-window",
        type=int,
        default=10,
        help="how many calls before first Write to consider 'canonical'",
    )
    ap.add_argument(
        "--success-threshold",
        type=float,
        default=0.85,
        help="treesim threshold to consider a run 'successful' for canonical extraction",
    )
    args = ap.parse_args()

    # --- CANONICAL FILES PER TASK ---
    # For each task, collect files read in the final K calls before first Write,
    # across all SUCCESSFUL runs in any of the 5 cells. Most-frequent files = canonical.
    task_canonical = {t: Counter() for t in TASKS}
    task_canonical_seen_in = {t: defaultdict(set) for t in TASKS}  # file -> set of (cell, seed)

    for task in TASKS:
        for cell in CELLS:
            for seed in SEEDS:
                ts = task_score(cell, seed, task)
                if ts is None or ts < args.success_threshold:
                    continue
                events = ROOT / f"autocamp_{cell}" / f"autocamp_{cell}_{seed}" / task / "events.jsonl"
                calls = load_calls(events)
                fw = first_write_idx(calls)
                if fw is None:
                    continue
                window_start = max(0, fw - args.canonical_window)
                files = files_read_in_window(calls, window_start, fw)
                for f in files:
                    if f.startswith("/workspace/"):
                        continue  # skip self-reads
                    task_canonical[task][f] += 1
                    task_canonical_seen_in[task][f].add((cell, seed))

    # Top canonical per task — files read in ≥3 successful runs
    task_canonical_top = {}
    for task, counter in task_canonical.items():
        top = []
        for f, n in counter.most_common(20):
            seen = task_canonical_seen_in[task][f]
            n_distinct = len(seen)
            if n_distinct >= 3:  # read in at least 3 (cell, seed) combos
                top.append({"file": f, "n_reads": n, "n_distinct_runs": n_distinct})
        task_canonical_top[task] = top

    # --- WASTED EXPLORATION ---
    # Per-task: files read ONLY in F0 (and no efficient cell)
    f0_only_per_task = {}
    for task in TASKS:
        all_efficient_files = set()
        f0_files = set()
        for cell in CELLS:
            for seed in SEEDS:
                events = ROOT / f"autocamp_{cell}" / f"autocamp_{cell}_{seed}" / task / "events.jsonl"
                calls = load_calls(events)
                files = [
                    c["input"].get("file_path", "")
                    for c in calls
                    if c["tool"] == "Read" and c["input"].get("file_path", "")
                ]
                files = [f for f in files if not f.startswith("/workspace/")]
                if cell == "F0":
                    f0_files.update(files)
                else:
                    all_efficient_files.update(files)
        f0_only = sorted(f0_files - all_efficient_files)
        f0_only_per_task[task] = f0_only[:30]

    # --- DEAD GREP/GLOB PATTERNS ---
    # Aggregate across all F0 trajectories
    dead_grep = Counter()
    dead_glob = Counter()
    live_grep = Counter()
    live_glob = Counter()
    for task in TASKS:
        for seed in SEEDS:
            events = ROOT / f"autocamp_F0" / f"autocamp_F0_{seed}" / task / "events.jsonl"
            calls = load_calls(events)
            followed, dead = search_calls_followed_up(calls)
            for c in dead:
                pat = c["input"].get("pattern", "") or c["input"].get("path", "")
                if c["tool"] == "Grep":
                    dead_grep[pat] += 1
                else:
                    dead_glob[pat] += 1
            for c in followed:
                pat = c["input"].get("pattern", "") or c["input"].get("path", "")
                if c["tool"] == "Grep":
                    live_grep[pat] += 1
                else:
                    live_glob[pat] += 1

    # --- HPP FILE READS (constitutive lookup) ---
    # Aggregate which .hpp files get read across all F0 trajectories,
    # and what Grep pattern preceded each one (if any).
    hpp_reads = Counter()
    hpp_preceding_pattern = defaultdict(Counter)  # hpp_file -> Counter of preceding-Grep-patterns
    for task in TASKS:
        for seed in SEEDS:
            for cell in CELLS:
                events = ROOT / f"autocamp_{cell}" / f"autocamp_{cell}_{seed}" / task / "events.jsonl"
                calls = load_calls(events)
                for i, c in enumerate(calls):
                    if c["tool"] != "Read":
                        continue
                    fp = c["input"].get("file_path", "")
                    if not fp.endswith(".hpp"):
                        continue
                    hpp_reads[fp] += 1
                    # Look back up to 5 calls for a Grep that might have led here
                    for back in range(max(0, i - 5), i):
                        prev = calls[back]
                        if prev["tool"] == "Grep":
                            pat = prev["input"].get("pattern", "")
                            hpp_preceding_pattern[fp][pat] += 1
                            break

    # Build name → header lookup: top hpp files with their best-fit grep pattern
    name_to_header = []
    for hpp, total in hpp_reads.most_common(40):
        prec = hpp_preceding_pattern.get(hpp, Counter()).most_common(3)
        name_to_header.append(
            {
                "header": hpp,
                "total_reads": total,
                "preceding_grep_patterns": [{"pattern": p, "n": n} for p, n in prec],
            }
        )

    # --- RECURRING SUCCESSFUL PATTERNS ---
    # Grep patterns that recur across multiple tasks AND were followed up
    pattern_tasks = defaultdict(set)
    pattern_followups = Counter()
    for task in TASKS:
        for seed in SEEDS:
            for cell in ["F2", "F4", "F6", "SE"]:  # efficient cells only
                events = ROOT / f"autocamp_{cell}" / f"autocamp_{cell}_{seed}" / task / "events.jsonl"
                calls = load_calls(events)
                followed, _ = search_calls_followed_up(calls)
                for c in followed:
                    if c["tool"] != "Grep":
                        continue
                    pat = c["input"].get("pattern", "")
                    pattern_tasks[pat].add(task)
                    pattern_followups[pat] += 1
    # Patterns that appear in 3+ different tasks
    cross_task_patterns = [
        {"pattern": p, "n_tasks": len(pattern_tasks[p]), "n_uses": pattern_followups[p]}
        for p, n in pattern_followups.most_common(50)
        if len(pattern_tasks[p]) >= 3
    ]

    # --- TASK-FAMILY KEYWORDS ---
    # For each task, what keywords does the agent search for? (The successful
    # ones become the canonical search patterns for that task family.)
    task_keywords = {}
    for task in TASKS:
        kw = Counter()
        for seed in SEEDS:
            for cell in ["F2", "F4", "F6", "SE"]:  # efficient cells
                events = ROOT / f"autocamp_{cell}" / f"autocamp_{cell}_{seed}" / task / "events.jsonl"
                calls = load_calls(events)
                followed, _ = search_calls_followed_up(calls)
                for c in followed:
                    pat = c["input"].get("pattern", "")
                    if pat:
                        kw[pat] += 1
        task_keywords[task] = [{"pattern": p, "n": n} for p, n in kw.most_common(8)]

    report = {
        "task_canonical_files": task_canonical_top,
        "f0_only_files_per_task": f0_only_per_task,
        "dead_search_patterns": {
            "grep_dead_top20": dead_grep.most_common(20),
            "glob_dead_top20": dead_glob.most_common(20),
            "grep_live_top20": live_grep.most_common(20),
        },
        "constitutive_name_to_header": name_to_header,
        "cross_task_grep_patterns": cross_task_patterns,
        "task_keywords": task_keywords,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    # Quick console summary
    print(f"=== Per-task canonical files (read by ≥3 successful runs, last {args.canonical_window} calls before first Write) ===\n")
    for task in TASKS:
        top = task_canonical_top[task][:5]
        if not top:
            print(f"  {task}: (no canonical found at threshold)")
            continue
        print(f"  {task}:")
        for entry in top:
            print(f"    - {entry['file']} (read {entry['n_reads']}× in {entry['n_distinct_runs']} runs)")
    print()
    print("=== Top dead Grep patterns (no Read in next 5 calls) ===")
    for pat, n in dead_grep.most_common(10):
        print(f"  {n}× {pat[:80]}")
    print()
    print("=== Top live Grep patterns (followed by Read) ===")
    for pat, n in live_grep.most_common(10):
        print(f"  {n}× {pat[:80]}")
    print()
    print("=== Top cross-task Grep patterns (used in 3+ tasks) ===")
    for entry in cross_task_patterns[:10]:
        print(f"  {entry['pattern']}: {entry['n_tasks']} tasks, {entry['n_uses']} uses")
    print()
    print("=== Top constitutive header reads ===")
    for entry in name_to_header[:10]:
        prec = ", ".join(p["pattern"] for p in entry["preceding_grep_patterns"][:2])
        print(f"  {entry['total_reads']}× {entry['header']}  (prec: {prec})")
    print()
    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()

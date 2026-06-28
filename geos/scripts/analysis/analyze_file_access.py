#!/usr/bin/env python3
"""
analyze_file_access.py
======================

For every completed agent run under ``data/eval/<agent_key>/<run_name>/<task_name>/``,
parse ``events.jsonl`` and characterise *what* the agent reads:

  - Read tool calls (file_path categorisation)
  - Glob / Grep tool calls (pattern + path)
  - Bash commands that are read-equivalents (cat/head/tail/less/more/sed/awk/grep/rg)
    on documentation / xml files, plus any invocation of ``xmllint``.

Outputs (in --out-dir, default scripts/analysis/out/file_access/):
  - file_access_per_run.csv : long form, one row per (run, file, tool)
  - file_access_summary.csv : one row per (agent, run_name, model)
  - file_access_summary.md  : narrative answering headline questions

Run as plain python3 (uses stdlib + pandas; pandas is already a project dep).

Example:
  python3 scripts/analysis/analyze_file_access.py
  python3 scripts/analysis/analyze_file_access.py --agent-keys claude_code_no_plugin,claude_code_repo3_plugin
  python3 scripts/analysis/analyze_file_access.py --max-tasks-per-run 2
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from collections import Counter, defaultdict
from glob import glob
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd

EVAL_ROOT_DEFAULT = Path("/home/matt/sci/repo3/data/eval")
DEFAULT_OUT = Path("/home/matt/sci/repo3/scripts/analysis/out/file_access")

# ---- categorisation ---------------------------------------------------------

SPHINX_DIR_FRAGMENT = "/src/docs/sphinx/"
INPUT_FILES_FRAGMENT = "/inputFiles/"
WORKSPACE_PREFIX = "/workspace"
GEOS_LIB_PREFIX = "/geos_lib"


def categorize_file(path: str) -> str:
    """Bucket a file path the agent referenced into one of the analysis classes."""
    if not path:
        return "other"
    p = path.strip()
    low = p.lower()
    if low.endswith(".rst"):
        if SPHINX_DIR_FRAGMENT in p:
            return "rst_sphinx"
        return "rst_nonsphinx"
    if low.endswith(".xml"):
        if p.startswith(WORKSPACE_PREFIX):
            return "xml_workspace"
        if INPUT_FILES_FRAGMENT in p:
            return "xml_input_files"
        # XML under sphinx (rare) or under workspace-rooted docs
        return "xml_other"
    if low.endswith(".xsd"):
        return "xsd_schema"
    if low.endswith(".py"):
        return "python"
    return "other"


# ---- bash command parsing ---------------------------------------------------

# Words that, when leading a pipeline, indicate a "read-equivalent" command.
READ_EQUIV_CMDS = {"cat", "head", "tail", "less", "more", "sed", "awk", "grep", "rg",
                   "egrep", "fgrep", "view", "bat"}

# Tokens we treat as path arguments worth categorising. Anything containing a
# slash and an extension we recognise is fair game.
PATH_RE = re.compile(r"[\w./\-+]+\.(?:rst|xml|xsd|py|md|txt|json)\b")
# Bare filenames like ``Example.rst`` slip past PATH_RE but are usually arguments
# to ``find -name`` rather than real reads. Require at least one path separator
# OR a leading ./ to count it as a real path.
ABS_OR_REL_PATH_RE = re.compile(r"^(?:\.{0,2}/|/)[\w./\-+]+\.(?:rst|xml|xsd|py|md|txt|json)$")


def _split_pipeline(cmd: str) -> list[str]:
    """Split a bash command on || && | ; and newline; return non-empty stages."""
    # A naive split is fine — we only need the leading word of each stage.
    parts = re.split(r"\|\||&&|;|\n|\|", cmd)
    return [p.strip() for p in parts if p.strip()]


def parse_bash(command: str) -> dict:
    """Classify a bash command and extract any documentation/xml paths it touches.

    Returns:
        {
          'has_xmllint': bool,
          'read_doc_paths': list[str],   # paths we infer were read by cat/head/etc
          'kind': 'bash_xmllint' | 'bash_read_rst' | 'bash_read_xml'
                  | 'bash_read_other_file' | 'bash_other',
        }
    """
    cmd = command or ""
    has_xmllint = bool(re.search(r"\bxmllint\b", cmd))

    paths: list[str] = []
    is_read_equiv = False
    stages = _split_pipeline(cmd)
    for stage in stages:
        try:
            tokens = shlex.split(stage, posix=True)
        except ValueError:
            tokens = stage.split()
        if not tokens:
            continue
        head = tokens[0].split("/")[-1]  # handle /usr/bin/grep
        if head in READ_EQUIV_CMDS:
            is_read_equiv = True
        # Always harvest path-shaped tokens — they may be args to find -path,
        # xmllint, or piped-to commands that consume them later.
        for tok in tokens[1:]:
            if PATH_RE.search(tok):
                # Strip surrounding quotes / colons from sed expressions.
                m = PATH_RE.search(tok)
                if m:
                    paths.append(m.group(0))

    # Also fall back to a global path scan in case shlex couldn't tokenise (heredocs, etc).
    if not paths:
        paths = PATH_RE.findall(cmd)

    # Drop bare filenames (e.g. "Example.rst" used as a -name argument). Real
    # reads always have a directory component.
    paths = [p for p in paths if "/" in p]
    # Filter to 'documentation-ish' files when reporting kind
    read_paths = [p for p in paths if p.lower().endswith((".rst", ".xml", ".xsd"))]

    if has_xmllint:
        kind = "bash_xmllint"
    elif is_read_equiv and any(p.lower().endswith(".rst") for p in read_paths):
        kind = "bash_read_rst"
    elif is_read_equiv and any(p.lower().endswith((".xml", ".xsd")) for p in read_paths):
        kind = "bash_read_xml"
    elif is_read_equiv and read_paths:
        kind = "bash_read_other_file"
    else:
        kind = "bash_other"

    return {
        "has_xmllint": has_xmllint,
        "read_doc_paths": read_paths,
        "kind": kind,
    }


# ---- run discovery ----------------------------------------------------------


def iter_task_dirs(eval_root: Path, agent_keys: list[str] | None) -> Iterator[Path]:
    if agent_keys:
        agent_dirs = [eval_root / k for k in agent_keys]
    else:
        # Anything under data/eval/ that has at least one events.jsonl underneath.
        agent_dirs = [p for p in eval_root.iterdir() if p.is_dir()]
    for agent_dir in agent_dirs:
        if not agent_dir.exists():
            print(f"[warn] missing agent_key dir: {agent_dir}", file=sys.stderr)
            continue
        # agent_dir / run_name / task / events.jsonl
        for events in agent_dir.glob("*/*/events.jsonl"):
            yield events.parent


def load_status(task_dir: Path) -> dict:
    f = task_dir / "status.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text())
    except Exception:
        return {}


def load_meta(task_dir: Path) -> dict:
    f = task_dir / "eval_metadata.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text())
    except Exception:
        return {}


# ---- core extraction --------------------------------------------------------


def extract_from_events(events_path: Path) -> dict:
    """Walk events.jsonl and return per-task aggregates.

    Returns dict with:
      file_rows: list[dict]            # one per (file_path, tool) with n_reads
      bash_xmllint: int
      bash_read_rst_count: int
      bash_read_xml_count: int
      glob_calls: list[(pattern, path)]
      grep_calls: list[(pattern, path)]
    """
    file_counter: Counter = Counter()  # (tool, file_path, category) -> count
    glob_calls: list[tuple[str, str]] = []
    grep_calls: list[tuple[str, str]] = []
    bash_xmllint = 0
    bash_read_rst = 0
    bash_read_xml = 0
    bash_read_other = 0
    bash_total = 0

    with events_path.open() as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") != "assistant":
                continue
            content = e.get("message", {}).get("content", []) or []
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                name = b.get("name") or ""
                inp = b.get("input") or {}
                if name == "Read":
                    fp = inp.get("file_path") or inp.get("path") or ""
                    if fp:
                        cat = categorize_file(fp)
                        file_counter[("Read", fp, cat)] += 1
                elif name == "Glob":
                    glob_calls.append((inp.get("pattern", ""), inp.get("path", "")))
                elif name == "Grep":
                    grep_calls.append((inp.get("pattern", ""), inp.get("path", "")))
                elif name == "Bash":
                    bash_total += 1
                    cmd = inp.get("command", "")
                    parsed = parse_bash(cmd)
                    if parsed["has_xmllint"]:
                        bash_xmllint += 1
                    if parsed["kind"] == "bash_read_rst":
                        bash_read_rst += 1
                    elif parsed["kind"] == "bash_read_xml":
                        bash_read_xml += 1
                    elif parsed["kind"] == "bash_read_other_file":
                        bash_read_other += 1
                    # Attribute any read_doc_paths to a "Bash" tool so they show up
                    # in the per-file long form.
                    for fp in parsed["read_doc_paths"]:
                        cat = categorize_file(fp)
                        file_counter[("Bash", fp, cat)] += 1

    file_rows = [
        {"tool": tool, "file_path": fp, "file_category": cat, "n_reads": n}
        for (tool, fp, cat), n in file_counter.items()
    ]
    return {
        "file_rows": file_rows,
        "bash_xmllint": bash_xmllint,
        "bash_read_rst": bash_read_rst,
        "bash_read_xml": bash_read_xml,
        "bash_read_other": bash_read_other,
        "bash_total": bash_total,
        "glob_calls": glob_calls,
        "grep_calls": grep_calls,
    }


# ---- main -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval-root", type=Path, default=EVAL_ROOT_DEFAULT)
    ap.add_argument("--agent-keys", type=str, default=None,
                    help="Comma-separated subset of agent_keys (default: all).")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--max-tasks-per-run", type=int, default=0,
                    help="Cap N tasks per (agent_key, run_name) for fast sampling. 0=all.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    keys = [k.strip() for k in args.agent_keys.split(",")] if args.agent_keys else None
    args.out_dir.mkdir(parents=True, exist_ok=True)

    long_rows: list[dict] = []
    summary_rows: list[dict] = []
    glob_grep_rows: list[dict] = []  # auxiliary
    seen_per_run: dict[tuple[str, str], int] = defaultdict(int)

    n_tasks = 0
    n_skipped = 0

    for task_dir in iter_task_dirs(args.eval_root, keys):
        meta = load_meta(task_dir)
        status = load_status(task_dir)

        agent = meta.get("agent") or task_dir.parent.parent.name
        run_name = meta.get("run_name") or task_dir.parent.name
        task_name = meta.get("task") or task_dir.name
        model = meta.get("claude_model") or status.get("claude_model") or ""
        plugin_enabled = meta.get("plugin_enabled")
        process_status = status.get("process_status") or "unknown"

        if args.max_tasks_per_run:
            key = (agent, run_name)
            if seen_per_run[key] >= args.max_tasks_per_run:
                continue
            seen_per_run[key] += 1

        events_path = task_dir / "events.jsonl"
        if not events_path.exists():
            n_skipped += 1
            continue
        try:
            agg = extract_from_events(events_path)
        except Exception as ex:
            print(f"[warn] failed to parse {events_path}: {ex}", file=sys.stderr)
            n_skipped += 1
            continue
        n_tasks += 1

        # Long-form per-file rows
        for r in agg["file_rows"]:
            long_rows.append({
                "agent": agent,
                "run_name": run_name,
                "task": task_name,
                "model": model,
                "plugin_enabled": plugin_enabled,
                "process_status": process_status,
                **r,
            })

        # Glob/Grep auxiliary rows
        for pat, p in agg["glob_calls"]:
            glob_grep_rows.append({
                "agent": agent, "run_name": run_name, "task": task_name,
                "tool": "Glob", "pattern": pat, "path": p,
            })
        for pat, p in agg["grep_calls"]:
            glob_grep_rows.append({
                "agent": agent, "run_name": run_name, "task": task_name,
                "tool": "Grep", "pattern": pat, "path": p,
            })

        # Per-task summary row (rolled up to per-run later)
        cats = Counter()
        unique_files = set()
        for r in agg["file_rows"]:
            cats[r["file_category"]] += r["n_reads"]
            unique_files.add(r["file_path"])
        summary_rows.append({
            "agent": agent,
            "run_name": run_name,
            "task": task_name,
            "model": model,
            "plugin_enabled": plugin_enabled,
            "process_status": process_status,
            "n_unique_files_referenced": len(unique_files),
            "n_rst_sphinx_reads": cats.get("rst_sphinx", 0),
            "n_rst_nonsphinx_reads": cats.get("rst_nonsphinx", 0),
            "n_xml_input_files_reads": cats.get("xml_input_files", 0),
            "n_xml_workspace_reads": cats.get("xml_workspace", 0),
            "n_xsd_schema_reads": cats.get("xsd_schema", 0),
            "n_python_reads": cats.get("python", 0),
            "n_other_reads": cats.get("other", 0) + cats.get("xml_other", 0),
            "n_bash_total": agg["bash_total"],
            "n_bash_xmllint": agg["bash_xmllint"],
            "n_bash_read_rst": agg["bash_read_rst"],
            "n_bash_read_xml": agg["bash_read_xml"],
            "n_glob_calls": len(agg["glob_calls"]),
            "n_grep_calls": len(agg["grep_calls"]),
        })

        if not args.quiet and n_tasks % 50 == 0:
            print(f"  ... processed {n_tasks} tasks", file=sys.stderr)

    if not long_rows:
        print(f"[err] no rows produced (n_tasks={n_tasks}, n_skipped={n_skipped})", file=sys.stderr)
        return 2

    long_df = pd.DataFrame(long_rows)
    summary_df = pd.DataFrame(summary_rows)

    # Roll up per-task summary into per-run summary
    grp_cols = ["agent", "run_name", "model", "plugin_enabled"]
    metric_cols = [c for c in summary_df.columns
                   if c.startswith("n_") and c != "n_unique_files_referenced"]
    per_run = (summary_df
               .groupby(grp_cols, dropna=False)
               .agg(n_tasks=("task", "nunique"),
                    n_unique_files_referenced=("n_unique_files_referenced", "sum"),
                    **{c: (c, "sum") for c in metric_cols})
               .reset_index())

    # Save
    long_path = args.out_dir / "file_access_per_run.csv"
    summary_path = args.out_dir / "file_access_summary.csv"
    per_task_path = args.out_dir / "file_access_per_task.csv"
    glob_grep_path = args.out_dir / "file_access_glob_grep.csv"
    long_df.to_csv(long_path, index=False)
    per_run.to_csv(summary_path, index=False)
    summary_df.to_csv(per_task_path, index=False)
    pd.DataFrame(glob_grep_rows).to_csv(glob_grep_path, index=False)

    # ---- markdown summary ---------------------------------------------------
    md = [f"# File-access summary ({n_tasks} tasks)\n"]
    md.append(f"- Eval root: `{args.eval_root}`\n")
    md.append(f"- Skipped tasks (no events.jsonl or parse error): {n_skipped}\n")
    md.append(f"- Agent keys analysed: "
              f"{', '.join(sorted(long_df['agent'].unique())) if len(long_df) else '(none)'}\n\n")

    # Headline 1 — non-sphinx rst
    nonsphinx = long_df[long_df["file_category"] == "rst_nonsphinx"]
    md.append("## Q1. Have any non-sphinx .rst files been read?\n\n")
    if nonsphinx.empty:
        md.append("**No.** Across all parsed events, zero Read or Bash-read calls hit a "
                  "`.rst` file outside `src/docs/sphinx/`.\n\n")
    else:
        agg = (nonsphinx.groupby("file_path")["n_reads"]
               .sum().sort_values(ascending=False))
        md.append(f"**Yes** — {len(agg)} distinct non-sphinx rst files were referenced, "
                  f"{int(agg.sum())} total reads. Top 10:\n\n")
        md.append("| file_path | n_reads | first_seen_in (agent / run) |\n|---|---:|---|\n")
        for fp, n in agg.head(10).items():
            sub = nonsphinx[nonsphinx["file_path"] == fp].iloc[0]
            md.append(f"| `{fp}` | {int(n)} | {sub['agent']} / {sub['run_name']} |\n")
        md.append("\n")

    # Headline 2 — xmllint
    xmllint_runs = summary_df[summary_df["n_bash_xmllint"] > 0]
    md.append("## Q2. Has xmllint ever been invoked?\n\n")
    if xmllint_runs.empty:
        md.append("**No.** No `xmllint` invocation found in any parsed Bash command.\n\n")
    else:
        n_calls = int(xmllint_runs["n_bash_xmllint"].sum())
        md.append(f"**Yes.** {n_calls} total invocations across "
                  f"{len(xmllint_runs)} task-runs. Distribution by agent:\n\n")
        by_agent = (xmllint_runs.groupby("agent")["n_bash_xmllint"]
                    .sum().sort_values(ascending=False))
        md.append("| agent | n_xmllint |\n|---|---:|\n")
        for a, n in by_agent.items():
            md.append(f"| {a} | {int(n)} |\n")
        md.append("\n")

    # Top RST files (sphinx)
    md.append("## Top 15 most-read sphinx .rst files\n\n")
    rst_sphinx = (long_df[long_df["file_category"] == "rst_sphinx"]
                  .groupby("file_path")["n_reads"].sum()
                  .sort_values(ascending=False).head(15))
    if rst_sphinx.empty:
        md.append("(none)\n\n")
    else:
        md.append("| file_path | n_reads |\n|---|---:|\n")
        for fp, n in rst_sphinx.items():
            md.append(f"| `{fp}` | {int(n)} |\n")
        md.append("\n")

    # Top XML example files
    md.append("## Top 15 most-read .xml example files (under inputFiles/)\n\n")
    xmls = (long_df[long_df["file_category"] == "xml_input_files"]
            .groupby("file_path")["n_reads"].sum()
            .sort_values(ascending=False).head(15))
    if xmls.empty:
        md.append("(none)\n\n")
    else:
        md.append("| file_path | n_reads |\n|---|---:|\n")
        for fp, n in xmls.items():
            md.append(f"| `{fp}` | {int(n)} |\n")
        md.append("\n")

    # Per-agent rollup snapshot
    md.append("## Per-agent rollup (sums across runs/tasks)\n\n")
    snap = (per_run.groupby("agent")
            [["n_tasks", "n_rst_sphinx_reads", "n_rst_nonsphinx_reads",
              "n_xml_input_files_reads", "n_xml_workspace_reads",
              "n_bash_xmllint", "n_unique_files_referenced"]]
            .sum().sort_values("n_tasks", ascending=False))
    md.append("| agent | n_tasks | rst_sphinx | rst_nonsphinx | xml_input | "
              "xml_workspace | xmllint | unique_files |\n"
              "|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for a, row in snap.iterrows():
        md.append(f"| {a} | {int(row['n_tasks'])} | "
                  f"{int(row['n_rst_sphinx_reads'])} | "
                  f"{int(row['n_rst_nonsphinx_reads'])} | "
                  f"{int(row['n_xml_input_files_reads'])} | "
                  f"{int(row['n_xml_workspace_reads'])} | "
                  f"{int(row['n_bash_xmllint'])} | "
                  f"{int(row['n_unique_files_referenced'])} |\n")
    md.append("\n")

    md.append("## Output files\n\n")
    md.append(f"- `{long_path}`\n")
    md.append(f"- `{per_task_path}`\n")
    md.append(f"- `{summary_path}` (per-run rollup)\n")
    md.append(f"- `{glob_grep_path}`\n")

    md_path = args.out_dir / "file_access_summary.md"
    md_path.write_text("".join(md))
    print(f"wrote: {long_path}")
    print(f"wrote: {per_task_path}")
    print(f"wrote: {summary_path}")
    print(f"wrote: {glob_grep_path}")
    print(f"wrote: {md_path}")
    print(f"n_tasks_processed={n_tasks}  n_skipped={n_skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

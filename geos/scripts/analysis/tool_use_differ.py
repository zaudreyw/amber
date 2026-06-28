#!/usr/bin/env python3
"""Tool-use diff between two task runs.

Reads `events.jsonl` from each run dir, counts tool_use events, and
emits per-tool deltas + bash-subcommand and Read-by-directory
breakdowns.

Usage (as a script):
    python3 tool_use_differ.py <task_dir_a> <task_dir_b>

Importable function (for the orchestrator):
    diff_tool_use(task_dir_a, task_dir_b) -> dict
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict


_BASH_FIRST_TOKEN = re.compile(r"^[\s({]*([A-Za-z0-9_./-]+)")
_PATH_PREFIX = [
    ("/geos_lib/inputFiles",     "inputFiles"),
    ("/geos_lib/src/docs/sphinx","docs_sphinx"),
    ("/geos_lib/src/docs",       "docs_other"),
    ("/geos_lib/src/coreComponents","src_core"),
    ("/geos_lib/src",            "src_other"),
    ("/geos_lib",                "geos_other"),
    ("/workspace/inputs",        "workspace_inputs"),
    ("/workspace",               "workspace_other"),
    ("/plugins/repo3",           "plugin"),
]


def _classify_path(p: str) -> str:
    for prefix, label in _PATH_PREFIX:
        if p.startswith(prefix):
            return label
    return "other"


def _classify_bash(cmd: str) -> str:
    m = _BASH_FIRST_TOKEN.match(cmd or "")
    if not m:
        return "(empty)"
    tok = m.group(1).split("/")[-1]  # strip path
    return tok


def _iter_assistant_tool_uses(events_path: Path):
    """Yield (tool_name, tool_input_dict) for every assistant tool_use."""
    if not events_path.exists():
        return
    with events_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if ev.get("type") != "assistant":
                continue
            content = (ev.get("message") or {}).get("content") or []
            if not isinstance(content, list):
                continue
            for blk in content:
                if isinstance(blk, dict) and blk.get("type") == "tool_use":
                    yield blk.get("name", "?"), (blk.get("input") or {})


def summarize_one(task_dir: Path) -> dict:
    tools = Counter()
    bash_subs = Counter()
    reads_by_dir = Counter()
    rag_queries = []
    for name, inp in _iter_assistant_tool_uses(task_dir / "events.jsonl"):
        tools[name] += 1
        if name == "Bash":
            bash_subs[_classify_bash(inp.get("command", ""))] += 1
        elif name == "Read":
            p = inp.get("file_path", "") or ""
            reads_by_dir[_classify_path(p)] += 1
        elif name.startswith("mcp__geos-rag__"):
            q = inp.get("query") or inp.get("q") or ""
            if q:
                rag_queries.append(q[:120])
    return {
        "tools": dict(tools),
        "bash_subs": dict(bash_subs),
        "reads_by_dir": dict(reads_by_dir),
        "rag_queries": rag_queries,
        "total_tool_calls": sum(tools.values()),
    }


def diff_tool_use(task_dir_a: Path, task_dir_b: Path) -> dict:
    a = summarize_one(Path(task_dir_a))
    b = summarize_one(Path(task_dir_b))
    keys = set(a["tools"]) | set(b["tools"])
    delta = {k: b["tools"].get(k, 0) - a["tools"].get(k, 0) for k in keys}
    bullets = []
    if a["total_tool_calls"] and b["total_tool_calls"]:
        ratio = b["total_tool_calls"] / a["total_tool_calls"]
        if ratio < 0.7:
            bullets.append(f"B made {a['total_tool_calls']/max(b['total_tool_calls'],1):.1f}× fewer tool calls than A "
                           f"({b['total_tool_calls']} vs {a['total_tool_calls']})")
        elif ratio > 1.4:
            bullets.append(f"B made {b['total_tool_calls']/max(a['total_tool_calls'],1):.1f}× more tool calls than A "
                           f"({b['total_tool_calls']} vs {a['total_tool_calls']})")
    # File-search strategy
    a_search = sum(a["tools"].get(k, 0) for k in ("Glob", "Grep")) + a["bash_subs"].get("find", 0) + a["bash_subs"].get("grep", 0) + a["bash_subs"].get("rg", 0)
    b_search = sum(b["tools"].get(k, 0) for k in ("Glob", "Grep")) + b["bash_subs"].get("find", 0) + b["bash_subs"].get("grep", 0) + b["bash_subs"].get("rg", 0)
    if a_search > b_search * 2 and a_search >= 4:
        bullets.append(f"A used filesystem search {a_search}× vs B {b_search}× (Glob+Grep+find+grep+rg)")
    a_rag = sum(v for k,v in a["tools"].items() if k.startswith("mcp__geos-rag__"))
    b_rag = sum(v for k,v in b["tools"].items() if k.startswith("mcp__geos-rag__"))
    if b_rag > a_rag and b_rag >= 3:
        bullets.append(f"B made {b_rag} RAG queries vs A {a_rag} (geos-rag MCP)")
    a_reads = a["tools"].get("Read", 0); b_reads = b["tools"].get("Read", 0)
    if a_reads > b_reads * 2 and a_reads >= 8:
        bullets.append(f"A read {a_reads} files vs B {b_reads} (3× ratio)")
    return {
        "a": a,
        "b": b,
        "tool_delta": dict(sorted(delta.items(), key=lambda kv: -abs(kv[1]))),
        "summary_bullets": bullets,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    a = Path(sys.argv[1]); b = Path(sys.argv[2])
    out = diff_tool_use(a, b)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()

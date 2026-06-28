#!/usr/bin/env python3
"""Stage 1: bottleneck diagnostic extraction (no LLM).

For each (agent, run, task) tuple, mine:
  - `<results_root>/_results/<run>/<agent>/<task>_eval.json` for treesim_detail
  - `<results_root>/<agent>/<run>/<task>/events.jsonl` for trajectory
  - `<results_root>/<agent>/<run>/<task>/tool_calls.json` for tool count summary

Emit one JSON per task to <out_dir>/<agent>__<run>__<task>.json with:
  - score: overall treesim, section_scores
  - worst_subtrees: top-K by impact = (1 - score) * gt_size
  - missing_elements: GT element types absent in generated XML
  - extra_elements: gen element types not in GT
  - trajectory: tool counts, file-access patterns, edit churn, search terms
  - excerpt: short trajectory excerpt (final ~12 turns) for downstream LLM context
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# ---------- treesim_detail mining ----------

def gt_size(node: dict) -> int:
    """Recursive GT subtree size (number of GT-side nodes)."""
    if not isinstance(node, dict):
        return 0
    n = 1 + max(0, node.get("n_gt_children", 0))
    for c in node.get("children", []) or []:
        n += gt_size(c) - 1  # don't double-count node itself; child subtree size already starts at 1
    # simpler approach: count only this node + recursive children listed
    return n

def _flatten(node: dict, path: str = "") -> list[dict]:
    """Yield (path, node) for every node in tree."""
    here = f"{path}/{node['tag']}"
    name = node.get("name") or ""
    if name:
        here = f"{here}[{name}]"
    out = [{"path": here, "node": node}]
    for c in node.get("children", []) or []:
        out.extend(_flatten(c, here))
    return out

def worst_subtrees(detail: dict, k: int = 8) -> list[dict]:
    """Top-K subtrees by 'impact' (1 - score) * (n_gt_children + 1).

    Skips leaves (n_gt_children == 0) — we want subtrees, not single elements.
    """
    if not detail:
        return []
    flat = _flatten(detail)
    scored = []
    for entry in flat:
        n = entry["node"]
        size = (n.get("n_gt_children") or 0) + 1
        if size <= 1:
            continue  # leaf — handled via missing/extra summary
        score = n.get("score", 1.0)
        impact = (1.0 - score) * size
        if impact <= 0:
            continue
        scored.append({
            "path": entry["path"],
            "score": round(score, 4),
            "attr_score": round(n.get("attr_score", 1.0), 4),
            "n_gt_children": n.get("n_gt_children", 0),
            "n_matched": n.get("n_matched", 0),
            "n_extra": n.get("n_extra", 0),
            "children_score": round(n.get("children_score", 1.0), 4),
            "impact": round(impact, 4),
            "missing_child_count": max(0, (n.get("n_gt_children") or 0) - (n.get("n_matched") or 0)),
        })
    scored.sort(key=lambda x: x["impact"], reverse=True)
    return scored[:k]

def per_section(detail: dict) -> dict:
    out = {}
    for c in (detail.get("children") or []):
        out[c["tag"]] = {
            "score": round(c.get("score", 1.0), 4),
            "n_gt_children": c.get("n_gt_children", 0),
            "n_matched": c.get("n_matched", 0),
            "n_extra": c.get("n_extra", 0),
        }
    return out

# ---------- trajectory mining ----------

XML_OUT_RE = re.compile(r"\.xml$", re.I)
RST_RE = re.compile(r"\.rst$", re.I)
GEOS_LIB_PREFIX = "/geos_lib"

def _path_in_args(args: dict | str, key_candidates=("file_path", "path", "pattern")) -> str | None:
    if isinstance(args, str):
        return None
    if not isinstance(args, dict):
        return None
    for k in key_candidates:
        v = args.get(k)
        if isinstance(v, str):
            return v
    return None

def mine_trajectory(events_path: Path, tool_calls_path: Path | None) -> dict:
    """Walk events.jsonl and produce structured features."""
    tools = Counter()
    files_read = []
    files_written = []
    edits = []
    grep_queries = []
    glob_patterns = []
    bash_cmds = []
    read_targets = Counter()
    n_assistant_msgs = 0
    n_thinking_blocks = 0
    n_tool_uses = 0
    n_user_results = 0

    if not events_path.exists():
        return {"error": "events.jsonl missing"}

    with events_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = ev.get("type")
            if etype == "assistant":
                msg = ev.get("message") or {}
                content = msg.get("content") or []
                if isinstance(content, list):
                    has_real = False
                    for blk in content:
                        if not isinstance(blk, dict):
                            continue
                        bt = blk.get("type")
                        if bt == "thinking":
                            n_thinking_blocks += 1
                            has_real = True
                        elif bt == "tool_use":
                            n_tool_uses += 1
                            tname = blk.get("name") or "?"
                            tools[tname] += 1
                            args = blk.get("input") or {}
                            if tname == "Read":
                                p = _path_in_args(args)
                                if p:
                                    files_read.append(p)
                                    read_targets[p] += 1
                            elif tname in ("Write",):
                                p = _path_in_args(args)
                                if p:
                                    files_written.append(p)
                            elif tname == "Edit":
                                p = _path_in_args(args)
                                if p:
                                    edits.append(p)
                            elif tname == "Grep":
                                pat = args.get("pattern") if isinstance(args, dict) else None
                                if isinstance(pat, str):
                                    grep_queries.append(pat)
                            elif tname == "Glob":
                                pat = args.get("pattern") if isinstance(args, dict) else None
                                if isinstance(pat, str):
                                    glob_patterns.append(pat)
                            elif tname == "Bash":
                                cmd = args.get("command") if isinstance(args, dict) else None
                                if isinstance(cmd, str):
                                    bash_cmds.append(cmd[:200])
                            has_real = True
                        elif bt == "text":
                            has_real = True
                    if has_real:
                        n_assistant_msgs += 1
            elif etype == "user":
                n_user_results += 1

    edit_churn = Counter(edits)
    most_edited = edit_churn.most_common(3)
    re_reads = sum(1 for _, c in read_targets.items() if c >= 2)
    geos_lib_reads = sum(1 for p in files_read if p.startswith(GEOS_LIB_PREFIX))
    rst_reads = sum(1 for p in files_read if RST_RE.search(p))
    xml_lib_reads = sum(1 for p in files_read if p.startswith(GEOS_LIB_PREFIX) and XML_OUT_RE.search(p))
    output_xml_writes = [p for p in files_written if XML_OUT_RE.search(p)]
    output_xml_edits = [p for p in edits if XML_OUT_RE.search(p)]

    # detect xmllint usage in bash
    xmllint_calls = sum(1 for c in bash_cmds if "xmllint" in c)
    geos_run_calls = sum(1 for c in bash_cmds if "geosx" in c.lower() or "geos " in c.lower())

    feats = {
        "n_assistant_msgs": n_assistant_msgs,
        "n_thinking_blocks": n_thinking_blocks,
        "n_tool_uses": n_tool_uses,
        "n_user_results": n_user_results,
        "tool_counts": dict(tools),
        "n_unique_files_read": len(read_targets),
        "n_re_read_files": re_reads,
        "geos_lib_reads": geos_lib_reads,
        "rst_reads": rst_reads,
        "xml_lib_reads": xml_lib_reads,
        "n_output_xml_writes": len(output_xml_writes),
        "n_output_xml_edits": len(output_xml_edits),
        "most_edited": [{"file": f, "count": c} for f, c in most_edited],
        "xmllint_calls": xmllint_calls,
        "geos_run_calls": geos_run_calls,
        "top_grep_queries": [q for q, _ in Counter(grep_queries).most_common(8)],
        "top_glob_patterns": [q for q, _ in Counter(glob_patterns).most_common(8)],
        "n_grep": len(grep_queries),
        "n_glob": len(glob_patterns),
    }
    if tool_calls_path and tool_calls_path.exists():
        try:
            tc = json.loads(tool_calls_path.read_text())
            feats["tool_calls_json"] = {
                "total": tc.get("total_tool_calls"),
                "primer_read": tc.get("primer_read"),
                "rag_tool_calls": tc.get("rag_tool_calls"),
            }
        except Exception:
            pass
    return feats

def trajectory_excerpt(events_path: Path, n_tail_turns: int = 8) -> list[dict]:
    """Last few assistant messages — compact form (tool name + arg summary or text snippet)."""
    if not events_path.exists():
        return []
    msgs: list[dict] = []
    with events_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "assistant":
                continue
            msg = ev.get("message") or {}
            content = msg.get("content") or []
            blocks = []
            for blk in content if isinstance(content, list) else []:
                if not isinstance(blk, dict):
                    continue
                t = blk.get("type")
                if t == "text":
                    txt = (blk.get("text") or "")[:300]
                    if txt.strip():
                        blocks.append({"text": txt})
                elif t == "tool_use":
                    args = blk.get("input") or {}
                    summary = ""
                    if isinstance(args, dict):
                        for k in ("file_path", "pattern", "command", "path"):
                            if k in args and isinstance(args[k], str):
                                summary = args[k][:200]
                                break
                    blocks.append({"tool": blk.get("name"), "summary": summary})
                elif t == "thinking":
                    txt = (blk.get("thinking") or "")[:200]
                    if txt.strip():
                        blocks.append({"thinking": txt})
            if blocks:
                msgs.append({"blocks": blocks})
    return msgs[-n_tail_turns:]

# ---------- driver ----------

def diagnostic_for_task(traj_root: Path, eval_root: Path, agent: str, run: str, task: str) -> dict | None:
    eval_path = eval_root / run / agent / f"{task}_eval.json"
    run_dir = traj_root / agent / run / task
    if not eval_path.exists():
        return {"task": task, "agent": agent, "run": run, "error": f"no eval file at {eval_path}"}
    try:
        ev = json.loads(eval_path.read_text())
    except Exception as e:
        return {"task": task, "agent": agent, "run": run, "error": f"eval read: {e}"}
    detail = ev.get("treesim_detail") or {}
    gt_types = ev.get("gt_element_types") or {}
    gen_types = ev.get("gen_element_types") or {}
    missing = sorted(set(gt_types) - set(gen_types))
    extra = sorted(set(gen_types) - set(gt_types))
    feats = mine_trajectory(run_dir / "events.jsonl", run_dir / "tool_calls.json")
    excerpt = trajectory_excerpt(run_dir / "events.jsonl", n_tail_turns=10)
    return {
        "task": task,
        "agent": agent,
        "run": run,
        "treesim": ev.get("treesim"),
        "overall_01": ev.get("overall_01"),
        "section_scores": per_section(detail),
        "worst_subtrees": worst_subtrees(detail, k=8),
        "missing_element_types": missing,
        "extra_element_types": extra,
        "gt_section_count": len(detail.get("children") or []),
        "gen_n_extra_top": detail.get("n_extra", 0),
        "trajectory": feats,
        "trajectory_excerpt": excerpt,
        "status": ev.get("status"),
    }

def discover_tasks(eval_root: Path, agent: str, run: str) -> list[str]:
    eval_dir = eval_root / run / agent
    if not eval_dir.exists():
        return []
    tasks = []
    for p in eval_dir.glob("*_eval.json"):
        tasks.append(p.stem.replace("_eval", ""))
    return sorted(tasks)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj-root", required=True, help="e.g. /data/.../autocamp_2026-05-01/dsv4 (contains <agent>/<run>/<task>/)")
    ap.add_argument("--eval-root", required=True, help="e.g. /data/.../autocamp_2026-05-01/_results (contains <run>/<agent>/<task>_eval.json)")
    ap.add_argument("--agent", action="append", required=True, help="agent name; repeat for multiple")
    ap.add_argument("--run", action="append", required=True, help="run name (e.g. autocamp_F0_s1); repeat")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    traj_root = Path(args.traj_root)
    eval_root = Path(args.eval_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    n_written = 0
    for agent in args.agent:
        for run in args.run:
            tasks = discover_tasks(eval_root, agent, run)
            if not tasks:
                print(f"[skip] no tasks for {agent}/{run}")
                continue
            for task in tasks:
                diag = diagnostic_for_task(traj_root, eval_root, agent, run, task)
                if diag is None:
                    continue
                fname = f"{agent}__{run}__{task}.json"
                (out / fname).write_text(json.dumps(diag, indent=2))
                n_written += 1
            print(f"[ok] {agent}/{run}: {len(tasks)} tasks")
    print(f"wrote {n_written} diagnostic files to {out}")

if __name__ == "__main__":
    main()

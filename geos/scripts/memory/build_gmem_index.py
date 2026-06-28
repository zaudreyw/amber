#!/usr/bin/env python3
"""Build a frozen 'G-Memory-lite' index from train trajectories.

For each train task, extract:
- task_id, task instructions summary, final TreeSim score
- Reference XML files the agent Read from /geos_lib (the ones that
  actually informed the agent's writing)
- RAG queries that returned helpful results (the ones followed by
  productive Reads)
- Key notes about what solver/physics family this task represents

Writes a JSON index that an MCP tool (memory_mcp.py) can serve at
eval time. No LLM calls — pure extraction from trajectories.

Usage:
  python scripts/memory/build_gmem_index.py \
      --split misc/memory_split.json \
      --run-dir /data/shared/.../repo3_eval_run4 \
      --scored-dir /data/shared/.../results/repo3_eval_run4/claude_code_repo3_plugin \
      --experiments-dir /data/shared/.../experiments \
      --out plugin/memory_index.json
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from collections import Counter


def extract_task_entry(task_id: str, events_path: Path, eval_path: Path, instructions_path: Path) -> dict:
    entry = {
        "task_id": task_id,
        "instructions_excerpt": "",
        "final_treesim": None,
        "reference_xmls": [],
        "written_xmls": [],
        "productive_rag_queries": [],
        "topic_keywords": [],
        "section_strengths": {},
    }

    if instructions_path.exists():
        inst = instructions_path.read_text()
        # Keep first ~400 chars as excerpt
        entry["instructions_excerpt"] = inst[:400].strip()

    if eval_path.exists():
        evj = json.loads(eval_path.read_text())
        entry["final_treesim"] = evj.get("treesim")
        sections = evj.get("treesim_section_scores", {})
        if sections:
            # Top 3 strongest sections (where agent got it right)
            entry["section_strengths"] = {
                k: round(v, 3) for k, v in sorted(sections.items(), key=lambda x: -x[1])[:3]
            }

    if not events_path.exists():
        return entry

    ref_xmls: list[str] = []
    written_xmls: list[str] = []
    rag_queries: list[tuple[str, str]] = []  # (tool, query)
    for raw in events_path.read_text().splitlines():
        if not raw.strip():
            continue
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if d.get("type") != "assistant":
            continue
        for block in d.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            inp = block.get("input", {}) or {}
            if "mcp__geos-rag" in name:
                q = inp.get("query", "") or inp.get("question", "")
                if q:
                    rag_queries.append((name.split("__")[-1], q))
            elif name == "Read":
                fp = inp.get("file_path", "")
                if fp.startswith("/geos_lib/") and fp.endswith(".xml"):
                    ref_xmls.append(fp)
            elif name in ("Write", "Edit"):
                fp = inp.get("file_path", "")
                if fp.startswith("/workspace/inputs/") and fp.endswith(".xml"):
                    written_xmls.append(fp)

    # Deduplicate, preserve order
    entry["reference_xmls"] = list(dict.fromkeys(ref_xmls))[:10]
    entry["written_xmls"] = list(dict.fromkeys(written_xmls))[:5]
    entry["productive_rag_queries"] = [q for _, q in rag_queries][:8]

    # Topic keywords: extract from task_id + instructions by camelCase + space splits
    text = (task_id + " " + entry["instructions_excerpt"]).lower()
    # split camelcase: insert space before uppercase
    words = re.findall(r"[a-z]+", re.sub(r"([A-Z])", r" \1", task_id + " " + entry["instructions_excerpt"]).lower())
    stop = set("a an and are as at be by for from has have in into is it its of on or that the to was were will with this these those we you your if not".split())
    words = [w for w in words if len(w) > 3 and w not in stop]
    counter = Counter(words)
    entry["topic_keywords"] = [w for w, _ in counter.most_common(12)]

    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--scored-dir", type=Path, required=True)
    ap.add_argument("--experiments-dir", type=Path, required=True,
                    help="Directory with task subdirs containing instructions.txt")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    split = json.loads(args.split.read_text())
    train = split["train"]

    entries = []
    for tid in train:
        e = extract_task_entry(
            tid,
            events_path=args.run_dir / tid / "events.jsonl",
            eval_path=args.scored_dir / f"{tid}_eval.json",
            instructions_path=args.experiments_dir / tid / "instructions.txt",
        )
        entries.append(e)
        print(f"{tid}: treesim={e['final_treesim']}, ref_xmls={len(e['reference_xmls'])}, rag_queries={len(e['productive_rag_queries'])}, keywords={e['topic_keywords'][:5]}")

    out = {
        "schema_version": 1,
        "generated_from": str(args.run_dir),
        "n_tasks": len(entries),
        "tasks": entries,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {len(entries)} entries to {args.out}")


if __name__ == "__main__":
    main()

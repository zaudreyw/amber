#!/usr/bin/env python3
"""MemP-style procedural memory build for GEOS XML authoring.

Adapted from MemP (Fang et al. 2025) "direct" build policy:
- For each train task, prompt gemini-3-flash-preview with the task
  query + trajectory → produce a "workflow" paragraph (procedural
  memory entry).
- Compute embedding of task description via qwen3-embedding-8b.
- Save library at misc/memory_artifacts/memp_dsv4/library.json.

Usage:
    python scripts/memory/distiller_memp.py
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path("/home/matt/sci/repo3")
ENV_PATH = REPO_ROOT / ".env"
SPLIT_PATH = REPO_ROOT / "misc" / "memory_split.json"
HARVEST_RUN_DIR = Path(
    "/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/"
    "abl_c2_min_sr_no_rag/harvest_c2_dsv4_s1"
)
EXPERIMENTS_DIR = Path(
    "/data/shared/geophysics_agent_data/data/eval/experiments_test36_template"
)
OUT_DIR = REPO_ROOT / "misc" / "memory_artifacts" / "memp_dsv4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"
DISTILL_MODEL = "google/gemini-3-flash-preview"
EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"


def _load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("OPENROUTER_API_KEY not found in env or .env")


def _load_task_instructions(task_id: str) -> str:
    instr_path = EXPERIMENTS_DIR / task_id / "instructions.txt"
    return instr_path.read_text() if instr_path.exists() else ""


def _load_trajectory_summary(task_id: str) -> str:
    """Compact trajectory: agent thinking + tool calls + outcomes.

    The full events.jsonl is large (~300 KB). For distillation we want
    a focused summary. Pull all assistant tool_use calls + their
    immediate effects.
    """
    ev_path = HARVEST_RUN_DIR / task_id / "events.jsonl"
    if not ev_path.exists():
        return ""
    chunks = []
    n_steps = 0
    with ev_path.open() as f:
        for line in f:
            try:
                ev = json.loads(line.strip())
            except Exception:
                continue
            if ev.get("type") != "assistant":
                continue
            content = (ev.get("message") or {}).get("content") or []
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "thinking":
                    txt = (c.get("thinking") or "")[:400]
                    if txt.strip():
                        chunks.append(f"THINK: {txt}")
                elif c.get("type") == "tool_use":
                    name = c.get("name", "?")
                    inp = c.get("input") or {}
                    if name == "Read":
                        chunks.append(f"READ: {inp.get('file_path','')}")
                    elif name == "Glob":
                        chunks.append(f"GLOB: {inp.get('pattern','')}")
                    elif name == "Grep":
                        chunks.append(f"GREP: {inp.get('pattern','')[:80]}")
                    elif name == "Bash":
                        cmd = (inp.get("command") or "")[:120]
                        chunks.append(f"BASH: {cmd}")
                    elif name == "Write":
                        fp = inp.get("file_path", "")
                        chunks.append(f"WRITE: {fp}")
                    elif name == "Edit":
                        fp = inp.get("file_path", "")
                        chunks.append(f"EDIT: {fp}")
                    elif name.startswith("mcp__"):
                        q = inp.get("query") or inp.get("xml_path") or ""
                        chunks.append(f"{name}: {q[:80]}")
                    n_steps += 1
            if n_steps > 80:
                break
    return "\n".join(chunks[:200])


WORKFLOW_PROMPT_TEMPLATE = """You are provided with a query and a trajectory taken to solve the query. The trajectory shows a coding agent (Claude Code) authoring GEOS XML input deck files for a multiphysics simulator.

Your task is to generate a WORKFLOW paragraph based on the critical steps to help solve similar GEOS XML authoring queries in the future. A critical step is one whose action contributed positively to producing valid, structurally correct XML — file discovery (Glob, Grep, Bash find), reading reference XMLs (Read), and writing final XMLs (Write).

Write the workflow as a natural, coherent paragraph (NOT a bullet list or numbered steps). Use clear concise language to describe what actions should be taken and in what general order. Focus on:
- WHICH reference XML files were the most useful starting point (without naming specific GT filenames — use physics-class descriptions like "wellbore stress problem" or "poromechanics consolidation").
- WHICH GEOS solver / constitutive elements were chosen and why.
- HOW to handle special features of this task class (e.g., multi-variant tutorials require multiple base XMLs, hydrofracture needs SurfaceGenerator, wellbore needs InternalWellbore mesh).
- COMMON PITFALLS to avoid (e.g., schema-hallucinated element names, missing variant files).

DO NOT include any GT filenames (e.g. PoroElastic_Mandel_base.xml). Use generic descriptions ("the base XML for poroelastic Mandel-type consolidation").
DO NOT include raw XML.
Output the workflow paragraph, 100-200 words. No preamble.

Query:
{query}

Trajectory (compacted):
{trajectory}
"""


def distill_workflow(query: str, trajectory: str, api_key: str) -> str:
    prompt = WORKFLOW_PROMPT_TEMPLATE.format(query=query[:3000], trajectory=trajectory[:6000])
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": DISTILL_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert GEOS multiphysics simulation engineer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 800,
    }
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=180)
            r.raise_for_status()
            d = r.json()
            return d["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  [warn attempt {attempt+1}] distill error: {e}", file=sys.stderr)
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def get_embedding(text: str, api_key: str) -> list[float]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {"model": EMBEDDING_MODEL, "input": text[:8000]}
    for attempt in range(3):
        try:
            r = requests.post(EMBEDDING_URL, headers=headers, json=body, timeout=120)
            r.raise_for_status()
            d = r.json()
            return d["data"][0]["embedding"]
        except Exception as e:
            print(f"  [warn attempt {attempt+1}] embed error: {e}", file=sys.stderr)
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


# Hygiene: strip GT filenames from distilled workflows
XML_FILENAME_RE = re.compile(r"\b([A-Za-z0-9_][A-Za-z0-9_\-]*\.xml)\b", flags=re.IGNORECASE)


def main():
    api_key = _load_api_key()
    split = json.loads(SPLIT_PATH.read_text())
    train_tasks = split["train"]
    print(f"distilling MemP workflows for {len(train_tasks)} train tasks → {OUT_DIR}/library.json")

    # Cumulative library (resume if exists)
    library_path = OUT_DIR / "library.json"
    library = {}
    if library_path.exists():
        existing = json.loads(library_path.read_text())
        library = {e["task_id"]: e for e in existing}
        print(f"  resume: {len(library)} entries already done")

    for i, task_id in enumerate(train_tasks):
        if task_id in library:
            print(f"[{i+1}/{len(train_tasks)}] SKIP (cached): {task_id}")
            continue
        print(f"[{i+1}/{len(train_tasks)}] distilling: {task_id}")
        query = _load_task_instructions(task_id)
        trajectory = _load_trajectory_summary(task_id)
        if not query or not trajectory:
            print(f"  WARN: missing query or trajectory for {task_id}")
            continue
        try:
            workflow = distill_workflow(query, trajectory, api_key)
            # Strip stray .xml filename mentions
            stripped = XML_FILENAME_RE.sub("<file>", workflow)
            n_stripped = len(XML_FILENAME_RE.findall(workflow))
            if n_stripped > 0:
                print(f"  hygiene: stripped {n_stripped} .xml filename mentions")
            embedding = get_embedding(query, api_key)
            library[task_id] = {
                "task_id": task_id,
                "query": query[:1500],
                "query_full_len": len(query),
                "workflow": stripped,
                "embedding": embedding,
                "embedding_dim": len(embedding),
                "n_stripped_xml_filenames": n_stripped,
            }
            # Save incrementally
            library_path.write_text(json.dumps(list(library.values()), indent=2))
        except Exception as e:
            print(f"  FAIL {task_id}: {e}")
            continue
    print(f"\nDONE. Library at {library_path} with {len(library)} entries.")


if __name__ == "__main__":
    main()

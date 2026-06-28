#!/usr/bin/env python3
"""Render per-test-task MemP primers via cosine retrieval.

For each of 17 v2 test tasks:
1. Compute embedding of task instructions.
2. Cosine-sim against the 18-entry train library.
3. Take top-K most similar; concatenate their workflows into a
   per-task primer file.

Output: plugin/memp_per_task/<task>.md  (17 files)

Usage:
    python scripts/memory/render_memp_per_task.py --top-k 3
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sys
from pathlib import Path

import requests

REPO_ROOT = Path("/home/matt/sci/repo3")
ENV_PATH = REPO_ROOT / ".env"
SPLIT_PATH = REPO_ROOT / "misc" / "memory_split.json"
LIBRARY_PATH = REPO_ROOT / "misc" / "memory_artifacts" / "memp_dsv4" / "library.json"
EXPERIMENTS_DIR = Path(
    "/data/shared/geophysics_agent_data/data/eval/experiments_test36_template"
)
OUT_DIR = REPO_ROOT / "plugin" / "memp_per_task"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"
EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"


def _load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("OPENROUTER_API_KEY not found")


def get_embedding(text: str, api_key: str) -> list[float]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": EMBEDDING_MODEL, "input": text[:8000]}
    r = requests.post(EMBEDDING_URL, headers=headers, json=body, timeout=120)
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


PRIMER_TEMPLATE = """## Procedural memory (retrieved by similarity)

Below are workflow notes from past similar GEOS XML authoring tasks. They are *guidance*, not commands — adapt to the current task. Top {k} most similar past tasks (cosine similarity in parentheses):

{entries}

---
"""

ENTRY_TEMPLATE = """### Past task: {task_id} (sim {sim:.3f})

{workflow}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    api_key = _load_api_key()
    library = json.loads(LIBRARY_PATH.read_text())
    print(f"loaded library with {len(library)} train entries")

    split = json.loads(SPLIT_PATH.read_text())
    test_tasks = split["test"]

    sim_summary = []
    for task_id in test_tasks:
        instr = (EXPERIMENTS_DIR / task_id / "instructions.txt").read_text()
        emb = get_embedding(instr, api_key)
        scored = []
        for entry in library:
            s = cosine(emb, entry["embedding"])
            scored.append((s, entry))
        scored.sort(key=lambda x: -x[0])
        top = scored[: args.top_k]
        # Render
        entries_text = "\n\n".join(
            ENTRY_TEMPLATE.format(task_id=e["task_id"], sim=s, workflow=e["workflow"])
            for s, e in top
        )
        primer_text = PRIMER_TEMPLATE.format(k=args.top_k, entries=entries_text)
        out_path = OUT_DIR / f"{task_id}.md"
        out_path.write_text(primer_text)
        sim_summary.append((task_id, [(s, e["task_id"]) for s, e in top]))

    # Print summary
    print(f"\n=== Top-{args.top_k} retrievals per test task ===\n")
    for task, top in sim_summary:
        print(f"{task}:")
        for s, t in top:
            print(f"  {s:.3f}  {t}")
    print(f"\nWrote {len(test_tasks)} per-task primers to {OUT_DIR}/")


if __name__ == "__main__":
    main()

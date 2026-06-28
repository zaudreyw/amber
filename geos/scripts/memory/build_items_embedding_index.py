#!/usr/bin/env python3
"""Pre-compute embeddings for memory items served by memory_mcp_embed.

Builds a JSON embedding index parallel to a reasoning-memory items JSON:

    [{"idx": 0, "embedding": [...]}, {"idx": 1, "embedding": [...]}, ...]

Each item's embedding is computed over a concatenation of its `title`,
`description`, `applies_when`, and `content` fields (the fields most
likely to semantically match a query).

Uses OpenRouter → `qwen/qwen3-embedding-8b` (matches geos-rag MCP config).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests


DEFAULT_API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_EMBED_MODEL = "qwen/qwen3-embedding-8b"
ENV_PATH = Path("/home/matt/sci/repo3/.env")


def _load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.strip().startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"\'')
    print("ERROR: no OPENROUTER_API_KEY", file=sys.stderr)
    sys.exit(1)


def _embed(text: str, *, api_key: str, model: str, base: str, retries: int = 2) -> list[float]:
    for attempt in range(retries + 1):
        resp = requests.post(
            f"{base}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": text},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["data"][0]["embedding"]
        print(f"  embed retry {attempt}: {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        time.sleep(2 ** attempt)
    raise RuntimeError(f"embed failed after {retries+1} attempts")


def _item_to_text(item: dict) -> str:
    parts = [
        item.get("title", ""),
        item.get("description", ""),
        item.get("applies_when", ""),
        item.get("content", ""),
    ]
    return "\n".join(p for p in parts if p)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--items", required=True, type=Path,
                   help="Path to memory items JSON (list of dicts)")
    p.add_argument("--out", required=True, type=Path,
                   help="Where to write the embedding index JSON")
    p.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    p.add_argument("--base", default=DEFAULT_API_BASE)
    args = p.parse_args(argv)

    items = json.loads(args.items.read_text())
    if not isinstance(items, list):
        print("ERROR: items is not a list", file=sys.stderr)
        return 2

    api_key = _load_api_key()
    index: list[dict] = []
    for i, item in enumerate(items):
        text = _item_to_text(item)
        if not text:
            print(f"  WARN: item {i} empty, skipping")
            continue
        emb = _embed(text, api_key=api_key, model=args.model, base=args.base)
        index.append({"idx": i, "embedding": emb})
        print(f"  [{i+1}/{len(items)}] dim={len(emb)} title={item.get('title','')[:50]}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(index))
    print(f"wrote embedding index: {args.out} ({len(index)} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

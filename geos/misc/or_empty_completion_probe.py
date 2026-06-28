#!/usr/bin/env python3
"""Minimal OpenRouter reproducer for the minimax empty-completion failure.

Replays the exact message shape from an observed E17 failure (an assistant
message containing `thinking` + 3 `tool_use` blocks, followed by 3 tool_result
user messages), asks for a 4th-turn completion, and counts how often the
response is empty (content=[] or empty string).

If E20 shows that neither the hook (C1) nor the noop MCP (C2) rescues the
failure, this tells us whether the empty completion is deterministic
(OpenRouter adapter bug) or stochastic (model-side noise).

Prereqs: OPENROUTER_API_KEY in env. Read-only; no side effects beyond
HTTP + prints.

Usage:
    uv run python misc/or_empty_completion_probe.py --n 20 \
        --sample-from data/eval/claude_code_repo3_plugin/plug_mm_v2_seed2/ExampleThermalLeakyWell
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import urllib.request
import urllib.error


def load_sample_trajectory(task_dir: Path) -> list[dict]:
    """Turn an events.jsonl into a list of API-shaped {role, content} messages
    up to (but not including) the first tool_result -> next assistant message
    boundary. This is the shape the 4th API turn would have seen in E17."""
    events_path = task_dir / "events.jsonl"
    if not events_path.exists():
        raise FileNotFoundError(f"no events.jsonl in {task_dir}")
    events = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]

    messages: list[dict] = []
    for ev in events:
        t = ev.get("type")
        msg = ev.get("message") or {}
        if t == "system":
            # system event has the initial system prompt; skip (we'll add it from another source)
            continue
        if t not in ("assistant", "user"):
            continue
        # Dedup assistant parts that share a message id — they're all one turn
        if t == "assistant":
            if messages and messages[-1]["role"] == "assistant" and messages[-1].get("_id") == msg.get("id"):
                # Merge contents
                messages[-1]["content"].extend(msg.get("content", []))
            else:
                messages.append({
                    "role": "assistant",
                    "_id": msg.get("id"),
                    "content": list(msg.get("content", [])),
                })
        else:
            messages.append({
                "role": "user",
                "content": list(msg.get("content", [])),
            })
    # Trim trailing tool_use-only assistant (no content/text) if any
    # Drop the _id marker before return
    for m in messages:
        m.pop("_id", None)
    return messages


def call_openrouter(messages: list[dict], model: str, max_tokens: int = 32000) -> dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY (or ANTHROPIC_AUTH_TOKEN) not set")
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/matt-repo3",
            "X-Title": "e20 empty-completion probe",
        },
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        data["_elapsed_s"] = time.time() - started
        return data
    except urllib.error.HTTPError as e:
        return {"_error": f"{e.code} {e.reason}", "_body": e.read()[:500].decode("utf-8", "replace")}


def is_empty_completion(resp: dict) -> bool:
    choices = resp.get("choices", [])
    if not choices:
        return True
    msg = choices[0].get("message", {})
    content = msg.get("content")
    tool_calls = msg.get("tool_calls") or []
    if tool_calls:
        return False
    if content in (None, "", []):
        return True
    if isinstance(content, str) and not content.strip():
        return True
    return False


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=10, help="Number of probes")
    p.add_argument("--model", default="minimax/minimax-m2.7")
    p.add_argument("--sample-from", type=Path, required=True,
                   help="Task dir with events.jsonl to replay")
    p.add_argument("--out", type=Path, default=Path("/tmp/or_probe_results.jsonl"))
    args = p.parse_args()

    try:
        messages = load_sample_trajectory(args.sample_from)
    except Exception as e:
        print(f"ERR loading trajectory: {e}", file=sys.stderr)
        return 1
    print(f"Loaded {len(messages)} messages from {args.sample_from}")

    empty = 0
    with args.out.open("w") as f:
        for i in range(args.n):
            resp = call_openrouter(messages, args.model)
            is_empty = is_empty_completion(resp)
            if is_empty:
                empty += 1
            rec = {
                "i": i,
                "empty": is_empty,
                "elapsed_s": resp.get("_elapsed_s"),
                "usage": resp.get("usage"),
                "error": resp.get("_error"),
            }
            f.write(json.dumps(rec) + "\n")
            print(f"[{i:02d}] empty={is_empty}  elapsed={resp.get('_elapsed_s', 0):.1f}s  "
                  f"tokens={(resp.get('usage') or {}).get('completion_tokens')}")
    print(f"\nEmpty completions: {empty}/{args.n} ({100*empty/args.n:.0f}%)")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Self-evolving agent reflection step.

Reads the most recent round's trajectories + treesim scores, prompts
DSv4-flash (via DeepSeek-direct Anthropic-compat endpoint or via
OpenRouter) to propose updates to the plugin, parses the response,
writes plugin_evolving/v{N+1}/.

Output file format the agent must emit:
    <file path="memory/cheatsheet.md">
    ... markdown body ...
    </file>
    <file path="skills/foo.md">
    ---
    name: foo
    description: ...
    ---
    ... body ...
    </file>
    <file path="agents/bar.md">
    ---
    name: bar
    description: ...
    tools: Read, Glob, Grep, Bash, Write
    ---
    ... system prompt ...
    </file>
    <file path="PRIMER.md">
    ... primer body ...
    </file>

If the agent emits malformed output, we keep the prior version.

Usage:
    python3 scripts/self_evolving/reflect.py --from-version 0
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import requests

REPO_ROOT = Path("/home/matt/sci/repo3")
PLUGIN_BASE = REPO_ROOT / "plugin_evolving"
RESULTS_ROOT = Path("/data/shared/geophysics_agent_data/data/eval/self_evolving_2026-04-30")
ENV_PATH = REPO_ROOT / ".env"

API_URL = "https://api.deepseek.com/anthropic/v1/messages"
MODEL = "deepseek-v4-flash"


def _load_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("DEEPSEEK_API_KEY not found")


def trajectory_summary(events_jsonl: Path, max_chars: int = 2500) -> str:
    """Compact assistant tool-uses into a short summary."""
    if not events_jsonl.exists():
        return ""
    out = []
    with events_jsonl.open() as f:
        for line in f:
            try:
                ev = json.loads(line.strip())
            except Exception:
                continue
            if ev.get("type") != "assistant":
                continue
            content = (ev.get("message") or {}).get("content") or []
            for c in content if isinstance(content, list) else []:
                if not isinstance(c, dict): continue
                if c.get("type") == "tool_use":
                    name = c.get("name", "?")
                    inp = c.get("input") or {}
                    if name == "Read":
                        out.append(f"R: {inp.get('file_path','')}")
                    elif name == "Glob":
                        out.append(f"G: {inp.get('pattern','')[:80]}")
                    elif name == "Grep":
                        out.append(f"GR: {inp.get('pattern','')[:60]}")
                    elif name == "Bash":
                        out.append(f"B: {(inp.get('command') or '')[:80]}")
                    elif name == "Write":
                        out.append(f"W: {inp.get('file_path','')}")
                    else:
                        out.append(f"{name[:30]}: ...")
    s = "\n".join(out)
    return s[:max_chars]


def gather_round(round_n: int, results_root: Path = RESULTS_ROOT) -> list[dict]:
    """Return list of {task, treesim, trajectory_summary} for round N."""
    run_name = f"se_round{round_n}_s1"
    run_dir = results_root / "abl_se_round" / run_name
    eval_dir = results_root / "_results" / run_name / "abl_se_round"
    if not run_dir.exists():
        print(f"WARN: no run dir at {run_dir}", file=sys.stderr)
        return []
    out = []
    for task_dir in sorted(run_dir.iterdir()):
        if not task_dir.is_dir(): continue
        task = task_dir.name
        ts = None
        ej = eval_dir / f"{task}_eval.json"
        if ej.exists():
            try:
                ts = json.loads(ej.read_text()).get("treesim")
            except Exception:
                pass
        out.append({
            "task": task,
            "treesim": ts,
            "trajectory": trajectory_summary(task_dir / "events.jsonl"),
        })
    return out


def render_current_plugin(plugin_dir: Path) -> str:
    """Dump the current plugin's editable contents (PRIMER + memory + skills + agents)."""
    parts = []
    primer = plugin_dir / "PRIMER.md"
    if primer.exists():
        parts.append(f"=== PRIMER.md ===\n{primer.read_text()}")
    for sub, label in [("memory", "MEMORY"), ("skills", "SKILLS"), ("agents", "AGENTS")]:
        d = plugin_dir / sub
        if d.exists():
            for f in sorted(d.glob("*.md")):
                parts.append(f"=== {label}: {sub}/{f.name} ===\n{f.read_text()}")
    return "\n\n".join(parts) or "(empty plugin)"


REFLECTION_PROMPT = """You are improving a Claude Code plugin that authors GEOS multiphysics XML input files.

Your job is to reflect on the most recent round of agent runs (6 tasks below)
and propose an updated plugin that should help the agent do better on similar
tasks in the future.

You may produce ANY of these 4 file types in the new plugin version:

1. **PRIMER.md** — replaces the system primer; brief background on GEOS XML.
   Keep ≤80 lines. Avoid GT XML filenames (use generic descriptions).

2. **memory/cheatsheet.md** — free-form lessons / patterns / pitfalls observed.
   Keep ≤300 lines total across all memory files.

3. **skills/<name>.md** — reusable procedural notes. Format:
   ```
   ---
   name: skill-name
   description: one-line summary
   ---
   ## Detailed instructions...
   ```
   Skills can be invoked by the agent (when CC is configured to surface them).

4. **agents/<name>.md** — subagent definition. Format:
   ```
   ---
   name: subagent-name
   description: when to invoke this subagent
   tools: Read, Glob, Grep, Bash, Write
   ---
   ## System prompt for the subagent...
   ```
   Subagents can be delegated to via Agent(subagent_type="<name>").

OUTPUT FORMAT — emit one or more <file>...</file> blocks:

<file path="PRIMER.md">
... primer content ...
</file>
<file path="memory/cheatsheet.md">
... cheatsheet content ...
</file>

CONSTRAINTS:
- Be conservative: only add content that addresses concrete failures or
  inefficiencies you observe in the recent trajectories.
- DO NOT include any GT XML filenames (e.g. "PoroElastic_Mandel_base.xml").
  Use generic physics-class descriptions.
- DO NOT include raw XML — describe shapes and patterns instead.
- If the current plugin is already working well (≥0.85 mean treesim),
  it's fine to make small additions or no changes (emit nothing or
  only PRIMER.md).

CURRENT PLUGIN (version v{ROUND}):

{CURRENT_PLUGIN}

RECENT ROUND RESULTS (mean treesim {MEAN_TS:.4f}, n={N}):

{ROUND_RESULTS}

Now propose updates for plugin v{NEXT_ROUND}. Emit only <file> blocks.
"""


FILE_BLOCK_RE = re.compile(r'<file path="([^"]+)">\s*(.*?)\s*</file>', re.DOTALL)


def call_dsv4(prompt: str, api_key: str, max_tokens: int = 4000) -> str:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(API_URL, headers=headers, json=body, timeout=300)
    r.raise_for_status()
    d = r.json()
    return "".join(c.get("text", "") for c in d.get("content", []))


def write_proposed_files(out_dir: Path, file_blocks: list[tuple[str, str]]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for rel_path, body in file_blocks:
        # Hygiene: reject path traversal
        if ".." in rel_path or rel_path.startswith("/"):
            print(f"  REJECT path traversal: {rel_path}")
            continue
        # Hygiene: only allowed paths
        allowed = (rel_path == "PRIMER.md"
                   or rel_path.startswith("memory/")
                   or rel_path.startswith("skills/")
                   or rel_path.startswith("agents/"))
        if not allowed:
            print(f"  REJECT disallowed path: {rel_path}")
            continue
        # Hygiene: strip GT XML mentions
        body_clean = re.sub(r"\b([a-z0-9_][a-z0-9_\-]*\.xml)\b", "<file>", body, flags=re.IGNORECASE)
        n_stripped = len(re.findall(r"\b([a-z0-9_][a-z0-9_\-]*\.xml)\b", body, flags=re.IGNORECASE))
        target = out_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body_clean.strip() + "\n")
        written.append({"path": rel_path, "bytes": len(body_clean), "stripped_xml_filenames": n_stripped})
    return {"written": written}


def copy_scaffolding(src: Path, dst: Path):
    """Copy hooks/, scripts/, .claude-plugin/ from src to dst (the
    parts that are scaffolding, not agent-editable content)."""
    for sub in ("hooks", "scripts", ".claude-plugin"):
        s = src / sub
        if s.exists():
            shutil.copytree(s, dst / sub, dirs_exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-version", type=int, required=True,
                    help="N: reflect on round N, produce v{N+1}")
    args = ap.parse_args()

    api_key = _load_api_key()
    n = args.from_version
    next_n = n + 1

    src_plugin = PLUGIN_BASE / f"v{n}"
    dst_plugin = PLUGIN_BASE / f"v{next_n}"
    if not src_plugin.exists():
        print(f"ERROR: source plugin missing: {src_plugin}", file=sys.stderr)
        sys.exit(2)
    if dst_plugin.exists():
        print(f"WARN: destination already exists: {dst_plugin}", file=sys.stderr)

    # Always start dst by copying scaffolding from src
    dst_plugin.mkdir(parents=True, exist_ok=True)
    copy_scaffolding(src_plugin, dst_plugin)
    # Also seed editable subdirs by copying from src (agent only OVERRIDES files)
    for sub in ("memory", "skills", "agents"):
        s = src_plugin / sub
        d = dst_plugin / sub
        if s.exists():
            shutil.copytree(s, d, dirs_exist_ok=True)
    # Default PRIMER inheritance
    src_primer = src_plugin / "PRIMER.md"
    if src_primer.exists():
        shutil.copy2(src_primer, dst_plugin / "PRIMER.md")

    round_results = gather_round(n)
    if not round_results:
        print(f"WARN: no round results for v{n}; emitting empty inheritance", file=sys.stderr)
        log_path = RESULTS_ROOT / "version_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            f.write(json.dumps({
                "version": next_n, "parent": n,
                "timestamp": datetime.now().isoformat(),
                "summary": "no round results; inherited from parent",
            }) + "\n")
        return

    treesims = [r["treesim"] for r in round_results if r["treesim"] is not None]
    mean_ts = sum(treesims) / len(treesims) if treesims else 0
    def _ts_str(t):
        return f"{t:.3f}" if t is not None else "N/A"
    round_summary = "\n\n".join(
        f"--- {r['task']} (treesim {_ts_str(r['treesim'])}) ---\n{r['trajectory']}"
        for r in round_results
    )

    prompt = REFLECTION_PROMPT.format(
        ROUND=n, NEXT_ROUND=next_n,
        CURRENT_PLUGIN=render_current_plugin(src_plugin),
        ROUND_RESULTS=round_summary,
        MEAN_TS=mean_ts, N=len(round_results),
    )

    print(f"[*] reflecting v{n} -> v{next_n}, mean_ts={mean_ts:.4f}")
    print(f"    prompt size = {len(prompt)} chars")
    response = call_dsv4(prompt, api_key)
    print(f"    response size = {len(response)} chars")

    blocks = FILE_BLOCK_RE.findall(response)
    if not blocks:
        print(f"  WARN: no <file> blocks parsed; v{next_n} = inherited from v{n}")
        result = {"written": []}
    else:
        result = write_proposed_files(dst_plugin, blocks)
        print(f"  wrote {len(result['written'])} files into v{next_n}")

    # Save reflection metadata
    (dst_plugin / ".reflection_meta.json").write_text(json.dumps({
        "version": next_n, "parent": n,
        "timestamp": datetime.now().isoformat(),
        "round_mean_treesim": mean_ts,
        "round_n_tasks": len(round_results),
        "files_proposed": [b[0] for b in blocks],
        **result,
    }, indent=2))

    log_path = RESULTS_ROOT / "version_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps({
            "version": next_n, "parent": n,
            "timestamp": datetime.now().isoformat(),
            "round_mean_treesim": mean_ts,
            "files_written": [w["path"] for w in result.get("written", [])],
        }) + "\n")
    print(f"[*] done. v{next_n} at {dst_plugin}")


if __name__ == "__main__":
    main()

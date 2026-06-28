#!/usr/bin/env python3
"""Standalone runner for the GEOS sub-agent orchestrator.

Parallel to src/runner.cli — does NOT modify src/runner/* (constraint:
concurrent OpenHands run uses src/runner). Imports read-only utilities
from src/runner for filtered-GEOS, blocklist, and prompt building.

The orchestrator agent and its 5 worker subagents are distributed via
plugin_orchestrator/. The runner mounts:
- plugin_orchestrator/  → /plugins/orchestrator (agents/, primers/, schema_slices/)
- plugin/                → /plugins/repo3       (geos-rag MCP, verify_outputs hook)

Default model: deepseek-v4-flash via the DeepSeek Anthropic-compatible endpoint
at https://api.deepseek.com/anthropic. Fallback to OpenRouter via --model and
--api-base flags.

Usage:
    python -m scripts.orchestrator.run_orchestrator_eval \\
        --run smoke_sneddon \\
        --include TutorialSneddon \\
        --workers 1 --timeout 1500

    # Full 17-task run on DSv4-flash:
    python -m scripts.orchestrator.run_orchestrator_eval \\
        --run orch_dsv4_s1 \\
        --include TutorialSneddon ExampleMandel ... \\
        --workers 2 --timeout 1500
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

# Make sure the runner package is importable. Run from repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Read-only imports from src.runner. We don't mutate any module-level state.
from src.runner.contamination import (  # noqa: E402
    cleanup_filtered_geos_copy,
    create_filtered_geos_copy,
    get_blocked_files_for_task,
)
from src.runner.docker_cmd import create_runtime_vector_db_copy  # noqa: E402
from src.runner.prompts import (  # noqa: E402
    build_task_prompt,
    load_agents_md,
    load_task_instructions,
)


# Constants — explicit so this script is self-contained and the OpenHands
# session's imports are never disturbed.
PLUGIN_ORCHESTRATOR_DIR = REPO_ROOT / "plugin_orchestrator"
PLUGIN_REPO3_DIR = REPO_ROOT / "plugin"
DEFAULT_VECTOR_DB_DIR = Path("/data/shared/geophysics_agent_data/data/vector_db")
DEFAULT_GEOS_LIB_DIR = Path("/data/shared/geophysics_agent_data/data/GEOS")
# /data/shared/.../tmp_geos is not writable for user `matt`; prefer matt-owned dir.
TEMP_GEOS_PARENT = Path("/data/matt/geos_eval_tmp")
DOCKER_IMAGE = "geos-eval"

CONTAINER_PLUGIN_ORCH = Path("/plugins/orchestrator")
CONTAINER_PLUGIN_REPO3 = Path("/plugins/repo3")
CONTAINER_VECTOR_DB_DIR = Path("/data/shared/geophysics_agent_data/data/vector_db")
CONTAINER_MCP_CONFIG_PATH = Path("/workspace/claude_mcp_config.json")
CONTAINER_SETTINGS_PATH = Path("/workspace/claude_settings.json")

DEFAULT_EXPERIMENTS_DIR = Path(
    "/data/shared/geophysics_agent_data/data/eval/experiments_test36_template"
)
DEFAULT_GROUND_TRUTH_DIR = Path(
    "/data/shared/geophysics_agent_data/data/eval/experiments_gt"
)
DEFAULT_RESULTS_ROOT = REPO_ROOT / "data" / "eval"

DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_API_BASE = "https://api.deepseek.com/anthropic"
DEFAULT_TIMEOUT = 1500  # 25 min per task — orchestrator + 5 subagents

# Tools we DENY for both orchestrator and subagents (subagents inherit unless
# their own frontmatter restricts further).
#
# Why we deny `Write` for the orchestrator:
# - The orchestrator's job is to delegate, not author. Allowing Write makes
#   the LLM very tempted to just author XML directly, defeating the purpose.
# - Bootstrap copy is done via Bash `cp` (the orchestrator system prompt
#   instructs this).
# - Splicing into the working file uses `Edit` (requires Read-first), which
#   is the right primitive for whole-block replacement.
# - Subagents are also denied Write in their frontmatter (they return text,
#   not edits to disk).
DISALLOWED_TOOLS = ["Skill", "AskUserQuestion", "Write"]


def write_orchestrator_mcp_config(
    *,
    result_dir: Path,
    blocked_xml_filenames: list[str],
    blocked_rst_relpaths: list[str],
) -> Path:
    """Write the MCP config Claude Code uses inside the container.

    Mirrors src/runner/claude_settings.write_claude_mcp_config but points the
    geos-rag MCP at the orchestrator plugin's copy of the script (or the repo3
    plugin's — they're identical). Either works; we use repo3's so we don't
    duplicate maintenance.
    """
    mcp_path = result_dir / CONTAINER_MCP_CONFIG_PATH.name
    payload = {
        "mcpServers": {
            "geos-rag": {
                "type": "stdio",
                "command": "uv",
                "args": [
                    "run",
                    "--script",
                    str(CONTAINER_PLUGIN_REPO3 / "scripts" / "geos_rag_mcp.py"),
                ],
                "env": {
                    "CLAUDE_PLUGIN_ROOT": str(CONTAINER_PLUGIN_REPO3),
                    "GEOS_VECTOR_DB_DIR": str(CONTAINER_VECTOR_DB_DIR),
                    "EXCLUDED_GT_XML_FILENAMES": json.dumps(blocked_xml_filenames),
                    "EXCLUDED_RST_PATHS": json.dumps(blocked_rst_relpaths),
                },
            },
        },
    }
    mcp_path.parent.mkdir(parents=True, exist_ok=True)
    mcp_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return mcp_path


def write_orchestrator_settings(*, result_dir: Path) -> Path:
    """Write a minimal claude_settings.json with the Stop hook disabled.

    The orchestrator's final-output check is xmllint, run in-band by the main
    thread itself. Using verify_outputs.py is unnecessary and can fight the
    orchestrator's own retry logic (it might fire mid-orchestration before all
    segments are spliced).
    """
    settings: dict[str, Any] = {}
    path = result_dir / CONTAINER_SETTINGS_PATH.name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True))
    return path


def build_command(
    *,
    filtered_geos: Path,
    result_dir: Path,
    vector_db_dir: Path,
    model: str,
    system_prompt: str,
    prompt: str,
) -> list[str]:
    cmd = [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{filtered_geos}:/geos_lib:ro",
        "-v", f"{result_dir}:/workspace:rw",
        "-v", f"{PLUGIN_ORCHESTRATOR_DIR}:{CONTAINER_PLUGIN_ORCH}:ro",
        "-v", f"{PLUGIN_REPO3_DIR}:{CONTAINER_PLUGIN_REPO3}:ro",
        "-v", f"{vector_db_dir}:{CONTAINER_VECTOR_DB_DIR}:rw",
        "-e", "HOME=/workspace/.claude_home",
        "-e", "XDG_CONFIG_HOME=/workspace/.claude_home/.config",
        "-e", "UV_CACHE_DIR=/workspace/.uv_cache",
        "-e", "ANTHROPIC_BASE_URL",
        "-e", "ANTHROPIC_API_KEY",
        "-e", "ANTHROPIC_AUTH_TOKEN",
        "-e", "OPENROUTER_API_KEY",
        "-e", "GEOS_VECTOR_DB_DIR",
        "-e", "EXCLUDED_GT_XML_FILENAMES",
        "-e", "EXCLUDED_RST_PATHS",
        "-e", f"CLAUDE_PLUGIN_ROOT={CONTAINER_PLUGIN_REPO3}",
        DOCKER_IMAGE,
        "claude",
        "-p",
        "--verbose",
        "--model", model,
        "--append-system-prompt", system_prompt,
        "--tools", "default",
    ]
    # P1B fix (RN-005): Claude Code expects a single comma-joined value
    # for --disallowedTools, not multiple repeated flags. The prior
    # multi-flag form was silently ignored, allowing Write to fire in
    # 4/17 tasks of the preliminary XN-018 run.
    cmd += ["--disallowedTools", ",".join(DISALLOWED_TOOLS)]
    cmd += [
        f"--mcp-config={CONTAINER_MCP_CONFIG_PATH}",
        "--strict-mcp-config",
        f"--plugin-dir={CONTAINER_PLUGIN_ORCH}",
        "--settings", str(CONTAINER_SETTINGS_PATH),
        "--output-format", "stream-json",
        "--permission-mode", "bypassPermissions",
        "--",
        prompt,
    ]
    return cmd


def build_env(
    *,
    blocked_xml_filenames: list[str],
    blocked_rst_relpaths: list[str],
    api_base: str,
    api_key: str,
) -> dict[str, str]:
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = api_base
    env["ANTHROPIC_API_KEY"] = api_key
    # Some Claude Code paths look at AUTH_TOKEN; mirror it.
    env["ANTHROPIC_AUTH_TOKEN"] = api_key
    env["GEOS_VECTOR_DB_DIR"] = str(CONTAINER_VECTOR_DB_DIR)
    env["EXCLUDED_GT_XML_FILENAMES"] = json.dumps(blocked_xml_filenames)
    env["EXCLUDED_RST_PATHS"] = json.dumps(blocked_rst_relpaths)
    if not env.get("OPENROUTER_API_KEY"):
        # geos_rag_mcp uses this for embeddings even when the model is DS;
        # fall through to the existing OR token if available.
        env["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_API_KEY", "")
    return env


def build_system_prompt(
    *,
    agents_context: str,
    geos_primer_path: Path,
    orchestrator_workflow_path: Path,
) -> str:
    """Assemble the main thread's system prompt.

    Order:
    1. AGENTS.md baked context (existing GEOS Primer or stripped variant).
    2. The orchestrator workflow (this is what makes this run an orchestrator).
    3. A short tail reminding the agent to use the Agent tool.
    """
    parts = [agents_context.strip()]
    if geos_primer_path.exists() and "# GEOS Primer" not in agents_context:
        parts.append("\n\n---\n# GEOS Primer\n\n" + geos_primer_path.read_text().strip())
    parts.append("\n\n---\n" + orchestrator_workflow_path.read_text().strip())
    parts.append(
        "\n\n---\nReminder: spawn segment subagents via the Agent tool. "
        "Do not author segment XML yourself."
    )
    return "".join(parts)


def run_one_task(
    *,
    task_name: str,
    experiments_dir: Path,
    ground_truth_dir: Path,
    geos_lib_dir: Path,
    tmp_geos_parent: Path,
    vector_db_dir: Path,
    results_dir: Path,
    run_name: str,
    model: str,
    api_base: str,
    api_key: str,
    timeout: int,
    geos_primer_path: Path,
    orchestrator_workflow_path: Path,
    agents_context: str,
    dry_run: bool = False,
) -> dict:
    task_dir = experiments_dir / task_name
    result_dir = results_dir / run_name / task_name
    (result_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (result_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (result_dir / ".claude_home" / ".config").mkdir(parents=True, exist_ok=True)
    (result_dir / ".uv_cache").mkdir(parents=True, exist_ok=True)

    task_instructions = load_task_instructions(task_dir)
    task_prompt = build_task_prompt(task_instructions)

    blocked = get_blocked_files_for_task(
        task_name, ground_truth_dir, geos_source_dir=geos_lib_dir
    )
    blocked_xml = blocked["blocked_xml_filenames"]
    blocked_rst = blocked["blocked_rst_paths"]
    # P1A fix (RN-005): block ALL test-task GT XMLs, not just current task.
    # Otherwise the agent can copy a sibling test-task's GT (e.g.
    # ExampleIsothermalLeakyWell copied thermalLeakyWell_base.xml).
    test_blocklist_path = REPO_ROOT / "misc" / "memory_artifacts" / "test_blocklist.json"
    if test_blocklist_path.exists():
        bl_data = json.loads(test_blocklist_path.read_text())
        union_xml = bl_data.get("union_xml", []) or []
        blocked_xml_set = set(blocked_xml) | {b.lower() for b in union_xml}
        blocked_xml = sorted(blocked_xml_set)
        # Also block all union RST files
        union_rst = bl_data.get("union_rst_relpaths", []) or []
        blocked_rst_set = set(blocked_rst) | set(union_rst)
        blocked_rst = sorted(blocked_rst_set)

    if dry_run:
        filtered = geos_lib_dir
    else:
        filtered = create_filtered_geos_copy(
            geos_lib_dir,
            blocked_xml_basenames=blocked_xml,
            blocked_rst_relpaths=blocked_rst,
            tmp_parent=tmp_geos_parent,
        )

    runtime_vdb = result_dir / ".vector_db_runtime"
    if not dry_run:
        runtime_vdb = create_runtime_vector_db_copy(vector_db_dir, result_dir)

    write_orchestrator_mcp_config(
        result_dir=result_dir,
        blocked_xml_filenames=blocked_xml,
        blocked_rst_relpaths=blocked_rst,
    )
    write_orchestrator_settings(result_dir=result_dir)

    system_prompt = build_system_prompt(
        agents_context=agents_context,
        geos_primer_path=geos_primer_path,
        orchestrator_workflow_path=orchestrator_workflow_path,
    )

    cmd = build_command(
        filtered_geos=filtered,
        result_dir=result_dir,
        vector_db_dir=runtime_vdb,
        model=model,
        system_prompt=system_prompt,
        prompt=task_prompt,
    )
    env = build_env(
        blocked_xml_filenames=blocked_xml,
        blocked_rst_relpaths=blocked_rst,
        api_base=api_base,
        api_key=api_key,
    )

    # Audit metadata
    (result_dir / "eval_metadata.json").write_text(json.dumps({
        "task": task_name,
        "agent": "orchestrator",
        "run_name": run_name,
        "model": model,
        "api_base": api_base,
        "plugin_orchestrator": str(PLUGIN_ORCHESTRATOR_DIR),
        "plugin_repo3": str(PLUGIN_REPO3_DIR),
        "blocked_gt_xml_filenames": blocked_xml,
        "started": datetime.now().isoformat(),
    }, indent=2))

    if dry_run:
        print(f"[DRY] {task_name}: would run cmd len={len(cmd)}")
        return {"task": task_name, "status": "dry_run"}

    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=timeout,
        )
        elapsed = time.time() - started
        (result_dir / "claude_stdout.json").write_text(proc.stdout)
        (result_dir / "stderr.txt").write_text(proc.stderr)
        (result_dir / "exit_code.txt").write_text(str(proc.returncode))
        # Determine final status
        inputs_dir = result_dir / "inputs"
        xmls = list(inputs_dir.glob("*.xml")) if inputs_dir.exists() else []
        if proc.returncode == 0 and xmls:
            status = "success"
        elif proc.returncode == 0 and not xmls:
            status = "failed_no_outputs"
        else:
            status = "failed"
        # P3 fix (RN-005): record started/ended ISO timestamps so
        # campaign-wall doesn't fall back to fs mtimes.
        ended_iso = datetime.now().isoformat()
        started_iso = datetime.fromtimestamp(started).isoformat()
        (result_dir / "status.json").write_text(json.dumps({
            "task": task_name,
            "agent": "orchestrator",
            "run_name": run_name,
            "status": status,
            "exit_code": proc.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "started": started_iso,
            "ended": ended_iso,
            "xml_files": [p.name for p in xmls],
            "updated": ended_iso,
        }, indent=2))
        return {
            "task": task_name,
            "status": status,
            "exit_code": proc.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "xmls": [p.name for p in xmls],
        }
    except subprocess.TimeoutExpired:
        (result_dir / "exit_code.txt").write_text("timeout")
        (result_dir / "status.json").write_text(json.dumps({
            "task": task_name,
            "status": "timeout",
            "elapsed_seconds": timeout,
        }, indent=2))
        return {"task": task_name, "status": "timeout"}
    except Exception as exc:
        (result_dir / "exit_code.txt").write_text("error")
        (result_dir / "stderr.txt").write_text(str(exc))
        (result_dir / "status.json").write_text(json.dumps({
            "task": task_name,
            "status": "error",
            "error": str(exc),
        }, indent=2))
        return {"task": task_name, "status": "error", "error": str(exc)}
    finally:
        if not dry_run:
            cleanup_filtered_geos_copy(filtered)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="Run name subfolder")
    p.add_argument("--include", nargs="+", help="Tasks to run")
    p.add_argument("--exclude", nargs="+", default=[])
    p.add_argument("--experiments-dir", type=Path, default=DEFAULT_EXPERIMENTS_DIR)
    p.add_argument("--ground-truth-dir", type=Path, default=DEFAULT_GROUND_TRUTH_DIR)
    p.add_argument("--geos-lib-dir", type=Path, default=DEFAULT_GEOS_LIB_DIR)
    p.add_argument("--vector-db-dir", type=Path, default=DEFAULT_VECTOR_DB_DIR)
    p.add_argument("--tmp-geos-parent", type=Path, default=TEMP_GEOS_PARENT)
    p.add_argument(
        "--results-root", type=Path, default=DEFAULT_RESULTS_ROOT,
        help="Per-agent result root (default: data/eval). Final path: <root>/orchestrator_<model_short>/<run>/<task>/")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help="Claude Code model. Default: deepseek-v4-flash. "
                        "Fallbacks: minimax/minimax-m2.7 (with --api-base https://openrouter.ai/api), "
                        "deepseek/deepseek-v3.2 (also OpenRouter).")
    p.add_argument("--api-base", default=DEFAULT_API_BASE,
                   help="ANTHROPIC_BASE_URL. Default: DeepSeek direct. "
                        "Use https://openrouter.ai/api for OpenRouter fallback.")
    p.add_argument("--api-key-env", default="DEEPSEEK_API_KEY",
                   help="Env var holding the API key. Default: DEEPSEEK_API_KEY. "
                        "Use OPENROUTER_API_KEY for OpenRouter fallback.")
    p.add_argument("--geos-primer-path", type=Path,
                   default=Path("/home/brianliu/geophys-embodied-agent-framework/modules/profile/GEOS_PRIMER.md"),
                   help="Existing GEOS primer to inline as the foundation context.")
    p.add_argument("--orchestrator-workflow",
                   type=Path, default=PLUGIN_ORCHESTRATOR_DIR / "ORCHESTRATOR_SYSTEM.md")
    p.add_argument("--strip-baked-primer", action="store_true",
                   help="Strip the GEOS Primer from AGENTS.md and inline the external one.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    api_key = os.environ.get(args.api_key_env, "")
    if not api_key and not args.dry_run:
        print(f"ERROR: {args.api_key_env} is empty in env. Export it first.")
        return 1

    # Make a short tag for results dir (e.g. "dsv4flash", "mm27", "dsv32")
    model_short = args.model.replace("/", "_").replace("-", "").replace(".", "")
    if "deepseekv4flash" in model_short:
        agent_subdir = "orchestrator_dsv4flash"
    elif "minimaxm27" in model_short:
        agent_subdir = "orchestrator_mm27"
    elif "deepseekv32" in model_short or "deepseekchatv32" in model_short:
        agent_subdir = "orchestrator_dsv32"
    else:
        agent_subdir = f"orchestrator_{model_short}"
    results_dir = args.results_root / agent_subdir

    # Discover tasks
    if not args.experiments_dir.exists():
        print(f"ERROR: experiments dir missing: {args.experiments_dir}")
        return 1
    all_tasks = sorted(d.name for d in args.experiments_dir.iterdir() if d.is_dir())
    if args.include:
        tasks = [t for t in args.include if t in all_tasks]
    else:
        tasks = all_tasks
    if args.exclude:
        tasks = [t for t in tasks if t not in set(args.exclude)]
    if not tasks:
        print("No tasks selected.")
        return 1

    agents_context = load_agents_md(strip_baked_primer=args.strip_baked_primer)

    print(f"=== orchestrator runner ===")
    print(f"  run_name      : {args.run}")
    print(f"  results_dir   : {results_dir}")
    print(f"  tasks         : {len(tasks)}")
    print(f"  workers       : {args.workers}")
    print(f"  timeout/task  : {args.timeout}")
    print(f"  model         : {args.model}")
    print(f"  api_base      : {args.api_base}")
    print(f"  plugin_orch   : {PLUGIN_ORCHESTRATOR_DIR}")
    print(f"  plugin_repo3  : {PLUGIN_REPO3_DIR}")
    print(f"  primer        : {args.geos_primer_path}")
    print(f"  workflow      : {args.orchestrator_workflow}")
    print(f"  strip_baked   : {args.strip_baked_primer}")
    print(f"  dry_run       : {args.dry_run}")
    print()

    results: list[dict] = []
    if args.workers <= 1:
        for i, task in enumerate(tasks, 1):
            r = run_one_task(
                task_name=task,
                experiments_dir=args.experiments_dir,
                ground_truth_dir=args.ground_truth_dir,
                geos_lib_dir=args.geos_lib_dir.resolve(),
                tmp_geos_parent=args.tmp_geos_parent,
                vector_db_dir=args.vector_db_dir,
                results_dir=results_dir,
                run_name=args.run,
                model=args.model,
                api_base=args.api_base,
                api_key=api_key,
                timeout=args.timeout,
                geos_primer_path=args.geos_primer_path,
                orchestrator_workflow_path=args.orchestrator_workflow,
                agents_context=agents_context,
                dry_run=args.dry_run,
            )
            results.append(r)
            print(f"[{i}/{len(tasks)}] {r.get('status'):<14} {task}  ({r.get('elapsed_seconds','?')}s)")
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            fut_to_task = {
                ex.submit(
                    run_one_task,
                    task_name=task,
                    experiments_dir=args.experiments_dir,
                    ground_truth_dir=args.ground_truth_dir,
                    geos_lib_dir=args.geos_lib_dir.resolve(),
                    tmp_geos_parent=args.tmp_geos_parent,
                    vector_db_dir=args.vector_db_dir,
                    results_dir=results_dir,
                    run_name=args.run,
                    model=args.model,
                    api_base=args.api_base,
                    api_key=api_key,
                    timeout=args.timeout,
                    geos_primer_path=args.geos_primer_path,
                    orchestrator_workflow_path=args.orchestrator_workflow,
                    agents_context=agents_context,
                    dry_run=args.dry_run,
                ): task for task in tasks
            }
            for i, f in enumerate(as_completed(fut_to_task), 1):
                r = f.result()
                results.append(r)
                task = fut_to_task[f]
                print(f"[{i}/{len(tasks)}] {r.get('status'):<14} {task}  ({r.get('elapsed_seconds','?')}s)")

    summary = {
        "run": args.run,
        "model": args.model,
        "api_base": args.api_base,
        "n_tasks": len(tasks),
        "n_success": sum(1 for r in results if r.get("status") == "success"),
        "n_failed_no_outputs": sum(1 for r in results if r.get("status") == "failed_no_outputs"),
        "n_failed": sum(1 for r in results if r.get("status") == "failed"),
        "n_timeout": sum(1 for r in results if r.get("status") == "timeout"),
        "n_error": sum(1 for r in results if r.get("status") == "error"),
        "results": results,
    }
    summary_path = results_dir / args.run / "_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\nSummary written to: {summary_path}")
    print(f"  success={summary['n_success']}/{summary['n_tasks']}, "
          f"no_outputs={summary['n_failed_no_outputs']}, failed={summary['n_failed']}, "
          f"timeout={summary['n_timeout']}, error={summary['n_error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

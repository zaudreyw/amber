#!/usr/bin/env python3
"""OpenHands harness baseline (D-009).

Runs the OpenHands coding-agent harness on the same 17-task GEOS XML
authoring set used by the vanilla-CC baseline, with the same model
(``minimax/minimax-m2.7`` via OpenRouter) and the same domain primer
(``run/AGENTS.md``). The only knob this varies is the agent harness
itself (Claude Code -> OpenHands).

Parity contract — see
``docs/2026-04-27_other-coding-agent-harness-selection.md`` and
``.copilot/decisions/D-009_other-coding-agent-baseline.md``.

Layout produced (scorer-compatible):

    data/eval/openhands_no_plugin/<run_name>/<task>/
      AGENTS.md            ← copy of run/AGENTS.md (loaded as project skill)
      task.txt             ← BEGIN/END SIMULATION SPECIFICATION wrapper
      inputs/*.xml         ← scored by scripts/eval/batch_evaluate.py
      outputs/             ← any agent-produced outputs
      events.jsonl         ← OpenHands --json stream (full trajectory)
      stderr.txt           ← container stderr
      exit_code.txt        ← container exit code or "timeout"
      status.json          ← {task, status, started, ended, elapsed,
                              tokens_in, tokens_out, tool_call_counts}
      metadata.json        ← {model, base_url, primer_sha256, started, ...}

Smoketest:

    python scripts/openhands_eval.py \\
        --run-name oh_smoke_s1 \\
        --include TutorialSneddon \\
        --workers 1 \\
        --timeout 600 \\
        --score

Full run:

    python scripts/openhands_eval.py \\
        --run-name oh_test17_s1 \\
        --workers 4 \\
        --timeout 1200 \\
        --score
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Re-use the canonical 17-task list + primer location from harnessless_eval
# rather than redefining (single source of truth).
from scripts.harnessless_eval import TEST_TASKS_17, AGENTS_MD_PATH

# Re-use the contamination filter so the same per-task blocklist applies as
# vanilla CC. This is critical for fairness — without it OpenHands would see
# GT files that CC cannot.
sys.path.insert(0, str(REPO_ROOT / "src"))
from runner.contamination import (  # noqa: E402
    cleanup_filtered_geos_copy,
    create_filtered_geos_copy,
    get_blocked_files_for_task,
)
from runner.constants import (  # noqa: E402
    DEFAULT_GEOS_LIB_DIR,
    GROUND_TRUTH_DIR as RUNNER_GROUND_TRUTH_DIR,
    TEMP_GEOS_PARENT,
)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

DEFAULT_SPECS_DIR = Path(
    "/data/shared/geophysics_agent_data/data/eval/experiments_from_mined_specs"
)
DEFAULT_GT_DIR = Path(
    "/data/shared/geophysics_agent_data/data/eval/experiments_gt"
)
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "eval" / "openhands_no_plugin"
DEFAULT_RESULTS_ROOT = REPO_ROOT / "data" / "eval" / "results"

# Docker image built from run/Dockerfile.openhands.
DEFAULT_DOCKER_IMAGE = "geos-eval-openhands"

# Vanilla-CC parity:
DEFAULT_MODEL = "openrouter/minimax/minimax-m2.7"  # litellm provider/model
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT = 1200  # 20 minutes, matches CC

# ----------------------------------------------------------------------
# Prompt construction (parity contract)
# ----------------------------------------------------------------------

def build_task_prompt(instructions: str) -> str:
    """Same wrapper vanilla CC uses (build_task_prompt in src/runner/prompts)."""
    return (
        "--- BEGIN SIMULATION SPECIFICATION ---\n"
        f"{instructions.strip()}\n"
        "--- END SIMULATION SPECIFICATION ---"
    )


def load_agents_md() -> str:
    """Load run/AGENTS.md verbatim. This is the entire 'domain adaptation'.

    Vanilla CC appends this via ``--append-system-prompt``. OpenHands
    auto-discovers AGENTS.md in the working directory and loads it as a
    project skill into the system context — same effective placement.
    """
    return AGENTS_MD_PATH.read_text()


def load_primer(primer_path: Path) -> str:
    """Load any primer markdown verbatim.

    Use this instead of ``load_agents_md`` when ``--primer-path`` is set
    to anything other than ``run/AGENTS.md`` (e.g. the minimal primer the
    CC pipeline switched to in 2026-04-27).
    """
    return primer_path.read_text()


def derive_primer_fingerprints(primer_text: str, n: int = 5) -> tuple[str, ...]:
    """Auto-pick distinctive substrings from the primer for stdout-presence
    parity checking. Picks the first ``n`` lines whose length lies in
    [25, 120] chars and that aren't pure markdown decoration. Robust
    across primer variants (full, minimal, future ablations) so we don't
    have to maintain a per-primer fingerprint table.
    """
    decoration = set("#-=* `")
    lines = [l.strip() for l in primer_text.splitlines() if l.strip()]
    out: list[str] = []
    for l in lines:
        if not (25 <= len(l) <= 120):
            continue
        if all(c in decoration for c in l):
            continue
        out.append(l)
        if len(out) >= n:
            break
    return tuple(out)


# ----------------------------------------------------------------------
# Per-task workspace prep
# ----------------------------------------------------------------------

RAG_INSTRUCTIONS_OH = (
    "GEOS RAG instructions: An MCP server named 'geos-rag' is connected; "
    "it exposes tools `search_navigator`, `search_schema`, and "
    "`search_technical` (or `mcp__geos-rag__search_*` depending on how "
    "the harness namespaces MCP tools). Use them before answering "
    "questions about GEOS XML syntax, examples, schema, or "
    "documentation. Use `search_navigator` for conceptual orientation, "
    "`search_schema` for authoritative XML attributes/types/defaults, "
    "and `search_technical` for real XML examples and line references."
)

MEMORY_PRIMER_PATH = REPO_ROOT / "plugin" / "memory_primer_m1u.md"


def build_inline_user_message(
    primer_text: str,
    instructions: str,
    *,
    plugin_enabled: bool = False,
    memory_primer_text: str = "",
) -> str:
    """Compose the single user message OpenHands receives.

    RN-004 P0 #1: writing AGENTS.md to the workspace did NOT auto-inject
    the primer into the model's system context — the agent saw only the
    file in `ls`, never opened it. To guarantee the primer reaches the
    model, prepend it inline to the user message above the spec wrapper.

    Placement note (parity caveat): vanilla CC's primer goes in the
    SYSTEM slot via `--append-system-prompt`. OpenHands' primer (this
    function) goes in the first USER slot. Documented in XN-016 as the
    one unavoidable parity differential — OpenHands v1.15 has no
    user-injectable system-prompt CLI flag.

    plugin_enabled: also prepends RAG_INSTRUCTIONS_OH (geos-rag MCP).
    memory_primer_text: prepends an optional memory primer (e.g. M1-u
        DC-Cu cheatsheet from XN-015). Empty string disables.
    """
    parts: list[str] = [primer_text.rstrip()]
    if plugin_enabled:
        parts.append(RAG_INSTRUCTIONS_OH.rstrip())
    if memory_primer_text:
        parts.append(memory_primer_text.rstrip())
    parts.append(build_task_prompt(instructions))
    return "\n\n---\n\n".join(parts)


def write_mcp_config(
    workspace: Path,
    *,
    enable_rag: bool = True,
    enable_xmllint: bool = False,
) -> Path:
    """Write OpenHands MCP config so OH loads our MCP servers.

    OpenHands reads MCP config from `<PERSISTENCE_DIR>/mcp.json`; we set
    `OPENHANDS_PERSISTENCE_DIR=/workspace/.openhands` per task, so the
    file lands at `<workspace>/.openhands/mcp.json`. Inside the
    container, the plugin is mounted at `/plugins/repo3` and the vector
    DB at `/data/shared/geophysics_agent_data/data/vector_db`.

    enable_rag: register the geos-rag MCP server (R factor in CC parlance).
    enable_xmllint: register the xmllint MCP validator (X factor).
    """
    mcp_dir = workspace / ".openhands"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    servers: dict = {}
    if enable_rag:
        servers["geos-rag"] = {
            "command": "uv",
            "args": [
                "run",
                "--script",
                "/plugins/repo3/scripts/geos_rag_mcp.py",
            ],
            "env": {
                "GEOS_VECTOR_DB_DIR":
                    "/data/shared/geophysics_agent_data/data/vector_db",
                "CLAUDE_PLUGIN_ROOT": "/plugins/repo3",
            },
        }
    if enable_xmllint:
        servers["xmllint"] = {
            "command": "uv",
            "args": [
                "run",
                "--script",
                "/plugins/repo3/scripts/xmllint_mcp.py",
            ],
            "env": {
                "CLAUDE_PLUGIN_ROOT": "/plugins/repo3",
                "XMLLINT_SCHEMA_PATH": "/geos_lib/src/coreComponents/schema/schema.xsd",
            },
        }
    cfg = {"mcpServers": servers}
    path = mcp_dir / "mcp.json"
    path.write_text(json.dumps(cfg, indent=2))
    return path


def prepare_task_workspace(
    task_dir: Path,
    primer_text: str,
    instructions: str,
) -> tuple[Path, str, str]:
    """Set up the per-task workspace.

    RN-004 P1 #4 fix: wipe `task_dir` if it already exists so re-runs do
    not silently mix new XMLs with stale ones from a previous attempt.
    RN-004 P1 #3 fix: do NOT write `task.txt` or `AGENTS.md` into the
    workspace — both are visible to the agent's own `ls`/`Read` tools and
    create a parity differential vs CC. Pass content inline via `--task`.

    Returns:
        (workspace_dir, inline_user_message, primer_sha256)
    """
    if task_dir.exists():
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True, exist_ok=False)
    (task_dir / "inputs").mkdir()
    (task_dir / "outputs").mkdir()

    primer_sha = hashlib.sha256(primer_text.encode("utf-8")).hexdigest()
    inline_msg = build_inline_user_message(primer_text, instructions)
    return task_dir, inline_msg, primer_sha


# ----------------------------------------------------------------------
# Docker invocation
# ----------------------------------------------------------------------

def build_docker_cmd(
    *,
    docker_image: str,
    task_dir: Path,
    filtered_geos: Path,
    api_key: str,
    model: str,
    base_url: str,
    inline_user_message: str,
    plugin_dir: Path | None = None,
    vector_db_dir: Path | None = None,
    container_name: str | None = None,
    extra_llm_envs: dict[str, str] | None = None,
) -> list[str]:
    """Build the docker run command for a single task.

    Mirrors vanilla CC's mount layout:
      - <task_dir> -> /workspace (rw)
      - <filtered_geos> -> /geos_lib (ro)

    The full primer + spec is passed via `--task` (inline) rather than
    `-f /workspace/task.txt` (RN-004 P1 #3 fix). The image's
    Dockerfile.openhands also disables OpenHands' user/public skill
    auto-loaders (RN-004 P0 #2 fix) so no keyword-matched extras can
    contaminate the prompt.
    """
    cmd = [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
    ]
    if container_name:
        cmd += ["--name", container_name]
    cmd += [
        "-v", f"{filtered_geos}:/geos_lib:ro",
        "-v", f"{task_dir}:/workspace:rw",
    ]
    # Mount plugin/ if any MCP server needs it. RAG additionally needs the
    # vector DB; xmllint needs only the plugin/ scripts dir.
    if plugin_dir is not None:
        cmd += ["-v", f"{plugin_dir}:/plugins/repo3:ro"]
        if vector_db_dir is not None:
            cmd += [
                "-v", f"{vector_db_dir}:/data/shared/geophysics_agent_data/data/vector_db:ro",
            ]
    cmd += [
        # OpenHands persistence (settings, conversations) — keep per-task
        # so runs are isolated.
        "-e", "OPENHANDS_PERSISTENCE_DIR=/workspace/.openhands",
        "-e", "OPENHANDS_WORK_DIR=/workspace",
        "-e", "OPENHANDS_SUPPRESS_BANNER=1",
        "-e", "TTY_INTERACTIVE=1",
        # LiteLLM env-var path. --override-with-envs makes OpenHands honor these
        # instead of falling back to an interactive setup wizard.
        "-e", f"LLM_API_KEY={api_key}",
        "-e", f"LLM_MODEL={model}",
        # Some models / providers also look at these.
        "-e", f"OPENROUTER_API_KEY={api_key}",
        "-e", f"OPENAI_API_KEY={api_key}",
        "-e", f"DEEPSEEK_API_KEY={api_key}",
    ]
    # Only set LLM_BASE_URL if non-empty. LiteLLM's native ``deepseek/`` provider
    # has its own default base (https://api.deepseek.com); forcing an explicit
    # base_url through LLM_BASE_URL can shadow that and break routing.
    if base_url:
        cmd += ["-e", f"LLM_BASE_URL={base_url}"]
    for k, v in (extra_llm_envs or {}).items():
        cmd += ["-e", f"{k}={v}"]
    cmd += [
        # Ensure HOME is writable inside container (OpenHands writes
        # ~/.openhands fallback even with PERSISTENCE_DIR).
        "-e", "HOME=/workspace/.home",
        docker_image,
        "openhands",
        "--headless",
        "--json",
        "--override-with-envs",
        "--exit-without-confirmation",
        "-t", inline_user_message,
    ]
    return cmd


# ----------------------------------------------------------------------
# Parity verifications (RN-004 P0 #1 + P0 #2)
# ----------------------------------------------------------------------

# Distinctive substrings from run/AGENTS.md. If none of these appear in
# the OpenHands stdout (events.jsonl), the primer never reached the model
# and the run is a parity failure. Kept as a fallback default — when the
# primer is anything other than run/AGENTS.md we derive fingerprints from
# the primer text via ``derive_primer_fingerprints``.
PRIMER_FINGERPRINTS = (
    "GEOS Expert",
    "PRIMARY RESPONSIBILITY",
    "# GEOS Primer",
    "two-file pattern",
    "GEOSDATA",
)


def verify_parity(
    stdout_text: str,
    fingerprints: tuple[str, ...] = PRIMER_FINGERPRINTS,
) -> dict[str, Any]:
    """Check that (a) the primer reached the model, (b) no public/user
    skills were auto-injected.

    Returns dict suitable for merging into status.json:
      - primer_in_context: bool — at least one PRIMER_FINGERPRINT seen
      - primer_fingerprints_seen: list[str] — which strings matched
      - activated_skills: list[str] — non-empty means OpenHands injected
        keyword-matched extras (RN-004 P0 #2). Should always be [] under
        the patched image.
    """
    primer_seen = [s for s in fingerprints if s in stdout_text]

    activated: list[str] = []
    # OpenHands' --json stream emits events with `"activated_skills": [...]`.
    # Cheapest reliable read: find every occurrence of the literal key and
    # parse the trailing list. Tolerant of pretty-printing / whitespace.
    import re
    for m in re.finditer(r'"activated_skills"\s*:\s*\[([^\]]*)\]', stdout_text):
        body = m.group(1)
        for tok in re.findall(r'"([^"]+)"', body):
            if tok not in activated:
                activated.append(tok)

    return {
        "primer_in_context": bool(primer_seen),
        "primer_fingerprints_seen": primer_seen,
        "activated_skills": activated,
    }


# ----------------------------------------------------------------------
# Trajectory parsing — extract token / tool-call totals from --json stream
# ----------------------------------------------------------------------

def read_oh_token_stats(task_dir: Path) -> dict[str, Any]:
    """Pull token + cost totals from OpenHands' per-conversation base_state.json.

    OpenHands writes the conversation state under
    ``<work_dir>/.openhands/conversations/<conv_id>/base_state.json`` with
    cumulative usage at ``stats.usage_to_metrics.agent``. The streaming
    --json events do NOT include usage, but this file does.
    """
    out: dict[str, Any] = {
        "accumulated_cost_usd": None,
        "prompt_tokens": None,
        "completion_tokens": None,
        "cache_read_tokens": None,
        "cache_write_tokens": None,
        "reasoning_tokens": None,
        "n_llm_calls": None,
    }
    conv_dir = task_dir / ".openhands" / "conversations"
    if not conv_dir.exists():
        return out
    convs = list(conv_dir.iterdir())
    if not convs:
        return out
    bs = convs[0] / "base_state.json"
    if not bs.exists():
        return out
    try:
        agent_metrics = json.loads(bs.read_text())["stats"]["usage_to_metrics"]["agent"]
    except (KeyError, json.JSONDecodeError):
        return out
    usage = agent_metrics.get("accumulated_token_usage", {})
    out["accumulated_cost_usd"] = agent_metrics.get("accumulated_cost")
    out["prompt_tokens"] = usage.get("prompt_tokens")
    out["completion_tokens"] = usage.get("completion_tokens")
    out["cache_read_tokens"] = usage.get("cache_read_tokens")
    out["cache_write_tokens"] = usage.get("cache_write_tokens")
    out["reasoning_tokens"] = usage.get("reasoning_tokens")
    out["n_llm_calls"] = len(agent_metrics.get("costs", []))
    return out


def summarize_events(stdout_text: str) -> dict[str, Any]:
    """Best-effort extraction of token usage and tool-call counts.

    OpenHands ``--json`` mode emits **pretty-printed** JSON objects
    separated by ``--JSON Event--`` markers, with terminal banner lines
    and Rich-styled status messages interleaved. Not strict JSONL.
    Strategy: split on the marker, then for each chunk extract the
    largest balanced ``{...}`` substring and json-decode it.
    """
    tokens_in = 0
    tokens_out = 0
    tool_calls: dict[str, int] = {}
    n_events = 0

    chunks = stdout_text.split("--JSON Event--")
    for chunk in chunks[1:]:  # first chunk is pre-event banner
        # Find the outermost balanced { ... } in the chunk.
        start = chunk.find("{")
        if start < 0:
            continue
        depth = 0
        end = -1
        for i in range(start, len(chunk)):
            c = chunk[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end < 0:
            continue
        try:
            ev = json.loads(chunk[start:end + 1])
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        n_events += 1
        # LLM usage events.
        usage = ev.get("usage") or (ev.get("llm") or {}).get("usage") or {}
        if isinstance(usage, dict):
            tokens_in += int(usage.get("prompt_tokens") or 0)
            tokens_out += int(usage.get("completion_tokens") or 0)
        # Tool / action events.
        action_field = ev.get("action") or ev.get("observation")
        action_name = None
        if isinstance(action_field, dict):
            action_name = action_field.get("kind") or action_field.get("command")
        elif isinstance(action_field, str):
            action_name = action_field
        if not action_name:
            action_name = ev.get("tool_name") or ev.get("type")
        if isinstance(action_name, str) and action_name:
            tool_calls[action_name] = tool_calls.get(action_name, 0) + 1
    return {
        "n_events": n_events,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tool_call_counts": tool_calls,
    }


# ----------------------------------------------------------------------
# Self-refine (mirrors plugin/hooks/verify_outputs.py for the OH harness)
# ----------------------------------------------------------------------

def _xml_problems(inputs_dir: Path) -> str | None:
    """Return None if /workspace/inputs has >=1 XML and all parse cleanly.
    Otherwise return a short human-readable reason — used as feedback for
    the next OH attempt under --self-refine."""
    import xml.etree.ElementTree as ET
    if not inputs_dir.exists():
        return f"Directory {inputs_dir.name}/ does not exist. Write your XML here."
    xmls = sorted(inputs_dir.rglob("*.xml"))
    if not xmls:
        return (f"No .xml files were written to {inputs_dir.name}/. "
                f"Write at least one well-formed GEOS input XML there before finishing.")
    bad: list[str] = []
    for x in xmls:
        try:
            ET.parse(x)
        except ET.ParseError as e:
            rel = x.relative_to(inputs_dir.parent) if inputs_dir.parent in x.parents else x
            bad.append(f"  - {rel}: {e}")
    if bad:
        return "The following XML files failed to parse:\n" + "\n".join(bad[:5])
    return None


def _build_refine_message(original_instructions: str, problem: str) -> str:
    """Compose a short corrective user-message for the next attempt."""
    return (
        "Your previous attempt did not produce valid GEOS input XML.\n\n"
        f"Issue:\n{problem}\n\n"
        "Re-read the original task spec below, fix the issue (e.g. write the "
        "missing files to /workspace/inputs/, repair malformed XML), and finish "
        "again when /workspace/inputs/ contains at least one well-formed GEOS XML.\n\n"
        "----- ORIGINAL TASK SPEC -----\n"
        f"{original_instructions}"
    )


# ----------------------------------------------------------------------
# Per-task driver
# ----------------------------------------------------------------------

def run_one_task(
    task_name: str,
    *,
    specs_dir: Path,
    output_dir: Path,
    primer_text: str,
    docker_image: str,
    api_key: str,
    model: str,
    base_url: str,
    timeout: int,
    geos_lib_dir: Path,
    gt_dir: Path,
    tmp_geos_parent: Path,
    dry_run: bool,
    plugin_dir: Path | None = None,
    vector_db_dir: Path | None = None,
    memory_primer_text: str = "",
    primer_path: Path = AGENTS_MD_PATH,
    primer_fingerprints: tuple[str, ...] = PRIMER_FINGERPRINTS,
    self_refine_max_retries: int = 0,
    extra_llm_envs: dict[str, str] | None = None,
    enable_xmllint_mcp: bool = False,
) -> dict[str, Any]:
    started_iso = datetime.now(timezone.utc).isoformat()
    started_t = time.time()

    spec_path = specs_dir / task_name / "instructions.txt"
    if not spec_path.exists():
        return {
            "task": task_name,
            "status": "error",
            "error": f"spec missing: {spec_path}",
        }
    instructions = spec_path.read_text()

    task_dir = output_dir / task_name
    task_dir, _, primer_sha = prepare_task_workspace(
        task_dir, primer_text, instructions,
    )
    plugin_enabled = plugin_dir is not None and vector_db_dir is not None
    # Need the plugin mount whenever we register any MCP server backed by
    # plugin/scripts/*.py, including xmllint_mcp.py.
    needs_plugin_mount = plugin_enabled or enable_xmllint_mcp
    if needs_plugin_mount and plugin_dir is None:
        plugin_dir = REPO_ROOT / "plugin"
    if plugin_enabled or enable_xmllint_mcp:
        write_mcp_config(
            task_dir,
            enable_rag=plugin_enabled,
            enable_xmllint=enable_xmllint_mcp,
        )
    inline_user_message = build_inline_user_message(
        primer_text, instructions,
        plugin_enabled=plugin_enabled,
        memory_primer_text=memory_primer_text,
    )

    # Per-task contamination filter (parity with vanilla CC).
    blocked = get_blocked_files_for_task(
        task_name, gt_dir, geos_source_dir=geos_lib_dir,
    )
    blocked_xml = blocked["blocked_xml_filenames"]
    blocked_rst = blocked["blocked_rst_paths"]

    if dry_run:
        filtered_geos = geos_lib_dir
        cleanup = False
    else:
        filtered_geos = create_filtered_geos_copy(
            geos_lib_dir,
            blocked_xml_basenames=blocked_xml,
            blocked_rst_relpaths=blocked_rst,
            tmp_parent=tmp_geos_parent,
        )
        cleanup = True

    # Capture pinned openhands version from inside the container so it's
    # in the audit trail per RN-004 P3 #6.
    try:
        oh_ver = subprocess.run(
            ["docker", "run", "--rm", docker_image, "openhands", "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=30, check=False,
        ).stdout.strip().splitlines()[-1]
    except Exception:
        oh_ver = "unknown"

    metadata = {
        "task": task_name,
        "harness": "openhands",
        "openhands_version": oh_ver,
        "model": model,
        "base_url": base_url,
        "primer_path": str(primer_path),
        "primer_sha256": primer_sha,
        "primer_delivery": "inline_user_message_prefix",
        "plugin_enabled": plugin_enabled,
        "plugin_dir": str(plugin_dir) if plugin_dir else None,
        "vector_db_dir": str(vector_db_dir) if vector_db_dir else None,
        "memory_primer_used": bool(memory_primer_text),
        "memory_primer_chars": len(memory_primer_text),
        "self_refine_max_retries": self_refine_max_retries,
        "blocked_gt_xml_filenames": blocked_xml,
        "blocked_rst_relpaths": blocked_rst,
        "filtered_geos_copy": str(filtered_geos),
        "docker_image": docker_image,
        "timeout_s": timeout,
        "started": started_iso,
    }
    (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    if dry_run:
        sample_cmd = build_docker_cmd(
            docker_image=docker_image, task_dir=task_dir,
            filtered_geos=filtered_geos, api_key=api_key, model=model,
            base_url=base_url, inline_user_message=inline_user_message,
            plugin_dir=plugin_dir, vector_db_dir=vector_db_dir,
            container_name=f"oh-{task_name}-dryrun",
            extra_llm_envs=extra_llm_envs,
        )
        # Don't print the API key — redact for display only.
        display_cmd = [
            tok if "API_KEY=" not in tok else tok.split("=", 1)[0] + "=<redacted>"
            for tok in sample_cmd
        ]
        print(f"[DRY RUN] {' '.join(display_cmd)}")
        return {"task": task_name, "status": "dry_run"}

    # ----- attempt loop (1 + self_refine_max_retries) -----
    attempts: list[dict[str, Any]] = []
    cur_message = inline_user_message
    status: str = "running"
    exit_code: int | str | None = None
    stdout = ""
    stderr = ""
    last_problem: str | None = None
    try:
        for attempt_idx in range(self_refine_max_retries + 1):
            container_name = f"oh-{task_name}-{int(time.time())}-{attempt_idx}"
            cmd = build_docker_cmd(
                docker_image=docker_image,
                task_dir=task_dir,
                filtered_geos=filtered_geos,
                api_key=api_key,
                model=model,
                base_url=base_url,
                inline_user_message=cur_message,
                plugin_dir=plugin_dir,
                vector_db_dir=vector_db_dir,
                container_name=container_name,
                extra_llm_envs=extra_llm_envs,
            )
            a_started = time.time()
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                )
                a_stdout = proc.stdout
                a_stderr = proc.stderr
                a_exit = proc.returncode
                a_status = "success" if proc.returncode == 0 else "failed"
            except subprocess.TimeoutExpired as exc:
                try:
                    subprocess.run(["docker", "kill", container_name],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   timeout=15, check=False)
                except Exception:
                    pass
                raw_out = exc.stdout or b""
                raw_err = exc.stderr or b""
                a_stdout = raw_out.decode("utf-8", errors="replace") if isinstance(raw_out, (bytes, bytearray)) else raw_out
                a_stderr = (raw_err.decode("utf-8", errors="replace") if isinstance(raw_err, (bytes, bytearray)) else raw_err) + "\n[runner] timeout expired"
                a_exit = "timeout"
                a_status = "timeout"
            except Exception as exc:  # pragma: no cover
                a_stdout = ""
                a_stderr = f"[runner] driver exception: {exc}"
                a_exit = "error"
                a_status = "error"

            a_elapsed = round(time.time() - a_started, 1)
            # Persist per-attempt artifacts (events_<idx>.jsonl, etc.) so post-hoc
            # analysis can see what happened in each pass.
            (task_dir / f"events_{attempt_idx}.jsonl").write_text(a_stdout)
            (task_dir / f"stderr_{attempt_idx}.txt").write_text(a_stderr)
            attempts.append({
                "attempt": attempt_idx,
                "exit_code": a_exit,
                "status": a_status,
                "elapsed_seconds": a_elapsed,
                "feedback_in": cur_message[:400] if attempt_idx > 0 else None,
            })
            # Latest-attempt artifacts also become the canonical ones.
            stdout = a_stdout
            stderr = a_stderr
            exit_code = a_exit
            status = a_status

            problem = _xml_problems(task_dir / "inputs")
            if problem is None:
                last_problem = None
                break
            last_problem = problem
            if attempt_idx >= self_refine_max_retries:
                break
            cur_message = _build_refine_message(instructions, problem)
    finally:
        if cleanup:
            cleanup_filtered_geos_copy(filtered_geos)

    elapsed = round(time.time() - started_t, 1)

    (task_dir / "events.jsonl").write_text(stdout if isinstance(stdout, str) else "")
    (task_dir / "stderr.txt").write_text(stderr if isinstance(stderr, str) else "")
    (task_dir / "exit_code.txt").write_text(str(exit_code))

    # Aggregate event-summary across the LAST attempt only (matches CC's
    # one-shot accounting; per-attempt counts live in events_<idx>.jsonl).
    summary = summarize_events(stdout if isinstance(stdout, str) else "")
    # Recursive: agents sometimes nest outputs (e.g. inputs/triaxialDriver/*.xml).
    # The scorer also globs recursively, so non-recursive count under-reports.
    n_xml = sum(1 for p in (task_dir / "inputs").rglob("*.xml"))
    if status == "success" and n_xml == 0:
        # Mirror CC's "failed_no_outputs" classification.
        status = "failed_no_outputs"

    # RN-004 P0 verifications (primer reaches model; no public skills inject).
    # Concatenate all attempt stdouts so a primer fingerprint seen on any pass counts.
    all_stdout = "\n".join(
        (task_dir / f"events_{i}.jsonl").read_text()
        for i in range(len(attempts))
    )
    parity = verify_parity(all_stdout, fingerprints=primer_fingerprints)
    if status == "success":
        if not parity["primer_in_context"]:
            status = "failed_parity_no_primer"
        elif parity["activated_skills"]:
            status = "failed_parity_skills_injected"

    if elapsed > 30 and summary["n_events"] == 0:
        # Trajectory parser drifted (RN-004 P2). Don't claim success.
        if status == "success":
            status = "failed_parser_silent"

    token_stats = read_oh_token_stats(task_dir)

    status_payload = {
        "task": task_name,
        "harness": "openhands",
        "status": status,
        "exit_code": exit_code,
        "started": started_iso,
        "ended": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed,
        "n_xml_files": n_xml,
        "n_attempts": len(attempts),
        "attempts": attempts,
        "self_refine_remaining_problem": last_problem,
        **summary,
        **parity,
        **token_stats,
    }
    (task_dir / "status.json").write_text(json.dumps(status_payload, indent=2))

    return status_payload


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-name", required=True)
    p.add_argument("--include", nargs="+", default=None,
                   help="Subset of tasks (default: all 17 from TEST_TASKS_17)")
    p.add_argument("--exclude", nargs="+", default=None)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--api-key-env", default="OPENROUTER_API_KEY",
                   help="Env var name to read the LLM API key from")
    p.add_argument("--specs-dir", type=Path, default=DEFAULT_SPECS_DIR)
    p.add_argument("--gt-dir", type=Path, default=DEFAULT_GT_DIR)
    p.add_argument("--geos-lib-dir", type=Path, default=DEFAULT_GEOS_LIB_DIR)
    p.add_argument("--tmp-geos-parent", type=Path, default=TEMP_GEOS_PARENT)
    p.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    p.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    p.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE)
    p.add_argument("--plugin", action="store_true",
                   help="Enable repo3 geos-rag MCP plugin (mounts plugin/, vector DB, writes mcp.json)")
    p.add_argument("--xmllint-mcp", action="store_true",
                   help="Register the xmllint validator MCP (X factor). Mounts plugin/ even "
                        "when --plugin is off so the xmllint_mcp.py script is reachable.")
    p.add_argument("--plugin-dir", type=Path, default=REPO_ROOT / "plugin")
    p.add_argument("--vector-db-dir", type=Path,
                   default=Path("/data/shared/geophysics_agent_data/data/vector_db"))
    p.add_argument("--memory-primer", type=Path, default=None,
                   help="Optional path to memory primer markdown to prepend (e.g. plugin/memory_primer_m1u.md)")
    p.add_argument("--primer-path", type=Path, default=AGENTS_MD_PATH,
                   help="Domain-adaptation primer to inline into the user message. "
                        "Default: run/AGENTS.md (the full primer). For parity with the "
                        "current vanilla-CC SOTA stack, pass plugin/GEOS_PRIMER_minimal.md.")
    p.add_argument("--self-refine", type=int, default=0,
                   help="Self-refinement budget. After the agent finishes, if "
                        "/workspace/inputs/ has 0 XML files OR any XML fails to parse, "
                        "re-invoke OpenHands in the same workspace with the failure "
                        "reason as feedback. Cap at this many extra attempts. Default 0 "
                        "(disabled). Mirrors plugin/hooks/verify_outputs.py for CC.")
    p.add_argument("--llm-env", action="append", default=[],
                   metavar="KEY=VALUE",
                   help="Extra LLM_* env vars to forward into the container. Repeatable. "
                        "Example: --llm-env LLM_REASONING_EFFORT=none disables thinking on "
                        "deepseek/* models (works around the deepseek reasoning_content "
                        "round-trip bug we hit on 2026-04-27).")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--score", action="store_true",
                   help="After all tasks finish, run scripts/eval/batch_evaluate.py")
    args = p.parse_args()

    plugin_dir_arg = args.plugin_dir if args.plugin else None
    vector_db_arg = args.vector_db_dir if args.plugin else None
    memory_text = args.memory_primer.read_text() if args.memory_primer else ""
    extra_llm_envs: dict[str, str] = {}
    for kv in args.llm_env:
        if "=" not in kv:
            print(f"--llm-env expects KEY=VALUE, got: {kv!r}", file=sys.stderr)
            return 2
        k, v = kv.split("=", 1)
        extra_llm_envs[k] = v

    # Resolve task list.
    tasks = list(args.include) if args.include else list(TEST_TASKS_17)
    if args.exclude:
        excl = set(args.exclude)
        tasks = [t for t in tasks if t not in excl]
    if not tasks:
        print("No tasks selected.", file=sys.stderr)
        return 2

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key and not args.dry_run:
        print(
            f"Missing {args.api_key_env} in environment.",
            file=sys.stderr,
        )
        return 2

    primer_text = load_primer(args.primer_path)
    primer_fingerprints = derive_primer_fingerprints(primer_text)
    if not primer_fingerprints:
        print(f"[openhands_eval] WARNING: could not derive parity fingerprints from "
              f"{args.primer_path} (primer too short / unusual). Falling back to the "
              f"AGENTS.md fingerprint set, which will likely flag every run as a parity "
              f"failure.", file=sys.stderr)
        primer_fingerprints = PRIMER_FINGERPRINTS
    output_dir = args.output_root / args.run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[openhands_eval] run_name={args.run_name}  tasks={len(tasks)}  workers={args.workers}")
    print(f"[openhands_eval] model={args.model}  base_url={args.base_url or '<unset>'}")
    print(f"[openhands_eval] primer={args.primer_path.name} ({len(primer_text)} chars, "
          f"{len(primer_fingerprints)} fingerprints)")
    print(f"[openhands_eval] plugin={args.plugin}  memory_primer={args.memory_primer}  "
          f"self_refine={args.self_refine}")
    if extra_llm_envs:
        print(f"[openhands_eval] extra_llm_envs={list(extra_llm_envs.keys())}")
    print(f"[openhands_eval] output_dir={output_dir}")

    results: list[dict[str, Any]] = []
    common_kwargs = dict(
        specs_dir=args.specs_dir,
        output_dir=output_dir,
        primer_text=primer_text,
        docker_image=args.docker_image,
        api_key=api_key,
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
        geos_lib_dir=args.geos_lib_dir.resolve(),
        gt_dir=args.gt_dir,
        tmp_geos_parent=args.tmp_geos_parent,
        dry_run=args.dry_run,
        plugin_dir=plugin_dir_arg,
        vector_db_dir=vector_db_arg,
        memory_primer_text=memory_text,
        primer_path=args.primer_path,
        primer_fingerprints=primer_fingerprints,
        self_refine_max_retries=args.self_refine,
        extra_llm_envs=extra_llm_envs,
        enable_xmllint_mcp=args.xmllint_mcp,
    )
    if args.workers <= 1:
        for t in tasks:
            print(f"[openhands_eval] -> {t}")
            r = run_one_task(t, **common_kwargs)
            results.append(r)
            print(f"[openhands_eval] <- {t}: {r.get('status')}  elapsed={r.get('elapsed_seconds')}s")
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {
                ex.submit(run_one_task, t, **common_kwargs): t for t in tasks
            }
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                print(f"[openhands_eval] <- {r.get('task')}: {r.get('status')}  elapsed={r.get('elapsed_seconds')}s")

    summary_path = output_dir / "_summary.json"
    summary_path.write_text(json.dumps({
        "run_name": args.run_name,
        "harness": "openhands",
        "model": args.model,
        "base_url": args.base_url,
        "n_tasks": len(tasks),
        "tasks": [r.get("task") for r in results],
        "status_counts": _count_statuses(results),
        "results": results,
        "completed": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    print(f"[openhands_eval] summary -> {summary_path}")

    if args.score and not args.dry_run:
        scorer = REPO_ROOT / "scripts" / "eval" / "batch_evaluate.py"
        results_dir = args.results_root / args.run_name / "openhands_no_plugin"
        results_dir.mkdir(parents=True, exist_ok=True)
        scorer_cmd = [
            "uv", "run", "python", str(scorer),
            "--experiments-dir", str(output_dir),
            "--ground-truth-dir", str(args.gt_dir),
            "--results-dir", str(results_dir),
        ]
        print(f"[openhands_eval] scoring: {' '.join(scorer_cmd)}")
        subprocess.run(scorer_cmd, check=False)

    return 0


def _count_statuses(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in results:
        s = str(r.get("status", "unknown"))
        counts[s] = counts.get(s, 0) + 1
    return counts


if __name__ == "__main__":
    sys.exit(main())

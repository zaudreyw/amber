"""
Programmatic evaluation for Amber MD agent outputs.

Compares agent-generated Amber input files against ground truth using:
  - NAMELIST parameter matching for .mdin files
  - Command-level comparison for tleap.in scripts
  - File-presence scoring for required workflow stages

Headline metric: AmberSim — weighted average of per-file similarity scores.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ============================================================
# Constants
# ============================================================

# Files that should always be present for a complete Amber setup
REQUIRED_FILES = {"tleap.in"}
STAGE_MDIN_NAMES = {
    "min":   ["mdin_min.in", "min.in", "01_min.in", "minimization.in"],
    "heat":  ["mdin_heat.in", "heat.in", "02_heat.in", "heating.in"],
    "equil": ["mdin_equil.in", "equil.in", "03_equil.in", "equilibration.in"],
    "prod":  ["mdin_prod.in", "prod.in", "03_prod.in", "04_prod.in", "production.in"],
}
# Canonical names for stage discovery (used when GT uses a different name)
ALL_MDIN_GLOBS = ["*.mdin", "*.in"]

# Stage weights for the headline score (must sum to 1.0)
STAGE_WEIGHTS = {
    "tleap": 0.20,
    "min":   0.20,
    "heat":  0.20,
    "equil": 0.20,
    "prod":  0.20,
}

NUMERIC_RTOL = 1e-4

# tleap commands that carry semantic weight in scoring
TLEAP_KEY_COMMANDS = {
    "source",
    "loadpdb", "loadmol2", "loadoff", "loadamberparams",
    "addions", "addions2",
    "solvateBox", "solvateOct", "solvateCap",
    "saveamberparm", "savepdb",
    "check",
}


# ============================================================
# NAMELIST parser
# ============================================================

_NL_BLOCK_RE = re.compile(
    r"&(\w+)\s*(.*?)\s*/",
    re.DOTALL | re.IGNORECASE,
)
_PARAM_RE = re.compile(
    r"(\w+)\s*=\s*([^,\n/&]+?)(?=[,\n/&]|$)",
    re.DOTALL,
)


def parse_mdin(text: str) -> dict[str, dict[str, str]]:
    """Parse an Amber .mdin file into {namelist: {key: value}} dicts.

    Returns an empty dict on unparseable input (gracefully tolerates partial files).
    """
    namelists: dict[str, dict[str, str]] = {}
    for m in _NL_BLOCK_RE.finditer(text):
        name = m.group(1).lower()
        body = m.group(2)
        params: dict[str, str] = {}
        for pm in _PARAM_RE.finditer(body):
            key = pm.group(1).strip().lower()
            val = pm.group(2).strip().rstrip(",").strip()
            params[key] = val
        namelists[name] = params
    return namelists


def _parse_numeric(v: str) -> float | None:
    try:
        return float(v.replace("d", "e").replace("D", "E"))
    except ValueError:
        return None


def param_values_equivalent(v1: str, v2: str) -> bool:
    """True if two NAMELIST parameter values are semantically equal."""
    if v1.strip() == v2.strip():
        return True
    n1 = _parse_numeric(v1)
    n2 = _parse_numeric(v2)
    if n1 is not None and n2 is not None:
        if n1 == 0.0 and n2 == 0.0:
            return True
        denom = max(abs(n1), abs(n2))
        return denom == 0.0 or abs(n1 - n2) / denom <= NUMERIC_RTOL
    return v1.strip().lower().strip("'\"") == v2.strip().lower().strip("'\"")


# ============================================================
# mdin scoring
# ============================================================

@dataclass
class MdinScore:
    overall: float
    namelist_scores: dict[str, float]
    matched_params: int
    total_params: int
    missing_params: list[str]
    extra_params: list[str]
    mismatched: list[str]


def score_mdin(gt_text: str, gen_text: str) -> MdinScore:
    """Score a generated .mdin file against ground truth.

    Each namelist block is scored independently as |matched| / |union|.
    Headline is weighted by the number of GT parameters in each block.
    """
    gt_nl = parse_mdin(gt_text)
    gen_nl = parse_mdin(gen_text)

    if not gt_nl:
        return MdinScore(
            overall=1.0 if not gen_nl else 0.5,
            namelist_scores={},
            matched_params=0, total_params=0,
            missing_params=[], extra_params=[], mismatched=[],
        )

    nl_scores: dict[str, float] = {}
    total_gt_params = 0
    total_matched = 0
    total_union = 0
    missing: list[str] = []
    extra: list[str] = []
    mismatched: list[str] = []

    all_namelists = set(gt_nl) | set(gen_nl)

    for nl in all_namelists:
        gt_params = gt_nl.get(nl, {})
        gen_params = gen_nl.get(nl, {})
        all_keys = set(gt_params) | set(gen_params)

        if not all_keys:
            nl_scores[nl] = 1.0
            continue

        matched = 0
        for k in all_keys:
            if k in gt_params and k in gen_params:
                if param_values_equivalent(gt_params[k], gen_params[k]):
                    matched += 1
                else:
                    mismatched.append(f"&{nl} {k}: GT={gt_params[k]!r} GEN={gen_params[k]!r}")
            elif k in gt_params:
                missing.append(f"&{nl} {k}")
            else:
                extra.append(f"&{nl} {k}")

        nl_scores[nl] = matched / len(all_keys)
        total_gt_params += len(gt_params)
        total_matched += matched
        total_union += len(all_keys)

    # Weighted headline: weight each namelist by its GT parameter count
    if total_union == 0:
        headline = 1.0
    else:
        headline = total_matched / total_union

    return MdinScore(
        overall=round(headline, 4),
        namelist_scores={k: round(v, 4) for k, v in nl_scores.items()},
        matched_params=total_matched,
        total_params=total_union,
        missing_params=missing,
        extra_params=extra,
        mismatched=mismatched,
    )


# ============================================================
# tleap script scoring
# ============================================================

_TLEAP_TOKEN_RE = re.compile(r"[^\s,=()]+")


def _tokenize_tleap_line(line: str) -> list[str]:
    line = line.split("#")[0].strip()  # strip comments
    return _TLEAP_TOKEN_RE.findall(line.lower())


def _extract_tleap_commands(text: str) -> list[tuple[str, list[str]]]:
    """Return [(command, [args...]), ...] for each non-empty, non-comment line."""
    cmds: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        tokens = _tokenize_tleap_line(line)
        if not tokens:
            continue
        cmd = tokens[0]
        args = tokens[1:]
        cmds.append((cmd, args))
    return cmds


def _extract_key_tleap_commands(text: str) -> dict[str, list[list[str]]]:
    """Return {command_name: [[args], ...]} for semantically important commands."""
    result: dict[str, list[list[str]]] = {}
    for cmd, args in _extract_tleap_commands(text):
        if cmd in TLEAP_KEY_COMMANDS:
            result.setdefault(cmd, []).append(args)
    return result


def score_tleap(gt_text: str, gen_text: str) -> dict[str, Any]:
    """Score a generated tleap.in against ground truth.

    Evaluates:
    - Command recall: fraction of GT key commands present
    - Source coverage: all required force fields sourced
    - Save command present
    """
    gt_cmds = _extract_key_tleap_commands(gt_text)
    gen_cmds = _extract_key_tleap_commands(gen_text)

    all_cmd_types = set(gt_cmds) | set(gen_cmds)
    if not all_cmd_types:
        return {"overall": 0.0, "details": {}, "missing_commands": [], "extra_commands": []}

    cmd_scores: dict[str, float] = {}
    missing: list[str] = []
    extra_cmds: list[str] = []

    for cmd in all_cmd_types:
        gt_count = len(gt_cmds.get(cmd, []))
        gen_count = len(gen_cmds.get(cmd, []))
        if gt_count == 0:
            extra_cmds.append(cmd)
            cmd_scores[cmd] = 1.0  # extra commands don't penalize
        elif gen_count == 0:
            missing.append(cmd)
            cmd_scores[cmd] = 0.0
        else:
            # Partial credit: min(gen, gt)/gt (reward having at least as many)
            cmd_scores[cmd] = min(gen_count, gt_count) / gt_count

    # Weight: GT commands matter; extra-only commands are neutral (weight 0)
    gt_cmd_types = set(gt_cmds)
    if not gt_cmd_types:
        overall = 1.0
    else:
        overall = sum(cmd_scores[c] for c in gt_cmd_types) / len(gt_cmd_types)

    return {
        "overall": round(overall, 4),
        "cmd_scores": {k: round(v, 4) for k, v in cmd_scores.items()},
        "missing_commands": missing,
        "extra_commands": extra_cmds,
    }


# ============================================================
# File discovery helpers
# ============================================================

def _find_file_by_candidates(directory: Path, candidates: list[str]) -> Path | None:
    """Return the first existing file matching any candidate name (case-insensitive)."""
    names_lower = {c.lower() for c in candidates}
    for f in directory.iterdir():
        if f.is_file() and f.name.lower() in names_lower:
            return f
    return None


def _find_tleap(directory: Path) -> Path | None:
    candidates = ["tleap.in", "leaprc", "leap.in", "system.in"]
    return _find_file_by_candidates(directory, candidates)


def _find_stage_mdin(directory: Path, stage: str) -> Path | None:
    return _find_file_by_candidates(directory, STAGE_MDIN_NAMES[stage])


def _discover_mdin_files(directory: Path) -> dict[str, Path]:
    """Find all .mdin/.in files in a directory and map them to stages."""
    found: dict[str, Path] = {}
    for stage, candidates in STAGE_MDIN_NAMES.items():
        p = _find_stage_mdin(directory, stage)
        if p is not None:
            found[stage] = p
    return found


# ============================================================
# Directory-level evaluation
# ============================================================

@dataclass
class AmberEvalResult:
    overall_score: float            # 0.0–1.0 headline
    stage_scores: dict[str, float]  # per-stage scores
    file_presence: dict[str, bool]  # which expected files were found
    details: dict[str, Any]         # per-file detail dicts


def evaluate_amber_dirs(gt_dir: Path, gen_dir: Path) -> AmberEvalResult:
    """Compare generated Amber input files in gen_dir against gt_dir.

    Scoring:
      - tleap.in: 20% of total
      - min/heat/equil/prod .mdin: 20% each
      - Missing files score 0 for their slot
    """
    stage_scores: dict[str, float] = {}
    file_presence: dict[str, bool] = {}
    details: dict[str, Any] = {}

    # --- tleap.in ---
    gt_tleap = _find_tleap(gt_dir)
    gen_tleap = _find_tleap(gen_dir)
    file_presence["tleap"] = gen_tleap is not None
    if gt_tleap is not None:
        if gen_tleap is not None:
            r = score_tleap(gt_tleap.read_text(), gen_tleap.read_text())
        else:
            r = {"overall": 0.0, "missing_commands": ["(file absent)"], "extra_commands": []}
        stage_scores["tleap"] = r["overall"]
        details["tleap"] = r
    else:
        # No GT tleap — if gen has one, neutral; if not, neutral
        stage_scores["tleap"] = 1.0 if gen_tleap is not None else 0.5
        details["tleap"] = {"note": "no GT tleap.in", "overall": stage_scores["tleap"]}

    # --- mdin stages ---
    gt_mdins = _discover_mdin_files(gt_dir)
    gen_mdins = _discover_mdin_files(gen_dir)

    for stage in ["min", "heat", "equil", "prod"]:
        gt_p = gt_mdins.get(stage)
        gen_p = gen_mdins.get(stage)
        file_presence[f"mdin_{stage}"] = gen_p is not None

        if gt_p is None:
            # GT doesn't have this stage — score presence only
            score = 1.0 if gen_p is not None else 0.5
            stage_scores[stage] = score
            details[f"mdin_{stage}"] = {"note": f"no GT mdin for stage {stage}", "overall": score}
            continue

        if gen_p is None:
            stage_scores[stage] = 0.0
            details[f"mdin_{stage}"] = {"note": "file absent", "overall": 0.0}
            continue

        mdin_result = score_mdin(gt_p.read_text(), gen_p.read_text())
        stage_scores[stage] = mdin_result.overall
        details[f"mdin_{stage}"] = {
            "overall": mdin_result.overall,
            "namelist_scores": mdin_result.namelist_scores,
            "matched_params": mdin_result.matched_params,
            "total_params": mdin_result.total_params,
            "missing_params": mdin_result.missing_params[:20],
            "extra_params": mdin_result.extra_params[:20],
            "mismatched": mdin_result.mismatched[:20],
        }

    # --- Headline score (dynamic: weight only stages present in GT) ---
    gt_present = []
    if gt_tleap is not None:
        gt_present.append("tleap")
    for s in ["min", "heat", "equil", "prod"]:
        if gt_mdins.get(s) is not None:
            gt_present.append(s)

    if gt_present:
        w = 1.0 / len(gt_present)
        overall = sum(stage_scores.get(s, 0.0) * w for s in gt_present)
    else:
        overall = sum(
            STAGE_WEIGHTS.get(s, 0.0) * stage_scores.get(s, 0.0)
            for s in STAGE_WEIGHTS
        )

    return AmberEvalResult(
        overall_score=round(overall, 4),
        stage_scores={k: round(v, 4) for k, v in stage_scores.items()},
        file_presence=file_presence,
        details=details,
    )


# ============================================================
# Top-level evaluation entry point
# ============================================================

def evaluate_amber(
    agent_output: dict[str, Any],
    task: dict[str, Any] | None = None,
    ground_truth: Any = None,
) -> dict[str, Any]:
    """Top-level evaluation entry point called by the eval runner.

    Args:
        agent_output: Dict with 'generated_dir' or 'workspace_root'
        task: Task dict with 'ground_truth_dir' and optional 'success_threshold'
        ground_truth: Override for ground truth directory
    """
    if agent_output.get("status") == "execution_error":
        error = agent_output.get("error") or {}
        return {
            "status": "execution_error",
            "success": False,
            "score": 0.0,
            "metrics": {
                "steps": int(agent_output.get("total_steps", 0) or 0),
                "return": float(agent_output.get("total_reward", 0.0) or 0.0),
            },
            "error": {
                "type": str(error.get("type") or "amber_execution_error"),
                "message": str(error.get("message") or "Amber execution failed."),
            },
        }

    generated_dir_raw = agent_output.get("generated_dir") or agent_output.get("workspace_root")
    if not generated_dir_raw:
        raise ValueError("agent_output must include 'generated_dir' or 'workspace_root'")
    generated_dir = Path(str(generated_dir_raw))

    task = task or {}
    ground_truth_raw = ground_truth or task.get("ground_truth_dir")
    if not ground_truth_raw:
        raise ValueError("Amber evaluation requires a ground_truth directory")
    ground_truth_dir = Path(str(ground_truth_raw))

    if agent_output.get("generated_subdir"):
        generated_dir = generated_dir / str(agent_output["generated_subdir"])
    elif task.get("generated_subdir"):
        generated_dir = generated_dir / str(task["generated_subdir"])

    success_threshold = float(task.get("success_threshold", 7.0))

    if not generated_dir.exists():
        return {
            "status": "execution_error",
            "success": False,
            "score": 0.0,
            "metrics": {
                "steps": int(agent_output.get("total_steps", 0) or 0),
                "return": float(agent_output.get("total_reward", 0.0) or 0.0),
                "ground_truth_dir": str(ground_truth_dir),
                "generated_dir": str(generated_dir),
            },
            "error": {"type": "missing_dir", "message": f"Generated dir not found: {generated_dir}"},
        }

    result = evaluate_amber_dirs(ground_truth_dir, generated_dir)

    # Scale 0–1 → 0–10 for parity with GEOS scoring
    score_10 = round(result.overall_score * 10.0, 2)
    success = bool(score_10 >= success_threshold)

    metrics: dict[str, Any] = {
        "steps": int(agent_output.get("total_steps", 0) or 0),
        "return": float(agent_output.get("total_reward", 0.0) or 0.0),
        "overall_score_10": score_10,
        "overall_score_01": result.overall_score,
        "stage_scores": result.stage_scores,
        "file_presence": result.file_presence,
        "success_threshold_10": success_threshold,
        "details": result.details,
        "ground_truth_dir": str(ground_truth_dir),
        "generated_dir": str(generated_dir),
    }

    return {
        "status": "success" if success else "task_failure",
        "success": success,
        "score": result.overall_score,
        "metrics": metrics,
    }

#!/usr/bin/env python3
"""Relax instructions.txt at Medium and Hard difficulty.

Rewrites the natural-language simulation specification using
deepseek-v4-pro so that:
  * Medium drops Tier-1 (software defaults) + Tier-2 (standard numerics).
  * Hard drops T1 + T2 + T3 (domain-inferable physics / material props).

The rewrite preserves all Tier-4 (problem-defining) values verbatim.
Output is a fluent rewrite (not regex deletion) plus an `_omitted.json`
record listing what was dropped, what remains, and what the rewrite
references but does not provide a value for.

Tier definitions match misc/geophys_todo.md and
/home/matt/sci/geos_agent/cc_docs/difficulty_tiers_pitch.md:

  T1  software_default  output format, restart, log levels, flags
  T2  standard_numerics solver tolerance, time stepping, discretisation
  T3  domain_inferable  density, viscosity, porosity, std BCs
  T4  problem_defining  geometry, well locations, applied loads, durations

The agent receiving the relaxed spec is told a separate addendum that
some details are unspecified and should be inferred. That addendum is
appended here so the runner needs no code change.

Usage:
    DEEPSEEK_API_KEY=... uv run python scripts/relax_specs.py \\
        --tasks ExampleMandel ExampleDPWellbore ... \\
        --src-dir /data/shared/.../experiments_test36_template \\
        --out-root data/eval

Outputs:
    <out-root>/experiments_relaxed_medium/<task>/instructions.txt
    <out-root>/experiments_relaxed_medium/<task>/_omitted.json
    <out-root>/experiments_relaxed_hard/<task>/instructions.txt
    <out-root>/experiments_relaxed_hard/<task>/_omitted.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

TIER_DEFS = """
We define four tiers of parameters in a simulation specification:

  T1 software_default  : output format, restart frequency, log levels,
                         boolean flags, event scheduling intervals,
                         lookup-table interpolation modes.
  T2 standard_numerics : Newton tolerance, linear solver, preconditioner,
                         max iterations, time-step limits, line-search,
                         discretisation method, element type.
  T3 domain_inferable  : water viscosity at reservoir conditions,
                         CO2 molar weight, typical reservoir porosity,
                         standard rock densities, Biot coefficients,
                         standard relative-permeability defaults, standard
                         boundary-condition values for the rock type.
  T4 problem_defining  : domain dimensions, well locations, injection
                         rates, applied loads, target BHP, simulation
                         duration, mesh resolution, prescribed history
                         tables, what is being modelled.

Tiers are NOT a strict hierarchy — they are categorical. T4 values are
the ones the principal investigator decides for a specific simulation.
"""

ADDENDUM_MEDIUM = """

Note: some procedural and numerical details are intentionally unspecified
in this brief. Where a value is missing, infer a reasonable default from
GEOS conventions, GEOS example simulations available to you, or standard
computational-science practice. Document your choices briefly in the XML
where appropriate.
"""

ADDENDUM_HARD = """

Note: only the problem-defining aspects of the simulation are specified
in this brief. Many physical, material, and numerical details have been
deliberately omitted. Where a value is missing, infer a reasonable
default from GEOS conventions, GEOS example simulations available to you,
analogous published geophysics setups, or standard practice for this
kind of problem. Document your choices briefly in the XML where
appropriate.
"""

REWRITE_SYSTEM = (
    "You rewrite scientific simulation briefs to control how much the "
    "human author specifies. You preserve the meaning and the writing "
    "style. You never invent numbers; you only DROP information."
)

REWRITE_USER_TEMPLATE = """\
Below is a fully detailed simulation brief. Your job is to produce a
rewrite at the **{level}** difficulty level.

{tier_defs}

For the **{level}** difficulty, the rewrite must:
{level_rules}

Hard requirements for ANY rewrite:
  * Preserve fluent natural-language style. Do NOT leave half-sentences
    or dangling references to numbers you removed.
  * Do NOT name GEOS XML tags or attributes (e.g. avoid mentioning
    "SinglePhaseFVM" or "discretization=...") unless the original brief
    already named them.
  * Do NOT invent new numeric values. You may only KEEP values from the
    original or DROP them.
  * If the original references external table files (e.g. .geos
    files for boundary conditions, history tables), you must KEEP those
    references at every difficulty level — they are problem-defining.
  * Keep the section structure where it makes sense; you may collapse
    sub-sections if the values inside them are all dropped.
  * Keep the final list of "XML files to create".

Return STRICTLY this JSON (no surrounding prose, no markdown fences):

{{
  "rewrite": "<the rewritten brief, plain text>",
  "kept_t4_values": ["<list each T4 value you preserved, e.g. '1.0 m x 0.1 m x 1.0 m domain'>"],
  "dropped_values": [
    {{ "tier": "T1|T2|T3", "what": "<short description>", "value": "<the original value>" }}
  ],
  "kept_t3_values": ["<only fill at Medium level, list T3 values you preserved>"]
}}

Original simulation brief:
---
{spec}
---
"""

LEVEL_RULES = {
    "medium": (
        "  * DROP every T1 value (output format, restart freq, log levels,\n"
        "    boolean flags, event-scheduling intervals).\n"
        "  * DROP every T2 value (solver tolerances, time-step limits,\n"
        "    Newton iterations, linear solver/preconditioner, line-search,\n"
        "    discretisation choices, element type).\n"
        "  * KEEP every T3 value (densities, viscosities, porosities,\n"
        "    permeabilities, Biot, standard BCs).\n"
        "  * KEEP every T4 value (geometry, applied loads, durations,\n"
        "    mesh resolution, well locations, history tables).\n"
        "  * It is OK if a section becomes much shorter. It is NOT OK to\n"
        "    leave a section with a header and no body — collapse it instead."
    ),
    "hard": (
        "  * DROP every T1 value.\n"
        "  * DROP every T2 value.\n"
        "  * DROP every T3 value (densities, viscosities, porosities,\n"
        "    permeabilities, Biot coefficients, all material properties\n"
        "    that a domain expert would pick from standard references).\n"
        "  * KEEP every T4 value (geometry, applied loads, durations,\n"
        "    mesh resolution, well locations, history tables, what is\n"
        "    being modelled).\n"
        "  * The rewrite should read like a 1–2 paragraph problem brief.\n"
        "  * `kept_t3_values` should be empty []."
    ),
}


# ---------------------------------------------------------------------------
# Hygiene
# ---------------------------------------------------------------------------

NUMERIC_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"-?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?"
    r"(?![A-Za-z0-9_])"
)


def numeric_tokens(text: str) -> set[str]:
    """Return numeric tokens that look like physical/numerical values.

    Filter out very short integers (1, 2, 3) which are usually structural
    (e.g. "x, y, z components", "first-order"), keep anything that has a
    decimal point, exponent, or is large enough to be a real value.
    """
    out: set[str] = set()
    for m in NUMERIC_RE.finditer(text):
        tok = m.group(0)
        # keep if it has a decimal/exp, OR is at least 2 digits (covers
        # 10, 100, 0.5, 1e-4 etc; drops bare 1/2/3)
        if "." in tok or "e" in tok.lower():
            out.add(tok)
        elif len(tok.lstrip("-")) >= 2:
            out.add(tok)
    return out


def _normalize_num(tok: str) -> str:
    """Normalise a numeric token for cross-format matching.

    Handles unicode minus and superscripts, scientific notation variants
    like "1.0×10⁻²", "1.0e-2", "1e-02". Returns a canonical lower-case
    decimal-or-scientific string. Returns "" if the token has no digits.
    """
    if not tok:
        return ""
    superscript_map = str.maketrans({
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
        "⁺": "+", "⁻": "-",
        "−": "-",
        "×": "*",
    })
    s = tok.translate(superscript_map).replace(" ", "")
    # collapse 'a*10^b' / 'a*10b' / 'a×10b' patterns to scientific
    s = re.sub(r"\*10\^?([+-]?\d+)", r"e\1", s)
    s = re.sub(r"\*10([+-]\d+)", r"e\1", s)
    if not re.search(r"\d", s):
        return ""
    try:
        f = float(s)
    except ValueError:
        return s.lower()
    if f == 0:
        return "0"
    # canonical: 6 sig figs, scientific
    return f"{f:.6e}"


# A "compound" numeric expression: optional sign + digits + decimal + optional
# exponent / multiplied-by-10 with superscript or 'e'.
COMPOUND_NUM_RE = re.compile(
    r"-?\d+(?:\.\d+)?(?:\s*[×x*]\s*10\s*[⁺⁻+-]?[⁰-⁹0-9]+|"
    r"e[+-]?\d+)?",
    re.IGNORECASE,
)


def hygiene_check(
    *,
    original_spec: str,
    rewrite: str,
    dropped_values: list[dict],
    level: str,
    kept_values: list[str],
) -> dict:
    """Check that the canonical numeric forms of *dropped* values do not
    appear in the rewrite, except where the same canonical value is also
    present in the *kept* values list (shared / ambiguous digits like
    "1.0 m" colliding with "1.0×10⁻²").
    """
    # canonical forms of every numeric in the kept-T3/T4 set
    kept_canon: set[str] = set()
    for kv in kept_values:
        for m in COMPOUND_NUM_RE.finditer(kv):
            c = _normalize_num(m.group(0))
            if c:
                kept_canon.add(c)

    # canonical forms of every numeric in the rewrite
    rewrite_canon: set[str] = set()
    for m in COMPOUND_NUM_RE.finditer(rewrite):
        c = _normalize_num(m.group(0))
        if c:
            rewrite_canon.add(c)

    # canonical-value occurrence count in the ORIGINAL spec.
    # A dropped value whose canonical also appears elsewhere in the
    # original (e.g. solver tolerance 1.0e-4 collides with the first
    # time-history sample 1.00000000e-04) is `shared` not `leaked`.
    # Normalise LaTeX scientific notation first so $1.0\times10^{-4}$
    # is captured as one numeric token, not split into 1.0 and 10.
    def _delatex(text: str) -> str:
        # \times10^{-4}  ->  ×10⁻⁴-style placeholder we can match
        text = re.sub(
            r"\\times\s*10\s*\^\s*\{?\s*([+-]?)\s*(\d+)\s*\}?",
            r"e\1\2",
            text,
        )
        # 10^{-4} / 10^-4 in case the prefix is dropped
        text = re.sub(
            r"10\s*\^\s*\{?\s*([+-]?)\s*(\d+)\s*\}?",
            r"10e\1\2",
            text,
        )
        return text

    original_norm = _delatex(original_spec)
    original_canon_counts: dict[str, int] = {}
    for m in COMPOUND_NUM_RE.finditer(original_norm):
        c = _normalize_num(m.group(0))
        if c:
            original_canon_counts[c] = original_canon_counts.get(c, 0) + 1

    leaks = []
    shared = []
    for entry in dropped_values:
        v = str(entry.get("value", ""))
        for m in COMPOUND_NUM_RE.finditer(v):
            tok = m.group(0)
            canon = _normalize_num(tok)
            if not canon:
                continue
            # ignore tiny structural integers (0, 1)
            try:
                fv = float(canon)
                if abs(fv) < 1.5 and fv == int(fv):
                    continue
            except ValueError:
                pass
            if canon in kept_canon:
                continue  # ambiguous; not a real leak
            if canon not in rewrite_canon:
                continue
            entry_out = {
                "tier": entry.get("tier"),
                "what": entry.get("what"),
                "leaked_value": tok,
                "canonical": canon,
                "original_occurrences": original_canon_counts.get(canon, 0),
            }
            if original_canon_counts.get(canon, 0) > 1:
                shared.append(entry_out)
            else:
                leaks.append(entry_out)

    # also: at HARD, the rewrite should be substantially shorter than original
    drop_ratio = 1.0 - (len(rewrite) / max(len(original_spec), 1))

    return {
        "ok": len(leaks) == 0,
        "leaks": leaks,
        "shared_values": shared,
        "drop_ratio": round(drop_ratio, 3),
        "rewrite_chars": len(rewrite),
        "original_chars": len(original_spec),
    }


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def call_rewriter(
    client: OpenAI,
    *,
    spec: str,
    level: str,
    model: str = "deepseek-v4-pro",
    max_retries: int = 3,
) -> dict:
    user = REWRITE_USER_TEMPLATE.format(
        level=level,
        tier_defs=TIER_DEFS,
        level_rules=LEVEL_RULES[level],
        spec=spec,
    )
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": REWRITE_SYSTEM},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            if "rewrite" not in data:
                raise ValueError("response missing 'rewrite' field")
            data.setdefault("kept_t4_values", [])
            data.setdefault("dropped_values", [])
            data.setdefault("kept_t3_values", [])
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"rewrite call failed after {max_retries}: {last_err}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def relax_one_task(
    *,
    client: OpenAI,
    task: str,
    src_path: Path,
    out_root: Path,
    levels: list[str],
    model: str,
) -> dict:
    spec = src_path.read_text()
    results: dict[str, dict] = {}
    for level in levels:
        out_dir = out_root / f"experiments_relaxed_{level}" / task
        out_dir.mkdir(parents=True, exist_ok=True)
        addendum = ADDENDUM_MEDIUM if level == "medium" else ADDENDUM_HARD
        data = call_rewriter(client, spec=spec, level=level, model=model)
        rewrite = data["rewrite"].rstrip() + addendum
        kept_values = list(data.get("kept_t4_values", [])) + list(
            data.get("kept_t3_values", [])
        )
        check = hygiene_check(
            original_spec=spec,
            rewrite=rewrite,
            dropped_values=data["dropped_values"],
            level=level,
            kept_values=kept_values,
        )
        (out_dir / "instructions.txt").write_text(rewrite)
        (out_dir / "_omitted.json").write_text(json.dumps({
            "task": task,
            "level": level,
            "model": model,
            "kept_t4_values": data["kept_t4_values"],
            "kept_t3_values": data["kept_t3_values"],
            "dropped_values": data["dropped_values"],
            "hygiene": check,
        }, indent=2))

        # also create the inputs/ and outputs/ subdirs the runner expects
        (out_dir / "inputs").mkdir(exist_ok=True)
        (out_dir / "outputs").mkdir(exist_ok=True)

        results[level] = check
        print(f"[{task}/{level}] drop_ratio={check['drop_ratio']:.3f} "
              f"leaks={len(check['leaks'])} "
              f"shared={len(check['shared_values'])}",
              flush=True)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--src-dir", type=Path, required=True)
    ap.add_argument("--out-root", type=Path, default=Path("data/eval"))
    ap.add_argument("--levels", nargs="+", default=["medium", "hard"])
    ap.add_argument("--model", default="deepseek-v4-pro")
    args = ap.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    summary: dict[str, dict] = {}
    failures: list[str] = []

    def _do_task(task: str) -> tuple[str, dict | None, str | None]:
        src = args.src_dir / task / "instructions.txt"
        if not src.exists():
            return task, None, f"missing {src}"
        try:
            res = relax_one_task(
                client=client,
                task=task,
                src_path=src,
                out_root=args.out_root,
                levels=args.levels,
                model=args.model,
            )
            return task, res, None
        except Exception as e:
            return task, None, str(e)

    # Parallelise across tasks. Each task does 2 sequential LLM calls
    # internally (medium + hard); cross-task threads keep wall time
    # bounded by the slowest task rather than the sum.
    with ThreadPoolExecutor(max_workers=min(8, len(args.tasks))) as ex:
        futs = {ex.submit(_do_task, t): t for t in args.tasks}
        for fut in as_completed(futs):
            task = futs[fut]
            task_id, res, err = fut.result()
            if err:
                print(f"FAIL {task_id}: {err}", flush=True)
                failures.append(task_id)
            else:
                summary[task_id] = res or {}
                # already printed inside relax_one_task

    summary_path = args.out_root / "_relax_specs_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps({
        "tasks": list(args.tasks),
        "levels": args.levels,
        "model": args.model,
        "summary": summary,
        "failures": failures,
    }, indent=2))
    print(f"\nSummary -> {summary_path}", flush=True)
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())

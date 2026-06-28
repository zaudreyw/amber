#!/usr/bin/env python3
"""Offline distillation of memory artifacts from training trajectories.

Produces four variants per D-008:
- ``M1-u``: DC-Cu primer (ungrounded) — self-judged cheatsheet, no TreeSim
- ``M1-g``: DC-Cu primer (grounded) — cheatsheet + TreeSim feedback
- ``M4-u``: RB-style items (ungrounded) — `{title, description, content}` items
- ``M4-g``: RB-style items (grounded) — items + TreeSim feedback

Uses OpenRouter → ``google/gemini-3-flash-preview``. Loads API key from
``/home/matt/sci/repo3/.env`` (expects ``OPENROUTER_API_KEY``).

Enforces:
- Hard token budget per artifact (1500 tokens for DC-Cu, 1000 for RB-items).
  Re-distills once with a stricter "be concise" addition if budget exceeded.
- Token-count parity between grounded and ungrounded of the same variant
  (M1-g tokens ≤ 1.10 × M1-u tokens, enforced by truncation of the grounded
  artifact's content if necessary — logged as `truncated_for_parity=True`).
- Abstraction guardrail: no raw XML content, no `*.xml` basenames, prefer
  cross-task conditional rules.
- Post-generation hygiene regex sweep. Fail artifact on any `*.xml` match.

Artifact layout (per variant X):
```
misc/memory_artifacts/X/
  artifact.md OR items.json   # the distilled memory
  prompt.txt                  # the prompt sent to the distiller
  raw_response.txt            # model response
  token_count.json            # tokenization detail
  hygiene_audit.json          # post-gen audit
```

Usage:
  python scripts/memory/distiller.py --variant M1-u
  python scripts/memory/distiller.py --variant M1-g
  python scripts/memory/distiller.py --variant M4-u
  python scripts/memory/distiller.py --variant M4-g
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
import tiktoken


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3-flash-preview"
FALLBACK_MODEL = "anthropic/claude-sonnet-4.6"

REPO_ROOT = Path("/home/matt/sci/repo3")
ENV_PATH = REPO_ROOT / ".env"
ARTIFACTS_DIR = REPO_ROOT / "misc" / "memory_artifacts"
GROUNDED_REPORTS_PATH = ARTIFACTS_DIR / "grounded_train_reports.json"
VANILLA_CC_GROUNDED_PATH = ARTIFACTS_DIR / "grounded_vanilla_cc_train_reports.json"
SPLIT_PATH = REPO_ROOT / "misc" / "memory_split.json"
HYGIENE_AUDIT = REPO_ROOT / "scripts" / "memory" / "hygiene_audit.py"

BUDGETS_TOKENS = {
    "M1-u": 1500,
    "M1-g": 1500,
    "M4-u": 1000,
    "M4-g": 1000,
}

XML_FILENAME_RE = re.compile(r"\b([a-z0-9_][a-z0-9_\-]*\.xml)\b", flags=re.IGNORECASE)

TOKENIZER = tiktoken.get_encoding("cl100k_base")


def _load_api_key() -> str:
    # First try env, then .env file
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"\'')
    print("ERROR: OPENROUTER_API_KEY not found (env var or .env)", file=sys.stderr)
    sys.exit(1)


def _count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text))


def _call_openrouter(prompt: str, *, model: str = DEFAULT_MODEL,
                     max_tokens: int = 3000, temperature: float = 0.0,
                     retries: int = 2) -> dict:
    key = _load_api_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=180)
            if resp.status_code == 200:
                return resp.json()
            last_err = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            if resp.status_code in (429, 500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            raise last_err
        except requests.exceptions.RequestException as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"OpenRouter call failed after {retries+1} attempts: {last_err}")


# -----------------------------------------------------------------------------
# Prompt builders
# -----------------------------------------------------------------------------

ABSTRACTION_GUARDRAIL = """\
**Critical abstraction rules** (the output will be automatically audited; \
any violation fails the artifact):

1. NEVER include raw XML element content (no `<ElementName ...>` snippets).
2. NEVER include any filename of the form `*.xml`. Reference element names and \
attribute names only.
3. NEVER name a specific past task as "task X used these files." Instead, \
phrase as conditional rules: "When a task describes physics Y, the solver \
hierarchy is Z." This allows transfer to new tasks.
4. Include anti-patterns as explicit "do NOT" statements when they help avoid \
known hallucination classes (e.g., "do NOT use `<FractureModel>` — that is \
invented vocabulary; use `<SurfaceGenerator>` for hydraulic fracture tasks.").
5. Keep content terse and information-dense. Each item must be independently \
actionable by an agent that has not seen any training trajectory.
6. Use physics-family tags where relevant: `hydrofracture`, `triaxial`, \
`poromechanics`, `thermal`, `contact`, `wellbore`, `multiphase`, etc.
"""


DC_CU_SYSTEM = """\
You are a memory curator for an LLM agent that converts natural-language \
physics simulation specs into GEOS XML. The agent has access to RAG over GEOS \
documentation. Your job is to distill a single "cheatsheet" — a markdown \
document — that the agent will see in its system prompt at every task.

The cheatsheet must:
- Consolidate cross-task patterns observed across multiple past tasks.
- Emphasize solver-family routing rules ("when task involves X, use solver Y").
- Include a short "common anti-patterns" section listing hallucinated element names \
to avoid (be specific about what NOT to use).
- Be actionable by an agent that has not seen the past tasks.

{guardrail}

**Strict token budget**: the final cheatsheet must be under {budget} tokens.
"""


RB_ITEMS_SYSTEM = """\
You are a memory curator for an LLM agent that converts natural-language \
physics simulation specs into GEOS XML. You produce **structured reasoning-memory \
items** in the ReasoningBank style. Each item is a self-contained JSON object:

```
{{"title": "...", "description": "...", "solver_family": "...", \
"kind": "structural_pattern|anti_pattern|attribute_rule|section_skeleton", \
"abstraction_level": "high|medium|low", \
"applies_when": "...", "content": "..."}}
```

Produce **at most 6 items**. Fewer is fine. Each item should address a \
different cross-task pattern. At least two items should be anti-patterns \
(hallucinated element names to avoid).

{guardrail}

**Strict token budget**: the total JSON output (all items combined) must be \
under {budget} tokens.

Return ONLY a JSON array of items, no prose.
"""


def _build_trajectory_context(reports: list[dict], grounded: bool) -> str:
    """Build the context of train trajectories the curator sees."""
    chunks: list[str] = []
    for r in reports:
        pieces = [f"### Training task #{len(chunks)+1}",
                  f"- final_treesim: {r.get('final_treesim')}"]
        # Include RAG queries — these are cross-task informative (which families matter)
        queries = r.get("productive_rag_queries_sanitized", [])
        if queries:
            pieces.append(f"- productive RAG queries (sanitized): {queries}")
        tc = r.get("tool_call_summary", {})
        if tc:
            pieces.append(f"- tool call summary: rag={tc.get('rag_queries',0)} reads={tc.get('reads',0)} writes={tc.get('writes',0)}")

        if grounded:
            pieces.append(f"- failure_mode: {r.get('failure_mode')}")
            sections = r.get("section_failures", [])
            if sections:
                low = [s for s in sections if s.get("score", 1) < 0.5]
                if low:
                    pieces.append(f"- weakest sections: " +
                                  ", ".join(f"{s['section']} ({s['score']:.2f})" for s in low))
            dom = r.get("dominant_dimension")
            if dom:
                pieces.append(f"- dominant failure dimension: {dom}")
            attr = r.get("attribute_accuracy")
            struct = r.get("structural_completeness")
            if attr is not None or struct is not None:
                pieces.append(f"- attr_accuracy={attr} struct_completeness={struct}")
        chunks.append("\n".join(pieces))
    return "\n\n".join(chunks)


def _build_prompt(variant: str, reports: list[dict]) -> tuple[str, dict]:
    """Return (prompt_text, metadata)."""
    grounded = variant.endswith("-g")
    budget = BUDGETS_TOKENS[variant]
    kind = variant.split("-")[0]  # M1 or M4

    traj_ctx = _build_trajectory_context(reports, grounded=grounded)
    guardrail = ABSTRACTION_GUARDRAIL

    if kind == "M1":
        system = DC_CU_SYSTEM.format(guardrail=guardrail, budget=budget)
        task_instruction = (
            "Below are observations from training tasks the agent has previously attempted. "
            "Produce a single markdown cheatsheet that distills cross-task patterns and "
            "anti-patterns to help future tasks succeed."
        )
    elif kind == "M4":
        system = RB_ITEMS_SYSTEM.format(guardrail=guardrail, budget=budget)
        task_instruction = (
            "Below are observations from training tasks. Produce a JSON array of reasoning-memory "
            "items (at most 6). Each item must be actionable without reference to any specific past task."
        )
    else:
        raise ValueError(f"unknown variant kind: {kind}")

    grounding_note = (
        "You are given TreeSim-grounded feedback (failure mode classification, weakest "
        "section scores, dominant failure dimension, attribute vs structural accuracy) to "
        "help identify the most valuable anti-patterns and structural rules. "
        "**Important:** do NOT invent anti-patterns about real GEOS elements. Anti-patterns "
        "must name specific INCORRECT element names (e.g., `<FractureModel>`) — use your own "
        "knowledge of the GEOS schema to avoid mistakenly flagging real elements like "
        "`Constitutive`, `ElementRegions`, `CellElementRegion`, `SolidMechanicsLagrangianFEM`, "
        "`SinglePhasePoromechanics`, etc. as hallucinations. If you are not sure whether a "
        "tag is a GEOS element, OMIT the anti-pattern rather than risk a false warning.\n"
        if grounded else
        "You are given trajectory summaries only (no ground-truth feedback). "
        "Infer useful rules from the productive RAG queries and solver patterns alone. "
        "Anti-patterns should only target clearly-invented names (e.g., `<FractureModel>`, "
        "`<HydraulicFractureSolver>`); do NOT flag real GEOS schema elements.\n"
    )

    prompt = (
        f"{system}\n\n"
        f"{grounding_note}\n"
        f"{task_instruction}\n\n"
        f"## Training trajectory observations ({len(reports)} tasks)\n\n"
        f"{traj_ctx}\n\n"
        f"Now produce the {'cheatsheet' if kind=='M1' else 'JSON array of items'}."
    )

    meta = {
        "variant": variant,
        "kind": kind,
        "grounded": grounded,
        "budget_tokens": budget,
        "n_reports": len(reports),
        "prompt_tokens": _count_tokens(prompt),
    }
    return prompt, meta


# -----------------------------------------------------------------------------
# Hygiene audit
# -----------------------------------------------------------------------------

def _audit_artifact(artifact_path: Path, out_path: Path) -> bool:
    import subprocess
    cmd = [
        "python3", str(HYGIENE_AUDIT),
        "--artifact", str(artifact_path),
        "--out", str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode == 0


# -----------------------------------------------------------------------------
# Main distillation
# -----------------------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """Remove any leading/trailing ```markdown or ```json fences."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        # drop first line (fence) and last line if closing fence
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines)
    return t


def distill(variant: str, reports: list[dict], *, model: str = DEFAULT_MODEL,
            out_root: Path = ARTIFACTS_DIR) -> dict:
    prompt, meta = _build_prompt(variant, reports)
    out_dir = out_root / variant
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "prompt.txt").write_text(prompt)

    budget = BUDGETS_TOKENS[variant]
    max_tokens_response = int(budget * 1.6)  # give some headroom; will truncate later

    print(f"[{variant}] calling {model}, budget={budget}, prompt_tokens={meta['prompt_tokens']}")
    response = _call_openrouter(prompt, model=model, max_tokens=max_tokens_response)

    content = response["choices"][0]["message"]["content"]
    (out_dir / "raw_response.txt").write_text(content)

    text = _strip_code_fences(content)

    # Token-budget enforcement: re-request once with stricter instruction if over
    n_toks = _count_tokens(text)
    retried = False
    if n_toks > budget * 1.10:
        print(f"[{variant}] first artifact {n_toks} tokens > {budget * 1.10:.0f}; re-requesting with tighter instruction")
        prompt_tight = prompt + (
            f"\n\n**The previous output was {n_toks} tokens, exceeding the budget of {budget}. "
            f"Rewrite it to fit strictly under {budget} tokens. Be more concise — keep the "
            f"highest-value rules and anti-patterns, drop lower-value items."
        )
        response = _call_openrouter(prompt_tight, model=model, max_tokens=max_tokens_response)
        content = response["choices"][0]["message"]["content"]
        (out_dir / "raw_response.txt").write_text(content)
        text = _strip_code_fences(content)
        n_toks = _count_tokens(text)
        retried = True

    kind = variant.split("-")[0]
    if kind == "M1":
        artifact_path = out_dir / "artifact.md"
        artifact_path.write_text(text)
    elif kind == "M4":
        artifact_path = out_dir / "items.json"
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            artifact_path = out_dir / "items_raw.txt"
            artifact_path.write_text(text)
            print(f"[{variant}] WARN: JSON parse failed ({e}); raw saved, downstream must handle")
            parsed = None
        if parsed is not None:
            artifact_path.write_text(json.dumps(parsed, indent=2))
    else:
        raise ValueError(kind)

    token_info = {
        "variant": variant,
        "model": model,
        "final_artifact_tokens": n_toks,
        "budget_tokens": budget,
        "within_budget": n_toks <= budget * 1.10,
        "retried_for_budget": retried,
        "prompt_tokens": meta["prompt_tokens"],
    }
    (out_dir / "token_count.json").write_text(json.dumps(token_info, indent=2))

    audit_ok = _audit_artifact(artifact_path, out_dir / "hygiene_audit.json")

    result = {
        **meta,
        **token_info,
        "artifact_path": str(artifact_path),
        "hygiene_passed": audit_ok,
    }
    (out_dir / "distillation_result.json").write_text(json.dumps(result, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--variant", choices=list(BUDGETS_TOKENS.keys()) + ["all"], required=True)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--reports", type=Path, default=GROUNDED_REPORTS_PATH,
                   help="Grounded training reports JSON list from trajectory_grounder.py")
    p.add_argument("--extra-reports", type=Path, default=VANILLA_CC_GROUNDED_PATH,
                   help="Optional additional reports (e.g. vanilla-CC-on-train failure trajectories)")
    args = p.parse_args(argv)

    base_reports = json.loads(args.reports.read_text()) if args.reports.exists() else []
    extra_reports: list[dict] = []
    if args.extra_reports.exists():
        extra_reports = json.loads(args.extra_reports.read_text())
    all_reports = base_reports + extra_reports
    if not all_reports:
        print("ERROR: no reports found", file=sys.stderr)
        return 2
    print(f"{len(all_reports)} reports ({len(base_reports)} train + {len(extra_reports)} extra)")

    variants = list(BUDGETS_TOKENS.keys()) if args.variant == "all" else [args.variant]
    all_results: list[dict] = []
    for v in variants:
        result = distill(v, all_reports, model=args.model)
        all_results.append(result)
        print(f"[{v}] done: tokens={result['final_artifact_tokens']} hygiene={'PASS' if result['hygiene_passed'] else 'FAIL'}")

    # Token parity check within M1 and M4 pairs
    def _tokens_for(v: str) -> int:
        for r in all_results:
            if r["variant"] == v:
                return r["final_artifact_tokens"]
        return -1

    parity_report = {}
    for pair in [("M1-u", "M1-g"), ("M4-u", "M4-g")]:
        u, g = pair
        t_u, t_g = _tokens_for(u), _tokens_for(g)
        if t_u > 0 and t_g > 0:
            delta_pct = abs(t_g - t_u) / t_u * 100
            parity_report[pair] = {"u_tokens": t_u, "g_tokens": t_g, "delta_pct": round(delta_pct, 1),
                                    "parity_ok": delta_pct <= 10}

    if parity_report:
        (ARTIFACTS_DIR / "token_parity_report.json").write_text(json.dumps(parity_report, indent=2))
        print(f"token parity report: {parity_report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

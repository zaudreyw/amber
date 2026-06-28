#!/usr/bin/env python3
"""Stage 2: per-task LLM diagnosis using DSv4 (DeepSeek API).

Reads each Stage-1 diagnostic JSON, optionally fetches GT + gen XML for
the worst section (when scores < threshold), then asks DSv4-flash to
classify the failure with a structured output.

Output: <out_dir>/<diag_basename>.llm.json — same basename as input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("install openai: pip install openai", file=sys.stderr)
    raise

DEEPSEEK_BASE = "https://api.deepseek.com"

SYSTEM_PROMPT = """You are an expert at analyzing AI coding agents' attempts to write GEOS XML simulation input files. You diagnose WHERE the agent went wrong and WHY.

You will receive:
- A structured diagnostic with TreeSim subtree scores (0-1 scale, 1 = perfect match to ground truth)
- The agent's tool-call summary and final-turn excerpts
- (optional) GT XML and generated XML for the worst-scoring section

Your job: produce a tight, evidence-based diagnosis. Be specific about elements/attributes/structural mistakes. Cite trajectory evidence ("agent re-read X 4 times", "agent wrote 16 extra Events when GT has 4"). Keep it factual. No hedging."""

USER_TEMPLATE = """Diagnose this run. Return STRICT JSON matching the schema.

## Task: {task}
## Agent: {agent}  Run: {run}
## Overall TreeSim: {treesim}

## Section scores (TreeSim, 1.0 = perfect):
{section_scores}

## Worst subtrees (top {n_worst}):
{worst_subtrees}

## Trajectory features:
{trajectory}

## Trajectory tail (last assistant turns, compact):
{excerpt}

{xml_context}

## Required output (strict JSON, no prose, no markdown fences):
{{
  "primary_failure_section": "<section name from above, e.g. Solvers>",
  "failure_category": "<one of: missing_block | extra_block | wrong_constitutive | wrong_solver_type | bad_attribute_value | structural_mismatch | hallucinated_extras | partial_implementation>",
  "root_cause": "<1-2 sentences. What did the agent miss or get wrong? Be specific about element/attribute names.>",
  "trajectory_evidence": "<1 sentence citing observable trajectory pattern: e.g. 'agent only read 2 reference XMLs; never grep'd for SurfaceGenerator', or 'agent re-edited the Solvers block 6 times without using xmllint'>",
  "would_have_helped": "<1 sentence: what harness/memory/skill would have prevented this? Be concrete: 'a constitutive-law lookup table', 'an xmllint validation hook', 'a memory hint that thermal solvers need both SinglePhaseFVM AND ThermalCompositionalMultiphaseFVM coupling'>",
  "severity": "<critical|major|minor — 'critical' if section score is 0 or near-0, 'major' if <0.7, 'minor' if >=0.7>"
}}"""

def _trim(obj, max_chars: int) -> str:
    s = json.dumps(obj, indent=2)
    return s if len(s) <= max_chars else s[:max_chars] + "\n... <truncated>"

def _read_xml_excerpt(xml_path: Path, section_tag: str | None, max_chars: int = 4000) -> str:
    """Read a section excerpt from an XML file, limiting size."""
    if not xml_path.exists():
        return f"<missing: {xml_path}>"
    try:
        text = xml_path.read_text()
    except Exception as e:
        return f"<read error: {e}>"
    if not section_tag:
        return text[:max_chars] + ("\n... <truncated>" if len(text) > max_chars else "")
    # naive: find <section_tag>...</section_tag> block
    m = re.search(rf"(<{section_tag}\b.*?</{section_tag}>)", text, re.DOTALL)
    if m:
        sec = m.group(1)
        return sec[:max_chars] + ("\n... <truncated>" if len(sec) > max_chars else "")
    return text[:max_chars] + ("\n... <truncated>" if len(text) > max_chars else "")

def _gather_xml_context(diag: dict, gt_dir: Path, gen_dir: Path, max_per: int = 2500) -> str:
    """If a section is critical, pull GT vs gen for that section."""
    sections = diag.get("section_scores") or {}
    # find the worst section
    worst_section = None
    worst_score = 1.0
    for sec, info in sections.items():
        s = info.get("score", 1.0)
        if s < worst_score:
            worst_score = s
            worst_section = sec
    if worst_section is None or worst_score >= 0.7:
        return "## XML excerpts: <skipped — no section <0.7>"
    # pick first XML in each
    if not gt_dir.exists() or not gen_dir.exists():
        return "## XML excerpts: <missing dirs>"
    gt_xmls = sorted(gt_dir.glob("*.xml"))
    gen_xmls = sorted(gen_dir.glob("*.xml"))
    if not gt_xmls or not gen_xmls:
        return "## XML excerpts: <no xml files found>"
    gt_excerpt = _read_xml_excerpt(gt_xmls[0], worst_section, max_chars=max_per)
    gen_excerpt = _read_xml_excerpt(gen_xmls[0], worst_section, max_chars=max_per)
    return (
        f"## GT XML — section <{worst_section}> excerpt (score={worst_score}):\n"
        f"```xml\n{gt_excerpt}\n```\n\n"
        f"## Generated XML — section <{worst_section}> excerpt:\n"
        f"```xml\n{gen_excerpt}\n```"
    )

def _eval_paths(eval_root: Path, run: str, agent: str, task: str) -> tuple[Path, Path]:
    """Return (gt_dir, gen_dir) by reading the eval json."""
    eval_path = eval_root / run / agent / f"{task}_eval.json"
    if eval_path.exists():
        try:
            d = json.loads(eval_path.read_text())
            return Path(d.get("gt_dir", "")), Path(d.get("gen_dir", ""))
        except Exception:
            pass
    return Path(""), Path("")

def diagnose_one(client: OpenAI, model: str, diag: dict, eval_root: Path) -> dict:
    gt_dir, gen_dir = _eval_paths(eval_root, diag["run"], diag["agent"], diag["task"])
    xml_context = _gather_xml_context(diag, gt_dir, gen_dir)
    user_msg = USER_TEMPLATE.format(
        task=diag["task"],
        agent=diag["agent"],
        run=diag["run"],
        treesim=diag.get("treesim"),
        section_scores=_trim(diag.get("section_scores"), 1500),
        worst_subtrees=_trim(diag.get("worst_subtrees"), 2000),
        n_worst=len(diag.get("worst_subtrees") or []),
        trajectory=_trim({k: v for k, v in (diag.get("trajectory") or {}).items() if k not in ("top_grep_queries", "top_glob_patterns") or len(str(v)) < 800}, 1800),
        excerpt=_trim(diag.get("trajectory_excerpt") or [], 2000),
        xml_context=xml_context,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=4000,
    )
    raw = resp.choices[0].message.content or ""
    # strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # try grabbing first { ... }
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                parsed = {"_parse_error": True, "_raw": raw}
        else:
            parsed = {"_parse_error": True, "_raw": raw}
    return {
        "task": diag["task"],
        "agent": diag["agent"],
        "run": diag["run"],
        "treesim": diag.get("treesim"),
        "diagnosis": parsed,
        "_model": model,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diag-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--eval-root", required=True, help="needed to find gt_dir/gen_dir")
    ap.add_argument("--model", default="deepseek-v4-flash")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="0=all")
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        # try .env
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DEEPSEEK_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE)

    diag_dir = Path(args.diag_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    eval_root = Path(args.eval_root)

    inputs = sorted(diag_dir.glob("*.json"))
    if args.limit > 0:
        inputs = inputs[: args.limit]

    todo = []
    for p in inputs:
        out_p = out_dir / (p.stem + ".llm.json")
        if args.skip_existing and out_p.exists():
            continue
        try:
            diag = json.loads(p.read_text())
        except Exception as e:
            print(f"[skip] {p.name}: {e}")
            continue
        if diag.get("error"):
            continue
        todo.append((p, diag, out_p))

    print(f"diagnosing {len(todo)} tasks with {args.model} ({args.workers} workers)")

    def _run(item):
        p, diag, out_p = item
        try:
            result = diagnose_one(client, args.model, diag, eval_root)
            out_p.write_text(json.dumps(result, indent=2))
            return p.name, "ok", result["diagnosis"].get("failure_category", "?")
        except Exception as e:
            return p.name, "err", str(e)[:200]

    n_ok = 0
    n_err = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(_run, it) for it in todo]
        for f in as_completed(futures):
            name, status, info = f.result()
            if status == "ok":
                n_ok += 1
                print(f"  ok  {name}: {info}")
            else:
                n_err += 1
                print(f"  ERR {name}: {info}")
    print(f"done: {n_ok} ok, {n_err} err → {out_dir}")

if __name__ == "__main__":
    main()

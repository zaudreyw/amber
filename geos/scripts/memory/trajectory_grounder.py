#!/usr/bin/env python3
"""Convert a training trajectory + TreeSim eval into a structured grounded feedback report.

Per training task, emits a compact JSON dict the distiller can ingest:

```
{
  "task_id": ...,
  "final_treesim": 0.94,
  "failure_mode": "success" | "F1_schema_hallucination" | "F2_attr_drift" | ...,
  "section_failures": [{"section": "Solvers", "score": 0.0}, ...],
  "top_missed_elements": ["SurfaceElementRegion", ...],
  "top_hallucinated_elements": ["Fracture", ...],
  "dominant_dimension": "element_type_match",
  "attr_score": 0.65,
  "structural_completeness": 0.42,
  "tool_call_summary": {"rag_queries": 14, "reads": 9, ...},
  "productive_rag_queries_sanitized": [...],
  "agent_response_tail": "...last 500 chars of agent response..."
}
```

Inputs (per task):
  - events.jsonl path under the trajectory run dir
  - eval JSON (treesim section scores, match_summary, dimension scores)
  - status.json (tool counts, agent response)

The grounder DOES NOT emit:
  - Raw XML content
  - File basenames (`*.xml`) — stripped before return, regex-enforced
  - Any test-task blocked basename substrings

Usage:
  from scripts.memory.trajectory_grounder import ground_trajectory
  report = ground_trajectory(run_dir=..., task_id=...)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


XML_FILENAME_RE = re.compile(r"\b([a-z0-9_][a-z0-9_\-]*\.xml)\b", flags=re.IGNORECASE)


def _sanitize(s: str) -> str:
    return XML_FILENAME_RE.sub("<xml_filename_stripped>", s)


def _coerce_count(val: Any) -> int:
    """match_summary lists may be materialized as int counts in older eval JSONs."""
    if isinstance(val, int):
        return val
    if isinstance(val, list):
        return len(val)
    return 0


def _classify_failure_mode(eval_data: dict, final_score: float) -> str:
    """Rough failure-mode tag based on dimension scores + section patterns.

    Uses thresholds from XN-014:
    - F1 schema hallucination: element_type_match low AND many gen_unmatched
    - F2 attr drift: attribute_accuracy low AND structural_completeness high
    - F3 missing components: structural_completeness low AND n_gt_unmatched high
    - F4 wrong solver class: Solvers section 0 AND structural_completeness high
    - success: final_score >= 0.7 and no dominant failure
    """
    if final_score is None or final_score >= 0.7:
        return "success"

    dims = eval_data.get("dimension_scores", {})
    sections = eval_data.get("treesim_section_scores", {})
    match = eval_data.get("match_summary", {})
    n_gt_unmatched = _coerce_count(match.get("gt_unmatched"))
    n_gen_unmatched = _coerce_count(match.get("gen_unmatched"))

    elem_type = dims.get("element_type_match", 1.0) or 0.0
    attr_acc = dims.get("attribute_accuracy", 1.0) or 0.0
    struct = dims.get("structural_completeness", 1.0) or 0.0

    if elem_type < 0.4 and n_gen_unmatched >= 5:
        return "F1_schema_hallucination"
    if attr_acc < 0.6 and struct >= 0.5:
        return "F2_attr_drift"
    if struct < 0.5 and n_gt_unmatched >= 10:
        return "F3_missing_components"
    solvers_score = sections.get("Solvers", 1.0) or 0.0
    if solvers_score < 0.3 and struct >= 0.5:
        return "F4_wrong_solver_class"
    return "mixed_failure"


def _extract_tool_call_summary(status_data: dict) -> dict:
    tc = status_data.get("per_tool_counts", {}) or {}
    rag_count = sum(v for k, v in tc.items() if "geos-rag" in k)
    reads = tc.get("Read", 0)
    writes = tc.get("Write", 0)
    edits = tc.get("Edit", 0)
    bashes = tc.get("Bash", 0)
    return {
        "rag_queries": rag_count,
        "reads": reads,
        "writes": writes,
        "edits": edits,
        "bashes": bashes,
        "total": sum(tc.values()),
    }


def _extract_productive_rag_queries(events_path: Path, max_n: int = 5) -> list[str]:
    """Return up to max_n RAG queries from the events stream, sanitized."""
    if not events_path.exists():
        return []
    queries: list[str] = []
    try:
        for line in events_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") != "assistant":
                continue
            for block in d.get("message", {}).get("content", []) or []:
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name", "")
                if "geos-rag" not in name:
                    continue
                q = block.get("input", {}).get("query", "") or block.get("input", {}).get("question", "")
                if q and isinstance(q, str):
                    queries.append(_sanitize(q)[:200])
            if len(queries) >= max_n * 3:
                break
    except Exception as e:
        print(f"  [grounder] event parse warn {events_path.parent.name}: {e}")
    # Dedupe preserving order
    seen = set()
    deduped: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
        if len(deduped) >= max_n:
            break
    return deduped


def _extract_top_elements(eval_data: dict, n: int = 8) -> tuple[list[str], list[str]]:
    """Top n element types from gt_unmatched and gen_unmatched, by frequency.

    Some older eval JSONs store only count ints; fall back to treesim_detail
    tree walk in that case.
    """
    match = eval_data.get("match_summary", {}) or {}
    gt_un_raw = match.get("gt_unmatched")
    gen_un_raw = match.get("gen_unmatched")

    # Prefer list form if available
    def _count_types(items) -> list[tuple[str, int]]:
        if not isinstance(items, list):
            return []
        counts: dict[str, int] = {}
        for it in items:
            if isinstance(it, dict):
                tag = it.get("tag") or it.get("element_type") or it.get("type") or "?"
            elif isinstance(it, str):
                tag = it
            else:
                tag = "?"
            counts[tag] = counts.get(tag, 0) + 1
        return sorted(counts.items(), key=lambda kv: -kv[1])

    top_missed_pairs = _count_types(gt_un_raw)
    top_hallucinated_pairs = _count_types(gen_un_raw)

    # Fallback: walk treesim_detail tree for unmatched tags when match_summary
    # has only int counts.
    if not top_missed_pairs and not top_hallucinated_pairs:
        td = eval_data.get("treesim_detail", {}) or {}
        missed_counts: dict[str, int] = {}

        def _walk(node: dict):
            if not isinstance(node, dict):
                return
            children = node.get("children")
            if isinstance(children, list):
                for ch in children:
                    if not isinstance(ch, dict):
                        continue
                    score = ch.get("score")
                    if score is None or score < 0.2:
                        tag = ch.get("tag", "?")
                        missed_counts[tag] = missed_counts.get(tag, 0) + 1
                    _walk(ch)

        _walk(td)
        top_missed_pairs = sorted(missed_counts.items(), key=lambda kv: -kv[1])

    # As a last resort, surface gen_element_types / gt_element_types summaries
    if not top_missed_pairs:
        gt_types = eval_data.get("gt_element_types", []) or []
        counts: dict[str, int] = {}
        for t in gt_types:
            if isinstance(t, str):
                counts[t] = counts.get(t, 0) + 1
        top_missed_pairs = sorted(counts.items(), key=lambda kv: -kv[1])[:n]
    if not top_hallucinated_pairs:
        gen_types = eval_data.get("gen_element_types", []) or []
        counts_g: dict[str, int] = {}
        for t in gen_types:
            if isinstance(t, str):
                counts_g[t] = counts_g.get(t, 0) + 1
        top_hallucinated_pairs = sorted(counts_g.items(), key=lambda kv: -kv[1])[:n]

    top_missed = [t for t, _ in top_missed_pairs[:n]]
    top_hallucinated = [t for t, _ in top_hallucinated_pairs[:n]]
    return top_missed, top_hallucinated


def _dominant_dim(eval_data: dict) -> str:
    dims = eval_data.get("dimension_scores", {}) or {}
    if not dims:
        return "unknown"
    weights = eval_data.get("weights", {}) or {}
    # The "dominant failure dimension" is the dim with the lowest weighted score
    scored: list[tuple[str, float]] = []
    for k, v in dims.items():
        w = weights.get(k, 1.0) or 1.0
        if v is None:
            continue
        scored.append((k, v * w))
    if not scored:
        return "unknown"
    return min(scored, key=lambda kv: kv[1])[0]


def ground_trajectory(
    run_dir: Path,
    task_id: str,
    eval_json_path: Path | None = None,
) -> dict[str, Any]:
    """Build a grounded feedback report for one training trajectory.

    Parameters
    ----------
    run_dir : Path to the run directory containing one subdir per task.
    task_id : name of the task subdirectory.
    eval_json_path : optional override for the eval JSON; defaults to
        searching `results/<run_name>/<agent_key>/<task_id>_eval.json`
        under `/data/shared/geophysics_agent_data/data/eval/results/`.
    """
    task_dir = run_dir / task_id
    if not task_dir.exists():
        raise FileNotFoundError(f"task dir missing: {task_dir}")

    # eval JSON
    if eval_json_path is None:
        run_name = run_dir.name
        # Infer agent key from parent of run_dir
        agent_key = run_dir.parent.name
        eval_json_path = (
            Path("/data/shared/geophysics_agent_data/data/eval/results")
            / run_name
            / agent_key
            / f"{task_id}_eval.json"
        )
    eval_data: dict = {}
    if eval_json_path.exists():
        try:
            eval_data = json.loads(eval_json_path.read_text())
        except Exception as e:
            print(f"  [grounder] eval parse warn: {e}")

    # status.json
    status_path = task_dir / "status.json"
    status_data: dict = {}
    if status_path.exists():
        try:
            status_data = json.loads(status_path.read_text())
        except Exception:
            pass

    events_path = task_dir / "events.jsonl"

    final_score = eval_data.get("treesim", status_data.get("final_treesim"))
    failure_mode = _classify_failure_mode(eval_data, final_score)

    # Section failures (bottom 5 by score)
    sections = eval_data.get("treesim_section_scores", {}) or {}
    section_failures = [
        {"section": k, "score": round(v, 3)}
        for k, v in sorted(sections.items(), key=lambda kv: kv[1] or 0)[:5]
    ]

    # Note: `gen_unmatched` from the eval JSON is "elements the agent wrote that did
    # not match GT by position/attribute" — it is NOT the same as "hallucinated element
    # names not in the GEOS schema." Passing these lists to the distiller caused false
    # anti-patterns (e.g., claiming `<Constitutive>` is a hallucination). We therefore
    # OMIT top_missed/top_hallucinated from the grounder output and let the distiller
    # rely on the semantic failure-mode classification + section scores + dominant
    # dimension, plus its own GEOS-schema knowledge. See distiller bug 2026-04-22.
    top_missed: list[str] = []
    top_hallucinated: list[str] = []

    dims = eval_data.get("dimension_scores", {}) or {}
    attr_score = dims.get("attribute_accuracy")
    struct_score = dims.get("structural_completeness")

    tool_summary = _extract_tool_call_summary(status_data)
    rag_queries = _extract_productive_rag_queries(events_path)

    resp = status_data.get("latest_agent_response", "")
    agent_response_tail = _sanitize(str(resp)[-500:]) if resp else ""

    report = {
        "task_id": task_id,
        "final_treesim": round(final_score, 4) if isinstance(final_score, (int, float)) else None,
        "failure_mode": failure_mode,
        "section_failures": section_failures,
        "top_missed_elements": top_missed,
        "top_hallucinated_elements": top_hallucinated,
        "dominant_dimension": _dominant_dim(eval_data),
        "attribute_accuracy": round(attr_score, 3) if isinstance(attr_score, (int, float)) else None,
        "structural_completeness": round(struct_score, 3) if isinstance(struct_score, (int, float)) else None,
        "tool_call_summary": tool_summary,
        "productive_rag_queries_sanitized": rag_queries,
        "agent_response_tail": agent_response_tail,
    }
    # Final hygiene sweep: stringify, strip any *.xml substring the classification path
    # might have missed
    report_str = json.dumps(report)
    if XML_FILENAME_RE.search(report_str):
        # Re-sanitize any accidentally-leaking string fields
        for k, v in list(report.items()):
            if isinstance(v, str):
                report[k] = _sanitize(v)
            elif isinstance(v, list):
                report[k] = [_sanitize(x) if isinstance(x, str) else x for x in v]
    return report


def ground_training_set(
    run_dir: Path,
    task_ids: list[str],
    out_path: Path,
) -> list[dict]:
    """Ground all tasks in task_ids and write to out_path as JSON list."""
    reports: list[dict] = []
    for tid in task_ids:
        try:
            r = ground_trajectory(run_dir, tid)
            reports.append(r)
        except FileNotFoundError as e:
            print(f"  [grounder] skip {tid}: {e}")
        except Exception as e:
            print(f"  [grounder] error {tid}: {e}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(reports, indent=2))
    print(f"wrote {len(reports)} reports → {out_path}")
    return reports


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", type=Path,
                   default=Path("/data/shared/geophysics_agent_data/data/eval/claude_code_repo3_plugin/repo3_eval_run4"))
    p.add_argument("--split", type=Path,
                   default=Path("/home/matt/sci/repo3/misc/memory_split.json"))
    p.add_argument("--out", type=Path,
                   default=Path("/home/matt/sci/repo3/misc/memory_artifacts/grounded_train_reports.json"))
    args = p.parse_args()
    split = json.loads(args.split.read_text())
    train_tasks = split["train"]
    print(f"grounding {len(train_tasks)} train trajectories from {args.run_dir}")
    ground_training_set(args.run_dir, train_tasks, args.out)

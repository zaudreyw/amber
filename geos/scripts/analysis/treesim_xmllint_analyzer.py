#!/usr/bin/env python3
"""Treesim component-wise loss + xmllint diff between two task runs.

For each big-swing task identifies:
- Which top-level sections lost the most points
- Which deeper nodes in `treesim_detail` lost the most points (worst
  by absolute lost-points = n_gt_children * (1 - score))
- Which schema errors `xmllint --schema` reports per condition

Importable function (for the orchestrator):
    analyze(task_dir_a, task_dir_b, eval_json_a, eval_json_b, schema_path)
        -> dict
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

DEFAULT_SCHEMA = Path("/data/shared/geophysics_agent_data/data/GEOS/src/coreComponents/schema/schema.xsd")


def _walk_node(node, depth=0, ancestors=None):
    """Yield (path, score, n_gt_children, lost_points) for each node."""
    ancestors = ancestors or []
    tag = node.get("tag") or "?"
    name = node.get("name") or ""
    label = f"{tag}[{name}]" if name else tag
    path = "/".join(ancestors + [label])
    score = node.get("score", 0.0) or 0.0
    n_gt = node.get("n_gt_children", 0) or 0
    lost = n_gt * (1.0 - score) if n_gt else 0.0
    yield path, score, n_gt, lost
    for c in node.get("children", []) or []:
        yield from _walk_node(c, depth+1, ancestors + [label])


def _node_loss_breakdown(eval_json: dict, top_n: int = 10) -> list:
    detail = eval_json.get("treesim_detail")
    if not detail:
        return []
    nodes = list(_walk_node(detail))
    # Sort by lost_points descending; only nodes with >= 1 lost point and score < 0.9
    nodes = [n for n in nodes if n[3] >= 0.5 and n[1] < 0.95]
    nodes.sort(key=lambda x: -x[3])
    return [
        {"path": p, "score": round(s, 3), "n_gt_children": n, "lost_points": round(l, 2)}
        for (p, s, n, l) in nodes[:top_n]
    ]


def _xmllint_one(xml_path: Path, schema_path: Path) -> list[str]:
    if not xml_path.exists():
        return [f"(file not found: {xml_path.name})"]
    try:
        r = subprocess.run(
            ["xmllint", "--noout", "--schema", str(schema_path), str(xml_path)],
            capture_output=True, text=True, timeout=20
        )
    except subprocess.TimeoutExpired:
        return ["(xmllint timeout)"]
    except FileNotFoundError:
        return ["(xmllint not installed on host)"]
    if r.returncode == 0:
        return []
    # stderr has the errors; trim
    errs = []
    for line in r.stderr.splitlines():
        line = line.strip()
        if not line: continue
        if line.endswith("validates"): continue
        # Strip the `<file>:` prefix if present
        if str(xml_path) in line:
            line = line.replace(str(xml_path) + ":", "").strip()
        errs.append(line)
    return errs[:8]


def _xmllint_dir(task_dir: Path, schema_path: Path) -> list[dict]:
    inputs = task_dir / "inputs"
    if not inputs.exists():
        return []
    out = []
    for xml in sorted(inputs.rglob("*.xml")):
        if ".claude_home" in str(xml): continue
        errs = _xmllint_one(xml, schema_path)
        out.append({"file": str(xml.relative_to(inputs)), "errors": errs})
    return out


def analyze(task_dir_a: Path, task_dir_b: Path,
            eval_json_a: Path, eval_json_b: Path,
            schema_path: Path = DEFAULT_SCHEMA) -> dict:
    a_eval = json.loads(Path(eval_json_a).read_text()) if Path(eval_json_a).exists() else {}
    b_eval = json.loads(Path(eval_json_b).read_text()) if Path(eval_json_b).exists() else {}
    a_secs = a_eval.get("treesim_section_scores") or {}
    b_secs = b_eval.get("treesim_section_scores") or {}
    keys = set(a_secs) | set(b_secs)
    section_loss = {k: round(b_secs.get(k, 0) - a_secs.get(k, 0), 3) for k in keys}
    a_nodes = _node_loss_breakdown(a_eval)
    b_nodes = _node_loss_breakdown(b_eval)
    a_xml = _xmllint_dir(Path(task_dir_a), schema_path)
    b_xml = _xmllint_dir(Path(task_dir_b), schema_path)
    a_errs_total = sum(len(x["errors"]) for x in a_xml)
    b_errs_total = sum(len(x["errors"]) for x in b_xml)
    bullets = []
    # Big section drops (B vs A)
    drop_secs = sorted([(k, v) for k, v in section_loss.items() if v <= -0.2], key=lambda kv: kv[1])
    for sec, d in drop_secs[:3]:
        bullets.append(f"Section '{sec}' dropped {d:+.2f} (A={a_secs.get(sec,0):.2f} → B={b_secs.get(sec,0):.2f})")
    if drop_secs == [] and a_eval.get("treesim", 0) - b_eval.get("treesim", 0) >= 0.1:
        bullets.append("Top-level section scores changed little — loss is in deeper sub-nodes (see node_loss_b)")
    if b_errs_total > a_errs_total + 1:
        bullets.append(f"B introduces {b_errs_total - a_errs_total} more xmllint errors than A "
                       f"({a_errs_total} → {b_errs_total})")
    return {
        "treesim_a": a_eval.get("treesim"),
        "treesim_b": b_eval.get("treesim"),
        "section_scores_a": a_secs,
        "section_scores_b": b_secs,
        "section_loss": section_loss,
        "node_loss_a": a_nodes,
        "node_loss_b": b_nodes,
        "xmllint_a": a_xml,
        "xmllint_b": b_xml,
        "xmllint_total_errors_a": a_errs_total,
        "xmllint_total_errors_b": b_errs_total,
        "summary_bullets": bullets,
    }


def main():
    if len(sys.argv) < 5:
        print("Usage: treesim_xmllint_analyzer.py <task_dir_a> <task_dir_b> <eval_json_a> <eval_json_b> [schema]")
        sys.exit(2)
    schema = Path(sys.argv[5]) if len(sys.argv) >= 6 else DEFAULT_SCHEMA
    out = analyze(
        Path(sys.argv[1]), Path(sys.argv[2]),
        Path(sys.argv[3]), Path(sys.argv[4]),
        schema_path=schema,
    )
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()

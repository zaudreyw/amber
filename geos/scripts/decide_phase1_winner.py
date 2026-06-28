#!/usr/bin/env python3
"""Read Phase 1 _summary.json files and pick the winning primer.
Outputs the path to stdout, ready for use as PHASE2_PRIMER env var.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import statistics

ROOT = Path("/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01")

CELLS = {
    "autocamp_p_contract": "plugin/GEOS_PRIMER_contract.md",
    "autocamp_p_method":   "plugin/GEOS_PRIMER_method.md",
}


def cell_score(agent: str) -> tuple[float, int]:
    """Return (mean_treesim, n_seeds_observed) over all runs of this agent."""
    seed_means = []
    for sf in (ROOT / "_results").rglob(f"*/_summary.json"):
        if sf.parent.name != agent:
            continue
        try:
            d = json.loads(sf.read_text())
        except Exception:
            continue
        scored = d.get("summary", {}).get("overall_score", {})
        m = scored.get("scored_mean")
        if m is None:
            results = d.get("results", [])
            scores = [r.get("treesim", 0) for r in results if isinstance(r.get("treesim"), (int, float))]
            if scores:
                m = sum(scores) / len(scores) * 10  # treesim back to 0-10 scale
        if isinstance(m, (int, float)):
            seed_means.append(m / 10.0)  # normalize to 0-1
    if not seed_means:
        return (0.0, 0)
    return (statistics.mean(seed_means), len(seed_means))


def main():
    print("# Phase 1 results", file=sys.stderr)
    best_agent = None
    best_score = -1
    for agent, primer in CELLS.items():
        score, n = cell_score(agent)
        print(f"  {agent}: {score:.3f} (n={n})", file=sys.stderr)
        if score > best_score:
            best_score = score
            best_agent = agent
    if best_agent is None:
        print("plugin/GEOS_PRIMER_method.md")  # safe default
        sys.exit(1)
    print(CELLS[best_agent])


if __name__ == "__main__":
    main()

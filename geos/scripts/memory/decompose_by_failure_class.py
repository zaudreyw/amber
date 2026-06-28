#!/usr/bin/env python3
"""Decompose memory-matrix results by failure-mode class (from XN-014).

For each memory condition, compute per-class mean delta vs A3 across the
failure classes defined in XN-014:

- F1 schema hallucination: pkn, Sneddon, ViscoDrucker, ModifiedCamClay,
  CasedContactThermoElastic
- F2 wrong-version drift: Mandel, ThermoporoelasticConsolidation,
  buckleyLeverett
- F3 missing components: Sneddon (also F1), IsothermalLeakyWell
- F4 under-specification: ThermalLeakyWell, ThermoporoelasticConsolidation
- plugin-already-good: DruckerPrager, DPWellbore, EDPWellbore, kgd,
  Deviated, ExtendedDruckerPrager, TutorialPoroelasticity

Usage:
  python scripts/memory/decompose_by_failure_class.py
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, stdev


TASK_CLASS: dict[str, list[str]] = {
    "F1_schema_hallucination": [
        "pknViscosityDominated",
        "TutorialSneddon",
        "AdvancedExampleViscoDruckerPrager",
        "AdvancedExampleModifiedCamClay",
        "AdvancedExampleCasedContactThermoElasticWellbore",
    ],
    "F2_wrong_version_drift": [
        "ExampleMandel",
        "ExampleThermoporoelasticConsolidation",
        "buckleyLeverettProblem",
    ],
    "F3_missing_components": [
        "ExampleIsothermalLeakyWell",
        "TutorialSneddon",
    ],
    "F4_under_specification": [
        "ExampleThermalLeakyWell",
        "ExampleThermoporoelasticConsolidation",
    ],
    "plugin_already_good": [
        "AdvancedExampleDruckerPrager",
        "AdvancedExampleExtendedDruckerPrager",
        "ExampleDPWellbore",
        "ExampleEDPWellbore",
        "kgdExperimentValidation",
        "AdvancedExampleDeviatedElasticWellbore",
        "TutorialPoroelasticity",
    ],
}


SCORES = Path("/home/matt/sci/repo3/misc/memory_artifacts/scores")
PAC1 = Path("/home/matt/sci/repo3/misc/pac1/scores")


def load_seeds(*paths: Path) -> list[dict[str, float]]:
    out = []
    for p in paths:
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        s = {r["experiment"]: float(r.get("treesim") or 0) for r in d.get("results", [])}
        out.append(s)
    return out


CONDITIONS: dict[str, list[Path]] = {
    "A3_RAG_SR": [PAC1 / "e23_summary.json", PAC1 / "e23s2_summary.json", PAC1 / "a3_s3_summary.json"],
    "A4p_RAG_Mem": [PAC1 / "a4prime_s1_summary.json", PAC1 / "a4prime_s2_summary.json"],
    "A5_FULL": [PAC1 / "e24_summary.json", PAC1 / "e24s2_summary.json", PAC1 / "e24s3_summary.json"],
    "M-placebo": [SCORES / f"mem_placebo_s{i}_summary.json" for i in (1, 2, 3)],
    "M1-u": [SCORES / f"mem_m1u_s{i}_summary.json" for i in (1, 2, 3)],
    "M1-g": [SCORES / f"mem_m1g_s{i}_summary.json" for i in (1, 2, 3)],
    "M3-g": [SCORES / f"mem_m3g_s{i}_summary.json" for i in (1, 2, 3)],
    "M4-u": [SCORES / f"mem_m4u_s{i}_summary.json" for i in (1, 2, 3)],
    "M4-g": [SCORES / f"mem_m4g_s{i}_summary.json" for i in (1, 2, 3)],
}


def class_mean(seeds: list[dict[str, float]], tasks: list[str]) -> float | None:
    per_task = []
    for t in tasks:
        vals = [s.get(t) for s in seeds if t in s]
        if vals:
            per_task.append(mean(vals))
    return mean(per_task) if per_task else None


def main() -> int:
    loaded = {name: load_seeds(*paths) for name, paths in CONDITIONS.items()}
    a3_seeds = loaded.get("A3_RAG_SR", [])
    a3_by_class = {c: class_mean(a3_seeds, tasks) for c, tasks in TASK_CLASS.items()}

    print(f'{"Condition":18} {"n":>3}  ', end="")
    for c in TASK_CLASS:
        print(f'{c[:15]:>16}', end="")
    print()

    for cname, seeds in loaded.items():
        n = len(seeds)
        if n == 0:
            continue
        print(f'{cname:18} {n:>3}  ', end="")
        for c, tasks in TASK_CLASS.items():
            cval = class_mean(seeds, tasks)
            if cval is None:
                print(f'{"—":>16}', end="")
            elif cname == "A3_RAG_SR":
                print(f'{cval:>16.3f}', end="")
            else:
                delta = cval - (a3_by_class.get(c) or 0)
                print(f'{cval:>8.3f}  {delta:+5.3f}', end="")
        print()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

"""Score Liam and Sahchit's buckleyLeverett_base.xml from the human baseline study.

Both humans produced only `buckleyLeverett_base.xml` within their hour timeslot.
The agent's task required two files (base + benchmark). We report two perspectives:

1. file-only TreeSim of base.xml vs GT base.xml (best-case for the human)
2. full directory TreeSim with the missing benchmark file (head-to-head with agent)
"""

import json
import shutil
import tempfile
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from eval.judge_geos import evaluate_directories, evaluate_files

HUMAN_DIR = Path("/home/matt/sci/repo3/data/human_baseline")
GT_DIR = Path(
    "/home/matt/sci/repo3/data/GEOS/inputFiles/compositionalMultiphaseFlow/"
    "benchmarks/buckleyLeverettProblem"
)
PARTICIPANTS = {
    "liam": HUMAN_DIR / "liam_buckleyLeverett_base.xml",
    "sahchit": HUMAN_DIR / "sahchit_buckleyLeverett_base.xml",
}

GT_BASE = GT_DIR / "buckleyLeverett_base.xml"


def file_score(gen: Path) -> dict:
    res = evaluate_files(GT_BASE, gen)
    return {
        "treesim": res.get("treesim"),
        "treesim_per_section": res.get("treesim_per_section"),
        "section_summary": {
            s: round(d, 3)
            for s, d in (res.get("treesim_per_section") or {}).items()
        },
    }


def dir_score(gen_xml: Path) -> dict:
    """Score as a directory: agent task required base+benchmark; humans only produced base."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copy(gen_xml, tmp_path / "buckleyLeverett_base.xml")
        gt_only_base_dir = tmp_path / "gt_only_base"
        gt_only_base_dir.mkdir()
        shutil.copy(GT_BASE, gt_only_base_dir / "buckleyLeverett_base.xml")

        partial_against_full = evaluate_directories(GT_DIR, tmp_path)
        partial_against_base = evaluate_directories(gt_only_base_dir, tmp_path)
    return {
        "treesim_full_gt": partial_against_full.get("treesim"),
        "treesim_base_only_gt": partial_against_base.get("treesim"),
    }


def main() -> None:
    out = {}
    for name, path in PARTICIPANTS.items():
        if not path.exists():
            out[name] = {"error": f"missing file {path}"}
            continue
        try:
            f_score = file_score(path)
            d_score = dir_score(path)
        except Exception as exc:
            out[name] = {"error": repr(exc)}
            continue
        out[name] = {
            "file_only_treesim": round(f_score["treesim"], 3) if f_score["treesim"] is not None else None,
            "file_only_per_section": f_score["section_summary"],
            "as_directory_full_gt": round(d_score["treesim_full_gt"], 3) if d_score["treesim_full_gt"] is not None else None,
            "as_directory_base_only_gt": round(d_score["treesim_base_only_gt"], 3) if d_score["treesim_base_only_gt"] is not None else None,
        }

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

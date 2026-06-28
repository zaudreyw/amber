"""
Programmatic XML evaluation for GEOS agent outputs.

Compares agent-generated XML against ground truth using hierarchical
bipartite matching that preserves parent-child context and handles
repeated tags (FieldSpecification, PeriodicEvent, etc.) correctly.

v2 improvements over original:
- Tree-aware matching instead of flat element list
- Bipartite matching for elements sharing the same tag
- PeriodicEvent ordering penalty
- All elements scored (no 38.6% dropout from setdefault)

v3 (XMLTreeSim):
- Single recursive tree-similarity headline metric
- Each GT node's score is proportional to its weight in the GT tree
- Old sub-metrics retained as diagnostics only
- Per-section TreeSim breakdowns reported
- Ordering reported as diagnostic, not baked into headline
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Constants
# ============================================================

REQUIRED_SECTIONS = {"Events", "Constitutive", "Mesh", "ElementRegions"}
OPTIONAL_SECTIONS = {"Functions", "Tasks", "Solvers", "NumericalMethods",
                     "Geometry", "FieldSpecifications", "Outputs"}
IGNORE_TAGS = {"Problem", "Included", "File"}

NUMERIC_RTOL = 1e-6

# Legacy dimension weights (retained for diagnostic backward compat)
WEIGHTS = {
    "structural_completeness": 0.15,
    "element_type_match": 0.35,
    "attribute_accuracy": 0.35,
    "tag_coverage": 0.15,
}

# TreeSim parameters
TREESIM_ALPHA = 0.3   # interior node: weight of own attrs vs subtree
TREESIM_BETA = 0.1    # penalty factor for extra (hallucinated) elements

_SCALAR_RE = re.compile(r"^[+-]?\d+(\.\d*)?([eE][+-]?\d+)?$")


# ============================================================
# XML loading with <Included> resolution
# ============================================================

def _resolve_included(
    root: ET.Element,
    base_dir: Path,
    _ancestors: Optional[Set[Path]] = None,
) -> ET.Element:
    # _ancestors is the chain of resolved file paths currently being expanded.
    # Skipping any candidate already in that chain breaks cycles from malformed
    # agent output (self-include, mutual include) without crashing the scorer.
    if _ancestors is None:
        _ancestors = set()
    for included in list(root.findall(".//Included")):
        parent = _find_parent(root, included)
        if parent is None:
            continue
        children = list(parent)
        try:
            insert_at = children.index(included)
        except ValueError:
            continue
        parent.remove(included)
        for file_tag in included.findall("File"):
            rel = file_tag.get("name") or file_tag.get("Name", "")
            if not rel:
                continue
            candidate = (base_dir / rel).resolve()
            if not candidate.exists():
                continue
            if candidate in _ancestors:
                continue
            try:
                child_root = ET.parse(candidate).getroot()
            except ET.ParseError:
                continue
            child_root = _resolve_included(
                child_root, candidate.parent, _ancestors | {candidate}
            )
            for elem in list(child_root):
                parent.insert(insert_at, elem)
                insert_at += 1
    return root


def _find_parent(root: ET.Element, target: ET.Element) -> ET.Element | None:
    for parent in root.iter():
        for child in list(parent):
            if child is target:
                return parent
    return None


def load_and_resolve_dir(directory: Path) -> ET.Element:
    xml_files = sorted(directory.rglob("*.xml"))
    if not xml_files:
        raise FileNotFoundError(f"No XML files found in {directory}")

    parsed: Dict[Path, ET.Element] = {}
    parse_errors: List[str] = []
    for xml_file in xml_files:
        try:
            parsed[xml_file.resolve()] = ET.parse(xml_file).getroot()
        except ET.ParseError as exc:
            parse_errors.append(f"{xml_file.name}: {exc}")

    if parse_errors and not parsed:
        raise ValueError(f"Failed to parse XMLs in {directory}: {'; '.join(parse_errors)}")

    referenced: set[Path] = set()
    for file_path, root in parsed.items():
        for file_tag in root.iter("File"):
            rel = file_tag.get("name") or file_tag.get("Name", "")
            if not rel:
                continue
            candidate = (file_path.parent / rel).resolve()
            if candidate.exists():
                referenced.add(candidate)

    entries = [fp for fp in parsed if fp not in referenced]
    if len(entries) == 1:
        return _resolve_included(parsed[entries[0]], entries[0].parent, {entries[0]})

    merged = ET.Element("Problem")
    for file_path, root in parsed.items():
        resolved = _resolve_included(root, file_path.parent, {file_path})
        for child in list(resolved):
            merged.append(child)
    return merged


def load_and_resolve_file(xml_path: Path) -> ET.Element:
    root = ET.parse(xml_path).getroot()
    return _resolve_included(root, xml_path.parent, {xml_path.resolve()})


# ============================================================
# Value comparison utilities
# ============================================================

def _parse_scalar(value: str) -> float | None:
    s = value.strip()
    if _SCALAR_RE.match(s):
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _parse_list(value: str) -> List[float] | None:
    tokens = [p.strip() for p in value.strip().strip("{").strip("}").split(",") if p.strip()]
    floats: List[float] = []
    for token in tokens:
        parsed = _parse_scalar(token)
        if parsed is None:
            return None
        floats.append(parsed)
    return floats if floats else None


def values_equivalent(v1: str, v2: str, rtol: float = NUMERIC_RTOL) -> bool:
    left = (v1 or "").strip()
    right = (v2 or "").strip()
    if left == right:
        return True

    n1 = _parse_scalar(left)
    n2 = _parse_scalar(right)
    if n1 is not None and n2 is not None:
        if n1 == 0.0 and n2 == 0.0:
            return True
        denom = max(abs(n1), abs(n2))
        return denom == 0.0 or abs(n1 - n2) / denom <= rtol

    l1 = _parse_list(left)
    l2 = _parse_list(right)
    if l1 is not None and l2 is not None and len(l1) == len(l2):
        return all(values_equivalent(str(a), str(b), rtol) for a, b in zip(l1, l2))

    return left.lower() == right.lower()


# ============================================================
# Tree-aware matching
# ============================================================

@dataclass
class MatchResult:
    """Result of recursive tree matching between GT and generated XML."""
    # Paired elements: (gt_elem, gen_elem, similarity_score)
    paired: List[Tuple[ET.Element, ET.Element, float]] = field(default_factory=list)
    # Unmatched GT elements (missing from generated)
    gt_unmatched: List[ET.Element] = field(default_factory=list)
    # Extra generated elements (not in GT)
    gen_unmatched: List[ET.Element] = field(default_factory=list)
    # Per-pair attribute details
    attr_details: List[Dict[str, Any]] = field(default_factory=list)


def compute_element_similarity(gt: ET.Element, gen: ET.Element,
                                rtol: float = NUMERIC_RTOL) -> float:
    """Compute similarity between two XML elements (0.0 to 1.0).

    Considers:
    - Tag match (must match, else 0)
    - name attribute match (strong signal)
    - Attribute value overlap
    """
    if gt.tag != gen.tag:
        return 0.0

    gt_attrs = dict(gt.attrib)
    gen_attrs = dict(gen.attrib)

    # Name match is a strong signal
    gt_name = gt_attrs.get("name", "")
    gen_name = gen_attrs.get("name", "")
    name_bonus = 0.0
    if gt_name and gen_name:
        name_bonus = 0.4 if gt_name == gen_name else 0.0

    # Attribute overlap (excluding name)
    all_keys = (set(gt_attrs) | set(gen_attrs)) - {"name"}
    if not all_keys:
        return 0.6 + name_bonus  # Tag matches, no attrs to compare

    matched = sum(
        1 for k in all_keys
        if k in gt_attrs and k in gen_attrs
        and values_equivalent(gt_attrs[k], gen_attrs[k], rtol)
    )
    attr_score = matched / len(all_keys) * 0.6

    return min(1.0, attr_score + name_bonus)


def _bipartite_match(gt_elems: List[ET.Element],
                     gen_elems: List[ET.Element],
                     rtol: float = NUMERIC_RTOL
                     ) -> Tuple[List[Tuple[int, int, float]], List[int], List[int]]:
    """Find optimal 1:1 matching between GT and generated elements.

    Uses greedy matching by descending similarity (exact Hungarian is overkill
    for groups of <15 elements, and greedy gives identical results when
    name-matching provides a clear signal).

    Returns:
        (matched_pairs, unmatched_gt_indices, unmatched_gen_indices)
        where matched_pairs = [(gt_idx, gen_idx, similarity), ...]
    """
    n_gt = len(gt_elems)
    n_gen = len(gen_elems)

    if n_gt == 0:
        return [], [], list(range(n_gen))
    if n_gen == 0:
        return [], list(range(n_gt)), []

    # Compute similarity matrix
    scores = []
    for i, gt in enumerate(gt_elems):
        for j, gen in enumerate(gen_elems):
            sim = compute_element_similarity(gt, gen, rtol)
            if sim > 0:
                scores.append((sim, i, j))

    # Greedy matching: pick highest similarity pairs first
    scores.sort(reverse=True)
    used_gt: Set[int] = set()
    used_gen: Set[int] = set()
    matched: List[Tuple[int, int, float]] = []

    for sim, gi, gj in scores:
        if gi not in used_gt and gj not in used_gen:
            matched.append((gi, gj, sim))
            used_gt.add(gi)
            used_gen.add(gj)

    unmatched_gt = [i for i in range(n_gt) if i not in used_gt]
    unmatched_gen = [j for j in range(n_gen) if j not in used_gen]

    return matched, unmatched_gt, unmatched_gen


def match_trees(gt_root: ET.Element, gen_root: ET.Element,
                rtol: float = NUMERIC_RTOL) -> MatchResult:
    """Recursively match GT and generated XML trees.

    Strategy:
    1. Group children of each node by tag
    2. For each tag group, run bipartite matching
    3. Recurse into matched pairs for their children
    """
    result = MatchResult()
    _match_children(gt_root, gen_root, result, rtol)
    return result


def _match_children(gt_parent: ET.Element, gen_parent: ET.Element,
                    result: MatchResult, rtol: float) -> None:
    """Match children of two parent elements and recurse."""
    gt_children = [c for c in gt_parent if isinstance(c.tag, str) and c.tag not in IGNORE_TAGS]
    gen_children = [c for c in gen_parent if isinstance(c.tag, str) and c.tag not in IGNORE_TAGS]

    # Group by tag
    gt_by_tag: Dict[str, List[ET.Element]] = defaultdict(list)
    gen_by_tag: Dict[str, List[ET.Element]] = defaultdict(list)
    for c in gt_children:
        gt_by_tag[c.tag].append(c)
    for c in gen_children:
        gen_by_tag[c.tag].append(c)

    all_tags = set(gt_by_tag) | set(gen_by_tag)

    for tag in all_tags:
        gt_group = gt_by_tag.get(tag, [])
        gen_group = gen_by_tag.get(tag, [])

        matched, unmatched_gt, unmatched_gen = _bipartite_match(gt_group, gen_group, rtol)

        # Record matched pairs and compute attribute details
        for gi, gj, sim in matched:
            gt_elem = gt_group[gi]
            gen_elem = gen_group[gj]
            result.paired.append((gt_elem, gen_elem, sim))

            # Detailed attribute comparison for this pair
            gt_attrs = dict(gt_elem.attrib)
            gen_attrs = dict(gen_elem.attrib)
            all_keys = set(gt_attrs) | set(gen_attrs)
            attr_matched = []
            attr_mismatched = []
            for k in all_keys:
                if k in gt_attrs and k in gen_attrs:
                    if values_equivalent(gt_attrs[k], gen_attrs[k], rtol):
                        attr_matched.append(k)
                    else:
                        attr_mismatched.append(f"{k}: GT={gt_attrs[k]!r} GEN={gen_attrs[k]!r}")
                elif k in gt_attrs:
                    attr_mismatched.append(f"{k}: missing in GEN")
                else:
                    attr_mismatched.append(f"{k}: extra in GEN")

            result.attr_details.append({
                "gt_tag": gt_elem.tag,
                "gt_name": gt_attrs.get("name", ""),
                "gen_name": gen_attrs.get("name", ""),
                "similarity": round(sim, 4),
                "attrs_matched": len(attr_matched),
                "attrs_total": len(all_keys),
                "mismatches": attr_mismatched,
            })

            # Recurse into children of matched pairs
            _match_children(gt_elem, gen_elem, result, rtol)

        # Record unmatched
        for idx in unmatched_gt:
            elem = gt_group[idx]
            result.gt_unmatched.append(elem)
            # Also count all descendants as unmatched
            for desc in elem.iter():
                if desc is not elem and isinstance(desc.tag, str) and desc.tag not in IGNORE_TAGS:
                    result.gt_unmatched.append(desc)
        for idx in unmatched_gen:
            elem = gen_group[idx]
            result.gen_unmatched.append(elem)
            for desc in elem.iter():
                if desc is not elem and isinstance(desc.tag, str) and desc.tag not in IGNORE_TAGS:
                    result.gen_unmatched.append(desc)


# ============================================================
# XMLTreeSim — recursive tree similarity
# ============================================================

def attr_similarity(gt: ET.Element, gen: ET.Element,
                    rtol: float = NUMERIC_RTOL) -> float:
    """Attribute-level similarity between two matched elements.

    Returns |matching attributes| / |union of attributes|.
    If neither element has attributes, returns 1.0 (vacuously correct).
    """
    gt_attrs = dict(gt.attrib)
    gen_attrs = dict(gen.attrib)
    all_keys = set(gt_attrs) | set(gen_attrs)
    if not all_keys:
        return 1.0
    matched = sum(
        1 for k in all_keys
        if k in gt_attrs and k in gen_attrs
        and values_equivalent(gt_attrs[k], gen_attrs[k], rtol)
    )
    return matched / len(all_keys)


@dataclass
class TreeSimDetail:
    """Per-node detail from TreeSim computation."""
    tag: str
    name: str
    score: float
    attr_score: float
    children_score: float  # -1 for leaves
    n_gt_children: int
    n_matched: int
    n_extra: int
    children: List["TreeSimDetail"] = field(default_factory=list)


def tree_sim(gt_node: ET.Element, gen_node: ET.Element,
             alpha: float = TREESIM_ALPHA, beta: float = TREESIM_BETA,
             rtol: float = NUMERIC_RTOL) -> Tuple[float, TreeSimDetail]:
    """Compute recursive tree similarity between GT and generated XML.

    Each GT child contributes equally (1/N_gt) to the parent score.
    Matched children contribute their attr_score (leaves) or a blend
    of attr_score and recursive subtree score (interior nodes).
    Unmatched GT children contribute 0. Extra gen children apply a
    small penalty.

    Returns (score, detail) where score is in [0, 1].
    """
    gt_children = [c for c in gt_node if isinstance(c.tag, str) and c.tag not in IGNORE_TAGS]
    gen_children = [c for c in gen_node if isinstance(c.tag, str) and c.tag not in IGNORE_TAGS]

    n_gt = len(gt_children)

    # Leaf node: score is just attribute similarity
    if n_gt == 0 and len(gen_children) == 0:
        a_score = attr_similarity(gt_node, gen_node, rtol)
        return a_score, TreeSimDetail(
            tag=gt_node.tag, name=gt_node.get("name", ""),
            score=a_score, attr_score=a_score, children_score=-1,
            n_gt_children=0, n_matched=0, n_extra=0,
        )

    # Group children by tag and run bipartite matching per group
    gt_by_tag: Dict[str, List[ET.Element]] = defaultdict(list)
    gen_by_tag: Dict[str, List[ET.Element]] = defaultdict(list)
    for c in gt_children:
        gt_by_tag[c.tag].append(c)
    for c in gen_children:
        gen_by_tag[c.tag].append(c)

    all_tags = set(gt_by_tag) | set(gen_by_tag)

    # Collect per-child scores and details
    child_scores: List[float] = []
    child_details: List[TreeSimDetail] = []
    total_extra = 0

    for tag in sorted(all_tags):
        gt_group = gt_by_tag.get(tag, [])
        gen_group = gen_by_tag.get(tag, [])

        matched, unmatched_gt, unmatched_gen = _bipartite_match(gt_group, gen_group, rtol)

        for gi, gj, _sim in matched:
            gt_elem = gt_group[gi]
            gen_elem = gen_group[gj]
            a_score = attr_similarity(gt_elem, gen_elem, rtol)

            gt_grandchildren = [c for c in gt_elem if isinstance(c.tag, str) and c.tag not in IGNORE_TAGS]
            if gt_grandchildren:
                subtree_score, subtree_detail = tree_sim(gt_elem, gen_elem, alpha, beta, rtol)
                child_score = alpha * a_score + (1 - alpha) * subtree_score
                subtree_detail.score = round(child_score, 4)
                subtree_detail.attr_score = round(a_score, 4)
                child_details.append(subtree_detail)
            else:
                child_score = a_score
                detail = TreeSimDetail(
                    tag=gt_elem.tag, name=gt_elem.get("name", ""),
                    score=round(child_score, 4), attr_score=round(a_score, 4),
                    children_score=-1,
                    n_gt_children=0, n_matched=0, n_extra=0,
                )
                child_details.append(detail)
            child_scores.append(child_score)

        # Unmatched GT children score 0
        for idx in unmatched_gt:
            elem = gt_group[idx]
            child_scores.append(0.0)
            child_details.append(TreeSimDetail(
                tag=elem.tag, name=elem.get("name", ""),
                score=0.0, attr_score=0.0, children_score=-1,
                n_gt_children=0, n_matched=0, n_extra=0,
            ))

        total_extra += len(unmatched_gen)

    # Compute this node's score
    if n_gt > 0:
        matched_score = sum(child_scores) / n_gt
    else:
        matched_score = 1.0  # GT has no children; gen has extras only

    extra_denom = n_gt + total_extra
    extra_penalty = beta * (total_extra / extra_denom) if extra_denom > 0 else 0.0

    node_score = max(0.0, min(1.0, matched_score - extra_penalty))

    # Own attribute score (for the node itself, not its children)
    own_attr = attr_similarity(gt_node, gen_node, rtol)

    detail = TreeSimDetail(
        tag=gt_node.tag, name=gt_node.get("name", ""),
        score=round(node_score, 4), attr_score=round(own_attr, 4),
        children_score=round(matched_score, 4),
        n_gt_children=n_gt, n_matched=len(child_scores) - sum(1 for s in child_scores if s == 0.0),
        n_extra=total_extra,
        children=child_details,
    )

    return node_score, detail


def tree_sim_section_scores(gt_root: ET.Element, gen_root: ET.Element,
                            alpha: float = TREESIM_ALPHA,
                            beta: float = TREESIM_BETA,
                            rtol: float = NUMERIC_RTOL,
                            ) -> Dict[str, Any]:
    """Compute TreeSim and return headline score + per-section breakdown."""
    score, detail = tree_sim(gt_root, gen_root, alpha, beta, rtol)
    section_scores = {}
    for child_detail in detail.children:
        key = child_detail.name or child_detail.tag
        section_scores[key] = child_detail.score
    return {
        "treesim": round(score, 4),
        "section_scores": section_scores,
        "detail": detail,
    }


# ============================================================
# Scoring functions (legacy diagnostics)
# ============================================================

def score_structural_completeness(gt_root: ET.Element,
                                   gen_root: ET.Element) -> Tuple[float, Dict[str, Any]]:
    """Check that required top-level sections are present."""
    gt_sections = {c.tag for c in gt_root if isinstance(c.tag, str)}
    gen_sections = {c.tag for c in gen_root if isinstance(c.tag, str)}
    required_in_gt = REQUIRED_SECTIONS & gt_sections
    if not required_in_gt:
        return 1.0, {"note": "GT has no required sections to check"}

    found = required_in_gt & gen_sections
    missing = required_in_gt - gen_sections
    return len(found) / len(required_in_gt), {
        "required_present": sorted(found),
        "required_missing": sorted(missing),
    }


def score_element_type_match(match: MatchResult,
                              gt_root: ET.Element,
                              gen_root: ET.Element) -> Tuple[float, Dict[str, Any]]:
    """Jaccard similarity of all XML tag types."""
    gt_types = {e.tag for e in gt_root.iter() if isinstance(e.tag, str)} - IGNORE_TAGS
    gen_types = {e.tag for e in gen_root.iter() if isinstance(e.tag, str)} - IGNORE_TAGS
    if not gt_types:
        return 1.0, {"note": "GT has no typed elements"}

    shared = gt_types & gen_types
    union = gt_types | gen_types
    score = len(shared) / len(union) if union else 1.0
    return score, {
        "gt_only": sorted(gt_types - gen_types),
        "gen_only": sorted(gen_types - gt_types),
        "shared": sorted(shared),
    }


def score_attribute_accuracy(match: MatchResult) -> Tuple[float, Dict[str, Any]]:
    """Attribute accuracy across all matched element pairs."""
    total_attrs = 0
    matched_attrs = 0

    for detail in match.attr_details:
        total_attrs += detail["attrs_total"]
        matched_attrs += detail["attrs_matched"]

    score = matched_attrs / total_attrs if total_attrs else 1.0

    # Top mismatches for reporting
    top_mismatches = [
        d for d in match.attr_details if d["mismatches"]
    ][:20]  # cap for readability

    return score, {
        "matched_attrs": matched_attrs,
        "total_attrs": total_attrs,
        "elements_compared": len(match.paired),
        "elements_unmatched_gt": len(match.gt_unmatched),
        "elements_unmatched_gen": len(match.gen_unmatched),
        "top_mismatches": top_mismatches,
    }


def score_tag_coverage(gt_root: ET.Element,
                       gen_root: ET.Element) -> Tuple[float, Dict[str, Any]]:
    """Recall: fraction of GT tag types present in generated."""
    gt_types = {e.tag for e in gt_root.iter() if isinstance(e.tag, str)} - IGNORE_TAGS
    gen_types = {e.tag for e in gen_root.iter() if isinstance(e.tag, str)} - IGNORE_TAGS
    if not gt_types:
        return 1.0, {"note": "GT has no types"}

    covered = gt_types & gen_types
    missing = gt_types - gen_types
    return len(covered) / len(gt_types), {
        "covered": sorted(covered),
        "missing": sorted(missing),
    }


def score_ordering(match: MatchResult, gt_root: ET.Element,
                   gen_root: ET.Element) -> Tuple[float, Dict[str, Any]]:
    """Check PeriodicEvent ordering within Events section.

    Uses Kendall tau distance: counts pairwise inversions between
    GT order and generated order of matched PeriodicEvents.
    Returns 1.0 if order is correct, lower if inverted.
    """
    # Find Events section in both
    gt_events = gt_root.find("Events")
    gen_events = gen_root.find("Events")
    if gt_events is None or gen_events is None:
        return 1.0, {"note": "No Events section to check ordering"}

    gt_periodic = [e for e in gt_events if e.tag == "PeriodicEvent"]
    gen_periodic = [e for e in gen_events if e.tag == "PeriodicEvent"]

    if len(gt_periodic) < 2:
        return 1.0, {"note": "Too few PeriodicEvents to check ordering"}

    # Match by name attribute
    gt_names = [e.get("name", f"unnamed_{i}") for i, e in enumerate(gt_periodic)]
    gen_names = [e.get("name", f"unnamed_{i}") for i, e in enumerate(gen_periodic)]

    # Build order mapping: for each GT name, find its position in generated
    gen_order = {name: idx for idx, name in enumerate(gen_names)}
    matched_gt_order = []
    matched_gen_order = []
    for gt_idx, name in enumerate(gt_names):
        if name in gen_order:
            matched_gt_order.append(gt_idx)
            matched_gen_order.append(gen_order[name])

    if len(matched_gt_order) < 2:
        return 1.0, {"note": "Too few matched PeriodicEvents for ordering check"}

    # Count inversions (Kendall tau)
    n = len(matched_gen_order)
    inversions = 0
    max_inversions = n * (n - 1) // 2
    for i in range(n):
        for j in range(i + 1, n):
            if matched_gen_order[i] > matched_gen_order[j]:
                inversions += 1

    score = 1.0 - (inversions / max_inversions) if max_inversions > 0 else 1.0
    return score, {
        "gt_order": gt_names,
        "gen_order": gen_names,
        "inversions": inversions,
        "max_inversions": max_inversions,
        "matched_count": len(matched_gt_order),
    }


# ============================================================
# Main evaluation entry points
# ============================================================

def _detail_to_dict(detail: TreeSimDetail, max_depth: int = 3, depth: int = 0) -> Dict[str, Any]:
    """Convert TreeSimDetail to a serializable dict, capping recursion depth."""
    d: Dict[str, Any] = {
        "tag": detail.tag,
        "name": detail.name,
        "score": detail.score,
        "attr_score": detail.attr_score,
        "n_gt_children": detail.n_gt_children,
        "n_matched": detail.n_matched,
        "n_extra": detail.n_extra,
    }
    if detail.children_score >= 0:
        d["children_score"] = detail.children_score
    if detail.children and depth < max_depth:
        d["children"] = [_detail_to_dict(c, max_depth, depth + 1) for c in detail.children]
    return d


def evaluate_xml(gt_root: ET.Element, gen_root: ET.Element,
                 rtol: float = NUMERIC_RTOL) -> Dict[str, Any]:
    """Evaluate generated XML against ground truth.

    Headline metric: XMLTreeSim — recursive tree similarity.
    Legacy dimension scores retained as diagnostics.
    """
    # --- Headline: TreeSim ---
    ts_result = tree_sim_section_scores(gt_root, gen_root, rtol=rtol)
    treesim_score = ts_result["treesim"]
    section_scores = ts_result["section_scores"]
    ts_detail = ts_result["detail"]

    # Scale to 0-10 for backward compat with downstream consumers
    overall_score = round(treesim_score * 10.0, 2)

    # --- Legacy diagnostics (not used in headline) ---
    match = match_trees(gt_root, gen_root, rtol)

    s_struct, d_struct = score_structural_completeness(gt_root, gen_root)
    s_types, d_types = score_element_type_match(match, gt_root, gen_root)
    s_attrs, d_attrs = score_attribute_accuracy(match)
    s_cov, d_cov = score_tag_coverage(gt_root, gen_root)
    s_order, d_order = score_ordering(match, gt_root, gen_root)

    dimension_scores = {
        "structural_completeness": round(s_struct, 4),
        "element_type_match": round(s_types, 4),
        "attribute_accuracy": round(s_attrs, 4),
        "tag_coverage": round(s_cov, 4),
    }

    gt_types = {e.tag for e in gt_root.iter() if isinstance(e.tag, str)} - IGNORE_TAGS
    gen_types = {e.tag for e in gen_root.iter() if isinstance(e.tag, str)} - IGNORE_TAGS

    return {
        "overall_score": overall_score,
        "overall_01": treesim_score,
        "treesim": treesim_score,
        "treesim_section_scores": section_scores,
        "treesim_detail": _detail_to_dict(ts_detail),
        # Legacy diagnostics
        "dimension_scores": dimension_scores,
        "ordering_score": round(s_order, 4),
        "weights": dict(WEIGHTS),
        "details": {
            "structural_completeness": d_struct,
            "element_type_match": d_types,
            "attribute_accuracy": d_attrs,
            "tag_coverage": d_cov,
            "ordering": d_order,
        },
        "match_summary": {
            "paired_elements": len(match.paired),
            "gt_unmatched": len(match.gt_unmatched),
            "gen_unmatched": len(match.gen_unmatched),
        },
        "gt_sections": sorted(
            c.tag for c in gt_root if isinstance(c.tag, str)
        ),
        "gen_sections": sorted(
            c.tag for c in gen_root if isinstance(c.tag, str)
        ),
        "gt_element_types": sorted(gt_types),
        "gen_element_types": sorted(gen_types),
    }


def evaluate_directories(gt_dir: Path, gen_dir: Path,
                         rtol: float = NUMERIC_RTOL) -> Dict[str, Any]:
    result = evaluate_xml(load_and_resolve_dir(gt_dir),
                          load_and_resolve_dir(gen_dir), rtol)
    result["mode"] = "directory"
    result["gt_dir"] = str(gt_dir)
    result["gen_dir"] = str(gen_dir)
    return result


def evaluate_files(gt_file: Path, gen_file: Path,
                   rtol: float = NUMERIC_RTOL) -> Dict[str, Any]:
    result = evaluate_xml(load_and_resolve_file(gt_file),
                          load_and_resolve_file(gen_file), rtol)
    result["mode"] = "file"
    result["gt_file"] = str(gt_file)
    result["gen_file"] = str(gen_file)
    return result


def evaluate_geos(agent_output: Dict[str, Any],
                  task: Dict[str, Any] | None = None,
                  ground_truth: Any = None,
                  enable_llm_judge: bool = False) -> Dict[str, Any]:
    """Top-level evaluation entry point called by the eval runner.

    Args:
        agent_output: Dict with 'generated_dir' or 'workspace_root'
        task: Task dict with 'ground_truth_dir'
        ground_truth: Override for ground truth directory
        enable_llm_judge: If True, also run LLM-based evaluation
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
                "type": str(error.get("type") or "geos_execution_error"),
                "message": str(error.get("message") or "GEOS execution failed."),
            },
        }

    generated_dir_raw = agent_output.get("generated_dir") or agent_output.get("workspace_root")
    if not generated_dir_raw:
        raise ValueError("agent_output must include 'generated_dir' or 'workspace_root'")
    generated_dir = Path(str(generated_dir_raw))

    task = task or {}
    ground_truth_raw = ground_truth or task.get("ground_truth_dir")
    if not ground_truth_raw:
        raise ValueError("GEOS evaluation requires a ground_truth directory")
    ground_truth_dir = Path(str(ground_truth_raw))

    if agent_output.get("generated_subdir"):
        generated_dir = generated_dir / str(agent_output["generated_subdir"])
    elif task.get("generated_subdir"):
        generated_dir = generated_dir / str(task["generated_subdir"])

    success_threshold = float(task.get("success_threshold", 7.0))

    try:
        xml_result = evaluate_directories(ground_truth_dir, generated_dir)
    except FileNotFoundError as exc:
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
            "error": {"type": "missing_xml", "message": str(exc)},
        }
    except (ET.ParseError, ValueError) as exc:
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
            "error": {"type": "xml_parse_error", "message": str(exc)},
        }

    programmatic_score = float(xml_result["overall_score"])
    treesim_score = float(xml_result["treesim"])

    # LLM judge (optional)
    llm_judge_score = None
    llm_judge_details = None
    if enable_llm_judge:
        try:
            from evaluation.llm_judge_geos import llm_judge_evaluate_dirs
            llm_result = llm_judge_evaluate_dirs(ground_truth_dir, generated_dir)
            llm_judge_score = float(llm_result.get("overall_score", 0))
            llm_judge_details = llm_result
        except Exception as exc:
            llm_judge_details = {"error": str(exc)}

    # Combined score: TreeSim is the headline; LLM is additive diagnostic
    if llm_judge_score is not None:
        combined_10 = 0.6 * programmatic_score + 0.4 * llm_judge_score
    else:
        combined_10 = programmatic_score

    success = bool(combined_10 >= success_threshold)

    metrics = {
        "steps": int(agent_output.get("total_steps", 0) or 0),
        "return": float(agent_output.get("total_reward", 0.0) or 0.0),
        "overall_score_10": combined_10,
        "overall_score_01": round(combined_10 / 10.0, 4),
        "programmatic_score_10": programmatic_score,
        "treesim": treesim_score,
        "treesim_section_scores": xml_result.get("treesim_section_scores", {}),
        "success_threshold_10": success_threshold,
        # Legacy diagnostics
        "dimension_scores": dict(xml_result["dimension_scores"]),
        "ordering_score": xml_result.get("ordering_score", 1.0),
        "match_summary": xml_result.get("match_summary", {}),
        "details": dict(xml_result["details"]),
        "ground_truth_dir": str(ground_truth_dir),
        "generated_dir": str(generated_dir),
        "gt_sections": list(xml_result["gt_sections"]),
        "gen_sections": list(xml_result["gen_sections"]),
        "gt_element_types": list(xml_result["gt_element_types"]),
        "gen_element_types": list(xml_result["gen_element_types"]),
    }

    if llm_judge_score is not None:
        metrics["llm_judge_score_10"] = llm_judge_score
        metrics["llm_judge_details"] = llm_judge_details

    return {
        "status": "success" if success else "task_failure",
        "success": success,
        "score": round(combined_10 / 10.0, 4),
        "metrics": metrics,
    }

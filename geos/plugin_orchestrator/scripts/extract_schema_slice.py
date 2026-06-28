#!/usr/bin/env python3
"""Extract per-segment slices from GEOS schema.xsd.

Pulls one or more `<xsd:complexType name="<Type>Type">...</xsd:complexType>`
blocks from the GEOS XML schema and writes them as a self-contained file.
Used at primer-build time to give each subagent the authoritative attribute
reference for its segment without inlining the entire 620 KB schema.

Usage:
    python extract_schema_slice.py \
        --schema /path/to/schema.xsd \
        --types ProblemType InternalMeshType VTKMeshType \
        --out plugin_orchestrator/schema_slices/mesh.xsd
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def extract_complex_type(schema_text: str, type_name: str) -> str:
    pattern = re.compile(
        r'(<xsd:complexType\s+name="' + re.escape(type_name) + r'".*?</xsd:complexType>)',
        re.DOTALL,
    )
    match = pattern.search(schema_text)
    if not match:
        return ""
    return match.group(1)


def extract_simple_type(schema_text: str, type_name: str) -> str:
    pattern = re.compile(
        r'(<xsd:simpleType\s+name="' + re.escape(type_name) + r'".*?</xsd:simpleType>)',
        re.DOTALL,
    )
    match = pattern.search(schema_text)
    if not match:
        return ""
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--types", nargs="+", required=True,
                        help="complexType or simpleType names to extract")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    schema_text = args.schema.read_text()
    out_blocks: list[str] = []
    missing: list[str] = []

    for name in args.types:
        block = extract_complex_type(schema_text, name)
        if not block:
            block = extract_simple_type(schema_text, name)
        if block:
            out_blocks.append(block)
        else:
            missing.append(name)

    if missing:
        print(f"WARN: not found: {missing}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "<!-- Extracted from GEOS schema.xsd. -->\n"
        "<!-- Authoritative: attribute names, types, defaults. -->\n"
        + "\n\n".join(out_blocks) + "\n"
    )
    print(f"Wrote {args.out} ({len(out_blocks)} types, {len(missing)} missing)")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())

---
name: geos-rag
description: Use when answering GEOS documentation, XML syntax, or schema questions with the plugin-provided search_navigator, search_technical, and search_schema MCP tools.
---

Use the GEOS RAG MCP tools before answering questions about GEOS XML syntax, examples, or documentation.

The GEOS primer is normally injected into the agent system context by the
experiment runner. Do not look for `/workspace/GEOS_PRIMER.md`; task
workspaces intentionally omit that file. Treat the system-provided primer as
the high-level orientation for the task, then use the RAG tools for
task-specific evidence and exact XML details.

Tool selection:

- Use `search_navigator` for conceptual orientation, feature discovery, solver docs, tutorials, and source RST references.
- Use `search_schema` for authoritative XML element attributes, types, defaults, and descriptions.
- Use `search_technical` for real XML examples, XML tag patterns, and references with `xml_reference` plus `line_range`.

Recommended workflow for XML authoring:

1. Search concepts with `search_navigator` when the relevant GEOS feature or solver is unclear.
2. Search exact element specs with `search_schema` before writing or changing attributes.
3. Search examples with `search_technical` to mirror working XML structure.
4. When a technical result returns an XML reference, read the referenced file and line range if the host environment provides file-reading tools.

The ChromaDB location is configured by `GEOS_VECTOR_DB_DIR` and defaults to `/data/shared/geophysics_agent_data/data/vector_db` in this plugin.

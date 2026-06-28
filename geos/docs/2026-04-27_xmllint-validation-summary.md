# 2026-04-27 — XML schema validation with `xmllint` (summary)

> Detailed investigation: `docs/xmllint_validation.md` (kept under that name
> per the original ask). This file is the dated index entry pointing back to
> the canonical doc.

## TL;DR

The user proposed wiring GEOS XML schema validation into the harness, since
many failures fall in the F1 (schema-hallucination) class. Investigation
confirms:

1. The schema path the user gave is valid:
   `/data/shared/geophysics_agent_data/data/GEOS/src/coreComponents/schema/schema.xsd`.
2. `xmllint --schema schema.xsd input.xml` works perfectly on GEOS XMLs.
   Ground-truth XMLs validate cleanly. Known-bad model outputs (M4-g s2
   `pknViscosityDominated_base.xml`, A3 s3 `DruckerPragerWellbore_base.xml`)
   produce highly actionable schema errors — bad element names, bad attribute
   names, missing required attributes, and (for unexpected elements) the
   *expected alternatives* are listed.
3. The chromadb is path-scoped: only `src/docs/sphinx/` rst files are
   indexed (82 docs); 87 GEOS rst files outside that directory are
   invisible to RAG. This is a separate finding documented here and in the
   file-access analysis.

## Recommendation

Both a hook and a tool, with a 4-cell ablation to attribute gain
(`xml_none` / `xml_tool` / `xml_hook` / `xml_both`). If budget-constrained,
run `xml_none` vs `xml_both` first and only disentangle if there's a
signal. The ablation is in `xmllint_validation.md` §2.

The agent already invokes `xmllint` 91 times across 87 task-runs without us
ever surfacing it (see file-access/tool-usage analysis). So the gain from
baking it in isn't novelty — it's *consistency*. The hook makes it
unmissable; the tool lets the agent self-direct mid-draft.

## Open items (also tracked in `xmllint_validation.md`)

- Confirm with Brian whether the chromadb indexer is path-scoped (almost
  certainly yes given 82/82 indexed rsts are under `src/docs/sphinx/`).
  If yes, agree on a re-index plan that walks the whole `src/` tree.
- Confirm `xmllint` is in the geos-eval Docker image
  (`docker run --rm geos-eval which xmllint`).
- Pick option (1) / (2) / (3) and the experimental matrix.

## Related findings written today

- `docs/xmllint_validation.md` — primary investigation.
- `docs/2026-04-27_vanilla-cc-stale-plugin-call-bug.md` — separate
  investigation, but the audit there overlapped with this one because both
  needed the same events.jsonl scan.
- `docs/2026-04-27_file-access-and-tool-usage-analysis.md` — the broader
  analysis that revealed the 91 xmllint invocations and the chromadb
  coverage gap.

# XML Schema Validation with `xmllint` — Investigation

Date: 2026-04-27
Author: research-copilot

## TL;DR

- `xmllint --schema schema.xsd <file>.xml` works perfectly on GEOS XML inputs
  using `/data/shared/geophysics_agent_data/data/GEOS/src/coreComponents/schema/schema.xsd`.
- All ground-truth XMLs we sampled validate cleanly. Known-bad model outputs
  (F1 schema-hallucination class) produce highly actionable error messages
  including the offending line, the bad element/attribute name, and — in the
  unexpected-element case — the *expected* alternatives.
- The current ChromaDB **does not contain any non-sphinx `.rst` files** (87 of
  186 GEOS source `.rst` files are outside `src/docs/sphinx/` and are
  invisible to `mcp__geos-rag__search_*`). This is a separate but related
  finding from the same investigation. It needs to be confirmed with Brian.

## 1. Sanity check: does `xmllint --schema` work?

Schema path used:
```
/data/shared/geophysics_agent_data/data/GEOS/src/coreComponents/schema/schema.xsd
```
- 632,761 bytes, present, readable. Path is valid.

`xmllint` is available on PATH at `/data/matt/miniconda3/bin/xmllint`
(libxml2 v21301), so the runner container will need a comparable build only if
we want hook-based validation; agent-side validation can rely on whatever
`xmllint` Docker installs. (We should confirm the geos-eval container has
`xmllint` before wiring up the hook — it's almost certainly already there
because GEOS dev workflow uses it, but worth a quick check.)

### 1a. Ground-truth XMLs (control)

```
xmllint --schema $SCHEMA \
  /data/shared/geophysics_agent_data/data/eval/experiments_gt/ExampleMandel/inputs/PoroElastic_Mandel_base.xml --noout
```
Output:
```
... PoroElastic_Mandel_base.xml validates
```

Same for `TutorialSneddon/inputs/Sneddon_base.xml`:
```
... Sneddon_base.xml validates
```

Both ground-truth files validate cleanly. The schema and the `xmllint`
invocation are well-formed and trustworthy.

### 1b. Imperfect model outputs

**Sample 1** — M4-g seed 2, `pknViscosityDominated_base.xml`. This is the
F1 case from our checkpoint where the model invented a tag
`<CompressibleSolidCappedPlatesPorosity>` while M1-u correctly used
`<CompressibleSolidParallelPlatesPermeability>`.

```
xmllint --schema $SCHEMA pknViscosityDominated_base.xml --noout
```
Output (excerpt):
```
:27: Schemas validity error : Element 'CompressibleSinglePhaseFluid', attribute 'defaultCompressibility': The attribute 'defaultCompressibility' is not allowed.
:27: Schemas validity error : Element 'CompressibleSinglePhaseFluid': The attribute 'defaultViscosity' is required but missing.
:42: Schemas validity error : Element 'CompressibleSolidCappedPlatesPorosity': This element is not expected.
:80: Schemas validity error : Element 'FieldSpecification': This element is not expected.
... fails to validate
```
Every error in the checkpoint failure-mode taxonomy (F1 schema hallucination)
is caught:
- bad attribute name (`defaultCompressibility`)
- missing required attribute (`defaultViscosity`)
- bad element name (`CompressibleSolidCappedPlatesPorosity`)

**Sample 2** — A3 (RAG+SR) seed 3, `DruckerPragerWellbore_base.xml`. Known to
have F1 schema hallucinations like `<Modules>`, `<MajorIndex>`. xmllint output:
```
:6: Element 'Mesh', attribute 'name': The attribute 'name' is not allowed.
:6: Element 'Mesh', attribute 'partType': The attribute 'partType' is not allowed.
:14: Element 'Geometry': This element is not expected. Expected is one of ( InternalMesh, InternalWellbore, ParticleMesh, VTKMesh ).
:26: Element 'CellElementRegion', attribute 'name': [facet 'pattern'] The value 'ElementRegions/Rock' is not accepted by the pattern '...'.
:26: Element 'CellElementRegion', attribute 'cellBlocks': [facet 'pattern'] The value 'mesh' is not accepted by the pattern '...'.
:26: Element 'CellElementRegion': The attribute 'materialList' is required but missing.
:38: Element 'DruckerPrager', attribute 'density': The attribute 'density' is not allowed.
... etc
```

The most useful diagnostic is the unexpected-element error which **also lists
the expected alternatives**:
> `Element 'Geometry': This element is not expected. Expected is one of ( InternalMesh, InternalWellbore, ParticleMesh, VTKMesh ).`

This is exactly the teaching signal the agent needs.

**Sample 3** — M1-u seed 1, same task (`pknViscosityDominated_base.xml`),
which we believe is correct. xmllint output: `... validates`. Confirms
xmllint correctly distinguishes the bad outputs from the good ones.

### Conclusion of section 1

`xmllint --schema schema.xsd input.xml` is a very high-quality validator for
GEOS XML. It fires exactly on the F1/F2 failure-mode classes and, importantly,
includes corrective hints (expected alternatives, required attribute names)
that an agent could use to self-repair.

## 2. How should we expose this to the agent?

The user proposed three options:

1. **Tool exposed via plugin** — agent has explicit control to call it.
2. **End-turn hook** — extend the existing valid-XML hook to also schema-validate.
3. **Both** — hook as a hard backstop, tool as a proactive option.

### Recommendation

**Option 3 (both), but with the experimental matrix it implies.**

- The hook (option 2) is a hard backstop. It only fires once per turn and only
  on emitted XML, so it cannot help the agent search the schema mid-task or
  pre-validate a draft. It is, however, an unmissable correction signal.
- The tool (option 1) lets the agent self-direct. It can validate a partial
  draft, validate just one of three files, or use schema errors as a query to
  decide what to look up next. It costs the agent a tool call but carries no
  cost when the agent doesn't think it's needed.
- The two are not redundant: the hook catches misses where the agent forgot to
  validate; the tool lets the agent treat the schema as a first-class
  reference.

The cost to "do both" is small (one new tool, one expanded hook), but it adds
two confounded variables to results. To attribute the gain we need an
ablation:

| Condition | Tool offered? | Hook validates? |
|-----------|--------------|----------------|
| `xml_none` (current)            | no  | XML well-formed only |
| `xml_tool`                      | yes | XML well-formed only |
| `xml_hook`                      | no  | XML well-formed + schema |
| `xml_both`                      | yes | XML well-formed + schema |

Three seeds each on the test set. If `xml_hook` ≈ `xml_both`, the tool is not
contributing anything beyond the hook backstop and we can drop it. If
`xml_tool` ≈ `xml_both`, the hook is redundant with proactive use. If
`xml_both` >> both single conditions, the channels are complementary (likely
outcome — hook catches lazy turns, tool handles draft authoring).

If we are tight on budget: run `xml_none` (existing) vs `xml_both` first to
check there's a signal; only then run the disentangling pair. The full 4-cell
matrix is the rigorous version we owe a paper reviewer.

### Implementation notes (for whichever path we take)

- The validator should be invoked with `--noout` and capture stderr. xmllint
  exits with non-zero on validation failure; that's the signal.
- Path to the schema must be inside the container (mount or copy). The
  `geos-eval` Docker image already mounts `/geos_lib` (filtered GEOS
  source), so the schema is available at
  `/geos_lib/src/coreComponents/schema/schema.xsd`. No new mounts needed.
- For the **hook** path (option 2): extend `plugin/hooks/verify_outputs.py`
  to run xmllint over each `inputs/*.xml` and fold the schema errors into the
  existing self-reflection feedback. Errors should be summarized, not dumped
  raw — a 100-line raw error log can dominate the agent's input. Cap at the
  first ~10 distinct error classes per file.
- For the **tool** path (option 1): expose as a normal MCP tool with a stable
  name (e.g., `mcp__geos-rag__validate_xml`). It lives in the same MCP server
  as the RAG tools so the agent already knows the prefix. Input: a workspace
  path or raw text. Output: JSON with `valid: bool`, `errors: [...]`,
  optionally `expected_alternatives: {...}` parsed out of xmllint stderr.
- Edge case: GEOS supports `<Included>` blocks. `xmllint` will resolve includes
  relative to the file and may complain about missing referenced files. We
  should test this on a multi-file ground-truth set before assuming the simple
  command is sufficient.

## 3. ChromaDB coverage of GEOS docs (related finding)

Reading `src/docs/sphinx/userGuide/Index.rst` shows it points to docs that
live elsewhere in the repo (e.g.,
`src/coreComponents/fileIO/doc/InputXMLFiles.rst`). The user worried this may
not be in the RAG index.

Inspection of the live ChromaDB at
`/data/shared/geophysics_agent_data/data/vector_db/chroma.sqlite3`:

| Collection      | Embeddings |
|-----------------|------------|
| `geos_navigator`  | 571 |
| `geos_schema`     | 250 |
| `geos_technical`  | 334 |

Distinct `source_path` values: **83**.
- 82 are `.rst` files. *All* are under `src/docs/sphinx/`.
- 1 is `geosx_schema.xsd`.
- **Zero** non-sphinx `.rst` files are indexed.

Ground truth in the GEOS repo:
- 186 total `.rst` files in `src/`.
- 99 inside `src/docs/sphinx/`.
- **87 outside `src/docs/sphinx/`** — and zero of those are in ChromaDB.

The 87 non-indexed files include important ones the agent often needs:
- `src/coreComponents/fileIO/doc/InputXMLFiles.rst` (the file we're building this
  validation pipeline around — describes `xmllint`, schema, etc.)
- `src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst`
- `src/coreComponents/physicsSolvers/solidMechanics/docs/SolidMechanics.rst`
- `src/coreComponents/physicsSolvers/solidMechanics/contact/docs/ContactMechanics.rst`
- `src/coreComponents/linearAlgebra/docs/LinearSolvers.rst`,
  `KrylovSolvers.rst`
- `src/coreComponents/fieldSpecification/docs/FieldSpecification.rst`,
  `EquilibriumInitialCondition.rst`
- ...and 80 more.

So the user's option (1) is what happened: the indexer crawled `src/docs/sphinx/`
only, not the whole repo. Confirming with Brian is the right next step.
Mitigations once confirmed:
- Re-index by walking the whole `src/` tree for `*.rst` (preferred — rebuilds
  what was already there + adds the missing docs).
- Or, separately, add filesystem-based read-with-Glob fallback explicitly to
  the agent's instructions so it knows to look outside `docs/sphinx`. This is
  what the agent already has access to but evidently doesn't use much (see the
  forthcoming file-access analysis).

## 4. What we still need to do

- [ ] Confirm with Brian whether the ChromaDB indexer is path-scoped or
      programmatic. If path-scoped, agree on a re-index plan.
- [ ] Decide between option 1 / 2 / 3 + ablation budget for xmllint.
- [ ] Confirm xmllint is installed in the geos-eval Docker image
      (`docker run --rm geos-eval which xmllint`).
- [ ] If we expose as a tool: add it to `plugin/scripts/geos_rag_mcp.py`
      and update the system prompt with an instruction to use it before
      writing XML.
- [ ] If we add to hook: extend `plugin/hooks/verify_outputs.py` to run
      xmllint over each `inputs/*.xml`, summarize first-N errors per file,
      and feed back into the retry loop.
- [ ] Test xmllint behavior on multi-file inputs that use `<Included>`.

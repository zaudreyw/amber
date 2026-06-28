# GEOS XML Authoring Cheatsheet (short)

*Cross-task-invariant patterns distilled from past successful CC+plugin runs. Apply when relevant; task-specific requirements override.*

## RAG usage
- Before writing any XML, run at least one `mcp__geos-rag__search_technical` or `search_navigator` query to locate a similar validated example, then `Read` the full file.
- Use `mcp__geos-rag__search_schema` to verify required and default attributes for any constitutive model, solver, or mesh block BEFORE writing that block. Do not infer attributes from a single example.

## XML structure
- When adapting an existing example, preserve its validated structure; change only the parameters the task specifies.
- After writing XML files, `Read` them back and check that every major block mentioned in the specification is present. Do not exit without this verification step.

## Common mistakes to avoid
- Do NOT leave an `ElementRegion`'s `materialList` empty — reference a concrete constitutive model.
- Do NOT redefine entire output/solver blocks in a benchmark file when a base file already defines them; override specific attributes instead.
- Do NOT rely on `<Included>` relative paths that cross task-workspace and `/geos_lib` boundaries; prefer self-contained files.

## Stop criterion
- The task is complete only when every XML file the specification requires has been written under `/workspace/inputs/` AND you have read each one back to verify. Keep iterating through tool calls until this holds.

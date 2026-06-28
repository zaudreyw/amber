# Runtime hygiene investigation — 2026-04-22

Post-launch audit of `events.jsonl` for mem_placebo_s1 revealed that 17/17
tasks contain cross-task blocked GT basenames in their event streams.
Investigation confirms the exposure is exclusively in `tool_result` blocks
from the RAG tool — the `geos-rag` MCP returns GEOS documentation that
references unredacted XML filenames as part of the doc text.

**This is NOT a memory-introduced leak.**

- Memory primer files: audited clean (no `*.xml` basenames, no test-GT
  substrings) via `scripts/memory/hygiene_audit.py`.
- Memory MCP tool outputs (M3-g): smoketest confirmed 0 calls in current
  sample; if the tool is called at test time, its output is the RB items
  content which is audited clean at build time.
- The RAG-tool leak is **pre-existing** and applies equally to ALL
  experimental conditions (A1-A5, M-placebo, M1-u/g, M3-g, M4-u/g).
  It is not a differential confound between memory and non-memory
  conditions.

The underlying question — whether RAG-tool exposure of test-GT filenames
in doc text affects our overall story — is a separate methodological
concern that predates D-008 and is out of scope for this sprint. It
applies equally to ALL runs in PAC-1 and earlier campaigns.

## Specific exposure path

RAG tool output contains doc text like:
  "the example `druckerpragerwellbore_base.xml` demonstrates..."

The agent reads this text but cannot `Read` the actual XML file at
`/geos_lib/inputFiles/solidMechanics/druckerpragerwellbore_base.xml`
because that file is filtered out of the decontaminated GEOS copy.

So the agent gets a filename hint but cannot get the file contents. This
is arguably not a full GT leak but a weaker hint. It applies uniformly
across conditions.

## Decision

No action. Document as known limitation of the broader evaluation pipeline.

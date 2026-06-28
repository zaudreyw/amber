# C0 (abs-min primer) — what does the agent choose to do without workflow guidance?

*2026-05-01 — post-hoc trajectory analysis of the C0 cell from the
2026-04-29 DSv4-flash ablation. 3 seeds × 17 tasks = 51 runs.*

## Why this writeup

In the DSv4 ablation, **C0 (abs-min primer, no plugin) scored 0.865 ±
0.067** vs **C1 (minimal_vanilla primer with workflow steps) at 0.671 ±
0.014** — a +0.194 paired delta. C0 is the first DSv4 cell where we
gave the agent essentially no task guidance: the primer is 5 lines and
only states (a) GEOS is a multiphysics simulator that needs an XML
input, (b) the source repo is at `/geos_lib/`, (c) the output goes to
`/workspace/inputs/`. No workflow recipe, no XML skeleton, no
"recommended steps."

The question: **with all guidance stripped, what does DSv4-flash
naturally choose to do?** This note describes the tool-use distribution,
the bash command distribution, and the file-access pattern across all
51 C0 runs.

Source data: `/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/abl_c0_true_vanilla/`
(events.jsonl per task × seed, `tool_calls.json` summaries).

## TL;DR

- DSv4 spontaneously executes the same "find-similar-example, adapt,
  read-back" workflow that C1's primer prescribes — but without the
  primer telling it to.
- **48% of all tool calls are Read; 36% are filesystem search
  (Glob 16% + Grep 20%).** Bash is only 5%.
- **Bash is used almost exclusively for filesystem orientation**: 48%
  `ls`, 19% `mkdir`, 18% `find`. Almost no shell pipelines, no
  scripting beyond a single `python3 -c "..."` for ad-hoc XML
  validation.
- **File reads concentrate hard on `/geos_lib/inputFiles/` (66%)** —
  the canonical example XML library — followed by
  `/geos_lib/src/` (24%, mostly `coreComponents/constitutive/` and
  `src/docs/sphinx/`), then read-backs of files the agent itself wrote
  in `/workspace/inputs/` (4%).
- **Mean tool-use per run: 83.5; mean unique files read per run: 32.3.**
  C0 reads broadly: source code (.hpp/.cpp), Sphinx docs (.rst), and
  example XMLs all show up — not just XMLs.
- **Emergent verification:** the C0 primer never tells the agent to
  read its own outputs back, yet there are 81 reads under
  `/workspace/inputs/` across 51 runs (~1.6 read-backs/run on average,
  more for triaxial-driver tasks where multi-file outputs need to be
  cross-checked).

## 1. Setup recap

| field | value |
|---|---|
| primer | `plugin/GEOS_PRIMER_absolute_min.md` (5 lines) |
| AGENTS.md | retained (5KB GEOS guidance, baked-in) |
| plugin | not loaded (no MCP, no SR hook, no RAG) |
| flags | `--strip-baked-primer` ON |
| model | `deepseek-v4-flash` via Anthropic-compatible endpoint |
| seeds | 1, 2, 3 |
| tasks | 17 (canonical PAC-1 / D-008 set) |
| tools available | Task/Agent, Bash, Edit, Glob, Grep, Read, TodoWrite, Write, plus several harness-supplied no-ops (CronCreate, EnterPlanMode, etc.) |

The C0 primer in full:

> GEOS is an open-source multiphysics simulator. Tasks require authoring
> an XML input file (or a small set of XMLs cross-referenced via
> `<Included>`).
> - The GEOS source repository is mounted at `/geos_lib/`.
> - Write your final XML output to `/workspace/inputs/`.

### AGENTS.md status — verified 2026-05-01

Both C0 (in `dsv4_ablation_2026-04-29/abl_c0_true_vanilla/`) and
C1redux (in `c6prime_c1redux_2026-05-01/`) launchers explicitly pass
**`--strip-baked-primer`** (verified by reading the launcher scripts
and `runner/prompts/__init__.py:load_agents_md`). The 14,836-char
embedded `# GEOS Primer` block IS removed in both conditions.

What remains in AGENTS.md (5,359 chars / 106 lines, **identical
across C0 and C1**) is a sizeable operational preamble that both
conditions inherit:

- **Identity**: "You are GEOS Expert, an assistant for the GEOS
  multiphysics simulator..."
- **`USING DOCUMENTATION EXAMPLES`** — explicitly tells the agent:
  > "Documentation examples and references are REFERENCES, not
  > templates to copy verbatim. ... Use it to understand the XML
  > structure, required tags, and solver configuration. Do NOT copy
  > its parameter values wholesale..."
- **`INPUT FILE ORGANIZATION (Base/Benchmark Pattern)`** — the
  `*_base.xml` / `*_benchmark.xml` convention.
- **`WORKFLOW — AVAILABLE STEPS`** — a 4-step generic workflow
  ("Determine physics setup → Ask or assume missing specs →
  Generate/patch XML → Post-processing").
- **`CRITICAL FILE LOCATION RULES`** — `inputs/`, `outputs/`,
  `inputs/scripts/`.
- **`FILE ACCESS RULES`** — explicitly says "Browse
  `/geos_lib/inputFiles/` for reference XML examples" and "Browse
  `/geos_lib/src/docs/sphinx/` for RST documentation."
- **`GEOSDATA PATH RESOLUTION`**, **`DOCUMENTATION PATH RESOLUTION`**,
  **`SAFETY & CORRECTNESS`** — minor notes.

So **the "C0 has no guidance" framing is overstated**: AGENTS.md
already tells both conditions where examples and docs live, that
examples should be treated as references not templates, and the
base/benchmark pattern. The differential between C0 and C1 is the
**primer file** that gets *appended* on top:

- **C0 primer (5 lines)**: just "GEOS is multiphysics", `/geos_lib/`,
  output to `/workspace/inputs/`. Adds essentially nothing on top of
  AGENTS.md.
- **C1 primer (~34 lines)**: same file paths PLUS a top-level XML
  skeleton (Solvers / Mesh / Geometry / Events / NumericalMethods /
  ElementRegions / Constitutive / FieldSpecifications / Functions /
  Outputs / Tasks) PLUS an explicit "Recommended workflow: 1. Find a
  similar existing example using Glob/Grep/Read against
  /geos_lib/inputFiles/. Search by physics keyword (e.g. Glob for
  *Wellbore*.xml; Grep for `<SinglePhasePoromechanics`); use Read on
  the full example XMLs. 2. Read the full example XML and adapt it.
  3. Write to /workspace/inputs/. 4. Read each file back to verify."

So the C0→C1 delta isn't "no guidance vs some guidance"; it's
**"shared AGENTS.md baseline" vs "shared baseline + an XML skeleton +
a 4-step workflow recipe."** The C0 baseline already has enough
information to know that examples live in `/geos_lib/inputFiles/`
and docs live in `/geos_lib/src/docs/sphinx/`. What C1 adds is
*structure prescription* (the XML skeleton orders the sections; the
workflow numbers the steps).

This reframes the §1 finding: stripping the C1 primer's extra
structure isn't lifting "guidance vs no-guidance" by +0.194; it's
lifting "fixed-structure prescription" off a baseline that already
includes a "use examples as references" pointer. The agent in C0 is
free to pick any structural ordering it sees in examples, whereas C1
is anchored to the primer's skeleton.

## 2. Tool-call distribution (n=51 runs, 4260 tool calls)

| tool | count | share |
|---|---:|---:|
| Read | 2056 | 48.3% |
| Grep | 832 | 19.5% |
| Glob | 698 | 16.4% |
| Bash | 216 | 5.1% |
| TodoWrite | 190 | 4.5% |
| Write | 189 | 4.4% |
| Agent (subagent) | 73 | 1.7% |
| Edit | 5 | 0.1% |

Per-run averages: **107.4 assistant turns, 83.5 tool-use blocks, 8.2
text blocks.** Most assistant turns produce a tool call rather than
free-text — DSv4 spends ~78% of its turns doing things, ~22% planning
or summarizing.

Notable absences:
- **Edit barely used (5 calls total).** The agent overwhelmingly
  prefers Write (full-file replacement) over Edit (targeted patch).
- **No NotebookEdit, ScheduleWakeup, EnterPlanMode, CronCreate,
  WebFetch, WebSearch.** All of those tools were available; none were
  used. The agent does not try to use the network.

### 2.1 Subagent (Task/Agent) usage

73 Agent dispatches across 51 runs (≈1.4/run). Top descriptions:

| count | description |
|---:|---|
| 4 | Explore triaxial driver examples |
| 4 | Explore GEOS triaxial driver examples |
| 3 | Find triaxial driver examples |
| 3 | Explore GEOS compositional examples |
| 2 each | poroelastic, solid mechanics, hydrofracture, THM, multiphase, frac, thermoporoelastic |

Subagent prompt keywords (occurrences, multi-count per prompt):

| keyword | count |
|---|---:|
| search | 70 |
| example | 69 |
| solver | 54 |
| mesh | 50 |
| find | 48 |
| docs / documentation | 48 / 40 |
| constitutive | 38 |
| schema | 31 |
| element | 30 |

Pattern: subagents are dispatched almost exclusively for
**library-exploration tasks**, never for code generation or critique.
DSv4 uses the subagent as a "wide search" primitive — gather a lot of
files, summarize, hand back — rather than as a delegated worker.

## 3. Bash subcommand distribution (216 calls)

| first token | count | share |
|---|---:|---:|
| `ls` | 104 | 48.1% |
| `mkdir` | 41 | 19.0% |
| `find` | 38 | 17.6% |
| `cd` | 11 | 5.1% |
| `grep` | 8 | 3.7% |
| `python3` | 6 | 2.8% |
| `wc` | 3 | 1.4% |
| `head` | 3 | 1.4% |
| `echo` | 2 | 0.9% |

Bash is overwhelmingly **filesystem orientation, not computation**.
Combined `ls` + `find` = 65.7%; `mkdir` is the standard
"prepare /workspace/inputs/tables/" setup. The 6 `python3` calls are
all single-line `-c` invocations for ad-hoc XML well-formedness checks
(e.g. parsing each output file with `xml.etree.ElementTree` and
printing parse errors).

Where do the bash commands target?

| target | count |
|---|---:|
| `/workspace/inputs[/]` | 50 |
| `/workspace/inputs/tables[/]` | 14 |
| `/geos_lib[/]` | 19 |
| `/geos_lib/inputFiles/triaxialDriver/` | 8 |
| `/geos_lib/inputFiles/` | 5 |
| `/geos_lib/src/docs/sphinx/` | 4 |
| `/geos_lib/inputFiles/compositionalMultiphaseFlow/...` | 9 |

So Bash splits into two clear roles: (1) prepare the output workspace
(`mkdir`, then `ls` to confirm), and (2) breadth-first directory
listings of `/geos_lib/inputFiles/` early in the trajectory. Once the
agent has located the relevant subdirectory it switches to Glob/Grep
(which produce structured results) instead of `find`.

Verbatim examples of the *only* non-trivial bash invocations seen:

```
python3 -c "
import xml.etree.ElementTree as ET
import sys
errors = []
for f in ['DeviatedElasticWellbore_base.xml', ...]:
    ...
"

find / -maxdepth 4 -type d -name "geos_lib" 2>/dev/null
find / -maxdepth 5 -name "*.xml" -path "*Solid*" -o -name "*.xml" -path "*solid*" -o -name "*.xml" -path "*Mechanics*" -o -name "*.xml" -path "*wellbore*" 2>/dev/null
find /geos_lib/src/docs -name "*.rst" | xargs grep -l "TriaxialDriver" 2>/dev/null
```

The second `find` (with depth-bounded search across `/`) appears once —
the agent quickly orients itself, then never re-explores at that
breadth.

## 4. File-access pattern (2056 Read calls)

### 4.1 Top-level path distribution

| prefix | reads | share |
|---|---:|---:|
| `/geos_lib/inputFiles/` | 1451 | 70.6% |
| `/geos_lib/src/` | 517 | 25.1% |
| `/workspace/inputs/` | 81 | 3.9% |
| `/workspace/.claude_home/` | 4 | 0.2% |
| other | 3 | 0.1% |

The agent's reading is overwhelmingly anchored on the
`/geos_lib/inputFiles/` example library — exactly the directory
called out in the abs-min primer.

### 4.2 Reads inside `/geos_lib/src/`

The 517 reads under `/geos_lib/src/` decompose:

| subdirectory | reads |
|---|---:|
| `src/docs/sphinx/` | 226 |
| `src/coreComponents/constitutive/` | 100 |
| `src/coreComponents/integrationTests/` | 80 |
| `src/coreComponents/constitutiveDrivers/` | 29 |
| `src/coreComponents/physicsSolvers/` | 29 |
| `src/coreComponents/fileIO/` | 14 |
| `src/coreComponents/mesh/` | 10 |
| `src/coreComponents/schema/` | 9 |
| `src/coreComponents/events/` | 8 |
| `src/coreComponents/fieldSpecification/` | 6 |

Two stories here:

1. **Sphinx docs (~226 reads)** — DSv4 reaches for the prose
   documentation when example XMLs alone don't disambiguate. The
   `triaxialDriver/Example.rst` is read 11× and the
   `TriaxialDriver.rst` 10× — these are the highest-traffic
   non-XML files in the entire corpus.
2. **C++ source code (~291 reads)** — the agent reads .hpp/.cpp
   inside `coreComponents/constitutive*` to disambiguate constitutive
   model names and parameter sets. This was *not* suggested by the
   primer or AGENTS.md. The agent learned (or already knew from
   training prior) that GEOS's truth-source for constitutive XML
   attribute names is the `static constexpr char const *` lines in
   `.hpp` files. We can see this in the Grep patterns:
   `static constexpr char const \*` is one of the top-25 grep
   patterns (5 occurrences).

### 4.3 File extensions read

| extension | reads | note |
|---|---:|---|
| .xml | 1413 | example library, 67% of all reads |
| .rst | 313 | Sphinx documentation |
| .geos | 85 | TableFunction lookup tables (pure-text data files) |
| .txt | 76 | misc |
| .hpp | 57 | C++ headers (constitutive truth-source) |
| .py | 42 | helper scripts in the GEOS source tree |
| .ats | 26 | GEOS test-runner spec files |
| .cpp | 24 | C++ implementation |
| .xsd | 8 | XML schema |

### 4.4 Most-read individual files

The top-25 reads are dominated by `triaxialDriver` artifacts (because 4
of the 17 tasks are triaxial-driver constitutive tests, and each has
high cross-seed reuse). Top entries:

```
30  /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager_basicExample.xml
25  /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoExtendedDruckerPrager.xml
25  /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ViscoModifiedCamClay.xml
25  /geos_lib/inputFiles/triaxialDriver/triaxialDriver_DruckerPrager.xml
23  /geos_lib/inputFiles/triaxialDriver/tables/{time,axialStrain,radialStress}.geos
22  /geos_lib/inputFiles/triaxialDriver/triaxialDriver_ExtendedDruckerPrager.xml
18  /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml
15  /geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml
15  /geos_lib/inputFiles/triaxialDriver/triaxialDriver_base.xml
15  /geos_lib/inputFiles/poromechanics/PoroDruckerPragerWellbore_base.xml
14  /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_modifiedCamClay.xml
14  /geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml
14  /geos_lib/inputFiles/hydraulicFracturing/hydrofractureSinglePhase2d.xml
13  /geos_lib/src/coreComponents/integrationTests/constitutiveTests/testTriaxial_druckerPragerExtended.xml
13  /geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml
12  /geos_lib/inputFiles/solidMechanics/OpenWellbore.xml
12  /geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_benchmark.xml
11  /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
11  /geos_lib/src/coreComponents/constitutiveDrivers/solid/TriaxialDriver.hpp
10  /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
```

Per-run unique-file-read distribution:
**min 6, p25 21, median 31, p75 40, max 86; mean 32.3.**

### 4.5 Glob/Grep patterns (the actual queries)

Top Glob patterns:

```
35  *
28  **/*.rst
23  **/*
11  **/*.xml
10  **/triaxialDriver_base*
 9  **/*triaxial*
 9  *.xml
 9  **/doc/**/*.rst
 8  *base*
 6  **/*DruckerPrager*
 6  **/*poro*
```

Top Grep patterns:

```
25  TriaxialDriver
20  triaxialDriver_base
18  DruckerPrager
17  TableFunction
12  InternalMesh
11  SolidMechanicsLagrangianSSLE
10  SinglePhasePoromechanics
 6  ModifiedCamClay
 6  ElasticIsotropic
 6  TimeHistory
 6  BrooksCoreyRelativePermeability
 6  SinglePhasePoromechanics|SolidMechanics_LagrangianFEM
 5  ExtendedDruckerPrager
 5  CompositionalMultiphaseFlow
 5  static constexpr char const \*    ← targeting C++ truth-source
```

The Grep distribution is almost entirely **GEOS XML element / class
names** (CamelCase identifiers) plus a few file-name queries. The agent
treats the codebase as a name-keyed lookup, not as text to read
linearly.

The Glob distribution shows two phases: very generic patterns (`*`,
`**/*`, `**/*.xml`, `**/*.rst`) used for orientation, then highly
specific patterns (`**/triaxialDriver_base*`, `**/*DruckerPrager*`)
used to home in on a candidate set.

## 5. Output / write pattern (189 Write calls)

| target dir | writes |
|---|---:|
| `/workspace/inputs/` | 147 |
| `/workspace/inputs/tables/` | 35 |
| `/workspace/inputs/buckleyLeverett_table/` | 6 |
| `/workspace/inputs/scripts/` | 1 |

Extensions written: 135 .xml, 43 .geos (table data), 10 .txt, 1 .py.

The agent organizes its output into a stable convention:
- top-level XMLs in `inputs/`
- TableFunction data files in `inputs/tables/`
- task-specific subdirectories (e.g. `buckleyLeverett_table/`) when
  the task implies it.

This convention is **not specified anywhere in the C0 primer**. AGENTS.md
mentions a base/benchmark file pattern but doesn't say where tables go.

## 6. The emergent workflow

Putting the above together, here is the workflow DSv4 self-selects in
C0 (no primer guidance):

1. **Plan** — TodoWrite a 4-7 step plan keyed to the task spec
   (typical: "create dirs", "find example", "write base.xml", "write
   benchmark.xml", "write smoke.xml", "verify").
2. **Orient** — `ls /workspace/`, `mkdir /workspace/inputs/`,
   `ls /geos_lib/inputFiles/<physics-family>/` to find the right
   example subdirectory.
3. **Locate similar examples** — Glob with progressively narrower
   patterns; Grep for the constitutive-model / solver name; Read the
   most promising 5-15 example XMLs to extract structure.
4. **Disambiguate** — When XML names are ambiguous, Read the
   `.hpp`/`.cpp` constitutive source and the `.rst` Sphinx docs to
   confirm attribute names and ordering.
5. **Optionally dispatch a subagent** — when the search space is big
   (e.g. "thermoporoelastic + cased contact"), dispatch an Agent with a
   "search and summarize" prompt rather than reading 30 files inline.
6. **Write output** — Write `<task>_base.xml`, `<task>_benchmark.xml`,
   etc. to `/workspace/inputs/`.
7. **Verify** — Read its own output files back (~1.6 reads/run on
   average, higher for multi-file outputs); occasionally `python3 -c`
   for an XML well-formedness check.

This is, **structurally identical** to the workflow C1's primer
prescribes. The C1 primer says:

> 1. Find a similar existing example using `Glob`/`Grep`/`Read`...
> 2. `Read` the full example XML... and adapt it...
> 3. Write the adapted XML to `/workspace/inputs/`.
> 4. Read each file back to verify...

C0 does steps 1-4 unprompted. The +0.194 lift therefore is **not**
because C0 invents a better workflow — it's because C1's primer
prescribes a more *constrained* version of the same workflow that C0
executes more freely:

- C1's step 1 says use Glob/Grep against `/geos_lib/inputFiles/`. C0
  also reads `/geos_lib/src/coreComponents/constitutive/` (291 reads,
  ~14% of total reads) and `/geos_lib/src/docs/sphinx/` (226 reads,
  ~11%). C0 reaches for source code and prose docs that C1's primer
  doesn't endorse.
- C1's primer ships an XML skeleton with a fixed top-level ordering
  (Solvers, Mesh, Geometry, Events, NumericalMethods, ElementRegions,
  Constitutive, FieldSpecifications, Functions, Outputs, Tasks). C0
  has no such skeleton — it copies the structure of whatever example
  it found, which presumably matches the spec better than an arbitrary
  skeleton.
- C1's "step 4: read each file back" is interpreted as a single
  one-shot verification. C0 has no such step but still does ~1.6
  read-backs/run, often interleaved with edits/rewrites — the
  read-backs are *adaptive*, not ritual.

## 6.5 .xml vs .rst — how much is doc-reading vs. pure example-copying?

The user asked specifically: how much is the agent reading documentation
(`.rst` Sphinx docs) vs. just copying an example XML and figuring it
out? The answer at the global aggregate is "mostly example-copying,
with selective doc reads on a subset of tasks."

### Aggregate

| extension | reads | share | unique files |
|---|---:|---:|---:|
| .xml | 1413 | 68.7% | 361 |
| .rst | 313 | 15.2% | 99 |
| all others | 330 | 16.0% | 136 |

**.xml-to-.rst read ratio: 4.51×.** For every doc page DSv4 reads, it
reads ~4.5 example XML files. Examples drive the workflow; docs are a
secondary disambiguation channel.

### Per-run distribution of .rst reads (51 runs)

| stat | value |
|---|---:|
| min | 0 |
| p25 | 0 |
| median | 3 |
| p75 | 8 |
| max | 38 |
| mean | 6.14 |

- **15 of 51 runs (29%) read zero .rst files.** Those runs are pure
  "find an example XML, adapt, write" — no docs consulted.
- **36 of 51 runs (71%) read at least one .rst file.**
- The distribution is heavily right-skewed: a few runs (notably
  `ExampleThermalLeakyWell` mean 18, `TutorialSneddon` mean 15,
  triaxial-driver tasks mean 8-10) drag the mean above the median.

### Which tasks pull doc-heavy vs. doc-free

| task | mean .rst | mean .xml | seeds w/ ≥1 .rst |
|---|---:|---:|:---:|
| ExampleThermalLeakyWell | 18.0 | 28.7 | 2/3 |
| TutorialSneddon | 15.0 | 42.7 | 2/3 |
| AdvancedExampleDruckerPrager | 10.0 | 29.3 | 3/3 |
| AdvancedExampleExtendedDruckerPrager | 10.0 | 22.3 | 3/3 |
| AdvancedExampleViscoDruckerPrager | 8.3 | 33.7 | 3/3 |
| buckleyLeverettProblem | 7.7 | 26.7 | 3/3 |
| ExampleDPWellbore | 7.3 | 23.3 | 2/3 |
| ExampleIsothermalLeakyWell | 4.7 | 36.7 | 2/3 |
| kgdExperimentValidation | 4.7 | 26.0 | 3/3 |
| AdvancedExampleModifiedCamClay | 4.0 | 29.0 | 2/3 |
| AdvancedExampleDeviatedElasticWellbore | 3.3 | 24.0 | 2/3 |
| ExampleEDPWellbore | 3.3 | 34.7 | 2/3 |
| ExampleMandel | 2.7 | 23.3 | 2/3 |
| pknViscosityDominated | 2.7 | 14.7 | 2/3 |
| ExampleThermoporoelasticConsolidation | 2.3 | 21.0 | 2/3 |
| TutorialPoroelasticity | 0.3 | 25.7 | 1/3 |
| AdvancedExampleCasedContactThermoElasticWellbore | 0.0 | 29.3 | **0/3** |

`AdvancedExampleCasedContactThermoElasticWellbore` is the only task
where DSv4 *never* read a .rst file across any seed — it stayed
purely in example-XML mode (~29 XML reads/seed). The triaxial-driver
family (DruckerPrager, ExtendedDruckerPrager, ViscoDruckerPrager,
ModifiedCamClay) consistently consults docs because the driver's
input format isn't well-covered by a single example XML —
`triaxialDriver/Example.rst` and `TriaxialDriver.hpp/.rst` are the
canonical sources for the parameter list.

### What kind of .rst is being read?

Of 313 .rst reads (99 unique files):

| category | reads | share | unique files |
|---|---:|---:|---:|
| `sphinx/advancedExamples/...` (validation studies, benchmarks) | 121 | 38.7% | 36 |
| `coreComponents/<component>/docs/` (mesh, events, solver, fileIO API docs) | 56 | 17.9% | 25 |
| `coreComponents/constitutive/docs/` (constitutive model API docs) | 54 | 17.3% | 18 |
| `sphinx/basicExamples/` (introductory examples) | 38 | 12.1% | 7 |
| `sphinx/tutorials/` (step01 - step04) | 16 | 5.1% | 4 |
| `coreComponents/constitutiveDrivers/docs/` | 13 | 4.2% | 2 |
| `sphinx/developerGuide/` (XML meta-format, contributing) | 9 | 2.9% | 4 |
| `sphinx/userGuide/` | 4 | 1.3% | 1 |
| other | 2 | 0.6% | 2 |

The largest bucket (38.7%) is **`advancedExamples/validationStudies/`** —
these are the prose pages that *describe* a specific benchmark
problem and link to the example XMLs. They are essentially "Example
+ commentary" pages, not API reference. The agent reaches for them
because the test set itself is drawn from this directory.

API-reference-style docs (`coreComponents/.../docs/`, ~39% combined)
are the second use case — DSv4 hits these when it needs to confirm
solver parameters, constitutive model attribute names, or output-task
syntax. Tutorials and developer guide are minor (≈8% combined).

### Most-read .rst files (top 25)

```
11  /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
10  /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
10  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
 9  /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
 8  /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
 7  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
 7  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
 7  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
 7  /geos_lib/src/docs/sphinx/basicExamples/co2Injection/Example.rst
 7  /geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst
 7  /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst
 6  /geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst
 6  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/Index.rst
 6  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
 5  /geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst
 5  /geos_lib/src/coreComponents/mesh/docs/Mesh.rst
 5  /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/CompositionalMultiphaseFlow.rst
 5  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/Index.rst
 5  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalLeakyWell/Example.rst
 5  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdViscosityDominated/Example.rst
 5  /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/XML.rst
 5  /geos_lib/src/docs/sphinx/tutorials/step03/Tutorial.rst
 4  /geos_lib/src/coreComponents/events/docs/EventManager.rst
 4  /geos_lib/src/coreComponents/fieldSpecification/docs/FieldSpecification.rst
 4  /geos_lib/src/coreComponents/fileIO/doc/OutputTasks.rst
```

Two patterns are clear:

1. **The validation-study Example.rst pages co-located with the
   benchmark XMLs are the primary doc target.** These are the same
   pages that appear in the GEOS user-facing documentation site, and
   they describe the physics + the example XML side-by-side. DSv4
   reads them as "annotated examples."
2. **Constitutive-model docs are the secondary target.** The
   triaxial-driver task family (DruckerPrager, ExtendedDruckerPrager,
   ModifiedCamClay, ViscoPlasticity) accounts for ~40 doc reads on
   constitutive-model pages alone — these tasks are constitutive
   tests, so the agent's behavior matches the task structure.

### Full list of .rst files read (99 unique)

A complete count-sorted list is appended at the end of this writeup
in §11.

### Bottom line

DSv4 in C0 is **predominantly an example-copier (68.7% of reads are
.xml; 29% of runs read no docs at all)**, with **selective
doc-consultation on tasks where examples alone are insufficient** —
specifically the triaxial-driver constitutive tests and a handful of
multi-physics benchmarks. When it does read docs, it favors prose
example pages (validation-study `Example.rst`) over pure API reference,
which is consistent with its "looking for an annotated example"
strategy.

## 6.6 Per-task C0 vs C1 comparison

Joining per-task scores from the original ablation
(`docs/ablation_C1_vs_C0.json`) with per-task tool-use trajectories.

**Important caveat on the trajectory data**: the original C1 scores
come from the `dsv4_min_primer_s{1,2,3}` runs (April), but those
trajectory directories were not preserved on disk. The closest
available C1-trajectory dataset is the **c1redux** re-run from
2026-05-01
(`/data/shared/geophysics_agent_data/data/eval/c6prime_c1redux_2026-05-01/claude_code_no_plugin_minprimer/`),
which uses the same primer (`GEOS_PRIMER_minimal_vanilla.md`), the
same `--strip-baked-primer` flag, the same model, and the same
anti-leakage blocklist. So this section is "**original-C1 scores +
c1redux trajectories**" — the trajectory is a same-setup sample, not
the literal trajectory that produced those scores. All 17 tasks have
3/3 c1redux seeds.

### Score and read-volume comparison (sorted by Δ desc)

| task | C1 | C0 | Δ | C1 xml | C0 xml | C1 rst | C0 rst | C1 calls | C0 calls | C1 seeds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:-:|
| ExampleMandel | 0.312 | 0.953 | +0.641 | 12.3 | 23.3 | 0.3 | 2.7 | 34.7 | 62.3 | 3/3 |
| ExampleDPWellbore | 0.487 | 0.998 | +0.511 | 32.0 | 23.3 | 1.7 | 7.3 | 51.3 | 64.3 | 3/3 |
| AdvancedExampleDruckerPrager | 0.608 | 0.998 | +0.390 | 12.0 | 29.3 | 7.3 | 10.0 | 61.7 | 91.0 | 3/3 |
| AdvancedExampleModifiedCamClay | 0.570 | 0.941 | +0.370 | 9.0 | 29.0 | 4.7 | 4.0 | 52.0 | 86.0 | 3/3 |
| TutorialPoroelasticity | 0.365 | 0.636 | +0.271 | 16.0 | 25.7 | 1.0 | 0.3 | 44.3 | 63.3 | 3/3 |
| AdvancedExampleViscoDruckerPrager | 0.738 | 0.975 | +0.237 | 9.3 | 33.7 | 4.7 | 8.3 | 48.7 | 112.0 | 3/3 |
| TutorialSneddon | 0.643 | 0.868 | +0.226 | 58.0 | 42.7 | 0.0 | 15.0 | 91.0 | 117.7 | 3/3 |
| AdvancedExampleDeviatedElasticWellbore | 0.766 | 0.939 | +0.172 | 37.3 | 24.0 | 1.3 | 3.3 | 67.3 | 49.3 | 3/3 |
| buckleyLeverettProblem | 0.726 | 0.875 | +0.149 | 18.3 | 26.7 | 0.0 | 7.7 | 57.3 | 109.3 | 3/3 |
| ExampleEDPWellbore | 0.841 | 0.979 | +0.138 | 34.0 | 34.7 | 1.7 | 3.3 | 55.3 | 72.3 | 3/3 |
| kgdExperimentValidation | 0.773 | 0.910 | +0.137 | 22.7 | 26.0 | 0.0 | 4.7 | 40.0 | 62.7 | 3/3 |
| AdvancedExampleCasedContactThermoElasticWellbore | 0.699 | 0.813 | +0.114 | 25.3 | 29.3 | 1.7 | 0.0 | 56.7 | 53.7 | 3/3 |
| ExampleIsothermalLeakyWell | 0.791 | 0.878 | +0.087 | 23.7 | 36.7 | 2.0 | 4.7 | 60.3 | 114.0 | 3/3 |
| pknViscosityDominated | 0.899 | 0.986 | +0.087 | 18.3 | 14.7 | 0.0 | 2.7 | 48.7 | 49.3 | 3/3 |
| ExampleThermoporoelasticConsolidation | 0.769 | 0.819 | +0.050 | 11.0 | 21.0 | 2.0 | 2.3 | 39.0 | 86.7 | 3/3 |
| AdvancedExampleExtendedDruckerPrager | 0.769 | 0.705 | **−0.064** | 17.0 | 22.3 | 5.7 | 10.0 | 73.0 | 102.0 | 3/3 |
| ExampleThermalLeakyWell | 0.656 | 0.428 | **−0.227** | 16.3 | 28.7 | 0.0 | 18.0 | 52.0 | 124.0 | 3/3 |

(**read counts are mean per seed**; tool calls = total tool_use blocks
per seed.)

### Cross-task pattern signal

| | count |
|---|---:|
| C0 wins (Δ > 0) | 15/17 |
| C0 losses (Δ < 0) | 2/17 |
| C0 reads more XMLs than C1 | 13/17 |
| C0 reads more RSTs than C1 | 14/17 |
| C0 makes more total tool calls than C1 | 15/17 |
| C1 reads zero RSTs across all 3 seeds | **5/17** tasks (ThermalLeakyWell, kgdExperimentValidation, buckleyLeverettProblem, pknViscosityDominated, TutorialSneddon) |
| C0 reads zero RSTs across all 3 seeds | **1/17** (only `AdvancedExampleCasedContactThermoElasticWellbore`) |

In the **15 C0-wins**, on average:
- C0 reads **28.0 XMLs** vs C1 **22.6** (+24% more XML breadth)
- C0 reads **5.1 RSTs** vs C1 **1.9** (+170% more doc breadth)
- C0 makes **79.6 tool calls** vs C1 **53.9** (+48% more tool-use)

In the **2 C0-losses** (ExtendedDruckerPrager, ThermalLeakyWell), on
average:
- C0 reads **25.5 XMLs** vs C1 **16.7**
- C0 reads **14.0 RSTs** vs C1 **2.8** (~5× more) — both losses
  feature C0 reading much more documentation than C1
- C0 makes **113.0 tool calls** vs C1 **62.5** — dramatically longer
  trajectories

This is the cleanest cross-task signal we have so far for *why* C0
beats C1: **broader exploration**. C0 reads ~40% more XMLs and ~3×
more RSTs in the wins. The two losses are the runs where C0 went
*too* deep on docs — ThermalLeakyWell C0 read 18 .rst pages and
ended up with worse XML structure than C1's pure-example-copy
approach. The "Recommended workflow" text in C1's primer appears to
constrain doc-reading specifically (5/17 tasks have C1 reading
zero docs across all seeds).

### Tasks where the read-volume signal is strongest

The biggest C0 wins all have a clean exploration-volume gap:

- **ExampleMandel (Δ +0.641)**: C0 reads 23 XMLs + 3 RSTs vs C1's 12 +
  0.3. C0 finds more examples, including poromechanics-specific ones.
- **AdvancedExampleDruckerPrager (Δ +0.390)**: C0 reads 29 XMLs + 10
  RSTs vs C1's 12 + 7.3. The triaxial-driver family rewards docs but
  C0 still does ~2.5× more XML.
- **AdvancedExampleModifiedCamClay (Δ +0.370)**: C0 reads 29 XMLs vs
  C1's 9 — biggest XML-read ratio gap.
- **AdvancedExampleViscoDruckerPrager (Δ +0.237)**: C0 reads 33.7 XMLs
  + 8.3 RSTs vs C1's 9.3 + 4.7.

### Counter-examples (where C0 reads less but still wins)

- **ExampleDPWellbore (Δ +0.511)**: C0 reads **fewer** XMLs (23 vs
  C1's 32) but more RSTs (7.3 vs 1.7). Here doc-reading seems to
  substitute for redundant XML reads — C1 was thrashing in XML space
  without the right structural guidance.
- **AdvancedExampleDeviatedElasticWellbore (Δ +0.172)**: C0 reads
  fewer XMLs (24 vs 37) and fewer total calls (49 vs 67), yet still
  wins. C1's high-volume-but-narrow XML reading didn't help; C0's
  broader mix (more RSTs, fewer XMLs) won.

### The two losses

- **ExampleThermalLeakyWell (Δ −0.227)**: C0 read 18 RSTs (max in
  whole dataset) and 124 total tool calls. The XML it produced had
  parser errors (double-hyphen in comments, per the original
  ablation_C1_vs_C0 analysis) and dropped multiple top-level sections
  to score 0.0 (NumericalMethods, Outputs, Constitutive). High-volume
  doc-reading correlated with worse output here — possibly the agent
  got pulled into docs that didn't match the spec and lost track of
  the XML structure.
- **AdvancedExampleExtendedDruckerPrager (Δ −0.064)**: small loss; C0
  read 10 RSTs vs C1's 5.7. Within noise band, but the same direction
  as ThermalLeakyWell.

### Per-task XML/RST file lists

The full per-task list of *which specific files* each condition read
(top files by frequency, including unique-file counts per
(task, condition)) is in a companion document:

> `docs/2026-05-01_C0_C1_per_task_files.md`

That doc has, for each of the 17 tasks, four sub-blocks:
- C1 XMLs read (path, count)
- C0 XMLs read (path, count)
- C1 RSTs read (path, count)
- C0 RSTs read (path, count)

### Bottom line of §6.6

The score gap is **mostly explained by C0 doing more broad exploration**:
~40% more XML reads, ~3× more RST reads, ~60% more total tool calls.
The 5 tasks where C1 reads zero docs across all seeds correspond
exactly to the kind of behavior the "Recommended workflow" steers
toward (Glob → Read XML → Write → Read-back; no doc step). When C0
is freed from that prescription, it reaches for docs and source code
~3× more often, and that breadth is what the score gap reflects.

The two losses warn against a naive "more is better" reading: when
C0 spends >15 reads on .rst alone, it can lose ground. The right
target is breadth, not volume — confirmed by the ExampleDPWellbore
counter-example where C0 read *fewer* XMLs but won by 0.51.

## 7. What this implies for harness design

- **The minimal-vanilla primer does not add information; it constrains
  freedom.** Its workflow is what DSv4 already does — but adding it
  apparently anchors the agent to a narrower interpretation (one pass
  through Glob → Read → Write → Read), reducing the broad
  exploratory reads of `src/` and `src/docs/sphinx/` that seem to help.
- **DSv4 makes good use of source code as a truth-source.** ~14% of
  reads land in `src/coreComponents/constitutive*`. A primer that
  encourages this explicitly (e.g. "constitutive XML attribute names
  are defined in `<file>.hpp` via `static constexpr char const *`")
  could potentially help further — but only if it doesn't *also*
  constrain something that's currently helping.
- **The bash budget is small (5%) and almost all bookkeeping.** Any
  attempt to add a "validation" or "lint" step via Bash should be
  cheap; it would not displace useful behavior.
- **Subagent dispatch is rare and exploratory.** DSv4 uses Agent for
  breadth, not for delegation of generation. A "delegate XML
  generation" pattern is not part of its self-selected workflow.
- **The 81 emergent read-backs are a free correctness signal.** A
  Stop-hook that runs `xmllint` on `/workspace/inputs/*.xml` and
  injects a single "fix any errors" turn would compose with this
  existing pattern (rather than fight it).

## 8. Caveats and what this writeup does NOT establish

- **n=51 across 17 tasks; the triaxial-driver family is overrepresented**
  in the file-read distribution because 4/17 tasks share a
  `triaxialDriver_base.xml` ancestor. Patterns at the global aggregate
  may not generalize to a uniform task mix.
- **No counterfactual on C1 trajectories was reproduced here.** The
  per-task tool-use diffs in `ablation_C1_vs_C0.md` already showed
  some C0 runs make 2× more tool calls than C1, others make 2.7×
  fewer — so this aggregate description is the C0-side average, not a
  C0-vs-C1 mechanistic analysis. The "C1 anchors a narrower workflow"
  claim in §6 is consistent with the per-task tool-use diffs but is
  not directly tested by this writeup. A clean test would re-trace
  matched (task, seed) pairs across C0/C1 and diff the read-set
  trajectory, not just the final tool-count summary.
- **AGENTS.md is still loaded** (5KB of GEOS guidance, including a
  base/benchmark filename convention). C0 is not "fully empty" —
  removing AGENTS.md too would be the true capability floor for
  DSv4 + a 5-line primer.
- **The "1.6 read-backs/run" figure** counts reads of files under
  `/workspace/inputs/`. Some of those are reads of files the agent
  pre-populated from a triaxial example before editing — not strict
  output-verification reads. A trajectory-aware count (Read after the
  matching Write) would be tighter.

## 9. Verification of cited numbers

Per the project verification protocol, I cross-checked the headline
numbers cited in §1 and §6 against the raw `_summary.json` files
(treesim scored_mean, rescaled from 0-10 to 0-1):

| seed | C0 mean (raw) |
|---|---:|
| s1 | 0.7912 |
| s2 | 0.9219 |
| s3 | 0.8816 |

- **Mean across seeds: 0.8649** ✓ matches the 0.865 quoted from
  `2026-04-30_dsv4-ablation-final.md`.
- **Sample stdev: 0.0669** ≈ the 0.067 quoted.
- **Best seed (s2): 0.9219; best − mean gap = 5.7pp.** This exceeds
  the 3pp seed-dependence threshold in the verification protocol, so
  the right number to cite is the **mean (0.865)**, not best-seed —
  which is what this writeup and the parent ablation both do. Worth
  flagging: even C0's *worst* seed (0.791) still beats the C1 mean
  (0.671), so the qualitative finding "C0 > C1" survives the
  seed-dependence — but the magnitude of C0's lead depends materially
  on the seed.
- n_params not applicable: same model (`deepseek-v4-flash`) across C0
  and C1, so no parameter-count fairness gap.

## 10. Source data

```
runs/                /data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/abl_c0_true_vanilla/
                     {c0_dsv4_s1, c0_dsv4_s2, c0_dsv4_s3} × 17 tasks
                     events.jsonl + tool_calls.json per run
parent writeup       docs/2026-04-30_dsv4-ablation-final.md
ablation analyzer    docs/ablation_C1_vs_C0.{md,json}
abs-min primer       plugin/GEOS_PRIMER_absolute_min.md
minimal_vanilla      plugin/GEOS_PRIMER_minimal_vanilla.md
```

All numbers in this writeup are computed from the events.jsonl files
listed above (4260 tool_use blocks across 51 runs).

## 11. Appendix — full list of .rst files read in C0

99 unique files, sorted by total read count (across 51 runs). For
files tied at the same count, sorted alphabetically by path.

```
11  /geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst
10  /geos_lib/src/coreComponents/constitutiveDrivers/docs/TriaxialDriver.rst
10  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/DruckerPrager/Example.rst
 9  /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPrager.rst
 8  /geos_lib/src/coreComponents/constitutive/docs/solid/DruckerPragerExtended.rst
 7  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoDruckerPrager/Example.rst
 7  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoExtendedDruckerPrager/Example.rst
 7  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ViscoModifiedCamClay/Example.rst
 7  /geos_lib/src/docs/sphinx/basicExamples/co2Injection/Example.rst
 7  /geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst
 7  /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst
 6  /geos_lib/src/coreComponents/constitutive/docs/solid/ViscoPlasticity.rst
 6  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/Index.rst
 6  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ExtendedDruckerPrager/Example.rst
 5  /geos_lib/src/coreComponents/constitutive/docs/solid/ModifiedCamClay.rst
 5  /geos_lib/src/coreComponents/mesh/docs/Mesh.rst
 5  /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/CompositionalMultiphaseFlow.rst
 5  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/Index.rst
 5  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalLeakyWell/Example.rst
 5  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdViscosityDominated/Example.rst
 5  /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/XML.rst
 5  /geos_lib/src/docs/sphinx/tutorials/step03/Tutorial.rst
 4  /geos_lib/src/coreComponents/events/docs/EventManager.rst
 4  /geos_lib/src/coreComponents/fieldSpecification/docs/FieldSpecification.rst
 4  /geos_lib/src/coreComponents/fileIO/doc/OutputTasks.rst
 4  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdToughnessDominated/Example.rst
 4  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/Index.rst
 4  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/ModifiedCamClay/Example.rst
 4  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/dpWellbore/Example.rst
 4  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/verticalPoroElastoPlasticWellbore/Example.rst
 4  /geos_lib/src/docs/sphinx/tutorials/step01/Tutorial.rst
 4  /geos_lib/src/docs/sphinx/tutorials/step04/Tutorial.rst
 4  /geos_lib/src/docs/sphinx/userGuide/Index.rst
 3  /geos_lib/src/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability.rst
 3  /geos_lib/src/coreComponents/constitutive/docs/CO2BrineFluid.rst
 3  /geos_lib/src/coreComponents/constitutive/docs/solid/ElasticIsotropic.rst
 3  /geos_lib/src/coreComponents/constitutive/docs/solid/Plasticity.rst
 3  /geos_lib/src/coreComponents/constitutive/docs/solid/SolidModels.rst
 3  /geos_lib/src/coreComponents/constitutiveDrivers/docs/ConstitutiveDrivers.rst
 3  /geos_lib/src/coreComponents/events/docs/TasksManager.rst
 3  /geos_lib/src/coreComponents/physicsSolvers/PhysicsSolvers.rst
 3  /geos_lib/src/coreComponents/physicsSolvers/multiphysics/docs/Poromechanics.rst
 3  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/buckleyLeverett/Example.rst
 3  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/spe11b/Example.rst
 3  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/kgdValidation/Example.rst
 3  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/viscoplasticity/RelaxationTest/Example.rst
 3  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/edpWellbore/Example.rst
 3  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/kirschWellbore/Example.rst
 3  /geos_lib/src/docs/sphinx/basicExamples/poromechanics/Example.rst
 3  /geos_lib/src/docs/sphinx/tutorials/step02/Tutorial.rst
 2  /geos_lib/src/coreComponents/constitutive/docs/RelativePermeabilityModels.rst
 2  /geos_lib/src/coreComponents/constitutive/docs/TableRelativePermeability.rst
 2  /geos_lib/src/coreComponents/fileIO/doc/Index.rst
 2  /geos_lib/src/coreComponents/fileIO/doc/InputXMLFiles.rst
 2  /geos_lib/src/coreComponents/fileIO/doc/LogCsvOutputs.rst
 2  /geos_lib/src/coreComponents/linearAlgebra/docs/LinearSolvers.rst
 2  /geos_lib/src/coreComponents/physicsSolvers/SolutionStrategy.rst
 2  /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/contact/docs/ContactMechanics.rst
 2  /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/contact/docs/SolidMechanicsEmbeddedFractures.rst
 2  /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/docs/SolidMechanics.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/isothermalHystInjection/Example.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/Index.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/intersectFrac/Example.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/poromechanics/Index.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/thermoPoromechanics/Index.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/Index.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/casedElasticWellbore/Example.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/deviatedPoroElasticWellbore/Example.rst
 2  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/thermoPoroElasticWellbore/Example.rst
 2  /geos_lib/src/docs/sphinx/basicExamples/multiphaseFlowWithWells/Example.rst
 2  /geos_lib/src/docs/sphinx/developerGuide/Contributing/InputFiles.rst
 1  /geos_lib/inputFiles/compositionalMultiphaseFlow/rstFile/co2_flux_3d_restart.rst
 1  /geos_lib/src/coreComponents/constitutive/docs/BiotPorosity.rst
 1  /geos_lib/src/coreComponents/constitutive/docs/BlackOilFluid.rst
 1  /geos_lib/src/coreComponents/constitutive/docs/CompositionalMultiphaseFluid.rst
 1  /geos_lib/src/coreComponents/constitutive/docs/Constitutive.rst
 1  /geos_lib/src/coreComponents/constitutive/docs/FluidModels.rst
 1  /geos_lib/src/coreComponents/constitutive/docs/TableCapillaryPressure.rst
 1  /geos_lib/src/coreComponents/constitutive/docs/solid/Damage.rst
 1  /geos_lib/src/coreComponents/discretizationMethods/docs/NumericalMethodsManager.rst
 1  /geos_lib/src/coreComponents/fieldSpecification/docs/AquiferBoundaryCondition.rst
 1  /geos_lib/src/coreComponents/fieldSpecification/docs/EquilibriumInitialCondition.rst
 1  /geos_lib/src/coreComponents/functions/docs/FunctionManager.rst
 1  /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/ImmiscibleMultiphaseFlow.rst
 1  /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/ProppantTransport.rst
 1  /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/docs/SinglePhaseFlow.rst
 1  /geos_lib/src/coreComponents/physicsSolvers/fluidFlow/wells/docs/CompositionalMultiphaseWell.rst
 1  /geos_lib/src/coreComponents/physicsSolvers/solidMechanics/contact/docs/SolidMechanicsConformingFractures.rst
 1  /geos_lib/src/docs/sphinx/Publications.rst
 1  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/Index.rst
 1  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/thermalLeakyWell/Example.rst
 1  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/faultVerification/Example.rst
 1  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/faultMechanics/singleFracCompression/Example.rst
 1  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/hydraulicFracture/pennyFracViscosityDominated/Example.rst
 1  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/deviatedPoroElasticWellbore/Example2.rst
 1  /geos_lib/src/docs/sphinx/advancedExamples/validationStudies/wellboreProblems/mccWellbore/Example.rst
 1  /geos_lib/src/docs/sphinx/basicExamples/Index.rst
 1  /geos_lib/src/docs/sphinx/developerGuide/Contributing/IntegratedTests.rst
 1  /geos_lib/src/docs/sphinx/developerGuide/KeyComponents/WorkingWithData.rst
```

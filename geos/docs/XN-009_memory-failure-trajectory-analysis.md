---
id: XN-009
source: trajectory-analysis
title: Memory Augmentation Failures on Catastrophic-Rescue Tasks
dag_nodes: [E03, E04, E05, E07, E09, E11, I10]
created: 2026-04-20
---

## Executive Summary

All 6 memory augmentations (E04, E05, E07, E09, E11, and attempted E08) regress the plugin's catastrophic-failure rescue mechanism from 0.804/0.948/0.992 (Sneddon/Mandel/DPWellbore) to ~0.08/~0.27/~0.30. Root cause analysis of trajectory events reveals three distinct failure mechanisms:

1. **Memory anchoring to wrong solver family** (E04, E05): Cheatsheet/short-mem variants bias the agent toward non-semantic READs into workspace/unrelated reference XMLs, breaking the discovery phase.
2. **Filetree path hijacking semantic search** (E07): Agent uses provided paths directly instead of calling semantic RAG, bypassing the discovery phase entirely.
3. **Memory lookup returns wrong physics domain** (E11): G-memory tool suggests unrelated prior tasks (hydraulic fracturing instead of embedded fracture, KGD instead of poromechanics), poisoning early search queries.

The fundamental problem is that all augmentations fire **upfront as a warm-start**, contaminating the semantic discovery phase that works in E03. The plugin's rescue strategy depends on iterative RAG refinement starting from high-level physics keywords, progressively narrowing to reference XMLs via semantic similarity. All memory variants short-circuit this loop.

---

## Task-by-Task Analysis

### TutorialSneddon (Embedded Fracture Verification)

**E03 (Plugin-Only) Baseline — Score 0.804**

Plugin executes a principled discovery loop:
1. **Initial RAG queries** (semantic + navigational):
   - "embedded fracture surface generation solid mechanics" → finds EmbeddedFractures solver
   - "Lagrangian contact mechanics fracture interface" → surfaces ContactMechanics solver
   - "embedded fracture solver" → narrowing
2. **Key READs**:
   - `/geos_lib/inputFiles/lagrangianContactMechanics/ContactMechanics_TFrac_benchmark.xml` (first read, broad exploration)
   - `/geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_staticCondensation_benchmark.xml` (narrowed to embedded frac family)
3. **Adaptive exploration**: After reading ContactMechanics files, agent realizes Sneddon is embedded-frac specific and pivots to efemFractureMechanics directory.
4. **Final strategy**: Selects embedded fracture solver family with static condensation, then successfully adapts reference XML.

**E04 (Long Cheatsheet) — Score ~0.08**

Cheatsheet includes exact task names and file paths from offline memory:
- Memory contains: "Sneddon_embeddedFrac_base.xml", "TutorialSneddon", etc.

Divergence point (turns 1-2):
- RAG query: "Sneddon_embeddedFrac_base.xml" (direct file name lookup, NOT semantic)
- Searches now anchor to workspace/input files instead of library reference XMLs
- First READ: `/workspace/inputs/sneddon_embedded_benchmark.xml` (agent-created benchmark, not a reference)
- Subsequent READs loop between:
  - `/workspace/inputs/sneddon_embedded_benchmark.xml` (repeated 3x)
  - `/geos_lib/inputFiles/efemFractureMechanics/SneddonRotated_benchmark.xml` (rotated variant, wrong solver parameters)

**Failure mechanism**: Cheatsheet anchors agent to workspace outputs instead of reference XMLs. Agent never explores ContactMechanics or broad solver discovery; it pattern-matches on file names rather than physics. This prevents the iterative refinement that finds the correct embedded fracture family.

**E05 (Short Cheatsheet) — Score ~0.08**

Similar to E04 but with fewer memory entries. First RAG queries are semantic ("Sneddon embedded fracture base xml"), but then:
- Agent reads `Sneddon_embeddedFrac_base.xml` (correct)
- But then pivots to lagrangianContactMechanics reads: `Sneddon_smoke.xml`, `Sneddon_base.xml`, `ALM_Sneddon_benchmark.xml`
- Then searches for unrelated solvers: "Hydrofracture solver", "Coulomb" friction

**Failure mechanism**: Short cheatsheet is too sparse to guide correctly but still biases search. Agent reads both embedded-frac AND contact-mechanics variants, confusing the solver family selection. Without strong anchoring, it explores both paths superficially and fails to adapt correctly.

**E07 (Filetree) — Score ~0.08**

Filetree provides directory structure. Agent bypasses RAG entirely:
- First 3 RAG calls do semantic search ("Sneddon embedded fracture base xml", "efemFractureMechanics Sneddon")
- **But then directly READs from filetree paths**:
  - `/geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFracShapes_base.xml`
  - `/geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_staticCondensation_benchmark.xml`
  - Stops searching after 3 reads

**Failure mechanism**: Filetree provides "good enough" paths immediately, bypassing the search refinement loop. Agent reads the correct files but doesn't understand *why* they're correct or what other solvers might apply. The plugin's rescue mechanism requires understanding solver alternatives (contact vs embedded frac); filetree short-circuits that reasoning.

**E09 (Workspace Cheatsheet) — Score ~0.08**

Workspace cheatsheet is a dynamic memory of recent task workspace variables. First RAG queries are semantic ("Sneddon embedded fracture"), but then:
- READs jump between multiple solver families: embedded-frac, contact-mechanics, AND hydraulic fracturing
- Sequence: `Sneddon_embeddedFracShapes_base.xml` → `Sneddon_smoke.xml` (contact) → `ContactMechanics_Sneddon_benchmark.xml` → `ALM_Sneddon_benchmark.xml` → `Sneddon_hydroFrac_base.xml` (hydrofrac!)

**Failure mechanism**: Workspace memory contains variables from many solver families, creating a "soup of references." Agent explores all of them equally, never focusing on the correct family. The iterative narrowing that works in E03 (discover ContactMechanics, realize Sneddon is different, pivot to embedded-frac) is obscured by too many options at once.

**E11 (G-Memory MCP) — Score ~0.08**

G-memory tool returns: `memory_lookup("Sneddon fracture pressurized static fracture embedded fracture porous elastic medium")`

Results (ranked by match_score):
1. **ExampleTFrac** (match_score: 0.411, final_treesim: 0.5964)
   - Suggested XMLs: `casedWellbore.xml`, `Sneddon_embeddedFrac_verification.xml`, `SingleFracCompression_base.xml`
   - **Wrong domain**: TFrac is cased-wellbore + single fracture compression, NOT embedded fracture
2. **kgdViscosityDominated** (match_score: 0.358)
   - Suggested XMLs: hydraulic fracturing (KGD)
   - **Completely wrong physics**: hydrofracture, not embedded fracture

**What the agent did**:
- First READ: `/geos_lib/inputFiles/efemFractureMechanics/Sneddon_embeddedFrac_verification.xml` (from memory suggestion, correct by accident)
- But memory also surfaced `ALM_Sneddon_benchmark.xml` (augmented Lagrangian contact)
- Subsequent RAG pivots toward schema queries (PackCollection, Rectangle), losing physics focus

**Failure mechanism**: Memory lookup poisoned the search space with similar-sounding but wrong-domain tasks (kgdToughnessDominated from "Sneddon fracture"). The verification variant is correct but downstream queries diverge because the agent doesn't trust memory and oversearches, confusing embedded fracture with contact mechanics.

---

### ExampleMandel (Poromechanics Consolidation)

**E03 Baseline — Score 0.948**

Disciplined sequence:
1. RAG: "Mandel poromechanics benchmark" → finds SinglePhasePoromechanics solver
2. RAG: "PoroElastic_base.xml" → narrow to benchmark family
3. READs: Correctly identifies `PoroElastic_Mandel_*` files in poromechanics/ directory
4. Schema exploration: SinglePhasePoromechanics solver family confirmed
5. Success: Adapts reference XML with correct solver

**E04 Cheatsheet — Score ~0.27**

Cheatsheet anchors to:
- First RAG: "Mandel poromechanics benchmark XML configuration" (semantic)
- But then reads `Example.rst` (documentation, not executable XML!)
- Subsequent READs include Terzaghi (`PoroElastic_Terzaghi_base_direct.xml`), wrong benchmark

**Failure mechanism**: Cheatsheet inclusion of Example.rst diverts the agent to documentation browsing instead of XML parametrization. The agent never builds a model with Mandel-specific parameters; it gets stuck in schema understanding rather than adaptive XML editing.

**E05 Short Cheatsheet — Score ~0.27**

Slightly better than E04 (still fails) because memory is sparser:
- Correctly reads `PoroElastic_Mandel_smoke_fim.xml`
- But then searches for unrelated schemas: "PorousElasticIsotropic", "SinglePhaseFVM" (flow, not mechanics+flow coupling)
- Final READs: Jumps to workspace files `MandelConsolidation_base.xml` (repeated 4x), suggesting agent is lost and re-reading same file

**Failure mechanism**: Sparse memory doesn't guide well enough. Agent reads correct Mandel files but can't assemble them into a coupled solver configuration because memory doesn't emphasize the interaction between mechanics (SinglePhasePoromechanics) and flow (SinglePhaseFVM).

**E07 Filetree — Score ~0.27**

Filetree paths again short-circuit search:
- READs directly: `PoroElastic_Mandel_smoke_fim.xml`, `PoroElastic_Mandel_benchmark_sequential.xml`, etc.
- Agent never questions whether FIM or sequential is correct
- Then searches schema (SinglePhasePoromechanics) but explores irrelevant solvers: SinglePhaseFVM attributes, InternalMesh
- Final workspace READs repeated

**Failure mechanism**: Filetree provides multiple Mandel variants (smoke, benchmark_sequential, prism6_hybrid), but agent doesn't reason about which is appropriate. Without the semantic RAG loop that would justify solver choices, agent defaults to first-listed variants and fails to adapt parameters.

**E09 Workspace Cheatsheet — Score ~0.27**

Workspace contains prior Mandel task workspaces. Agent behavior:
- Semantic RAG queries: "Mandel consolidation poromechanics benchmark"
- READs: Correctly identifies all three Mandel variants
- But then searches too broadly: "Mandel consolidation" → finds Example.rst documentation
- Final reads: Jumps to unrelated solver (PoroElasticWellbore)

**Failure mechanism**: Workspace memory is too recent-task-focused. Agent reads correct files but documentation and workspace variables create ambiguity about which solver/parameters to use. The iteration that narrows (E03) is replaced by a broad search that finds all Mandel variants at once, with no principled selection.

**E11 G-Memory — Score ~0.27**

G-memory lookup returns **kgdToughnessDominated** (match_score: 0.49) as top result:
- Suggested XMLs: hydraulic fracturing (KGD model)
- **Completely wrong physics**: Query was "poromechanics Mandel consolidation", but top result is hydraulic fracturing

What agent did:
- Called memory_lookup immediately
- Memory suggested hydrofracture and fault-related examples
- Agent then performed its own semantic searches: "Mandel consolidation poromechanics"
- Correctly read Mandel files despite bad memory, but spent many turns on schema queries (porousMaterialNames, SinglePhasePoromechanics) trying to reconcile memory vs. semantics

**Failure mechanism**: Memory lookup's top result is *semantically similar but physically opposite* (fracture propagation vs. consolidation settlement). Agent distrusts memory and over-searches, wasting token budget on schema exploration instead of rapid adaptation. The low match_score (0.49) indicates the memory retrieval is genuinely confused between hydrofracture and poromechanics.

---

### ExampleDPWellbore (Drucker-Prager Elastoplasticity)

**E03 Baseline — Score 0.992**

Nearly perfect execution:
1. RAG: "SolidMechanicsLagrangianFEM Drucker Prager plasticity" → solver family identified
2. RAG: "ExtendedDruckerPragerWellbore_base.xml" → reference found
3. READs: Correct wellbore variants explored, extended plasticity chosen
4. Success: Parameters adapted correctly with correct solver

**E04 Cheatsheet — Score ~0.30**

Cheatsheet anchors to unrelated solvers:
- First RAG: "DruckerPragerWellbore_base.xml" (correct)
- But then reads `KirschProblem_base.xml` (elastic Kirsch problem, NO plasticity!)
- Searches become misdirected: "plasticStrain" field (correct concept, but reads K arch problem which is elastic)
- Final reads: `SolidFields.hpp`, `DruckerPrager.hpp` C++ source (implementation, not XML config)

**Failure mechanism**: Cheatsheet suggests Kirsch problem as a learning example. Agent reads it and then assumes it's the reference, spending many turns exploring wrong physics (elastic stress) instead of plastic deformation. Ultimately reads source code instead of example XMLs.

**E05 Short Cheatsheet — Score ~0.30**

Similar to E04 but memory is sparser:
- Correctly reads Extended DP wellbore variants
- But searches for unrelated concepts: "DruckerPrager defaultHardeningRate", "rock_plasticStrain"
- Final reads: `ModifiedCamClayWellbore_base.xml` (different plasticity model, Cam-Clay not DP!)
- Repeated reads to `DruckerPragerWellbore_base.xml` suggest agent is lost

**Failure mechanism**: Short cheatsheet doesn't emphasize wellbore+plasticity coupling. Agent reads correct files but explores incompatible plasticity models (Cam-Clay) and gets stuck trying to reconcile them.

**E07 Filetree — Score ~0.30**

Filetree suggests Extended DP wellbore files directly. Agent:
- READs: Correctly gets `ExtendedDruckerPragerWellbore_base.xml`, `_benchmark.xml`
- But then explores tangential searches: "defaultHardeningRate", "plastic strain field"
- READs: Jumps to incompatible plasticity (`ModifiedCamClayWellbore_base.xml`), then documentation
- Final workspace reads suggest adaptation failure

**Failure mechanism**: Filetree short-circuits early discovery. Agent has correct reference but doesn't understand *why* ExtendedDruckerPrager is appropriate (vs. ModifiedCamClay or viscoExtendedDP). Without the semantic reasoning loop, agent confuses related plasticity models and fails to adapt parameters.

**E09 Workspace Cheatsheet — Score ~0.30**

Workspace contains prior DP wellbore tasks. Agent:
- Semantic RAG: "DruckerPrager wellbore solid mechanics validation"
- READs: Correctly identifies `ExtendedDruckerPragerWellbore_base/benchmark.xml`
- But then searches: "PackCollection", "Traction" boundary conditions (correct concept, but explores multiple boundary condition types)
- Final reads: Correct files but then schema exploration, + source code (`DruckerPrager.hpp`)

**Failure mechanism**: Workspace memory is rich (many related fields/BC types), causing the agent to over-explore. The semantic loop that narrows (E03) is replaced by exploration of all related concepts, burning tokens on boundary condition schema instead of solver+plasticity parametrization.

**E11 G-Memory — Score ~0.30**

G-memory lookup returns **triaxialDriverExample** (match_score: 0.971, best-scored result):
- Suggested XMLs: `triaxialDriver_ExtendedDruckerPrager.xml`, `triaxialDriver_base.xml`, `triaxialDriver_DruckerPrager.xml`
- **Correct solver family** (Extended DP) but **wrong geometry** (triaxial lab test, not wellbore)

What agent did:
- Called memory_lookup first
- Memory suggested triaxial driver examples (good match on plasticity, poor on geometry)
- Correctly read some wellbore files, but then pivoted to triaxial files: `triaxialDriver_DruckerPrager.xml`
- Explored boundary conditions (Traction) heavily because triaxial uses simpler BCs than wellbore
- Final reads: Correct Extended DP wellbore files but also source code

**Failure mechanism**: Memory returned correct physics domain (ExtendedDruckerPrager) but wrong application (triaxial ≠ wellbore). Agent followed memory's suggestion and spent turns on triaxial examples, then had to back-track to wellbore geometry. The solver is right but the reference geometry and boundary conditions are wrong, breaking the adaptation process.

---

## Common Failure Mechanisms

### Pattern 1: Cheatsheet Anchoring (E04, E05)
- **What breaks**: Semantic discovery phase
- **Why**: Cheatsheet is derived from offline prior runs, mapping task name → file paths. Agent pattern-matches on names instead of understanding physics.
- **Evidence**: E04/E05 both read workspace input files first (outputs of previous runs) instead of library references.
- **Cost**: Prevents the iterative RAG refinement; agent never explores solver alternatives.

### Pattern 2: Filetree Hijacking (E07)
- **What breaks**: Reasoning about *why* a reference is appropriate
- **Why**: Filetree provides correct paths but no semantic justification. Agent takes paths as gospel rather than learning.
- **Evidence**: E07 reads correct files immediately but then explores unrelated schema/solvers.
- **Cost**: Adapter fails because agent doesn't understand solver family structure.

### Pattern 3: Memory Lookup Poisoning (E11)
- **What breaks**: Initial search space
- **Why**: Semantic similarity retrieves wrong domains (KGD hydrofracture vs. embedded fracture, triaxial vs. wellbore).
- **Evidence**: 
  - Sneddon query returns kgdViscosityDominated (wrong physics)
  - Mandel query returns kgdToughnessDominated (wrong physics)
  - DPWellbore query returns triaxialDriver (right solver, wrong geometry)
- **Cost**: Poisons RAG queries or forces agent to distrust memory and over-search.

### Universal Issue: Upfront Memory Firing
All augmentations activate memory **at the start of task** (cold start + memory warm-start). This contaminates the semantic discovery loop immediately. The plugin's catastrophic-failure rescue relies on **iterative refinement**: broad semantic search → progressive narrowing → reference file discovery → adaptive XML editing.

When memory fires upfront:
- Agent can't distinguish memory suggestions from own reasoning
- Early RAG queries are biased by memory anchors
- The iterative loop (which *works* in E03) is short-circuited

---

## Root Cause

The plugin's 0.804/0.948/0.992 performance on these three tasks depends on a **semantic-discovery RAG loop** that:

1. **Starts high-level** ("embedded fracture", "Mandel consolidation", "Drucker Prager elastoplasticity")
2. **Progressively narrows** through iterative RAG queries and READs
3. **Discovers solver families** by exploring alternative directories and schema
4. **Adapts reference XMLs** with specific solver+geometry+parameters

All memory variants replace this loop with either:
- **Anchor biasing** (E04/E05): Pattern-matching on names
- **Path hijacking** (E07): Short-circuiting to known files
- **Domain poisoning** (E11): Contaminating search with wrong-physics priors

The catastrophic failures (0.08/0.27/0.30 scores) reflect the agent either:
- Reading workspace outputs instead of library references (E04/E05)
- Exploring multiple incompatible solver families (E07/E09)
- Trusting wrong-domain memory suggestions (E11)

---

## Concrete Next-Experiment Proposals

### Proposal 1: Delay-Trigger Memory (Low Risk)
Memory activates **only if semantics fail to find reference XMLs in 3 RAG iterations**. Agent must attempt semantic discovery first; memory only fires as a rescue.

**Test design**:
- E12a: Same G-memory (E11) but triggered when `mcp__geos-rag__search_technical` returns <0.6 match score
- E12b: Same cheatsheet (E04) but only injected after 2 failed RAG rounds

**Rationale**: Preserves semantic discovery loop while allowing memory to rescue if needed. Expected score: 0.6–0.8 (better than E04/E07, might not reach E03).

### Proposal 2: Physics-Family Filtering
Memory retrieval filtered to **same-solver-family only**. For Sneddon queries, only return prior tasks with EmbeddedFractures or ContactMechanics solvers (not hydraulic fracturing).

**Test design**:
- E13: G-memory (E11) but memory lookup filters results by `solver_family` tag
- Require match that shares ≥1 solver with query task

**Rationale**: E11's failure was returning kgdToughnessDominated (hydrofracture) for Sneddon (embedded fracture). Physics-family filtering prevents cross-domain poisoning. Expected score: 0.7–0.9.

### Proposal 3: Memory as Negative Examples
Instead of "here are XMLs to read," memory provides "don't use these solvers; that failed before" and "this solver family is appropriate for Sneddon tasks."

**Test design**:
- E14: Structured memory entries: `{task_id, success_solver_family, failed_solver_families, reference_xmls_to_avoid}`
- Agent uses this to *exclude* options during semantic search, not to anchor reads

**Rationale**: Inverts memory's role from prescriptive (read X) to proscriptive (avoid Y). Preserves semantic loop while filtering bad paths. Expected score: 0.75–0.9.

---

## Conclusion

Memory augmentations fail because they activate upfront and disrupt the semantic-discovery RAG loop that is essential for catastrophic-failure rescue on Sneddon/Mandel/DPWellbore. The plugin's strengths (iterative narrowing, exploring solver alternatives, understanding physics families) are bypassed by memory's pattern-matching and path-hijacking.

**Key insight**: Memory is useful for *constraining search space*, not for *short-circuiting reasoning*. Delaying memory activation, filtering by physics family, or using memory for exclusion (not inclusion) could unlock the benefit of past experience without breaking the loop that makes the plugin work.


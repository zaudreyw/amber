# Jun 7 changelist — `jun7_v0.tex`

Changes applied in response to `jun7_feedback_v0.md`. Acted on the **first set** (advisor + collaborator) plus the user-requested limitation. The "Feedback to discuss" item (intro bullet-list) is **not** changed — discussion below.

Compiles clean (`pdflatex jun7_v0.tex`, exit 0, no errors).

---

## Advisor feedback

### 1. Abstract — "small" → "lightweight" (adapter description)
Last sentence of the active abstract.
- **Before:** "Together these results suggest that **a small**, self-improvable grounding layer is enough..."
- **After:** "Together these results suggest that **a lightweight**, self-improvable grounding layer is enough..."

### 2. Introduction — "small" → "lightweight" (last paragraph)
- **Before:** "**A small**, self-improvable grounding layer around a general coding agent can compress..."
- **After:** "**A lightweight**, self-improvable grounding layer around a general coding agent can compress..."
(Folded into change #3, same sentence.)

### 3. Introduction — rewrite confusing 2nd sentence of last paragraph ("Taken together...")
Advisor: too confusing / too much to read; wants it straightforward, less wordy; OK to shorten or parenthesize the mechanism→bottleneck mapping. Strong premium on clarity.
- **Before:** "A small, self-improvable grounding layer around a general coding agent can compress a representative deck-authoring task from hours to minutes, while adapting its mechanism to the simulator interface: validation when completeness is the bottleneck, and memory or retrieval when domain correctness is the bottleneck."
- **After:** "A lightweight, self-improvable grounding layer around a general coding agent can compress a representative deck-authoring task from hours to minutes, while adapting to each simulator's dominant bottleneck (validation for incomplete outputs; memory and retrieval for incorrect domain values)."
- Rationale: keeps the two ideas (speedup + bottleneck-adaptive mechanism), drops the "adapting its mechanism to the simulator interface:" clause, and compresses the MECH→BOTTLENECK mapping into a short parenthetical.

---

## Collaborator feedback

### 4. Table 1 (`tab:main-results`) — easier horizontal reading
Collaborator: hard to follow horizontally; suggested row lines, thicker/doubled existing rules, or alternating row backgrounds.
- **Change:** enabled alternating row background colors. Added `\rowcolors{3}{gray!12}{white}` immediately before `\begin{tabular}` (striping starts at the first data row, Vanilla), and switched `\usepackage{xcolor}` → `\usepackage[table]{xcolor}` to enable it.
- Chose striping over added `\hline`s because it preserves the existing booktabs rules (no need to thicken/double them) and makes the component `•` dots trivially trackable across each row.
- Verified `neurips_2026.sty` does not load xcolor/colortbl, so no package-option clash.

### 5. Background — DSL correctness ("a deck ... is a DSL")
Advisor: is it right to call a file (a set of files written in a DSL) a DSL? More correct: GEOS uses XML, but its vocabulary/schema make its *config language* more akin to a DSL.
- **Before:** "Although the surface syntax is XML, a deck is better understood as a small domain-specific language (DSL): a simulator-specific program whose tags name GEOS components and whose attributes set their parameters."
- **After:** "Although GEOS reads plain XML, its elaborate tag vocabulary and validation schema make its configuration language closer to a small domain-specific language (DSL); a deck is then a program in that language, whose tags name GEOS components and whose attributes set their parameters."
- Fix: the *language* is the DSL; a *deck* is a program written in it. Removes the file-is-a-DSL conflation while keeping the downstream "Writing a deck is a translation ... into a structured program" framing consistent.

### 6. Method / base harness & objective — generalize the reward metric (introduce TreeSim as the GEOS instantiation)
Advisor: TreeSim is used before it is introduced; readers may conflate it with the OpenFOAM/LAMMPS metrics. Clarify TreeSim is the GEOS quality metric specifically.
- **Rev 2 (current):** the reward equation now uses a generic quality metric `Q`, with TreeSim named as the GEOS instantiation. Keeps the Method section simulator-agnostic (matching its generic interface-grounding framing) and resolves the conflation in one move.
  - **Before:** `r(τ,x) = TreeSim(ŷ(τ), y*(x)) ∈ [0,1]` scores the deck...
  - **After:** `r(τ,x) = Q(ŷ(τ), y*(x)) ∈ [0,1]` scores the generated configuration... "where Q is a task-appropriate quality metric: tree-edit similarity (TreeSim) for GEOS, defined in §5, and the file-coverage and LLM-judge metrics of §6.6 and §6.7 for the transfer studies."
- (Rev 1 had kept TreeSim in the equation and appended a GEOS-specific clarifier sentence; superseded.)

### 7. Component paragraphs — bold R and M (parallel to S, X)
- **R paragraph:** the leading factor reference is now `\textbf{R}` (was plain "R").
- **M paragraph:** the leading factor reference is now `\textbf{M}` (was plain "M").
- Now consistent with the S+X paragraph, where `\textbf{S}` and `\textbf{X}` were already bold.

### 8. R paragraph — mention/define RAG; acknowledge agent already does find/grep retrieval
Advisor: the coding agent already does retrieval via find/grep (which we acknowledge), but due to its drawbacks we add semantic search that prior RAG research has investigated; cite `lewis2021rag`.
- **Added:** "The base coding agent can already retrieve over the simulator's documentation and example tree through its built-in `find`/`grep` tools, but this keyword search is brittle when the agent does not already know the right simulator terms to search for. **R** therefore adds semantic search over the same artifacts, the retrieval-augmented generation (RAG) approach that prior work has thoroughly investigated [lewis2021rag]: it extends the tool set with ..."
- `lewis2021rag` confirmed present in `references.bib`.

### 9. "The SIGA design space" — reword clunky "subset" definition
Advisor: "We refer to any wrapper instantiating such a subset as a SIGA" is clunky; prefer describing SIGA as the add-on (plugin) built on an existing coding agent from a minimal recipe (cross-session memory, knowledge-base connectors, validation/self-refinement).
- **Before:** "An adapter is thus an active subset b ∈ {0,1}^{R,S,X,M} of these slots; b=0 recovers the bare harness (Vanilla). We refer to any wrapper instantiating such a subset as a Simulator-Interface Grounding Adapter (SIGA), with the factor letters denoting which grounding interventions are enabled, and we study this design space by factorial ablation in §5."
- **After:** "A Simulator-Interface Grounding Adapter (SIGA) is the add-on, a plugin built on top of an existing coding agent, that instantiates this minimal recipe: cross-session procedural memory, additional connectors to domain knowledge bases, and validation-driven self-refinement. Concretely, a given adapter is an active subset b ∈ {0,1}^{R,S,X,M} of the four slots above, the factor letters denoting which grounding interventions are enabled; b=0 recovers the bare harness (Vanilla). We study this design space by factorial ablation in §5."

---

## User-requested addition (from feedback file intro)

### 10. Limitation — LLM user simulator in autonomy study
Added to the **Limitations** paragraph (App. D, "Extended discussion" — limitations live in the appendix, not the main text; main text §7 Broader impact defers them there).
- **Added:** "In the autonomy study (§6.5), the ``human supervisor'' the agent could consult was an LLM user simulator (a separate `deepseek-v4-flash` prompted with the full original brief), not a real human, for time and cost reasons; this is a reasonable proxy for measuring consultation behaviour but is not a substitute for studying live human–agent interaction."

---

## NeurIPS checklist removal (for arXiv preprint)

Not yet applied — see chat. The checklist is a single include at the end of the document:
```latex
\newpage
\input{checklist.tex}
```
To drop it for the preprint, comment out those two lines (or delete them). Optionally also switch `\usepackage{neurips_2026}` → `\usepackage[preprint]{neurips_2026}` to de-anonymize and remove the "submitted to NeurIPS" footer (see the comment on that line in the preamble).

---

## Round 2 (applied)

### 11. Intro last paragraph — full rewrite (3 sentences)
- **S1 (option A): drop the "rather than replacing scientific reasoning" framing.** It set up a false dichotomy and contradicted RQ4 (the task does require domain judgment). Reframed to bounded/near-term tool operation vs open-ended autonomous discovery, without claiming the task is reasoning-free.
  - **Before:** "...near-term AI-for-science agents can deliver value by mastering the interfaces of existing scientific tools, rather than by replacing scientific reasoning."
  - **After:** "...a pragmatic near-term target for AI-for-science: making agents reliable at operating the complex software scientific work already depends on. This is a bounded and immediately valuable goal, distinct from and a sensible precursor to the longer-term aim of autonomous scientific discovery."
- **S2: generalize away from the human-baseline-specific phrasing.** "compress"/"representative deck-authoring task" → "cut simulator setup from hours to minutes."
- **S3: drop the "We do not claim..." hedge** (the honest scoping stays in Limitations, App. D). Stated positively: "The minimal grounding design and the self-evolution mechanism together give a concrete recipe for adapting a general coding agent to a new simulator interface with modest effort."

### 12. SIGA design space — redefine as recipe / bounded design space (supersedes round-1 #9)
Round-1 reword kept the clunky "active subset" definition; removed now.
- SIGA is now defined as a plugin built from a small, fixed set of grounding **ideas** (M, R, X, S), i.e. a compact **design space**, not one fixed stack of four mandatory components.
- **Decision on the `{0,1}` formalism:** kept, but reframed. `b ∈ {0,1}^{R,S,X,M}` now describes *the design space* (a concrete adapter is a point in it); the Resolution-IV `2^{4-1}` factorial stays in §5.1 as *our instantiation* of searching that space. So the binary vector = recipe-level descriptor; the factorial = how this paper explores it.
- Adapting to a new simulator = instantiate the relevant ideas against the simulator's contract and keep those that help (which idea is binding is interface-dependent, per §6). Not a cop-out, because the paper supplies the bottleneck→component heuristic; "run a light ablation" is backed by the finding that the best subset shifts per simulator.
- No em dashes in the new S1-A and SIGA text, per author request.

### 13. Method reward metric — see revised #6 above (generic `Q`, TreeSim as GEOS instantiation).

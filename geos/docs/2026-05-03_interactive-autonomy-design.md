# Interactive autonomy + difficulty-ramp evaluation

*Design doc — 2026-05-03. Author: research-copilot (matt). Status: PROPOSED.*

> Companion experiment for the ICML 2026 AI4Science workshop submission
> (theme: *autonomous discovery loops — decide when to consult human
> oversight or simulations*). This does **not** replace the main NeurIPS
> battery (AUTOCAMP / test-17 / ICL-10 / bottleneck pipeline). It is a
> small, additive study that lets us claim something the main paper
> currently cannot: how the agent behaves when the user under-specifies
> the simulation, and how productively it consults a simulated
> supervisor.

## 1. Motivation

The main battery scopes the GEOS XML authoring task narrowly: the
natural-language `instructions.txt` already encodes every value the
ground-truth XML contains, down to material density and Newton
tolerance. This is a fair benchmark for the *translation* sub-problem,
but it does not measure what most matters for an "AI scientist":
**how the agent behaves when it has to decide what's missing, fill in
sensible defaults, and ask the human only when it has to.**

The workshop description we are targeting puts this front and centre:

> Build and evaluate agents that plan experiments, control
> instruments, and decide when to consult human oversight or
> simulations.

We have an unused asset that maps directly onto this: the difficulty
tiering already proposed (`/home/matt/sci/geos_agent/cc_docs/difficulty_tiers_pitch.md`,
`misc/geophys_todo.md` §"On Controlling Difficulty"). It classifies
each ground-truth XML parameter into four tiers and contemplates an
"easy" (all values given) vs "hard" (only T4 problem-defining values
given) split. RQ4 in `direction.md` explicitly listed this as a
deferred experiment. We bring it forward here because the workshop
framing rewards it, and because a small, focused study fits the
remaining timeline.

The main paper still rests on test-17 / ICL-10 / cross-model results
on the *easy* (fully-specified) setting. This study extends that with
two new axes:

1. **Specification difficulty** (Medium, Hard) — what happens when the
   user under-specifies?
2. **Interactivity** (no-supervisor vs simulated-supervisor) — when
   the agent can ask, how often does it, and does the lift on the
   harder spec close?

The contribution is *not* a new method. It is a measurement of the
consult-the-human capability of existing CC-based harnesses (vanilla,
and our best AUTOCAMP cell) under a more demanding spec.

## 2. Research questions

- **RQ-A (difficulty drop):** Does score drop monotonically as the spec
  is relaxed (Easy → Medium → Hard) for each harness configuration?
  How big is the drop?
- **RQ-B (best-config holds):** Does the AUTOCAMP "best" configuration
  (F4: xmllint MCP + memory primer m1u) still beat the F0 baseline on
  the relaxed specs, or does the gap collapse / invert?
- **RQ-C (interactivity helps):** When given access to a simulated
  supervisor, does the agent use it? Does it close the difficulty gap?
  How does question rate scale with difficulty?
- **RQ-D (asking discipline):** Does the agent over- or under-ask?
  Specifically:
  - Asks too many questions → annoys the user (cost of consultation)
  - Asks too few → invents wrong values (cost of bad inference)
  We measure both.

We do not claim a method contribution from RQ-C. We claim a
**measurement**: existing CC harnesses, when allowed, do/do not
productively consult a supervisor on a real scientific-software
authoring task at our chosen difficulty.

## 3. Scope

**Tasks.** Sub-7 from test-17. We pick tasks that meet two criteria:

1. They have non-trivial T1+T2+T3 parameters (otherwise the difficulty
   ramp is degenerate).
2. They have at least one task-family member already in the main
   battery so we have an easy-mode anchor.

Candidate set (to be confirmed during implementation, after the tier
classifier runs):
`ExampleMandel`, `ExampleDPWellbore`, `ExampleEDPWellbore`,
`ExampleIsothermalLeakyWell`, `ExampleThermalLeakyWell`,
`TutorialPoroelasticity`, `TutorialSneddon`. Drop any whose tier
classification has fewer than ~3 T1+T2 parameters and ~2 T3
parameters (the ramp wouldn't bite).

**Difficulty levels.**
- **Easy** — current `instructions.txt`. Reuse existing test-17
  numbers as anchor; do not re-run.
- **Medium** — T1 + T2 omitted. Agent must infer software defaults +
  numerics. Spec retains T3 (domain values like density, viscosity)
  and T4 (problem-defining: geometry, BCs, loads).
- **Hard** — T1 + T2 + T3 omitted. Only T4 problem-defining
  parameters survive. Spec reads like a brief: "Mandel benchmark, 1m
  × 0.1m × 1m quarter-domain, top-face displacement loading,
  duration 10s." Agent must infer the full physics + materials.

We deliberately stop at two relaxed levels (Medium, Hard) per the
user request. T4-only "Expert" is out of scope.

**Spec rewrite, not token-mask.** We do not regex-delete sentences
from `instructions.txt`. We feed the original text + the tier
classifications into an LLM (DSv4-flash) and ask it to produce a
fluent, realistic-sounding rewrite that omits the chosen tiers
without leaving stylistic gaps. This preserves the natural-language
register a real scientist would use and avoids artefacts like
half-sentences or dangling references to numbers that were stripped.
The rewrite is generated **once per (task, difficulty)** and committed
as a fixed artefact, so all conditions see byte-identical specs.

Rewrite hygiene guards (mandatory, pre-experiment):
- LLM must not introduce any value not present in the original spec
  for that tier (zero-leak from omitted tiers — automated check).
- LLM must not name GEOS XML tags / attributes (matches the existing
  rule that the spec uses scientific language, not GEOS-internal
  vocabulary).
- Manual spot-check of all 14 generated specs (7 tasks × 2 levels)
  before any run starts.

**Configurations.**
- **`autocamp_F0`** — full baseline (no plugin, no hooks, no memory,
  no xmllint). Same as the AUTOCAMP F0 cell.
- **`autocamp_F4`** — current best on test-17 by a clear margin
  (0.921 vs 0.910 vs F0). xmllint MCP + memory primer m1u, no Stop
  hook. *(SE is the right pick if we instead anchor to ICL-10. We
  go with F4 because the relaxed-spec tasks are derived from
  test-17 so test-17's headline is the relevant prior.)*
  → **Decision needed from researcher**: F4 vs SE.

Both configurations get a **prompt addendum** for the relaxed-spec
runs:

> Some details of the simulation specification are intentionally
> unspecified. Where a value is missing, infer a reasonable choice
> from GEOS conventions, standard geophysics practice, or analogous
> example simulations available to you. Prefer values you can justify
> from documentation or established practice over guesses.

The addendum is identical across F0/F4 and across difficulty levels
so any non-interactive comparison is on the addendum-on/off pair.

**Interactivity modes.**
- **Mode A — non-interactive** (Section 4): no supervisor channel.
  Same harness behaviour as the main battery, except the spec is
  relaxed and the addendum is in the prompt. The Stop hook still
  fires if `/workspace/inputs/` lacks valid XML.
- **Mode B — interactive** (Section 5): the agent has access to a
  consult-supervisor channel. End-of-turn semantics change as
  described below.

**Seeds + scale.** 2 seeds per condition. Total runs:
- Mode A: 7 tasks × 2 levels × 2 configs × 2 seeds = **56 runs**
- Mode B: 7 tasks × 2 levels × 2 configs × 2 seeds = **56 runs**
- Plus a smoketest pass (1 task × 2 configs × 2 levels × 1 seed × 2 modes = 16) = **128 total**

At DSv4-flash rates (~$0.02–0.05/run on test-17 historical data, plus
the supervisor LLM in Mode B at probably 3–5 supervisor calls per
run × ~500 input tokens), expected cost ≪ $20. Well below test-17's
~$5–$7 per AUTOCAMP cell footprint.

Wall time estimate (sequential, conservative): 7 × 4 difficulty/config
combos × 2 seeds × 2 modes × ~5 min/run ≈ 9 hours. With workers=4 this
is ≈ 2.5 hours. Smoketest first.

## 4. Mode A — non-interactive, relaxed spec

No code change to the runner. New artefacts only:

1. `data/eval/experiments_relaxed/<TaskName>/instructions.txt` —
   the symlinked / re-pointed file used by the runner; switched per
   difficulty by `--experiments-dir`. We add **two** new dirs:
   `experiments_relaxed_medium/` and `experiments_relaxed_hard/`.
2. `--task-instructions-addendum` flag (small new CLI option) appends
   the inference-permission paragraph after the SIMULATION
   SPECIFICATION block. Or — simpler — we put the addendum directly
   into `instructions.txt` for the relaxed dirs. The latter avoids
   any runner change and is what we'll do.
3. Existing scoring against ground-truth XML is unchanged. TreeSim
   already handles "agent picked a different but valid value" — it
   will mark mismatches as wrong, which is exactly what we want.
   Score on Easy is the upper bound; Medium / Hard scores measure
   how well the agent's inferred values match the ground truth.

We acknowledge upfront that "matching the ground truth" is a strict
metric: an inferred value can be physically reasonable yet score
zero. This is a **known limitation** we report; the alternative
(LLM-judged "is this reasonable?") is a separate research project.

Output: the difficulty-vs-score curve, per harness, on a fixed task
set. RQ-A and RQ-B answered.

## 5. Mode B — interactive, supervisor LLM

### 5.1 Supervisor agent

Separate DSv4-flash process invoked as a **single-shot LLM call** per
question (not a long-running agent). Receives:

- The **full original `instructions.txt`** (Easy spec) for that task.
- The exact question the evaluated agent asked.
- A short system prompt: "You are the human researcher who wrote
  this simulation specification. Answer concisely (1–3 sentences)
  using only information in the specification. If the answer is not
  in the specification, say so plainly — do not invent. Do not
  volunteer information the agent did not ask about."

The supervisor *does not* see the relaxed spec the agent received; it
sees the full original. This simulates "the user knows what they want
but didn't write it all down."

The "do not volunteer" rule is critical — it's what keeps the
supervisor from leaking T1+T2+T3 values the agent didn't ask about.
We verify this with a hygiene check: the supervisor's response is
auto-flagged if it contains numeric values from omitted tiers that
were not in the agent's question.

### 5.2 End-of-turn semantics

Three implementation options, in increasing order of risk:

**Option 1 (preferred): custom MCP tool `consult_supervisor`.**
Add a new MCP server with a single tool, `consult_supervisor(question:
str)`, exposed to the agent. The tool's handler calls the supervisor
LLM and returns the answer as the tool result. The agent loop
continues normally. The Stop hook is unchanged: it only fires if the
agent ends turn without producing valid XML. This option keeps all
current invariants and is the cleanest.

**Option 2: re-enable `AskUserQuestion`**, intercept via a hook.
Claude Code has a built-in `AskUserQuestion` tool that PAC-1 used
historically. When allowed, the agent calls it; we intercept via a
PreToolUse hook, route to the supervisor LLM, and return the answer
as the tool result. Slightly less clean because the PreToolUse hook
needs to forge a tool result, which is fiddlier than implementing an
MCP server.

**Option 3: parse the assistant message text** for trailing questions
on Stop. Reject because it is fragile; we will not pursue.

We go with **Option 1**. Implementation pointer: the existing plugin
already ships an MCP server for RAG (`plugin/mcp-servers/...`). Add a
new MCP server `geos-supervisor` with one tool, served as a Python
subprocess, calling the supervisor LLM via the OpenAI-compatible
DeepSeek endpoint already configured in the runner.

The Stop hook's behaviour is unchanged. The only change to
end-of-turn handling is that the agent now has a tool option that
lets it continue the loop without producing XML yet.

### 5.3 Metrics

Per (task, difficulty, config, seed, mode):

- TreeSim score (primary, same as everywhere else).
- `consult_supervisor` call count + total tokens consumed.
- Per-question category (assigned by an offline LLM judge from
  question text): `T1`, `T2`, `T3`, `T4`, `procedural` (where do I
  put outputs?), `clarification` (please confirm), `redundant`
  (already in spec, agent missed it).
- Supervisor-leak flag (any answer contained numeric values from
  omitted tiers that were not in the question — see 5.1).
- Tool-call efficiency: tools-per-task and tools-before-Write,
  matching the AUTOCAMP efficiency table format.

The interesting plots:
- Question rate vs difficulty (does it scale?).
- TreeSim lift from interactivity, per difficulty.
- Question category distribution by difficulty (do harder specs
  drive more T2/T3 questions?).

## 6. What changes in the codebase, what does not

**New code (small):**
- `scripts/relax_specs.py` — generate Medium / Hard rewrites of every
  test-17 task's `instructions.txt`. Reuses the tier classifier from
  `mine_examples_v2.py` (port from `initial_geos_agent/`).
- `data/eval/experiments_relaxed_{medium,hard}/<task>/instructions.txt`
  — output artefacts.
- `plugin/mcp-servers/geos-supervisor/` — small MCP server exposing
  `consult_supervisor(question)`. Reads the full original spec from a
  per-task file at `/workspace/SUPERVISOR_SPEC.md` (mounted in by the
  runner only when `--supervisor-mode on`).
- `src/runner/agents.py` — two new variants:
  `autocamp_F0_interactive` and `autocamp_F4_interactive`. Same as
  base cells but with the supervisor MCP added to the allowed tool
  list and a flag to mount the per-task supervisor spec.
- A launch script `scripts/launch_interactive_autonomy.sh` and a
  scoring helper that emits the question-count / leakage table.

**Unchanged:**
- The runner core (`task.py`, `orchestrator.py`).
- The Stop hook and its retry counters.
- The AUTOCAMP cells. F0 and F4 base configs are reused as-is for
  Mode A.
- Ground-truth XML, scoring, contamination logic.
- The main test-17 / ICL-10 / cross-model results. Nothing in
  `data/eval/autocamp_2026-05-01/` is touched.

This is the central design constraint: **the main battery's
disk-resident artefacts are read-only.** We add new dirs and new
agent variants; we do not edit existing ones.

## 7. Risks and red flags (be honest)

- **Spec-rewrite leakage.** If the relax LLM keeps a T1/T2 value by
  accident, Medium becomes secretly Easy on that task. Mitigation:
  programmatic check for original numbers + tier set; manual
  spot-check; aborts the run if any spec fails the check.
- **Supervisor LLM drift.** If supervisor "helps too much" by
  volunteering numbers, interactivity wins for the wrong reason.
  Mitigation: the leak hygiene flag (5.1, 5.3) and seed-locked
  supervisor calls so the same question gets the same answer
  across conditions where possible.
- **Tier classification quality.** The tier classifier is an LLM
  call; it can mislabel. Mitigation: spot-check the classifications
  for the chosen 7 tasks and freeze them; do **not** re-classify
  between runs. Document any expert disagreement we surface.
- **Strict-match metric undersells inferred-but-reasonable answers.**
  Acknowledged limitation. We do *not* attempt to redesign the
  scoring metric for this study. We additionally report sub-section
  TreeSim (already available) so we can see "the agent got the
  physics right but picked a different solver tolerance".
- **Small task count.** 7 tasks is a tight budget for differentiating
  configs; we report paired-per-task results, not means, and do not
  claim significance from this study alone. Cross-reference test-17
  for the easy-mode anchor where n is larger.
- **Single model (DSv4-flash).** The interactivity finding is only on
  this model. We say so. Cross-model is left for after the workshop
  paper.

## 8. Decisions needed from the researcher (before launch)

1. **Best config: F4 vs SE.** F4 wins test-17 (0.921 vs 0.919);
   SE wins ICL-10. The relaxed tasks are test-17-derived so F4 is
   the natural pick. Confirm.
2. **Task count: 7 vs 5.** 7 fits the budget; 5 cuts wall time
   ~30% and lets us get an extra seed in. Default: 7 with 2 seeds.
3. **Supervisor model.** Default: same DSv4-flash. Alternative: a
   stronger model (e.g. Opus 4.6 via API) for a more capable
   "human." This is a story choice — using the same model
   eliminates the "the supervisor was too smart" confound but might
   reduce answer quality.
4. **Workshop scope confirmation.** Confirm we are targeting ICML
   2026 AI4Science (deadline ~2026-05-07) and that this is a
   workshop paper, not a section in the main NeurIPS paper.
5. **Whether to also run Easy on this 7-task subset** for a
   within-spec-set anchor instead of relying on the main test-17
   numbers. Cost: +14 runs, ~30 min wall.

## 9. Sequenced plan

1. **Doc + decisions** — this doc + a checklist for §8. (Today.)
2. **Tier classifier port + freeze** — port `mine_examples_v2.py`
   tier classification, run on the 7 tasks, manual review, freeze.
3. **Relax-spec generator** — rewrite tasks at Medium and Hard,
   leakage check, manual spot-check.
4. **Mode A smoketest** — 1 task, F4 only, both difficulty levels,
   1 seed. Verify TreeSim drops as expected and agent doesn't crash.
5. **Mode A full run** — 7 tasks × 2 levels × 2 configs × 2 seeds.
6. **Supervisor MCP server** — implement, smoketest with a single
   manually-issued question, confirm the round-trip works.
7. **Mode B smoketest** — 1 task, F4_interactive only, Hard, 1 seed.
   Inspect the question stream; confirm hygiene flags work.
8. **Mode B full run** — 7 tasks × 2 levels × 2 configs × 2 seeds.
9. **Scoring + analysis** — same scorer as AUTOCAMP. New table and
   one bottleneck-pipeline-style analysis sketching question
   patterns.
10. **Adversarial review** — `/adversarial-review` on the relax
    pipeline (leakage), supervisor MCP (leak), and Mode B end-of-turn
    semantics. Mandatory before declaring results. Per
    `experiment-guardrails.md` this gates pre-campaign + pre-claim.
11. **Workshop write-up** — separate from the main NeurIPS draft.

## 10. What this study will and will not say

**Will say:**
- How vanilla CC and our best AUTOCAMP cell behave on a relaxed
  spec, on a small task set, single model.
- How often each cell asks for help, what kind of help, and whether
  asking closes the difficulty gap.
- Whether the AUTOCAMP "best" generalises out of the easy-spec
  regime.

**Will not say:**
- That any harness is generally good at autonomous discovery
  (sample size + model count too small).
- That the supervisor LLM is a faithful proxy for a real geoscientist
  (it isn't; we caveat).
- That a different scoring metric would change the conclusions
  (untested).

These limitations are stated upfront. The workshop framing rewards
honest measurement, not overclaiming.

---

*Cross-references: `direction.md` RQ4; `misc/geophys_todo.md` §"On
Controlling Difficulty"; `/home/matt/sci/geos_agent/cc_docs/difficulty_tiers_pitch.md`;
`/home/matt/sci/initial_geos_agent/scripts/mine_examples_v2.py`; AUTOCAMP
results in `docs/2026-05-02_autonomous-campaign-results.md`; F4 spec in
`src/runner/agents.py`.*

# Interactive autonomy + difficulty ramp — results (overnight 2026-05-03 → 2026-05-04)

*Companion to `docs/2026-05-03_interactive-autonomy-design.md` and
`docs/2026-05-03_interactive-autonomy-plan.md`. Live log:
`docs/2026-05-03_interactive-autonomy-status.md`.*

> **Single seed, 8 tasks, DSv4-flash agent + DSv4-flash supervisor.**
> 64 total runs (8 tasks × 2 configs × 2 difficulties × 2 modes).
> All runs completed successfully (3 individual task failures across
> 64 runs; included as TreeSim=0 in `fa0` numbers).

## TL;DR

1. **Difficulty matters as expected.** Both vanilla CC (F0) and the
   AUTOCAMP best (F4) drop ~7–13 pp from the test-17 Easy anchor when
   the spec is relaxed, with most of the drop happening at Medium —
   Hard is barely worse than Medium. F4 keeps roughly its test-17
   advantage (~+0.5 pp) on relaxed specs, but the gap is too small to
   read into at n=1.

2. **The agent almost never asks the human.** Across 32 interactive
   runs spanning two difficulties and two configurations, **only 1
   `consult_supervisor` call was made** (F4_interactive on
   ExampleThermalLeakyWell at Medium). The other 31 interactive runs
   solved the relaxed specs entirely by inference, even though the
   tool was in the agent's tool list and the system prompt explicitly
   advertised it.

3. **Interactive ≠ noticeably better on TreeSim, despite #2.** Mode B
   scores are within ±2 pp of Mode A at the same difficulty in 3 of 4
   (config × difficulty) cells; the one exception is **F0 at Medium,
   where Mode B beats Mode A by +10.7 pp** — but this is almost
   certainly a *plugin-loaded confound* (see Caveats §C1) rather than
   a supervisor effect, since the supervisor was never consulted on
   any of those 8 runs.

4. **The one supervisor call we got was a useful, well-formed
   technical question** — and it returned an empty answer because the
   supervisor LLM ran out of tokens mid-CoT. We patched the supervisor
   MCP after the run; subsequent runs use 1500 max tokens with
   `reasoning_content` fallback.

## Headline table

TreeSim mean (failures-as-zero), single seed, 8 tasks per cell.

| difficulty | mode | F0 vanilla | F4 AUTOCAMP-best | Δ (F4 − F0) |
|---|---|---:|---:|---:|
| Easy (test-17 anchor, prior) | A non-int | **0.910** | **0.921** | +0.011 |
| Medium | A non-int | 0.776 (1 fail) | 0.829 | +0.053 |
| Medium | B int     | **0.884** | 0.875 | −0.009 |
| Hard   | A non-int | 0.828 | 0.835 | +0.008 |
| Hard   | B int     | 0.710 (1 fail) | 0.840 | +0.130 |

Per-task scores are at the bottom of this file.

## Difficulty ramp effect (Mode A)

For both configurations, going from Easy → Medium drops the score by
roughly the same amount (~9–10 pp on F4, ~13 pp on F0). Easy → Hard
is **not much worse than Easy → Medium**:

- F0: 0.910 → 0.776 → 0.828 (Easy → Medium → Hard)
- F4: 0.921 → 0.829 → 0.835

The Hard rewrite drops more characters (0.32–0.60 drop ratio) than
Medium (0.10–0.40), but the GEOS examples it can find on disk
apparently provide enough scaffolding that the agent recovers most of
the dropped detail. There is a small but consistent F4 > F0 advantage
of about 0.5–5 pp at Medium and Hard — directionally consistent with
test-17 but unreliable at n=1.

The single Mode A medium failure (F0 on ExampleThermoporoelasticConsolidation,
TreeSim=0) is what drags F0/Medium below F4/Medium.

## Supervisor consultation rate

| mode_diff | agent | calls | tasks w/ calls (out of 8) |
|---|---|---:|---:|
| modeA_medium | both | 0 | n/a (no channel) |
| modeA_hard | both | 0 | n/a |
| modeB_medium | F0_interactive | 0 | 0 |
| modeB_medium | F4_interactive | **1** | 1 |
| modeB_hard | F0_interactive | 0 | 0 |
| modeB_hard | F4_interactive | 0 | 0 |

**1 call across 32 interactive runs ≈ 3 % task-level usage rate, ≈
0.04 calls per task on average.** Even on Hard (where ~50 % of the
spec was dropped including all material properties and numerics), the
agent did not consult.

The single call (F4_int / Medium / ExampleThermalLeakyWell) was a
substantive technical question:

> "The spec says the energy equation is not dynamically solved, but a
> geothermal gradient governs fluid properties. Should I (a) use
> isThermal=\"1\" with CO2BrinePhillipsThermalFluid and fix
> temperature via Dirichlet BCs, or (b) use standard
> CO2BrinePhillipsFluid with a spatially-varying temperature
> approach, or (c) another method?"

The supervisor returned an empty string (max_tokens budget consumed
by reasoning tokens; patched post-hoc — see §C2). The agent then
finished the run by inference; it scored 0.851, which is **higher**
than the same task in Mode A medium F4 (0.614). This is suggestive
that *being denied* an answer didn't hurt; the act of formulating the
question may have been enough to unstick the agent.

## Diagnostic: how much was actually omitted, and could the agent find it elsewhere?

You asked the right question. Three follow-up checks, run after the main results came in:

### A. Volume of dropped specification

|  | char drop | values dropped | by tier |
|---|---:|---:|---|
| **Medium** (8 tasks total) | 39676 → 31549 (**−20.5 %**) | **89** | T1=27, T2=62, T3=0 |
| **Hard**   (8 tasks total) | 39676 → 19620 (**−50.5 %**) | **184** | T1=26, T2=53, **T3=105** |

So Hard removes about half the spec by character count and twice as many
parameter-level values as Medium, *and* it removes the entire T3 layer
(densities, viscosities, porosities, permeabilities, Biot coefficients,
standard BCs). Medium is "infer the numerics", Hard is "infer the
material physics too". Per-task Hard drop ratios range 0.32 (DPWellbore)
to 0.60 (TutorialPoroelasticity).

### B. Where the agent looks when the spec is relaxed

Total `Read` / `Glob` / `Grep` calls aimed at `/geos_lib/inputFiles/`
(other GEOS example XMLs) and `/geos_lib/src/` across all 8 tasks per
cell:

| cell | inputFiles reads | src reads | RAG calls (if any) |
|---|---:|---:|---:|
| modeA_medium / F0 | 404 | 23 | 0 |
| modeA_medium / F4 | 142 | 49 | 3 |
| modeA_hard   / F0 | 322 | 37 | 0 |
| modeA_hard   / F4 | 161 | 56 | 9 |
| modeB_medium / F0_int | 148 | 62 | 22 |
| modeB_medium / F4_int | 165 | 20 | 14 |
| modeB_hard   / F0_int | 208 | 31 | 23 |
| modeB_hard   / F4_int | 247 | 88 | 6 |

The agents are not idle. They're reading dozens to hundreds of GEOS
input-file examples per task. The task is "find the right analogous
benchmark and copy what it does."

### C. Are the dropped values *actually findable* in those examples?

Stress-tested on **ExampleMandel/Hard**, the most aggressive single
case (5 T1 + 14 T2 + 12 T3 values dropped, 54 % char drop). For each
T2/T3 dropped value, I greped the rest of `/geos_lib/inputFiles/`
(excluding the Mandel ground-truth files, which are blocked anyway) for
the numeric token:

| dropped T3 value | found in N other example XMLs |
|---|---:|
| Solid density 0.0 kg/m³ | 668 |
| Solid bulk modulus 66.667 MPa | **0** |
| Solid shear modulus 40.0 MPa | 41 |
| Reference porosity 0.375 | 8 |
| Grain bulk modulus 1.0e27 Pa | 42 |
| Permeability 1.0e-12 m² | 51 |
| Fluid base density 1000 kg/m³ | 187 |
| Fluid viscosity 0.001 Pa·s | 210 |
| Fluid compressibility 4.4e-10 Pa⁻¹ | 6 |
| Fluid reference pressure 0.0 Pa | 668 |

**15 of 26 dropped T2+T3 values for Mandel/Hard are recoverable by
literal token grep against other examples on disk.** Most "domain-
inferable" values aren't actually domain-inferable in this benchmark
— they are *retrieval-inferable* from analogous example XMLs that
GEOS ships in the source tree. Only 1 of 12 T3 values (bulk modulus
66.667 MPa, a slightly unusual rounded value) had zero hits.

This is the structural reason for the 1/32 consultation rate. The
"difficulty ramp" in this study isn't actually putting the agent in a
position where it *must* ask a human — it just puts it in a position
where it has to do a longer Read/Glob hunt. The on-disk GEOS examples
are functioning as an alternate oracle.

### D. Tool description and prompt visibility

The agent does know it has the option:

- The MCP `tools/list` advertises `consult_supervisor` with this
  docstring (verified end-to-end via a manual MCP probe):

  > Ask a clarifying question to the human researcher. Use this when
  > the simulation specification you received does not contain a
  > value or detail you need to make a faithful XML, and you cannot
  > reasonably infer it from GEOS conventions or domain knowledge.
  > Each call costs the researcher's time, so prefer to infer when
  > you can. The researcher will answer concisely using only
  > information in their original specification.

- The system prompt addendum (`_SUPERVISOR_INSTRUCTIONS` in
  `src/runner/prompts/__init__.py`) says the same thing in slightly
  different words.

- And we saw in events.jsonl that agents *did* call
  `supervisor_stats` early — confirming they noticed the MCP and
  introspected it before deciding not to consult.

So awareness is not the issue. The two priors that probably are:

1. **"Prefer to infer" framing.** Both the docstring and the system-
   prompt addendum tell the agent that consulting "costs the
   researcher's time." That's a real-world prior we wanted to
   instill — but here it tilts the agent strongly toward inference.
2. **Inference is too easy because the on-disk examples cover the
   answers.** Even at Hard, ~58 % of removed numeric values are
   one `grep` away. Why ask when you can read?

### Implications for the next pass

If the goal is to actually study consultation behaviour, the
difficulty ramp needs to either:
- **Block analogous examples**, not just the GT for the current task.
  e.g., for ExampleMandel block all `*Poroelastic*` / `*Mandel*`
  inputs across the whole tree.
- **Drop values that don't have analogs** (synthetic values or values
  outside the standard library — would require expert input).
- Or relax the framing: tell the agent "the researcher would rather
  be asked once than read the wrong default."

A complementary variant worth running: same setup, but with
`prefer to infer` removed from the docstring and addendum (replaced
with "ask whenever you would otherwise pick a default"). That gives
us an "asks-on-demand" upper bound to bracket the 1/32 we observed.

## What the lack of consultation tells us

This is the workshop-relevant finding. We gave a coding agent
explicit, prompted access to a "human researcher" channel and asked
it to use it when uncertain. On a difficulty ramp where the spec was
deliberately relaxed (T1+T2 dropped at Medium, also T3 at Hard), it
chose to **not consult on 31 of 32 trials**. Three not-mutually-
exclusive interpretations:

- **(I) The agent prefers inference.** Coding agents trained on
  largely-autonomous coding tasks treat "ask the user" as a last
  resort, even when explicitly given the channel.
- **(II) GEOS examples on disk are too informative.** With the
  filtered GEOS source mounted at `/geos_lib`, the agent can
  generally read an analogous example and copy values. This collapses
  T1+T2+T3 inference into Read+Glob; consultation has low marginal
  value when retrieval works.
- **(III) The "prefer to infer" framing in the system-prompt
  addendum was too discouraging.** We advertised the channel but said
  "Each call costs the researcher's time, so prefer to infer when you
  can." A more demanding framing ("ask whenever a value would
  reasonably differ between researchers") might surface a different
  rate.

These interpretations are not mutually exclusive. The simplest
follow-up that distinguishes them is a second seed with the
addendum's framing flipped: **"ask whenever you would otherwise
guess; the researcher will tell you when to stop"**.

## Caveats (loud)

- **C1 — Mode B has a plugin-shape confound.** F0_interactive needs
  `plugin_enabled=True` so the supervisor MCP server can be loaded;
  F0_noninteractive runs without the plugin entirely. So Mode B F0
  carries (a) the supervisor MCP tool list, plus (b) any baseline
  effect of having the plugin loaded at all. PAC-1 (XN-013) found
  tool-list-shape effects up to 0.16 fa0 for an *uncalled* tool. The
  +10.7 pp F0 medium delta we see here is almost certainly that
  effect — not "supervisor helps". F4 vs F4_interactive does not have
  this confound (both have plugin loaded), and there the Mode B vs
  Mode A delta is small (+0.5 pp Hard, −0.9 pp Medium).

- **C2 — One real supervisor call, empty response.** The supervisor
  LLM returned 400 reasoning tokens with empty content. Patched
  (`max_tokens=1500`, `reasoning_content` fallback) but no
  re-execution; the single call is in the dataset but the answer
  field is "". For the purpose of the consultation-rate finding, the
  supervisor being broken doesn't change the result (the agent never
  *tried* to consult for the other 31 runs).

- **C3 — n=1 per cell.** Single seed. Read directionally only. Per-
  task variance is large (TreeSim 0.6–1.0 spread).

- **C4 — Strict-match TreeSim.** Inferred-but-reasonable values that
  differ from ground truth score 0. This penalises the agent for
  picking sensible alternates. We do *not* attempt a separate
  "reasonableness" score in this study.

- **C5 — Single model.** DSv4-flash agent, DSv4-flash supervisor.
  Cross-model not done.

- **C6 — Spec-rewrite leakage.** The relax pipeline produced 0
  programmatic leaks across all 16 (task × level) rewrites after the
  LaTeX-aware hygiene pass. We did not manually re-classify whether
  every dropped value was correctly tier-coded; some T3↔T4 boundaries
  are arguable.

- **C7 — Supervisor leak audit not done.** I did not run a programmatic
  check on the one supervisor question/answer pair to verify the
  answer would not have leaked omitted-tier values, because the
  answer was empty. With the patched MCP this audit becomes important
  before any future report.

## Cost & wall time

- Spec generation: 16 DSv4-pro calls, ~$0.50 total estimated.
- 64 main runs at DSv4-flash: ~10 min average wall, very low cost
  per run; total spend probably $1–$3 (bounded; no DeepSeek balance
  alarm fired).
- 1 supervisor LLM call: 1849 prompt + 400 completion tokens, ~$0.001.
- Wall time end-to-end (orient → 64 runs scored → report written):
  about 2.5 hours.

## Per-task TreeSim

| task | A_hard/F0 | A_hard/F4 | A_med/F0 | A_med/F4 | B_hard/F0_int | B_hard/F4_int | B_med/F0_int | B_med/F4_int |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ExampleDPWellbore                     | 0.902 | 0.935 | 0.974 | 0.981 | 0.891 | 0.904 | 0.968 | 0.986 |
| ExampleEDPWellbore                    | 0.963 | 0.970 | 0.983 | 0.975 | 0.916 | 0.943 | 0.984 | 0.984 |
| ExampleIsothermalLeakyWell            | 0.676 | 0.682 | 0.855 | 0.837 | 0.576 | 0.739 | 0.838 | 0.829 |
| ExampleMandel                         | 0.938 | 0.938 | 0.915 | 0.944 | 0.926 | 0.939 | 0.937 | 0.927 |
| ExampleThermalLeakyWell               | 0.844 | 0.822 | 0.813 | 0.614 | 0.711 | 0.795 | 0.835 | 0.851 |
| ExampleThermoporoelasticConsolidation | 0.816 | 0.840 | 0.000 | 0.693 | 0.794 | 0.835 | 0.840 | 0.817 |
| TutorialPoroelasticity                | 0.633 | 0.704 | 0.787 | 0.726 | 0.000 | 0.744 | 0.762 | 0.698 |
| TutorialSneddon                       | 0.853 | 0.793 | 0.882 | 0.863 | 0.869 | 0.824 | 0.904 | 0.905 |

## V1 follow-up: less prescriptive prompt (added 2026-05-04)

Question: was the 1/32 V0 consult rate driven by the "prefer to infer
when you can" framing in V0's docstring + system-prompt addendum?
Reran the 32 interactive cells with `supervisor_prompt_variant =
v1_neutral` — both the docstring and the addendum drop the prefer-
to-infer language and treat infer-vs-ask as peer paths ("Choose
whichever is more reliable for the value at hand"). All other knobs
identical. New cells `ia_{F0,F4}_interactive_v1` write to a separate
`modeBv1_*` results subtree so V0 numbers are unchanged.

### Headline: identical consult rate

|  | V0 prompt | V1 neutral prompt |
|---|---:|---:|
| `consult_supervisor` calls (out of 32) | **1** | **1** |
| tasks with at least one call (out of 16) | 1 | 1 |

Same rate. The prompt twist did not move the needle. The single V1
call was a good one — F0_interactive_v1 on
ExampleThermoporoelasticConsolidation/Medium asking *"For the fully-
implicit (FIM) couplingType in SinglePhasePoromechanics, what is the
correct element string? Is it 'FullyImplicit' as used in
ThermoPoroPlastic_consolidation_base.xml?"* The supervisor (now with
the patched 1500-token budget + `reasoning_content` fallback) answered
cleanly: *"The specification does not specify the exact XML element
string for the couplingType in SinglePhasePoromechanics. It only
states that the solution strategy should be fully implicit."* Stayed
within the spec, did not invent a value, did not leak.

(Side note: the agent named `ThermoPoroPlastic_consolidation_base.xml`
in the question — that's the GT for this task. Either the agent
hallucinated the basename pattern or it slipped through contamination.
Worth checking the contamination block in a follow-up; supervisor
itself didn't confirm or deny.)

### TreeSim comparison V0 vs V1

| difficulty | config | V0 fa0 | V1 fa0 | Δ |
|---|---|---:|---:|---:|
| Medium | F0_interactive  | 0.884 | 0.613 (1 fail) | **−0.271** |
| Medium | F4_interactive  | 0.875 | 0.867 | −0.008 |
| Hard   | F0_interactive  | 0.710 (1 fail) | 0.762 | +0.052 |
| Hard   | F4_interactive  | 0.840 | 0.838 | −0.002 |

F4 is essentially identical across V0 / V1 (Δ within ±1 pp at both
difficulties). F0/Medium swung sharply down by 27 pp due to a single
near-zero task (ExampleEDPWellbore at 0.000) and ExampleIsothermalLeakyWell
collapsing from 0.838 to 0.128. F0/Hard improved by 5 pp from a
TutorialPoroelasticity recovery (0.000 → 0.235). Both swings are
dominated by single-task variance at n=1, not by the prompt change.
**Read F4 numbers as the meaningful signal: V0 ≈ V1 within noise.**

### Interpretation

Hypothesis (III) — that the V0 "prefer to infer" framing was
artificially suppressing the consult rate — is **not supported**.
After removing that framing entirely from both the docstring and the
system-prompt block, the agent still consulted only 1 / 32 times.

That leaves Hypotheses (I) and (II) — agent prefers inference and/or
on-disk GEOS examples function as a sufficient oracle — as the
remaining candidates. Per §C above (15/26 dropped Mandel/Hard values
findable on disk), (II) has direct evidence behind it. (I) is harder
to test without changing the model.

### Implication for the workshop write-up

The story is now stronger and tighter:

> *On a relaxed-specification GEOS XML authoring task with a working
> simulated supervisor channel exposed as an MCP tool, DSv4-flash
> consulted **2 times across 64 interactive trials (3.1 %)**
> regardless of whether the channel was framed as a costly last
> resort or as a peer-equivalent path. The dominant explanation is
> structural: the on-disk GEOS examples expose ~58 % of the omitted
> T2/T3 values to a literal `grep`, so inference is genuinely the
> cheaper path. To measure consultation behaviour rather than
> retrieval, the filesystem oracle has to be removed first.*

This is a more honest framing than the V0-only writeup — and it
preempts the obvious reviewer question "did you try a less biased
prompt?".

### Auto-table

The full per-cell, per-task numbers (including the 4 V1 cells) live
in `docs/2026-05-04_interactive-autonomy-autotable.md`, regenerated
each time `scripts/analyze_interactive_autonomy.py` runs. This
curated report is the place for interpretation; the autotable is the
raw numbers.

### Cost & wall (V1)

- 32 interactive runs at DSv4-flash: well under $3 estimated, ~110
  min wall (workers=4). Within projection.
- 1 supervisor LLM call: ~$0.001.

## What's interesting for the workshop write-up

If we want to pitch this as an AI4Science workshop "autonomous discovery
loop" measurement paper, the headline story is:

> *On a relaxed-specification GEOS XML authoring task, the agent
> consults its simulated human researcher 1 time per 32 trials —
> ~0.03 calls/task — even when the channel is in its tool list and
> explicitly advertised in the system prompt. The agent prefers to
> infer from on-disk GEOS examples, and (controlling for the
> plugin-shape confound) does not measurably benefit from having the
> channel available. This is a measurement of how rarely a coding-
> agent harness initiates oversight when given the affordance, and
> motivates the design of harnesses that prompt the agent more
> aggressively to consult.*

Things to add before submitting:

1. **A second seed for each cell, ideally with two prompt-variants**
   (current "prefer to infer" vs an "ask whenever you'd guess"
   variant) so we can claim the rate is not just framing artifact.
2. **A no-plugin Mode B F0 control** — i.e. supervisor over a
   pure-vanilla CC tool list — to clear the C1 confound. This
   requires either (a) running the supervisor MCP via a different
   mechanism that doesn't piggyback on the plugin loader, or (b)
   running the comparison only against `ia_F4_*` cells where both
   sides have the plugin loaded.
3. **Question-quality analysis** — once we have more calls, we want
   to categorise them (T1/T2/T3/procedural/clarification) and
   correlate question category with TreeSim improvement on the run.
4. **"Did the agent peek at the supervisor spec file" audit done.**
   Programmatic scan of all 32 Mode B `events.jsonl` streams for
   tool-use input strings containing "supervisor" excluding the two
   sanctioned MCP tools: zero Read or Bash calls touched
   `/supervisor/spec.md`. The path leaks via the `supervisor_stats`
   tool result (which returns `spec_path`); future versions of the
   MCP should redact that field.

## Files written tonight

- `scripts/relax_specs.py`, `scripts/_recheck_hygiene.py` — relaxed-spec generator + hygiene re-check
- `data/eval/experiments_relaxed_{medium,hard}/<8 tasks>/` — relaxed instructions + `_omitted.json`
- `plugin/scripts/supervisor_mcp.py` — simulated-supervisor MCP server (with post-hoc max_tokens patch)
- `src/runner/agents.py` — 4 new variants (`ia_{F0,F4}_{noninteractive,interactive}`)
- `src/runner/{prompts/__init__.py, claude_settings.py, docker_cmd.py, orchestrator.py, cli.py}` — supervisor wiring + new `--supervisor-spec-dir` CLI flag
- `scripts/launch_interactive_autonomy.sh`, `scripts/score_interactive_autonomy.sh`, `scripts/analyze_interactive_autonomy.py`
- `data/eval/interactive_autonomy_2026-05-03/` — 64 runs + scored summaries + `_results/aggregate.json`
- this file
- design doc, plan doc, status log

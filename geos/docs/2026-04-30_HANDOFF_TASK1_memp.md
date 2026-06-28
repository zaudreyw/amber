# Handoff for Task 1: MemP memory implementation

*This is a small handoff doc to bootstrap a fresh session after /compact.
Read this + the overnight instructions and you have everything you need
to start Task 1.*

## Overnight instructions path (always reload)

`/home/matt/sci/repo3/misc/apr30_overnight_instructions.md`

This file lists all 3 tasks (Task 1 = MemP, Task 2 = multi-agent
orchestrator, Task 3 = self-evolving agent).

## Where we just stopped (Task 0 = DSv4 ablation campaign)

Ablation campaign C0-C11 done, 12 cells × 3 seeds × 17 v2 tasks.

**Best cell**: C6 (min primer + plugin loaded + xmllint Stop hook,
no RAG, no memory) at 0.921 ± 0.006. q/$ = 10.4.

**Best q/$**: C9 (C2 minus plugin-prefix) at 11.2.

Memory cells (C5, C10, C11) all null on quality. The current
"DSv4 hero memory" is `plugin/memory_primer_dsv4_m1u.md` (820
tokens, distilled from 18-task harvest under C2 setup via
gemini-3-flash-preview). On C2 it adds 0.000pp; on C6 it adds
−0.008pp; on C7 it adds +0.006pp. **Memory is currently the
weakest component.**

Big summary: `docs/2026-04-30_dsv4-ablation-SESSION-SUMMARY.md`

## Task 1: MemP

The current memory baseline is M1-u-style monolithic cheatsheet
(Dynamic Cheatsheet, Suzgun 2025). Test a different memory paradigm:
**MemP (Fang 2025; Zhejiang)** which is procedural memory.

### Steps (per overnight instructions)

1. **Paper already downloaded** at `docs/literature/memp_2508.06433v4.html`.
   - Convert HTML → markdown (use html2text or `pandoc`).
   - Read carefully.
   - Write notes (like prior memory papers — see
     `docs/literature/memory_survey_2026-04-22.md` and
     `docs/LN-001_memory-test-time-literature.md` for tone/format).

2. **Clone repo**: `git clone https://github.com/zjunlp/MemP` somewhere
   under `/home/matt/sci/repo3/misc/memp_external/` (or similar) for
   implementation guide. Don't add it to git.

3. **Implement MemP for our pipeline**:
   - 18 train tasks for memory init (already used for M1-u distillation;
     train list in `misc/memory_split.json["train"]`).
   - Adapt the existing distiller pipeline at
     `scripts/memory/distiller.py` if useful, or write a new MemP-specific
     distiller at `scripts/memory/distiller_memp.py`.
   - Output should be a memory primer file at
     `plugin/memory_primer_dsv4_memp.md` (or similar).
   - Use trajectories from the existing harvest at
     `/data/shared/.../dsv4_ablation_2026-04-29/abl_c2_min_sr_no_rag/harvest_c2_dsv4_s1/`.
   - Grounded reports already exist at
     `misc/memory_artifacts/grounded_train_reports_dsv4.json`.

4. **Test MemP variant**: add an agent variant `abl_cMP_dsv4_memp` that
   is C2/C7/whichever-base + MemP cheatsheet. Run 3 seeds × 17 tasks,
   workers=6. Output to
   `/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/`
   (just add the new agent dir alongside existing `abl_c{0..11}_*`).

5. **Score + analyze** with existing tools:
   - `bash scripts/score_dsv4_ablation.sh <new-cond> <seed>` — but
     update the script to know the new agent name.
   - `python3 scripts/analysis/ablation_analyzer.py ...` — same shape
     as prior pairs; compare MemP-cell vs the corresponding no-mem
     baseline.

6. **Big writeup**: `docs/2026-04-30_TASK1_memp.md` covering paper
   notes, implementation, ablation results, comparison to M1-u
   memory primer, recommendation for "best memory" going forward.

7. **Small handoff** for Task 2: `docs/2026-04-30_HANDOFF_TASK2_orchestrator.md`.

8. **/compact** then start Task 2.

### Things to know

- DSv4-flash via DeepSeek direct: `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`,
  `ANTHROPIC_AUTH_TOKEN=$DEEPSEEK_API_KEY` (in `.env`).
- `--strip-baked-primer` always required.
- Test set: 17 v2 tasks (list embedded in `scripts/launch_dsv4_ablation.sh`,
  also at `misc/memory_split.json["test"]`).
- Train set for memory init: 18 tasks at `misc/memory_split.json["train"]`.
- Memory cheatsheet delivery: agent dict has `cheatsheet_path` field
  pointing at the markdown file. Already wired.
- DO NOT touch `claude_code_repo3_plugin_*` agents; those are baselines.
- Output dir: `/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/`.
  New runs add new subdirs; nothing overwrites.

### Decision: which baseline to stack MemP on?

For comparability with M1-u memory tests:
- M1-u was tested at C5 (on top of C2): null mean, σ tightening
- M1-u was tested at C10 (on top of C6): −0.008
- M1-u was tested at C11 (on top of C7): +0.006

I'd stack MemP at the **same three** baselines for direct comparison:
- C2 + MemP
- C6 + MemP
- C7 + MemP

But that's 3 cells × 3 seeds = 9 task-batches. If time-constrained,
just C7 + MemP (most-features setup, clearest comparison).

Alternatively a "hero comparison": MemP-best vs M1-u-best, single
"best" stack each.

### MemP paper key info (from quick scan)

URL: https://arxiv.org/html/2508.06433v4
Title: "𝑀𝑒𝑚^𝑝: Exploring Agent Procedural Memory" (Fang et al. 2025)
Repo: https://github.com/zjunlp/MemP

Procedural memory — vs declarative cheatsheet. The agent learns
"how to do things" rather than "facts". Should fit naturally with
our XML authoring task where "how to author" is the goal.

I haven't read it carefully yet. Step 1 is converting to markdown
and taking notes, like we did for the Dynamic Cheatsheet and
ReasoningBank papers earlier in the project.

## Stopping rules / time budget

User has ~6h until next meeting. Total budget for 3 tasks = ~6h.
- Task 1 (MemP): aim for ~1.5-2h end-to-end (including paper read).
- Task 2 (orchestrator refresh): 1.5-2h.
- Task 3 (self-evolving agent): 2h.

If Task 1 paper-reading is going long, just write minimum-viable notes
(paragraph summary + key claim + key implementation choice) and move on.

Ready to start Task 1.

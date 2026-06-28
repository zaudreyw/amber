#!/usr/bin/env bash
# Single-shot pipeline that runs after cMP campaign finishes:
# 1. Score cMP a + b across 3 seeds
# 2. Run analyzer pairs
# 3. Launch orchestrator postfix in background
# 4. Launch SE full evolution in background
# 5. Print results table
set -uo pipefail
cd /home/matt/sci/repo3

echo "=== Phase 1: Score cMP ==="
bash scripts/score_all_dsv4_ablation.sh 2>&1 | grep -E "cMP|Summary|^c"

echo ""
echo "=== Phase 2: Analyzer pairs ==="
ROOT="/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29"
RESROOT="$ROOT/_results"

# cMPa vs C5
python3 scripts/analysis/ablation_analyzer.py \
  --cond-a-name "C5_M1u_memory" --cond-a-agent "abl_c5_dsv4_mem" \
  --cond-a-runs "$ROOT"/abl_c5_dsv4_mem/c5_dsv4_s{1,2,3} \
  --cond-a-eval-root "$RESROOT" \
  --cond-b-name "cMPa_MemP_per_task" --cond-b-agent "abl_cMP_a_memp_on_c2" \
  --cond-b-runs "$ROOT"/abl_cMP_a_memp_on_c2/cMPa_dsv4_s{1,2,3} \
  --cond-b-eval-root "$RESROOT" \
  --threshold 0.10 --out docs/ablation_C5_vs_cMPa.md 2>&1 | tail -2

# cMPa vs C2 (does any memory help?)
python3 scripts/analysis/ablation_analyzer.py \
  --cond-a-name "C2_no_mem" --cond-a-agent "abl_c2_min_sr_no_rag" \
  --cond-a-runs "$ROOT"/abl_c2_min_sr_no_rag/c2_dsv4_s{1,2,3} \
  --cond-a-eval-root "$RESROOT" \
  --cond-b-name "cMPa_MemP_per_task" --cond-b-agent "abl_cMP_a_memp_on_c2" \
  --cond-b-runs "$ROOT"/abl_cMP_a_memp_on_c2/cMPa_dsv4_s{1,2,3} \
  --cond-b-eval-root "$RESROOT" \
  --threshold 0.10 --out docs/ablation_C2_vs_cMPa.md 2>&1 | tail -2

# cMPb vs C11
python3 scripts/analysis/ablation_analyzer.py \
  --cond-a-name "C11_M1u_full" --cond-a-agent "abl_c11_xmllint_full_mem" \
  --cond-a-runs "$ROOT"/abl_c11_xmllint_full_mem/c11_dsv4_s{1,2,3} \
  --cond-a-eval-root "$RESROOT" \
  --cond-b-name "cMPb_MemP_full" --cond-b-agent "abl_cMP_b_memp_on_c7" \
  --cond-b-runs "$ROOT"/abl_cMP_b_memp_on_c7/cMPb_dsv4_s{1,2,3} \
  --cond-b-eval-root "$RESROOT" \
  --threshold 0.10 --out docs/ablation_C11_vs_cMPb.md 2>&1 | tail -2

# cMPb vs C7
python3 scripts/analysis/ablation_analyzer.py \
  --cond-a-name "C7_no_mem" --cond-a-agent "abl_c7_xmllint_full_no_rag" \
  --cond-a-runs "$ROOT"/abl_c7_xmllint_full_no_rag/c7_dsv4_s{1,2,3} \
  --cond-a-eval-root "$RESROOT" \
  --cond-b-name "cMPb_MemP_full" --cond-b-agent "abl_cMP_b_memp_on_c7" \
  --cond-b-runs "$ROOT"/abl_cMP_b_memp_on_c7/cMPb_dsv4_s{1,2,3} \
  --cond-b-eval-root "$RESROOT" \
  --threshold 0.10 --out docs/ablation_C7_vs_cMPb.md 2>&1 | tail -2

echo ""
echo "=== Phase 3: 14-cell consolidated table ==="
python3 - <<'PYEOF'
import json, statistics
from pathlib import Path
ROOT = Path('/data/shared/geophysics_agent_data/data/eval/dsv4_ablation_2026-04-29/_results')
PRIOR_ROOT = Path('data/eval/results')
def gather(cond, agent, prior=False):
    means = []
    for s in (1,2,3):
        if prior:
            p = PRIOR_ROOT/f'dsv4_min_primer_s{s}/claude_code_no_plugin_minprimer'
            if p.exists():
                files = list(p.glob('*_eval.json'))
                if files:
                    means.append(statistics.mean([json.load(open(f))['treesim'] for f in files]))
        else:
            sj = ROOT/f'{cond}_dsv4_s{s}'/agent/'_summary.json'
            if sj.exists():
                means.append(json.load(open(sj))['summary']['treesim']['scored_mean'])
    return means

cells = [
    ('C1','PRIOR','min primer, no plugin', None, True),
    ('C0','c0','true vanilla', 'abl_c0_true_vanilla', False),
    ('C2','c2','min primer + plugin (no RAG), parse-SR', 'abl_c2_min_sr_no_rag', False),
    ('C3','c3','RAG, no SR', 'abl_c3_min_rag_no_sr', False),
    ('C4','c4','RAG + parse-SR', 'abl_c4_min_rag_sr', False),
    ('C5','c5','C2 + M1-u memory', 'abl_c5_dsv4_mem', False),
    ('C6','c6','xmllint hook', 'abl_c6_xmllint_hook', False),
    ('C7','c7','C6 + xmllint MCP tool', 'abl_c7_xmllint_full_no_rag', False),
    ('C8','c8','C7 + RAG', 'abl_c8_xmllint_full_rag', False),
    ('C9','c9','C2 - prefix', 'abl_c9_no_prefix', False),
    ('C10','c10','C6 + M1-u memory', 'abl_c10_xmllint_hook_mem', False),
    ('C11','c11','C7 + M1-u memory', 'abl_c11_xmllint_full_mem', False),
    ('cMPa','cMPa','C2 + MemP per-task', 'abl_cMP_a_memp_on_c2', False),
    ('cMPb','cMPb','C7 + MemP per-task', 'abl_cMP_b_memp_on_c7', False),
]
print(f'{"cell":5s}  {"mean":>7s}  {"σ":>7s}  description')
print('-'*100)
for name, code, desc, agent, prior in cells:
    means = gather(code, agent, prior=prior)
    if means:
        m = statistics.mean(means); sd = statistics.stdev(means) if len(means)>1 else 0
        print(f'{name:5s}  {m:>7.4f}  {sd:>7.4f}  {desc}')
PYEOF

echo ""
echo "=== Phase 4: Launch orchestrator postfix (background) ==="
nohup bash scripts/orchestrator/launch_3seed_postfix.sh > /tmp/orch_master.log 2>&1 &
echo "  orchestrator launcher pid: $!"
sleep 3

echo ""
echo "=== Phase 5: Launch SE full evolution (background) ==="
nohup bash scripts/self_evolving/run_full_evolution.sh > /tmp/se_master.log 2>&1 &
echo "  SE launcher pid: $!"

echo ""
echo "=== ALL DONE post-cMP at $(date -u +%FT%TZ) ==="
echo "Now waiting for orchestrator + SE to finish (~2-3h)."

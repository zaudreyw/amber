#!/bin/bash
# OH + RAG (plugin) + memory-primer M1u + self-refine on DSv4-flash + minimal primer, 2 seeds.
set -euo pipefail
cd /home/matt/sci/repo3
set -a; source .env; set +a
for SEED in 1 2; do
  echo "=== oh_dsv4_adapt_s${SEED} ==="
  python3 scripts/openhands_eval.py \
    --run-name "oh_dsv4_adapt_s${SEED}" \
    --model deepseek/deepseek-v4-flash --base-url "" \
    --api-key-env DEEPSEEK_API_KEY \
    --primer-path plugin/GEOS_PRIMER_minimal.md \
    --plugin --memory-primer plugin/memory_primer_m1u.md \
    --self-refine 2 \
    --tmp-geos-parent /data/shared/geophysics_agent_data/data/eval/tmp_geos_matt \
    --workers 4 --timeout 1800 \
    --llm-env 'LLM_LITELLM_EXTRA_BODY={"thinking":{"type":"disabled"}}' \
    >> "logs/oh_campaigns/adapt_s${SEED}.log" 2>&1
done
echo "=== adapt DONE ==="

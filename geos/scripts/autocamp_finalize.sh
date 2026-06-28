#!/usr/bin/env bash
# Finalization: score everything, run the analyzer, append metrics
# section to results doc.
set -euo pipefail
cd /home/matt/sci/repo3

echo "=== finalize at $(date -u +%H:%M:%SZ) ==="

# 1. Score all (idempotent: skips already-scored runs)
bash scripts/score_autocamp.sh

# 2. Run analyzer — writes to docs/2026-05-02_autocamp_metrics.md
python3 scripts/analyze_autocamp.py

# 3. Append metrics into the main results doc (replace placeholder)
RES_DOC="/home/matt/sci/repo3/docs/2026-05-02_autonomous-campaign-results.md"
METRICS_DOC="/home/matt/sci/repo3/docs/2026-05-02_autocamp_metrics.md"

# Find the marker line and replace everything below it
python3 - "$RES_DOC" "$METRICS_DOC" <<'PY'
import sys
res_path, metrics_path = sys.argv[1], sys.argv[2]
res = open(res_path).read()
metrics = open(metrics_path).read()
marker = "# Auto-generated metrics"
idx = res.find(marker)
if idx >= 0:
    head = res[:idx]
    new = head + metrics
    open(res_path, "w").write(new)
    print(f"updated {res_path}")
else:
    # append
    open(res_path, "a").write("\n\n" + metrics)
    print(f"appended metrics to {res_path}")
PY

echo "=== finalize done at $(date -u +%H:%M:%SZ) ==="

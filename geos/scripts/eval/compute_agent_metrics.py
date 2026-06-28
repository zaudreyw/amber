#!/usr/bin/env python3
"""CLI wrapper — compute tool-error and RAG-retrieval metrics from agent logs.

Delegates to ``src.eval.agent_metrics.main``.  See that module's docstring
for full options.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.eval.agent_metrics import main

if __name__ == "__main__":
    sys.exit(main() or 0)

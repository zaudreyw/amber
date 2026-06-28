#!/usr/bin/env python3
"""CLI wrapper — aggregate billed tokens across JSONL/JSON agent logs.

Delegates to ``src.eval.token_usage.main``.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.eval.token_usage import main

if __name__ == "__main__":
    sys.exit(main() or 0)

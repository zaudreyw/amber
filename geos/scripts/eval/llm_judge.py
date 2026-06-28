#!/usr/bin/env python3
"""CLI wrapper — LLM-as-judge XML evaluation (OpenAI / OpenRouter).

Delegates to ``src.eval.llm_judge.main``.  Requires ``OPENROUTER_API_KEY``
(or ``OPENAI_API_KEY``) in the environment or a ``.env`` file.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.eval.llm_judge import main

if __name__ == "__main__":
    sys.exit(main() or 0)

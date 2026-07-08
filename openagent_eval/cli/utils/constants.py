"""CLI constants for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("./reports")

DEFAULT_CONFIG_CONTENT = """\
# OpenAgent Eval Configuration
# See documentation for options: https://github.com/OpenAgentHQ/openagent-eval

dataset:
  path: data/questions.json
  # limit: 100

llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0

retrieval:
  # provider: chromadb
  # collection_name: my_collection

evaluation:
  metrics:
    - answer_relevancy
    - faithfulness
    - context_precision
    - context_recall

report:
  output: terminal
  output_dir: ./reports
"""

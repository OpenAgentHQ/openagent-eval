"""CLI constants for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("./reports")

DEFAULT_CONFIG_CONTENT = """\
# OpenAgent Eval Configuration
# See documentation for options: https://github.com/OpenAgentHQ/openagent-eval
#
# For a fully offline dry-run (no API keys / vector store required), set:
#   llm.provider: mock
#   retriever.provider: mock

dataset:
  path: data/questions.json
  # limit: 100

llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0

retriever:
  provider: chroma
  settings:
    collection_name: my_collection

metrics:
  retrieval:
    - context_precision
    - context_recall
    - mrr
  generation:
    - faithfulness
    - answer_relevancy
  performance:
    - latency
  cost:
    - token_count

report:
  output: terminal
  output_dir: ./reports
"""

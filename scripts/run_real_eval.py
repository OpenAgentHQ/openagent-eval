"""End-to-end smoke test: real Groq LLM + Sentence-Transformers embeddings.

Runs the full OpenAgent Eval pipeline (retrieve -> generate -> metrics) using:
  * LLM: Groq ``llama-3.3-70b-versatile`` (reads GROQ_API_KEY from env/.env)
  * Embedder: sentence-transformers ``all-MiniLM-L6-v2``
  * Retriever: in-memory cosine vector store over data/corpus.json

Usage:
    python scripts/run_real_eval.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

# Load .env if present (keeps the real API key out of the command line).
if os.path.exists(".env"):
    with open(".env", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    ReportConfig,
    RetrieverConfig,
    EmbedderConfig,
)
from openagent_eval.core.engine import Engine


async def main() -> None:
    dataset_path = "tests/sample_data/valid_dataset.json"
    with open(dataset_path, encoding="utf-8") as fh:
        dataset = json.load(fh)

    config = Config(
        dataset=DatasetConfig(path=dataset_path),
        llm=LLMConfig(
            provider="groq",
            model="llama-3.3-70b-versatile",
            temperature=0.0,
        ),
        retriever=RetrieverConfig(
            provider="memory",
            settings={"documents_path": "data/corpus.json", "k": 3},
            embedder=EmbedderConfig(
                provider="sentence_transformers",
                model="all-MiniLM-L6-v2",
            ),
        ),
        metrics=MetricsConfig(
            retrieval=[],
            generation=["semantic_similarity", "exact_match", "f1_score"],
            performance=["latency"],
            cost=["token_count"],
        ),
        report=ReportConfig(output="terminal"),
        parallel=False,
    )

    engine = Engine(config)
    try:
        report = await engine.run(dataset)
    finally:
        engine.shutdown()

    print("\n==================== EVALUATION REPORT ====================")
    print(f"LLM provider : {report.metadata.get('llm_provider')}")
    print(f"Retriever    : {report.metadata.get('retriever_provider')}")
    print(f"Summary      : {report.summary}")
    print("\n-- Per-item --")
    for i, res in enumerate(report.result.results, 1):
        print(f"\n[{i}] Q: {res.question}")
        print(f"    A: {res.answer[:160]}")
        print(f"    contexts({len(res.contexts)}): {[c[:50] for c in res.contexts]}")
        print(f"    metrics : {res.metrics}")
        print(f"    tokens  : {res.metadata.get('total_tokens')}")
    if report.result.errors:
        print("\n-- Errors --")
        for err in report.result.errors:
            print(f"  {err['type']}: {err['error']}")


if __name__ == "__main__":
    asyncio.run(main())

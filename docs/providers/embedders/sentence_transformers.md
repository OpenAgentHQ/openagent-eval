# Sentence Transformers

Sentence Transformers produces dense vector embeddings locally using PyTorch.
The default model `all-MiniLM-L6-v2` (384 dimensions) is a good general-purpose
choice that runs fast on CPU without API calls.

## When should you use this?

Use it as your default embedder for local RAG evaluation. It works offline,
runs on CPU, and is fast enough for datasets up to ~10k documents.

## Prerequisites

```bash
pip install sentence-transformers
```

## Step 1 — Install

```bash
pip install sentence-transformers
```

## Step 2 — Configure

```yaml title="config.yaml"
embedder:
  provider: sentence_transformers
  settings:
    model_name: all-MiniLM-L6-v2
    # device: cpu   # optional; auto-detected
```

This embedder is used inside retrievers that embed client-side (PGVector,
Memory, Elasticsearch kNN, Qdrant with local embeddings, etc.).

## Step 3 — Reference from a retriever

```yaml title="config.yaml"
retriever:
  provider: memory
  embedder:
    provider: sentence_transformers
    settings:
      model_name: all-MiniLM-L6-v2
  settings:
    documents_path: documents.json
```

## Python SDK example

```python title="eval_with_embedder.py"
import asyncio

from openagent_eval.config.models import (
    Config,
    RetrieverConfig,
    EmbedderConfig,
)
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="memory",
        embedder=EmbedderConfig(
            provider="sentence_transformers",
            settings={"model_name": "all-MiniLM-L6-v2"},
        ),
        settings={"documents_path": "documents.json"},
    ),
    metrics={"retrieval": ["context_precision", "context_recall", "mrr"]},
)

engine = Engine(config)
report = asyncio.run(engine.run(dataset))
print(report.summary["metrics_summary"])
```

## All configuration options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model_name` | `str` | `all-MiniLM-L6-v2` | Hugging Face model identifier. |
| `device` | `str \| null` | `null` | Torch device (`cpu`, `cuda`, etc.). Auto-detected if omitted. |

## Popular models

| Model | Dimensions | Speed | Notes |
|-------|-----------|-------|-------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good default for English |
| `all-mpnet-base-v2` | 768 | Medium | Higher quality, slower |
| `multi-qa-MiniLM-L6-cos-v1` | 384 | Fast | Optimized for QA retrieval |
| `bge-small-en-v1.5` | 384 | Fast | Strong retrieval performance |

## Troubleshooting

- **`ImportError: sentence_transformers`** — Install with
  `pip install sentence-transformers`.
- **Slow first query** — Model loading happens on first use. Subsequent
  queries reuse the loaded model.
- **CUDA out of memory** — Use `device: cpu` or choose a smaller model.

## Related

- Need no embedder at all? Use [Chroma](../retrievers/chroma.md) (embeds
  server-side) or [BM25](../retrievers/bm25.md) (no embeddings).
- Need a testing embedder? See [Mock](mock.md).

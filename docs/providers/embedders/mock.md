# Mock (testing)

The mock embedder produces **deterministic, normalized vectors** from a
hash of the input text. No model download, no network calls, no GPU.

## When should you use this?

Use it for CI pipelines, unit tests, and dry runs where you need the full
pipeline to execute without downloading models. Identical strings always
produce identical vectors, enabling reproducible cosine similarity checks.

## Prerequisites

None — zero dependencies.

## Step 1 — Configure

```yaml title="config.yaml"
embedder:
  provider: mock
  settings:
    dimension: 32   # default
```

## Step 2 — Reference from a retriever

```yaml title="config.yaml"
retriever:
  provider: memory
  embedder:
    provider: mock
    settings:
      dimension: 32
  settings:
    documents_path: documents.json
```

## Python SDK example

```python title="eval_mock_embedder.py"
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
            provider="mock",
            settings={"dimension": 32},
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
| `dimension` | `int` | `32` | Vector dimensionality. |

## How it works

Each input text is hashed with SHA-256 to produce a deterministic vector
of the configured dimension, then L2-normalized to unit length. This means:

- Identical strings → identical vectors
- Different strings → different vectors (usually)
- Vectors are normalized → cosine similarity = dot product

## Troubleshooting

- **Retrieval scores seem random** — Mock vectors are hash-based, not
  semantic. Similarity scores won't reflect meaning. Use
  `sentence_transformers` for real evaluation.
- **Want different results** — Change the `dimension` parameter to alter
  the vector space.

## Related

- Ready for real evaluation? Switch to
  [Sentence Transformers](sentence_transformers.md).
- Some retrievers embed server-side and don't need an embedder: see
  [Chroma](../retrievers/chroma.md).

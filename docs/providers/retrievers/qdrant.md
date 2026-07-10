# Qdrant

Qdrant is a high-performance vector database (self-hosted or Qdrant Cloud). It
**requires an embedder** because it stores and searches dense vectors you supply.

## When should you use this?

Use it when you already run Qdrant in production or need a scalable vector store.

## Prerequisites

- Install the client:
  ```bash
  pip install "openagent-eval[qdrant]"
  ```
- An embedder (e.g. `sentence_transformers`) — **required**.
- A Qdrant instance (local `:memory:`, Docker, or Cloud).

## Step 1 — Install

```bash
pip install "openagent-eval[qdrant]"
```

## Step 2 — Configure

```yaml title="config.yaml"
retriever:
  provider: qdrant
  settings:
    collection_name: my_docs
    url: http://localhost:6333
    # api_key: <your-qdrant-key>     # for Qdrant Cloud
    distance: Cosine                  # Cosine | Euclid | Dot
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

## Step 3 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_qdrant.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig, EmbedderConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="qdrant",
        settings={
            "collection_name": "my_docs",
            "url": "http://localhost:6333",
            "distance": "Cosine",
        },
        embedder=EmbedderConfig(
            provider="sentence_transformers", model="all-MiniLM-L6-v2"
        ),
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
| `collection_name` | `str` | — | **Required.** Qdrant collection. |
| `embedder` | `Embedder` | — | **Required.** Injected automatically from `retriever.embedder`. |
| `url` | `str \| null` | `null` | Qdrant URL; `null` → in-memory `:memory:`. |
| `api_key` | `str \| null` | `null` | For Qdrant Cloud. |
| `prefer_grpc` | `bool` | `False` | Use gRPC transport. |
| `distance` | `str` | `Cosine` | `Cosine`, `Euclid`, or `Dot`. |

## Troubleshooting

- **`ProviderConnectionError: embedder is required`** — add `retriever.embedder`.
- **Connection failed** — verify `url` and `api_key` (Cloud).

## Related

- Choose an embedder in [../embedders/index.md](../embedders/index.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

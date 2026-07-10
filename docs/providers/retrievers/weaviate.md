# Weaviate

Weaviate is a vector database with hybrid (vector + keyword) search. It can embed
**server-side** via its `text2vec` module, so an embedder is **optional** — supply
one only if you want to embed the query locally.

## When should you use this?

Use it when you run Weaviate in production and want hybrid retrieval evaluation.

## Prerequisites

- Install the client:
  ```bash
  pip install "openagent-eval[weaviate]"
  ```
- A Weaviate instance (local `connect_to_local` or Weaviate Cloud).

## Step 1 — Install

```bash
pip install "openagent-eval[weaviate]"
```

## Step 2 — Configure

Server-side embedding (no embedder needed):

```yaml title="config.yaml"
retriever:
  provider: weaviate
  settings:
    collection: Article
    url: http://localhost:8080
    # api_key: <weaviate-key>     # for Weaviate Cloud
```

Or with a local embedder for the query:

```yaml title="config.yaml"
retriever:
  provider: weaviate
  settings:
    collection: Article
    url: http://localhost:8080
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

## Step 3 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_weaviate.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig, EmbedderConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="weaviate",
        settings={"collection": "Article", "url": "http://localhost:8080"},
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
| `collection` | `str` | — | **Required.** Weaviate collection. |
| `embedder` | `Embedder \| null` | `null` | Optional; embed query locally if provided. |
| `url` | `str \| null` | `null` | Falls back to `WEAVIATE_URL`. |
| `api_key` | `str \| null` | `null` | Falls back to `WEAVIATE_API_KEY`. |

## Troubleshooting

- **Connection failed** — set `WEAVIATE_URL` / `WEAVIATE_API_KEY` or pass them.
- **Embedding mismatch** — if you use server-side `text2vec`, do **not** also
  pass an embedder (let Weaviate handle it).

## Related

- Choose an embedder in [../embedders/index.md](../embedders/index.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

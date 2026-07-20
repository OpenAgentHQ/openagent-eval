# Pinecone

Pinecone is a fully managed cloud vector database. It **requires an embedder**
because you supply the dense vectors.

## When should you use this?

Use it when your production RAG runs on Pinecone's managed infrastructure.

## Prerequisites

- Install the client:
  ```bash
  pip install "openagent-eval[pinecone]"
  ```
- An embedder (e.g. `sentence_transformers`) — **required**.
- A Pinecone account and an existing index.

## Step 1 — Install

```bash
pip install "openagent-eval[pinecone]"
```

## Step 2 — Set your API key

```bash
export PINECONE_API_KEY=...
```

## Step 3 — Configure

```yaml title="config.yaml"
retriever:
  provider: pinecone
  settings:
    index_name: my-index
    # api_key omitted -> falls back to the PINECONE_API_KEY env var exported above
    # (config values are used literally; ${VAR} is not expanded)
    # namespace: production     # optional
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

## Step 4 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_pinecone.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig, EmbedderConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="pinecone",
        settings={"index_name": "my-index", "api_key": "pc-..."},
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
| `index_name` | `str` | — | **Required.** Pinecone index. |
| `embedder` | `Embedder` | — | **Required.** |
| `api_key` | `str \| null` | `null` | Falls back to `PINECONE_API_KEY`. |
| `environment` | `str \| null` | `null` | Legacy index environment. |
| `namespace` | `str \| null` | `null` | Optional index namespace. |

## Troubleshooting

- **`ProviderConnectionError: embedder is required`** — add `retriever.embedder`.
- **Auth error** — set `PINECONE_API_KEY` or pass `api_key`.
- **Index not found** — confirm `index_name` exists in your Pinecone project.

## Related

- Choose an embedder in [../embedders/index.md](../embedders/index.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

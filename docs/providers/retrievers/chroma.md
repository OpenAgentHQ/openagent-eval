# Chroma

Chroma is a lightweight, local-first vector database. It **embeds server-side**,
so you do **not** need to configure an embedder.

## When should you use this?

Use it for local RAG evaluation with minimal setup — Chroma is the default
retriever and the easiest vector store to get running.

## Prerequisites

- Install Chroma:
  ```bash
  pip install chromadb
  ```

## Step 1 — Install

```bash
pip install chromadb
```

## Step 2 — Configure

```yaml title="config.yaml"
retriever:
  provider: chroma
  settings:
    collection_name: my_collection
    # persist_directory: ./chroma_db   # optional; omit for in-memory
    # distance_fn: cosine              # cosine | l2 | ip
```

No `embedder` block — Chroma embeds internally.

## Step 3 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_chroma.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="chroma",
        settings={"collection_name": "my_collection"},
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
| `collection_name` | `str` | — | **Required.** Chroma collection to use. |
| `persist_directory` | `str \| null` | `null` | Directory for durable storage; omit for in-memory. |
| `distance_fn` | `str` | `cosine` | `cosine`, `l2`, or `ip`. |

## Troubleshooting

- **`ProviderConnectionError`** — Chroma failed to start; ensure `chromadb` is
  installed and the collection exists (or let OpenAgent Eval create it).
- **No embedder needed** — do not add `retriever.embedder`; Chroma handles
  embeddings itself.

## Related

- Need a local store that embeds *your* way? See [memory](memory.md) or
  [faiss](faiss.md) (these need an embedder).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

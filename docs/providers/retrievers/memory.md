# Memory (in-process vector store)

Memory is a lightweight, dependency-minimal vector retriever that runs
entirely in-process using NumPy. It **embeds client-side**, so you **must**
configure an embedder.

## When should you use this?

Use it for local RAG evaluation without any external database. It embeds your
documents in memory on first query and performs cosine similarity search with
NumPy. Ideal for quick experiments, testing, and small-to-medium datasets.

## Prerequisites

```bash
pip install numpy
```

Plus an embedder (e.g., `pip install sentence-transformers`).

## Step 1 — Install

```bash
pip install numpy sentence-transformers
```

## Step 2 — Prepare documents

```json title="documents.json"
[
  {"content": "Python is a high-level programming language.", "id": "1"},
  {"content": "RAG combines retrieval with language model generation.", "id": "2"},
  {"content": "PostgreSQL supports vector search via the pgvector extension.", "id": "3"}
]
```

## Step 3 — Configure

```yaml title="config.yaml"
retriever:
  provider: memory
  embedder:
    provider: sentence_transformers
    settings:
      model_name: all-MiniLM-L6-v2
  settings:
    documents_path: documents.json
    # k: 5  # default results to return
```

An `embedder` block is **required** — Memory uses it to embed documents and
queries.

## Step 4 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_memory.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig, EmbedderConfig
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
| `documents` | `list[dict] \| null` | `null` | Inline document list (`{"content": str}`). |
| `documents_path` | `str \| null` | `null` | Path to JSON list or JSONL file. |
| `k` | `int` | `5` | Default number of results. |

## How it works

1. On first query, documents are embedded in batch using your configured
   embedder.
2. Vectors are stored in a NumPy matrix in memory.
3. Each query is embedded and ranked by cosine similarity against all
   document vectors.
4. The top-k results are returned with scores in `[0, 1]`.

## Troubleshooting

- **`ProviderConnectionError: requires an embedder`** — Add a
  `retriever.embedder` block to your config.
- **Slow first query** — Document embedding happens on first use. Subsequent
  queries are fast.
- **`ImportError: numpy`** — Install with `pip install numpy`.

## Related

- Need a lexical baseline? See [BM25](bm25.md) (no embedder needed).
- Need a persistent vector store? See [Chroma](chroma.md) or
  [PGVector](pgvector.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

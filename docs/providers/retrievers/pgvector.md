# PGVector

PGVector is a PostgreSQL extension for vector similarity search. It
**embeds client-side**, so you **must** configure an embedder.

## When should you use this?

Use it when you already have a PostgreSQL database and want to add vector
search without introducing another service. Great for production RAG systems
that need ACID transactions alongside vector search.

## Prerequisites

- A running PostgreSQL instance with the `vector` extension enabled
- Install the driver:
  ```bash
  pip install "psycopg[binary]" pgvector
  ```

## Step 1 — Install

```bash
pip install "psycopg[binary]" pgvector
```

## Step 2 — Configure

```yaml title="config.yaml"
retriever:
  provider: pgvector
  embedder:
    provider: sentence_transformers
    settings:
      model_name: all-MiniLM-L6-v2
  settings:
    table: documents
    dsn: postgresql://user:pass@localhost:5432/mydb
    # content_column: content     # default
    # embedding_column: embedding # default
    # metric: cosine              # cosine | l2
```

An `embedder` block is **required** — PGVector uses it to embed queries.

## Step 3 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_pgvector.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig, EmbedderConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="pgvector",
        embedder=EmbedderConfig(
            provider="sentence_transformers",
            settings={"model_name": "all-MiniLM-L6-v2"},
        ),
        settings={
            "table": "documents",
            "dsn": "postgresql://user:pass@localhost:5432/mydb",
        },
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
| `table` | `str` | — | **Required.** Table or view containing embeddings. |
| `dsn` | `str \| null` | `null` | Postgres DSN; falls back to `DATABASE_URL` env. |
| `content_column` | `str` | `content` | Column holding document text. |
| `embedding_column` | `str` | `embedding` | Column holding the `vector`. |
| `metric` | `str` | `cosine` | `cosine` or `l2`. |

## Troubleshooting

- **`ProviderConnectionError`** — Check that PostgreSQL is running, the
  `vector` extension is installed (`CREATE EXTENSION IF NOT EXISTS vector`),
  and the DSN is correct.
- **Missing embedder** — PGVector requires a `retriever.embedder` block.
- **`ImportError: psycopg`** — Install with
  `pip install "psycopg[binary]" pgvector`.

## Related

- Need a managed vector store? See [Chroma](chroma.md) or
  [Pinecone](pinecone.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

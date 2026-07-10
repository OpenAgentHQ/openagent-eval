# Elasticsearch

Elasticsearch supports both **lexical** (BM25) and **kNN** vector search. It
**embeds client-side** when using kNN mode.

## When should you use this?

Use it when you already run Elasticsearch and want hybrid search (keyword +
semantic) in a single system. The lexical mode is a zero-dependency BM25
baseline; kNN mode adds semantic search with an embedder.

## Prerequisites

- A running Elasticsearch cluster
- Install the client:
  ```bash
  pip install elasticsearch
  ```

## Step 1 — Install

```bash
pip install elasticsearch
```

## Step 2 — Configure

=== "Lexical (BM25)"

    ```yaml title="config.yaml"
    retriever:
      provider: elasticsearch
      settings:
        index: my_documents
        hosts: http://localhost:9200
        # api_key: YOUR_API_KEY   # optional; or set ELASTICSEARCH_API_KEY
        # content_field: content  # default
        mode: lexical
    ```

    No `embedder` block needed for lexical mode.

=== "kNN (vector)"

    ```yaml title="config.yaml"
    retriever:
      provider: elasticsearch
      embedder:
        provider: sentence_transformers
        settings:
          model_name: all-MiniLM-L6-v2
      settings:
        index: my_documents
        hosts: http://localhost:9200
        vector_field: embedding
        content_field: content
        mode: knn
    ```

    An `embedder` block is **required** for kNN mode.

## Step 3 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_elasticsearch.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="elasticsearch",
        settings={
            "index": "my_documents",
            "hosts": "http://localhost:9200",
            "mode": "lexical",
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
| `index` | `str` | — | **Required.** Elasticsearch index name. |
| `hosts` | `str \| list[str] \| null` | `null` | ES host(s); falls back to `ELASTICSEARCH_HOSTS` env. |
| `api_key` | `str \| null` | `null` | API key; falls back to `ELASTICSEARCH_API_KEY` env. |
| `vector_field` | `str \| null` | `null` | Field holding the dense vector (kNN mode). |
| `content_field` | `str` | `content` | Field holding document text. |
| `mode` | `str` | `lexical` | `lexical` (BM25) or `knn`. |

## Troubleshooting

- **`ProviderConnectionError`** — Check that Elasticsearch is running and
  the `hosts` URL is correct.
- **Missing embedder in kNN mode** — Add a `retriever.embedder` block.
- **`ImportError: elasticsearch`** — Install with
  `pip install elasticsearch`.
- **Scores seem odd** — Lexical scores are min-max normalized; kNN scores
  come from the embedder cosine similarity.

## Related

- Need a simpler keyword baseline? See [BM25](bm25.md).
- Need a managed vector store? See [Pinecone](pinecone.md) or
  [Qdrant](qdrant.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

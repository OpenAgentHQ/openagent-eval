# Retriever Providers

OpenAgent Eval ships with a pluggable retriever layer so you can evaluate RAG
systems against whatever vector store or search engine you actually use in
production. Every retriever implements the same
`Retriever` interface and returns `Document` objects with a relevance `score`
normalized to the `[0.0, 1.0]` range (higher = more relevant).

## Quick start

```yaml
# config.yaml
dataset:
  path: tests/sample_data/valid_dataset.json

llm:
  provider: groq
  model: llama-3.3-70b-versatile
  temperature: 0.0

retriever:
  provider: memory            # in-memory cosine store, no external service
  settings:
    documents_path: data/corpus.json
    k: 3
  embedder:                   # required by vector retrievers
    provider: sentence_transformers
    model: all-MiniLM-L6-v2

metrics:
  generation: [semantic_similarity, exact_match, f1_score]
  performance: [latency]
  cost: [token_count]
```

```bash
export GROQ_API_KEY=gsk_...
oaeval run --config config.yaml
```

A fully working example (real Groq + Sentence-Transformers) lives at
`scripts/run_real_eval.py`.

## The Retriever interface

```python
from openagent_eval.providers.base.retriever import Retriever


class MyRetriever(Retriever):
    name = "my_retriever"
    description = "A custom document retriever"

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        ...
        return [Document(content=..., metadata=..., score=0.9, id="doc-1")]
```

`retrieve` must raise `ProviderConnectionError` on setup/connection failure and
`ProviderExecutionError` on query failure. Input validation is available via
`self.validate_inputs(query=..., k=...)`.

## Embedders

Vector retrievers (memory, FAISS, Qdrant, Pinecone, pgvector) need query and
document embeddings. OpenAgent Eval provides an `Embedder` abstraction so the
retrieval layer stays embedding-agnostic. Configure it once under
`retriever.embedder` and it is injected automatically:

```yaml
retriever:
  provider: memory
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2      # 384-dim, local, no API key
```

| Embedder | Install | Notes |
|----------|---------|-------|
| `sentence_transformers` | `pip install openagent-eval[evaluation]` or `sentence-transformers` | Local dense vectors; default `all-MiniLM-L6-v2` |
| `mock` | built-in | Deterministic hash vectors for offline tests/CI |

Server-side embedding backends (Chroma, Weaviate) ignore `embedder` and embed
internally.

## Score normalization

Different backends report relevance in incompatible scales (cosine distance,
L2, inner product, raw BM25/Elasticsearch `_score`). All retrievers funnel raw
scores through the shared helpers in `providers/retrievers/_scoring.py`
(`normalize_distance`, `minmax_normalize`, `rank_based_normalize`) so every
`Document.score` lands in `[0.0, 1.0]`.

## Built-in retrievers

### `memory` — in-memory vector store (recommended for local eval)
- **Install:** none (uses NumPy, already a dependency)
- **Embedder:** required
- Indexes documents from `settings.documents` or `settings.documents_path`
  (JSON list or JSONL) and ranks by cosine similarity.

```yaml
retriever:
  provider: memory
  settings:
    documents_path: data/corpus.json
    k: 5
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

### `bm25` — lexical baseline
- **Install:** `pip install openagent-eval[bm25]` (`rank-bm25`)
- **Embedder:** not required
- Classic keyword baseline; useful to check whether an expensive vector
  retriever actually beats BM25. Scores are min-max normalized.

```yaml
retriever:
  provider: bm25
  settings:
    documents_path: data/corpus.json
    k: 5
```

### `http` — generic REST endpoint
- **Install:** none (uses `httpx`, already a dependency)
- **Embedder:** not required
- Points at any search API. Map the JSON response with dot-paths:

```yaml
retriever:
  provider: http
  settings:
    url: http://localhost:9200/my-index/_search
    method: POST
    results_path: hits.hits
    content_path: _source.content
    id_path: _id
    score_path: _score
    score_mode: minmax        # or "passthrough" (default, clamp to [0,1])
```

When `score_path` is omitted, results are ranked by array order.

### `chroma` — ChromaDB
- **Install:** `pip install chromadb`
- **Embedder:** not required (Chroma embeds internally)
- See `docs/08_plugin_system.md` for the original example.

### `qdrant` — Qdrant
- **Install:** `pip install openagent-eval[qdrant]`
- **Embedder:** required

```yaml
retriever:
  provider: qdrant
  settings:
    collection_name: my_docs
    url: http://localhost:6333
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

### `pinecone` — Pinecone
- **Install:** `pip install openagent-eval[pinecone]`
- **Embedder:** required

```yaml
retriever:
  provider: pinecone
  settings:
    index_name: my-index
    api_key: $PINECONE_API_KEY
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

### `weaviate` — Weaviate
- **Install:** `pip install openagent-eval[weaviate]`
- **Embedder:** optional (Weaviate can embed server-side via its `text2vec`
  module; supply one to embed the query locally instead)

```yaml
retriever:
  provider: weaviate
  settings:
    collection: Article
    url: http://localhost:8080
```

### `faiss` — local FAISS index
- **Install:** `pip install openagent-eval[faiss]` (`faiss-cpu`)
- **Embedder:** required

```yaml
retriever:
  provider: faiss
  settings:
    documents_path: data/corpus.json
    metric: cosine        # or "l2"
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

### `pgvector` — PostgreSQL + pgvector
- **Install:** `pip install openagent-eval[pgvector]`
- **Embedder:** required

```yaml
retriever:
  provider: pgvector
  settings:
    table: documents
    dsn: postgresql://user:pass@localhost:5432/db
    metric: cosine        # or "l2"
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

### `elasticsearch` — Elasticsearch
- **Install:** `pip install openagent-eval[elasticsearch]`
- **Embedder:** required for `mode: knn`; not required for `mode: lexical`

```yaml
retriever:
  provider: elasticsearch
  settings:
    index: my-index
    mode: lexical          # or "knn"
    vector_field: embedding
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

### `mock` — offline
- Returns deterministic documents (the dataset's `ground_truth_contexts` when
  available) so the full pipeline runs without any vector store or API key.

## Adding a custom retriever

1. Subclass `Retriever` and implement `async retrieve(...)`.
2. Normalize scores to `[0,0, 1.0]` with `providers/retrievers/_scoring.py`.
3. Register it in `providers/factory.py` `_RETRIEVER_PROVIDERS` (and add a lazy
   export in `providers/retrievers/__init__.py`).
4. (Optional) Expose it via the
   `[project.entry-points."openagent_eval.retrievers"]` entry point.

See `providers/retrievers/memory.py` for the minimal reference implementation.

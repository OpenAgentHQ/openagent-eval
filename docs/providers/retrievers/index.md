# Retriever Providers

Retriever providers fetch the documents/contexts that OpenAgent Eval measures for
retrieval quality (context precision, recall, MRR, …). Every retriever returns
`Document` objects with a relevance `score` normalized to `[0.0, 1.0]`.

## Which one should a beginner pick?

- **Just learning / no infra?** Use [`mock`](mock.md) — zero setup, offline.
- **Local, no external service?** Use [`memory`](memory.md) with the
  `sentence_transformers` embedder — pure NumPy, no server.
- **Already have a vector DB?** Use its adapter (chroma, qdrant, pinecone, weaviate, faiss, pgvector).
- **Want a keyword baseline?** Use [`bm25`](bm25.md) — no embeddings needed.
- **Have a custom search API?** Use [`http`](http.md) to point at any REST endpoint.

## Comparison matrix

| Provider | Install extra | Embedder needed? | Server-side embed? | Needs key? |
|----------|---------------|------------------|-------------------|-----------|
| [Chroma](chroma.md) | `chromadb` | ❌ | ✅ | ❌ |
| [Qdrant](qdrant.md) | `openagent-eval[qdrant]` | ✅ | ❌ | optional |
| [Pinecone](pinecone.md) | `openagent-eval[pinecone]` | ✅ | ❌ | ✅ |
| [Weaviate](weaviate.md) | `openagent-eval[weaviate]` | optional | ✅ | optional |
| [FAISS](faiss.md) | `openagent-eval[faiss]` | ✅ | ❌ | ❌ |
| [PGVector](pgvector.md) | `openagent-eval[pgvector]` | ✅ | ❌ | optional |
| [Elasticsearch](elasticsearch.md) | `openagent-eval[elasticsearch]` | knn mode only | ❌ | optional |
| [BM25](bm25.md) | `openagent-eval[bm25]` | ❌ | ❌ | ❌ |
| [Memory](memory.md) | *(none — NumPy)* | ✅ | ❌ | ❌ |
| [HTTP](http.md) | *(none — httpx)* | ❌ | ❌ | ❌ |
| [Mock](mock.md) | *(built-in)* | ❌ | ❌ | ❌ |

## Common configuration

Retriever options live under `settings:`. Embedders (when required) go under
`embedder:`.

```yaml title="config.yaml"
retriever:
  provider: memory
  settings:
    documents_path: data/corpus.json
    k: 5
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

!!! warning "Embedder requirement"
    `memory`, `faiss`, `qdrant`, `pinecone`, and `pgvector` **require** an
    `embedder`. `elasticsearch` requires one only in `mode: knn`. `weaviate`
    makes it optional (it can embed server-side). `chroma`, `bm25`, `http`, and
    `mock` do **not** need an embedder.

## Score normalization

Different backends report relevance in incompatible scales (cosine distance, L2,
inner product, raw BM25/Elasticsearch `_score`). All retrievers funnel raw scores
through shared helpers so every `Document.score` lands in `[0.0, 1.0]` (higher =
more relevant).

## Next steps

- Open a provider page above for a full walkthrough.
- Need an embedder? See [../embedders/index.md](../embedders/index.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

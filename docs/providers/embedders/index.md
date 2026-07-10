# Embedders

Embedders turn text into vectors. They are only needed by retrievers that embed
**locally** (memory, faiss, qdrant, pinecone, pgvector, and elasticsearch in
`knn` mode). Server-side embedding backends (chroma, weaviate) ignore this
setting and embed internally.

You configure an embedder once under `retriever.embedder` and OpenAgent Eval
injects it automatically into the retriever.

```yaml title="config.yaml"
retriever:
  provider: memory
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

## Comparison matrix

| Embedder | Install extra | Local? | Default model | Needs key? |
|----------|---------------|--------|---------------|-----------|
| [Sentence-Transformers](sentence_transformers.md) | `openagent-eval[evaluation]` | ✅ | `all-MiniLM-L6-v2` (384-dim) | ❌ |
| [Mock](mock.md) | *(built-in)* | ✅ | deterministic hash vectors | ❌ |

## Which one should a beginner pick?

- **Real semantic search?** Use [`sentence_transformers`](sentence_transformers.md)
  with `all-MiniLM-L6-v2` — small, fast, runs on CPU, no API key.
- **Offline tests / CI?** Use [`mock`](mock.md) — deterministic vectors, nothing
  to install.

## Common configuration

| Setting | Type | Default | Notes |
|---------|------|---------|-------|
| `provider` | `str` | — | Required. `sentence_transformers` or `mock`. |
| `model` | `str` | `all-MiniLM-L6-v2` | Model id (sentence-transformers) or ignored (mock). |
| `settings.device` | `str \| null` | `null` | `cpu` / `cuda` (sentence-transformers only). |
| `settings.dimension` | `int` | `32` | Vector size (mock only). |

## Next steps

- Open an embedder page above for a full walkthrough.
- See which retrievers need an embedder in
  [../retrievers/index.md](../retrievers/index.md).

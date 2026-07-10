# Providers

OpenAgent Eval talks to your RAG stack through **providers** — pluggable adapters
for LLMs, retrievers (vector stores / search engines), and embedders. This section
is the practical "how to use" guide for every provider. If you are a beginner,
start here: pick the provider you already use in production, copy the config, and
run your first evaluation in minutes.

## Three kinds of providers

| Kind | What it does | Config key | Example |
|------|--------------|-----------|---------|
| **LLM** | Generates the answer that gets evaluated | `llm.provider` | `openai`, `anthropic`, `ollama`, `mock` |
| **Retriever** | Finds the documents/contexts to evaluate | `retriever.provider` | `chroma`, `memory`, `bm25`, `mock` |
| **Embedder** | Turns text into vectors (needed by some retrievers) | `retriever.embedder.provider` | `sentence_transformers`, `mock` |

## How configuration maps to providers

You almost never construct providers by hand. You describe them in `config.yaml`
and OpenAgent Eval builds the right adapter for you.

```yaml title="config.yaml"
llm:
  provider: openai          # <- LLM provider name
  model: gpt-4o-mini
  api_key: ${OPENAI_API_KEY}   # or leave out and use the env var

retriever:
  provider: chroma          # <- Retriever provider name
  settings:
    collection_name: my_docs
  embedder:                 # <- Embedder (only some retrievers need it)
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

- **LLM providers** read `model`, `api_key`, `temperature`, and `max_tokens`.
- **Retriever providers** read their options from the `settings:` dict.
- **Embedder providers** are attached under `retriever.embedder` and are injected
  automatically into retrievers that embed locally.

!!! tip "No API keys? Start with `mock`"
    Every category has a `mock` provider that runs **fully offline** with zero
    credentials. It is perfect for your first run, CI, and learning the workflow:

    ```yaml
    llm: { provider: mock }
    retriever: { provider: mock }
    ```

## Provider directories

Pick your provider from the lists below. Each page has install steps, the exact
env var, a minimal `config.yaml`, a CLI run command, and a Python SDK example.

- **LLM Providers** → [llm/index.md](llm/index.md)
  (openai, anthropic, gemini, groq, openrouter, ollama, mock)
- **Retriever Providers** → [retrievers/index.md](retrievers/index.md)
  (chroma, qdrant, pinecone, weaviate, faiss, pgvector, elasticsearch, bm25, memory, http, mock)
- **Embedders** → [embedders/index.md](embedders/index.md)
  (sentence_transformers, mock)

## Beginner path

1. Install: `pip install openagent-eval`
2. Pick an LLM from [llm/index.md](llm/index.md) and a retriever from
   [retrievers/index.md](retrievers/index.md).
3. Copy the minimal `config.yaml` from each page into one file.
4. Run: `oaeval run config.yaml`
5. Read the report: `oaeval report latest`

That's it — you are evaluating your RAG pipeline.

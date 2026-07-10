# FAISS

FAISS (Facebook AI Similarity Search) is a local, in-process vector index. It
**requires an embedder** and builds the index from a list of documents or a file.

## When should you use this?

Use it for fast, dependency-light local vector search without a database server.

## Prerequisites

- Install FAISS:
  ```bash
  pip install "openagent-eval[faiss]"
  ```
  (installs `faiss-cpu` + `numpy`)
- An embedder (e.g. `sentence_transformers`) — **required**.

## Step 1 — Install

```bash
pip install "openagent-eval[faiss]"
```

## Step 2 — Configure

Provide your corpus via `documents` (inline list) or `documents_path` (JSON/JSONL):

```yaml title="config.yaml"
retriever:
  provider: faiss
  settings:
    documents_path: data/corpus.json
    metric: cosine            # cosine | l2
    k: 5
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

`data/corpus.json` is a list of `{"content": "...", "metadata": {...}, "id": "..."}`.

## Step 3 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_faiss.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig, EmbedderConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="faiss",
        settings={"documents_path": "data/corpus.json", "metric": "cosine", "k": 5},
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
| `documents` | `list[dict] \| null` | `null` | Inline corpus items. |
| `documents_path` | `str \| null` | `null` | JSON/JSONL corpus file (used if `documents` absent). |
| `embedder` | `Embedder` | — | **Required.** |
| `index_path` | `str \| null` | `null` | Load a prebuilt `.index` file. |
| `metric` | `str` | `l2` | `l2` or `ip` (inner product). |
| `k` | `int` | `5` | Default number of results. |

## Troubleshooting

- **`ImportError: faiss`** — run `pip install "openagent-eval[faiss]"`.
- **`ProviderConnectionError: embedder is required`** — add `retriever.embedder`.
- **Empty results** — confirm `documents` / `documents_path` point to real text.

## Related

- Choose an embedder in [../embedders/index.md](../embedders/index.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).

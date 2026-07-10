# Mock (testing)

The mock retriever returns **deterministic documents** without any vector
store. It is the default for dry runs and CI pipelines.

## When should you use this?

Use it to test your evaluation pipeline end-to-end without needing a
database, embeddings, or network access. In mock mode, ground-truth contexts
from your dataset are returned as retrieved documents so retrieval metrics
can be exercised meaningfully.

## Prerequisites

None — zero dependencies.

## Step 1 — Configure

```yaml title="config.yaml"
retriever:
  provider: mock
```

That's it. No settings, no embedder, no external services.

## Step 2 — Run

```bash
oaeval run config.yaml
```

## What it returns

- **With `ground_truth_contexts`** in the dataset row: Those strings are
  returned as retrieved documents with `score=1.0`.
- **Without ground truth**: Deterministic placeholder documents are returned:
  ```python
  Document(content="Mock context 1 for query: ...", score=1.0, id="mock-0")
  Document(content="Mock context 2 for query: ...", score=0.75, id="mock-1")
  Document(content="Mock context 3 for query: ...", score=0.5, id="mock-2")
  ```

## Python SDK example

```python title="eval_mock.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(provider="mock"),
    metrics={"retrieval": ["context_precision", "context_recall", "mrr"]},
)

engine = Engine(config)
report = asyncio.run(engine.run(dataset))
print(report.summary["metrics_summary"])
```

## All configuration options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `collection_name` | `str` | `mock` | Informational name (reported in logs). |

## Troubleshooting

- **Retrieval metrics are all 1.0** — This is expected when using mock mode
  with ground-truth contexts (they perfectly match). Use a real retriever
  for meaningful retrieval metric values.

## Related

- Ready to go live? Switch to [Chroma](chroma.md) or any other vector
  store and update `retriever.provider`.
- Pair with an LLM from [../llm/index.md](../llm/index.md).

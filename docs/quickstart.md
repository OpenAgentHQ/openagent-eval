# Quickstart

This guide takes you from a fresh install to your first evaluation report in a few minutes.

## 1. Initialize a configuration

```bash
oaeval init
```

This writes a `config.yaml` with sensible defaults:

```yaml title="config.yaml"
dataset:
  path: data/questions.json
  # limit: 100

llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0

retriever:
  provider: chroma
  settings:
    collection_name: my_collection

metrics:
  retrieval:
    - context_precision
    - context_recall
    - mrr
  generation:
    - faithfulness
    - answer_relevancy
  performance:
    - latency
  cost:
    - token_count

report:
  output: terminal
  output_dir: ./reports
```

!!! tip "Use the interactive wizard"
    For a guided setup, use the interactive wizard:

    ```bash
    oaeval init --interactive
    ```

    The wizard will prompt you to select:
    - LLM provider (OpenAI, Anthropic, Gemini, Groq, OpenRouter)
    - Model based on your provider
    - Retriever (Chroma, Qdrant, Pinecone, Weaviate, FAISS, Memory)
    - Metric preset (Quick, Standard, Comprehensive)
    - Output format

!!! tip "Legacy shorthand still works"
    The loader also accepts the flat, single-string form used in older examples:

    ```yaml
    dataset: data/questions.json
    metrics: [faithfulness, answer_relevancy, latency, token_count]
    ```

    It is normalized to the canonical nested structure automatically.

## 2. Validate your configuration

Before running an evaluation, validate your configuration:

```bash
oaeval validate config.yaml
```

This checks:
- YAML syntax
- Configuration schema
- API key availability
- Dataset file existence
- Output directory accessibility

!!! tip "Test without API keys"
    Use the built-in mock LLM and retriever to run the complete pipeline without
    credentials, network access, or a vector database. Follow the
    [offline testing guide](testing-offline.md) for a ready-to-run fixture and
    configuration.

## 3. Prepare a dataset

OpenAgent Eval loads datasets in **JSON**, **JSONL**, **CSV**, or **PDF** format. Each item needs a
`question`; `ground_truth`, `context`, and `ground_truth_contexts` are optional.

```json title="data/questions.json"
[
  {
    "question": "What is the capital of France?",
    "ground_truth": "The capital of France is Paris.",
    "context": "France is a country in Western Europe. Its capital is Paris."
  }
]
```

## 4. Run the evaluation

```bash
oaeval run config.yaml
```

Override the output format from the command line:

```bash
oaeval run config.yaml --output html
```

!!! tip "Use dry-run mode"
    Preview the evaluation plan without running it:

    ```bash
    oaeval run config.yaml --dry-run
    ```

    This shows what would be evaluated without incurring API costs.

!!! tip "Override metrics"
    Run specific metrics instead of all configured ones:

    ```bash
    oaeval run config.yaml --metrics faithfulness,answer_relevancy,latency
    ```

## 5. View the report

```bash
oaeval report latest
```

Other report commands:

```bash
# List all stored evaluations
oaeval list

# List with sorting
oaeval list --sort score --limit 5

# Compare two experiments
oaeval compare exp-001 exp-002

# Delete old reports
oaeval delete exp-001
oaeval delete all --force
```

## 6. Use the Python SDK

The same pipeline is available as a library so you can embed it in `pytest`. The `Engine.run` method is
`async`, so drive it with `asyncio.run`:

```python title="test_eval.py"
import asyncio

from openagent_eval.config.models import Config
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "openai", "model": "gpt-4o-mini"},
    retriever={"provider": "chroma", "settings": {"collection_name": "my_collection"}},
    metrics={"generation": ["faithfulness"], "retrieval": ["context_precision"]},
)

dataset = [
    {
        "question": "What is RAG?",
        "ground_truth": "Retrieval-Augmented Generation.",
        "context": "RAG combines retrieval with generation.",
    }
]

engine = Engine(config)
report = asyncio.run(engine.run(dataset))

assert report.summary["metrics_summary"]["faithfulness"] >= 0.8
```

## Configuration reference

| Key | Type | Description |
| --- | --- | --- |
| `dataset.path` | `str` | Path to the dataset file |
| `dataset.format` | `str` \| `null` | Explicit format: `json`, `jsonl`, `csv`, `pdf` (auto-detected from extension otherwise) |
| `dataset.limit` | `int` \| `null` | Maximum number of items to load |
| `dataset.shuffle` | `bool` | Shuffle items before loading |
| `llm.provider` | `str` | `openai`, `gemini`, `anthropic`, `groq`, `openrouter`, `ollama`, `mock` |
| `llm.model` | `str` | Model identifier (e.g. `gpt-4o-mini`) |
| `llm.temperature` | `float` | Sampling temperature (default `0.0`) |
| `retriever.provider` | `str` | Chroma, Memory, BM25, FAISS, Qdrant, Pinecone, Weaviate, Elasticsearch, PGVector, HTTP, Mock |
| `retriever.settings` | `dict` | Provider-specific options (e.g. `collection_name`) |
| `retriever.embedder` | `dict` \| `null` | Embedder config for local vector retrievers |
| `metrics.retrieval` | `list[str]` | Retrieval metric names |
| `metrics.generation` | `list[str]` | Generation metric names |
| `metrics.performance` | `list[str]` | Performance metric names |
| `metrics.cost` | `list[str]` | Cost metric names |
| `report.output` | `str` | `terminal`, `markdown`, `html`, `json` |
| `report.output_dir` | `str` | Directory for persisted reports |

## Next steps

- Add an API-key-free smoke test with the [offline testing guide](testing-offline.md).
- Understand the internals on the [Architecture](architecture.md) page.
- Learn every flag in the [CLI Reference](cli.md).
- Discover the full API in [API Reference](api.md).

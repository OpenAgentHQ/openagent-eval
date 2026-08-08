# Configuration Reference

This page documents the complete YAML configuration schema for OpenAgent Eval (`config.yaml`). OpenAgent Eval uses configuration files to define datasets, LLM providers, retrievers, evaluation metrics, report formatting, corpus audits, and global runtime parameters.

All configuration files are strictly validated using [Pydantic](https://docs.pydantic.dev/). If any required fields are missing, or if field values violate specified type constraints (such as invalid enum choices or out-of-range numerical values), a `ValidationError` will be raised at loading time.

## Quick Start Example

Below is a complete, annotated `config.yaml` example demonstrating all available top-level sections and common settings:

```yaml
# Dataset configuration
dataset:
  path: data/sample_qa.json
  format: json
  limit: 100
  shuffle: false

# LLM provider configuration
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.0
  max_tokens: 1000

# Retriever configuration
retriever:
  provider: memory
  settings:
    documents_path: data/corpus.json
    k: 3
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
    settings:
      device: cpu

# Metric evaluation configuration
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

# Report export configuration
report:
  output: terminal
  output_dir: ./reports
  include_examples: true
  max_examples: 10

# Optional corpus quality audit configuration
corpus:
  path: ./knowledge_base/
  checks:
    - contradiction
    - staleness
    - duplicate
    - coverage
  llm_provider: openai
  model: gpt-4o-mini
  max_documents: 1000
  similarity_threshold: 0.92
  staleness_days: 365
  embedding_model: all-MiniLM-L6-v2

# Global runtime options
verbose: false
parallel: true
max_workers: 4
timeout: 300.0
```

---

## `dataset`

The `dataset` section configures the input dataset used for evaluation. Datasets contain evaluation samples consisting of questions, answers, ground truth answers, and context documents.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `path` | `str` | *None* | Yes | Path to the dataset file. |
| `format` | `str \| None` | `None` | No | Dataset format (`json`, `jsonl`, `csv`, `hf`). Auto-detected if omitted. |
| `limit` | `int \| None` | `None` | No | Maximum number of items to load (`>= 1`). |
| `shuffle` | `bool` | `false` | No | Whether to shuffle dataset items prior to evaluation. |

### Example

```yaml
dataset:
  path: data/sample_qa.json
  format: json
  limit: 50
  shuffle: true
```

---

## `llm`

The `llm` section specifies the Large Language Model provider and configuration used for candidate generation and LLM-as-a-Judge metric evaluations.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `provider` | `str` | *None* | Yes | LLM provider identifier (e.g., `openai`, `gemini`, `anthropic`, `groq`, `openrouter`, `ollama`, `mock`). |
| `model` | `str` | *None* | Yes | Model identifier (e.g., `gpt-4o`, `gemini-2.5-flash-lite`, `claude-3-5-sonnet-20241022`). |
| `api_key` | `SecretStr \| None` | `None` | No | API key string (must be at least 10 characters if specified). Falls back to provider environment variable if omitted. |
| `temperature` | `float` | `0.0` | No | Sampling temperature for generation (`0.0` to `2.0`). |
| `max_tokens` | `int \| None` | `None` | No | Maximum number of tokens to generate (`>= 1`). |

### Example

```yaml
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.0
  max_tokens: 500
```

---

## `retriever`

The `retriever` section configures the document retrieval component. It supports server-side vector search backends as well as local in-memory vector indexing.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `provider` | `str` | `"chroma"` | Yes | Retriever provider name (e.g., `chroma`, `memory`, `qdrant`, `pinecone`, `weaviate`, `faiss`, `pgvector`, `elasticsearch`, `bm25`, `http`, `mock`). |
| `settings` | `dict[str, Any]` | `{}` | No | Dictionary of provider-specific configuration settings. |
| `embedder` | `EmbedderConfig \| None` | `None` | No | Local embedder configuration for retrievers requiring client-side embeddings. Ignored by server-side backends. |

### `retriever.embedder`

Sub-configuration for local embedding generation used by retrievers such as `memory`, `faiss`, `qdrant`, `pinecone`, and `pgvector`.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `provider` | `str` | *None* | Yes | Embedder provider identifier (e.g., `sentence_transformers`, `mock`). |
| `model` | `str` | `"all-MiniLM-L6-v2"` | No | Embedding model identifier. |
| `settings` | `dict[str, Any]` | `{}` | No | Provider-specific embedder settings (e.g., `device: "cpu"` or `device: "cuda"`). |

### Example

```yaml
retriever:
  provider: memory
  settings:
    documents_path: data/corpus.json
    k: 3
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
    settings:
      device: cpu
```

---

## `metrics`

The `metrics` section defines which evaluation metrics are computed across retrieval, generation, performance, and cost categories. Metric names must correspond to registered keys in `openagent_eval.metrics.METRIC_REGISTRY`.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `retrieval` | `list[str]` | `["context_precision", "context_recall", "mrr"]` | No | Retrieval accuracy metrics to compute. |
| `generation` | `list[str]` | `["faithfulness", "answer_relevancy"]` | No | Generation quality metrics to compute. |
| `performance` | `list[str]` | `["latency"]` | No | Latency and speed performance metrics to track. |
| `cost` | `list[str]` | `["token_count"]` | No | Token usage and financial cost metrics to track. |

### Example

```yaml
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
```

---

## `report`

The `report` section controls how evaluation summaries and output files are generated.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `output` | `OutputFormat` | `"terminal"` | No | Output format for reports. Allowed values: `"terminal"`, `"markdown"`, `"html"`, `"json"`. 
| `output_dir` | `str` | `"./reports"` | No | Output directory path where generated reports will be stored. |
| `include_examples` | `bool` | `true` | No | Whether to include detailed itemized examples in generated reports. |
| `max_examples` | `int` | `10` | No | Maximum number of individual evaluation sample details to include (`>= 1`). |

### Example

```yaml
report:
  output: markdown
  output_dir: ./reports
  include_examples: true
  max_examples: 10
```

---

## `corpus`

The optional `corpus` section configures knowledge base quality audits to detect contradictions, stale files, semantic duplicates, and coverage gaps across document corpora.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `path` | `str` | *None* | Yes | Path to the target corpus directory or document file. |
| `checks` | `list[str]` | `["contradiction", "staleness", "duplicate", "coverage"]` | No | Corpus health checks to run. Allowed values: `"contradiction"`, `"staleness"`, `"duplicate"`, `"coverage"`. |
| `llm_provider` | `str \| None` | `None` | No | LLM provider used for contradiction detection via LLM-as-a-Judge. |
| `model` | `str \| None` | `None` | No | LLM model identifier used for contradiction evaluation. |
| `max_documents` | `int` | `1000` | No | Maximum number of corpus documents to audit (`>= 1`). |
| `similarity_threshold` | `float` | `0.92` | No | Cosine similarity threshold for flagging semantic duplicates (`0.0` to `1.0`). |
| `staleness_days` | `int` | `365` | No | Document age threshold in days past which files are flagged as stale (`>= 1`). |
| `embedding_model` | `str` | `"all-MiniLM-L6-v2"` | No | Embedding model name used for duplicate detection. |

### Example

```yaml
corpus:
  path: ./knowledge_base/
  checks:
    - contradiction
    - staleness
    - duplicate
    - coverage
  llm_provider: openai
  model: gpt-4o-mini
  max_documents: 1000
  similarity_threshold: 0.92
  staleness_days: 365
  embedding_model: all-MiniLM-L6-v2
```

---

## `global`

Global settings configure overall execution and concurrency behavior. These fields are defined directly at the top level of `config.yaml`.

| Field | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `verbose` | `bool` | `false` | No | Enable detailed log output during evaluation. |
| `parallel` | `bool` | `true` | No | Enable parallel processing of dataset items. |
| `max_workers` | `int` | `4` | No | Maximum worker threads/processes for parallel execution (`>= 1`). |
| `timeout` | `float` | `300.0` | No | Overall evaluation timeout limit in seconds (`>= 1.0`). |

### Example

```yaml
verbose: false
parallel: true
max_workers: 4
timeout: 300.0
```

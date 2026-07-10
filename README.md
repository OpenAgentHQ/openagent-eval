# OpenAgent Eval

**Open-source CLI framework for evaluating RAG systems and AI Agents.**

[![PyPI Version](https://img.shields.io/pypi/v/openagent-eval.svg)](https://pypi.org/project/openagent-eval/)
[![Python Versions](https://img.shields.io/pypi/pyversions/openagent-eval.svg)](https://pypi.org/project/openagent-eval/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## Overview

OpenAgent Eval is a local-first, developer-friendly evaluation framework that runs entirely from the command line. It helps developers measure quality, compare experiments, detect hallucinations, and identify retrieval failures in their RAG systems.

**Goal:** Become the `pytest` of AI evaluation.

---

## Features

- **Local-First** - No cloud services, dashboards, or authentication required
- **CLI + SDK** - Use via command line or import as a Python library
- **Framework Agnostic** - Works with any RAG implementation (LangChain, LlamaIndex, custom)
- **Plugin-Based** - Extend with custom metrics, providers, and report generators
- **Comprehensive Metrics** - Retrieval, generation, performance, and cost evaluation
- **Beautiful Reports** - Terminal, Markdown, HTML, and JSON output formats
- **Failure Analysis** - Identify why evaluations fail, not just that they failed

---

## Installation

```bash
pip install openagent-eval
```

For development:

```bash
git clone https://github.com/openagenthq/openagent-eval.git
cd openagent-eval
uv sync
```

---

## Quick Start

### 1. Initialize Configuration

```bash
oaeval init
```

This creates a `config.yaml` file with default settings.

### 2. Configure Your Setup

Edit `config.yaml`:

```yaml
dataset: data/questions.json

retriever:
  provider: chroma
  settings:
    collection_name: my_docs

llm:
  provider: openai
  model: gpt-4o

metrics:
  - faithfulness
  - answer_relevancy
  - hallucination
  - latency

output: terminal
output_dir: ./reports
```

### 3. Run Evaluation

```bash
oaeval run config.yaml
```

### 4. View Results

```bash
oaeval report latest
```

---

## Tutorials

| Tutorial | Description | Link |
|----------|-------------|------|
| **RAG Evaluation Tutorial** | Complete end-to-end guide: build a RAG pipeline, evaluate with all 18 metrics, interpret results, and apply best practices | [`examples/rag_evaluation_tutorial.ipynb`](examples/rag_evaluation_tutorial.ipynb) |

> **Note**: The tutorial runs entirely offline using mock providers — no API keys required!

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `oaeval init` | Create configuration file |
| `oaeval run <config>` | Run evaluation pipeline |
| `oaeval report <id>` | View evaluation reports |
| `oaeval compare <a> <b>` | Compare two experiments |
| `oaeval list` | List previous evaluations |
| `oaeval doctor` | Check environment and dependencies |

---

## SDK Usage

Use OpenAgent Eval as a Python library:

```python
from openagent_eval.core import Engine
from openagent_eval.config import load_config

config = load_config("config.yaml")
engine = Engine(config)
report = await engine.run(dataset)

print(report.summary)
```

---

## Evaluation Metrics

### Retrieval
- Context Precision
- Context Recall
- Precision@K
- Recall@K
- Hit Rate
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG)

### Generation
- Faithfulness
- Answer Relevancy
- Hallucination Detection
- Semantic Similarity
- Exact Match
- F1 Score
- BLEU
- ROUGE
- BERTScore

### Performance
- Latency (embedding, retrieval, LLM stages)

### Cost
- Token counting (prompt, completion, total)
- Cost estimation per provider

---

## Supported Providers

### LLM Providers
- OpenAI
- Anthropic
- Google Gemini
- Groq
- OpenRouter
- Ollama (local)

### Retriever Providers
- Chroma
- Qdrant
- Pinecone
- Weaviate
- FAISS
- pgvector
- Elasticsearch
- BM25
- Memory
- HTTP

---

## Project Structure

```
openagent-eval/
├── openagent_eval/          # Main package
│   ├── cli/                 # CLI commands (Typer)
│   ├── config/              # Configuration system (Pydantic)
│   ├── core/                # Core orchestration
│   ├── datasets/            # Dataset loaders
│   ├── metrics/             # Evaluation metrics
│   ├── providers/           # LLM/Retriever adapters
│   ├── reports/             # Report generators
│   ├── plugins/             # Plugin system
│   └── exceptions/          # Custom exceptions
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration
└── README.md
```

---

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/openagenthq/openagent-eval.git
cd openagent-eval

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=openagent_eval

# Run specific test file
uv run pytest tests/unit/test_exceptions.py
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Licensed under the Apache License, Version 2.0 - see [LICENSE](LICENSE) for details.

---

## Support

- **Documentation:** [docs.openagenthq.com](https://docs.openagenthq.com)
- **Issues:** [GitHub Issues](https://github.com/openagenthq/openagent-eval/issues)
- **Discussions:** [GitHub Discussions](https://github.com/openagenthq/openagent-eval/discussions)

# OpenAgent Eval

**Open-source CLI framework for evaluating RAG systems and AI Agents.**

[![CI](https://github.com/OpenAgentHQ/openagent-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenAgentHQ/openagent-eval/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/OpenAgentHQ/openagent-eval/branch/main/graph/badge.svg)](https://codecov.io/gh/OpenAgentHQ/openagent-eval)
[![PyPI Version](https://img.shields.io/pypi/v/openagent-eval.svg)](https://pypi.org/project/openagent-eval/)
[![Python Versions](https://img.shields.io/pypi/pyversions/openagent-eval.svg)](https://pypi.org/project/openagent-eval/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CodeQL](https://github.com/OpenAgentHQ/openagent-eval/actions/workflows/codeql.yml/badge.svg)](https://github.com/OpenAgentHQ/openagent-eval/actions/workflows/codeql.yml)

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
from openagent_eval import Evaluator

evaluator = Evaluator(config_path="config.yaml")
result = evaluator.evaluate(dataset)

print(result.summary)
```

---

## Evaluation Categories

### Retrieval Metrics
- Context Precision
- Context Recall
- Recall@K / Precision@K
- Hit Rate
- Mean Reciprocal Rank (MRR)
- NDCG

### Generation Metrics
- Faithfulness (via Ragas)
- Answer Relevancy (via Ragas)
- Hallucination Detection (via DeepEval)
- Semantic Similarity
- Exact Match / F1 Score
- BLEU / ROUGE
- BERTScore

### Performance Metrics
- Embedding latency
- Retrieval latency
- LLM latency
- Total latency

### Cost Metrics
- Token counting (prompt, completion, total)
- Cost estimation per provider
- Total experiment cost

---

## Supported Providers

### LLM Providers
- OpenAI
- Google Gemini
- Anthropic
- Groq
- OpenRouter
- Ollama (local)

### Retriever Providers
- Chroma
- (More coming soon)

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

## Roadmap

### v1.0 (Current)
- RAG evaluation
- CLI + SDK interfaces
- Plugin architecture
- Multiple report formats

### v2.0 (Planned)
- AI Agent evaluation
- Tool-call evaluation
- Planning evaluation
- Memory evaluation
- Multi-agent evaluation

### v3.0 (Future)
- CI/CD integration
- GitHub Action
- Cloud synchronization
- Hosted evaluation platform

---

## License

Licensed under the Apache License, Version 2.0 - see [LICENSE](LICENSE) for details.

---

## Support

- **Documentation:** [docs.openagenthq.com](https://docs.openagenthq.com)
- **Issues:** [GitHub Issues](https://github.com/openagenthq/openagent-eval/issues)
- **Discussions:** [GitHub Discussions](https://github.com/openagenthq/openagent-eval/discussions)

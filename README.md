<div align="center">

<!-- Social-card PNG (1280x640) also available at ./docs/assets/banner.png -->
![OpenAgent Eval — pytest-level simplicity for AI evaluation](./docs/assets/banner.svg)

# OpenAgent Eval

**The open-source evaluation framework for RAG systems and AI Agents.**

[![PyPI Version](https://img.shields.io/pypi/v/openagent-eval?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/openagent-eval/)
[![Python Versions](https://img.shields.io/pypi/pyversions/openagent-eval?logo=python&logoColor=white)](https://pypi.org/project/openagent-eval/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Downloads](https://static.pepy.tech/personalized-badge/openagent-eval?period=total&units=INTERNATIONAL_SYSTEM&left_color=grey&right_color=green&left_text=downloads)](https://pepy.tech/projects/openagent-eval)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/OpenAgentHQ/openagent-eval?style=social)](https://github.com/OpenAgentHQ/openagent-eval/stargazers)
[![Forks](https://img.shields.io/github/forks/OpenAgentHQ/openagent-eval?style=social)](https://github.com/OpenAgentHQ/openagent-eval/network/members)
[![Contributors](https://img.shields.io/github/contributors/OpenAgentHQ/openagent-eval?style=social)](https://github.com/OpenAgentHQ/openagent-eval/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/OpenAgentHQ/openagent-eval)](https://github.com/OpenAgentHQ/openagent-eval/issues)

Local-first. Framework-agnostic. Developer-friendly.

[Getting Started](#installation) · [Documentation](https://openagenthq.github.io/openagent-eval/) · [Contributing](#contributing--community)

</div>

---

## Why OpenAgent Eval?

Evaluating RAG systems shouldn't require a PhD or a cloud account. OpenAgent Eval brings **pytest-level simplicity** to AI evaluation — run from your terminal, get actionable insights, and ship with confidence.

- **Local-first** — No cloud services, dashboards, or authentication required
- **Framework-agnostic** — Works with LangChain, LlamaIndex, or any custom RAG pipeline
- **18+ metrics** — Retrieval, generation, faithfulness, relevancy, performance, and cost
- **Plugin-based** — Extend with custom metrics, providers, and report generators
- **Production-ready** — Corpus auditing, failure diagnosis, and synthetic test data generation

---

## Installation

```bash
pip install openagent-eval
```

For development:

```bash
git clone https://github.com/OpenAgentHQ/openagent-eval.git
cd openagent-eval
uv sync
```

---

## Quick Start

### 1. Initialize Configuration

```bash
oaeval init --interactive
```

![oaeval interactive wizard](static/openagent-eval.png)

### 2. Validate Configuration

```bash
oaeval validate config.yaml
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

## Contributing & Community

OpenAgent Eval is community-built and welcomes contributors of every experience level. If you've used the tool, you already know something worth sharing — a bug, a rough edge in the docs, or a metric you wish existed.

**Ways to help:**

- **Code** — pick up a [good first issue](https://github.com/OpenAgentHQ/openagent-eval/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or something labeled [help wanted](https://github.com/OpenAgentHQ/openagent-eval/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22), fix a bug, or add a metric or provider.
- **Docs** — clarify a guide, fix a typo, or expand the [documentation](https://openagenthq.github.io/openagent-eval/).
- **Bug reports** — hit something unexpected? [Open an issue](https://github.com/OpenAgentHQ/openagent-eval/issues/new/choose) with steps to reproduce.
- **Tutorials & examples** — show how you use OpenAgent Eval by adding to [`examples/`](examples/).

**Getting started:**

1. Fork the repository and create a feature branch (`git checkout -b feature/your-change`)
2. Make your change and add tests where it makes sense
3. Run the checks (`uv run pytest` and `uv run ruff check .`)
4. Open a pull request

New to the project? [CONTRIBUTING.md](CONTRIBUTING.md) walks through setup, the development workflow, and coding conventions in detail.

**Where to connect:**

- [GitHub Discussions](https://github.com/OpenAgentHQ/openagent-eval/discussions) — ask questions, share ideas, and show what you built
- [GitHub Issues](https://github.com/OpenAgentHQ/openagent-eval/issues) — bug reports and feature requests
- [Documentation](https://openagenthq.github.io/openagent-eval/) — guides and API reference
- [Changelog](CHANGELOG.md) — release history

---

## Features

| Feature | Description |
|---------|-------------|
| **CLI + SDK** | Use via command line or import as a Python library |
| **Beautiful Reports** | Terminal, Markdown, HTML, and JSON output formats |
| **Failure Analysis** | Identify why evaluations fail, not just that they failed |
| **Corpus Health Auditor** | Detect contradictions, staleness, and duplicates before evaluation |
| **LLM-as-Judge Metrics** | NLI-based scoring for faithfulness and relevancy |
| **Component Diagnosis** | Blame attribution — retrieval vs generation vs chunking |
| **Synthetic Test Data** | Auto-generate test cases from your knowledge base |

---

## Evaluation Metrics

<details>
<summary><strong>Retrieval Metrics</strong></summary>

- Context Precision & Recall
- Precision@K & Recall@K
- Hit Rate
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG)

</details>

<details>
<summary><strong>Generation Metrics</strong></summary>

- Faithfulness (NLI-based)
- Answer Relevancy (NLI-based)
- Hallucination Detection
- Semantic Similarity
- Exact Match & F1 Score
- BLEU & ROUGE
- BERTScore
- LLM-as-Judge (custom criteria)

</details>

<details>
<summary><strong>Performance & Cost</strong></summary>

- Latency tracking (embedding, retrieval, LLM stages)
- Token counting (prompt, completion, total)
- Cost estimation per provider

</details>

---

## Supported Providers

**LLM Providers:** OpenAI · Anthropic · Google Gemini · Groq · OpenRouter · Ollama

**Retriever Providers:** Chroma · Qdrant · Pinecone · Weaviate · FAISS · pgvector · Elasticsearch · BM25

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `oaeval init` | Create configuration file (interactive wizard) |
| `oaeval run <config>` | Run evaluation pipeline |
| `oaeval report <id>` | View evaluation reports |
| `oaeval compare <a> <b>` | Compare two experiments |
| `oaeval list` | List previous evaluations |
| `oaeval validate <config>` | Validate configuration |
| `oaeval doctor` | Check environment and dependencies |
| `oaeval audit --corpus <path>` | Audit corpus health |
| `oaeval diagnose --report <id>` | Diagnose failures and attribute blame |
| `oaeval synth --corpus <path>` | Generate synthetic test cases |

---

## SDK Usage

```python
from openagent_eval.core import Engine
from openagent_eval.config import load_config

config = load_config("config.yaml")
engine = Engine(config)
report = await engine.run(dataset)

print(report.summary)
```

---

## Project Structure

```
openagent-eval/
├── openagent_eval/
│   ├── cli/              # CLI commands (Typer)
│   ├── config/           # Configuration system (Pydantic)
│   ├── core/             # Core orchestration engine
│   ├── metrics/          # 18+ evaluation metrics
│   ├── providers/        # LLM & Retriever adapters
│   ├── corpus/           # Corpus Health Auditor
│   ├── diagnosis/        # Component Diagnosis
│   ├── synthesis/        # Synthetic Test Data
│   ├── reports/          # Report generators
│   └── plugins/          # Plugin system
├── tests/                # Test suite
├── docs/                 # Documentation
└── examples/             # Tutorials and examples
```

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with care by the [OpenAgent](https://github.com/OpenAgentHQ) community.**

</div>

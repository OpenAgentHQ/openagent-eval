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
- **Developer Experience** - Shell completion, config auto-discovery, dry-run mode, and more

### Production-Grade Features (v0.3.0)

- **Corpus Health Auditor** - Detect contradictions, staleness, and duplicates BEFORE connecting to RAG
- **LLM-as-Judge Metrics** - NLI-based scoring for faithfulness and relevancy (not just word overlap)
- **Component Diagnosis** - Blame attribution when things fail (retrieval vs generation vs chunking)
- **Synthetic Test Data** - Auto-generate test cases from your knowledge base

---

## Installation

```bash
pip install openagent-eval
```

To upgrade to the latest version:

```bash
pip install --upgrade openagent-eval
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

This creates a `config.yaml` file with default settings. Use the interactive wizard to select your provider, model, and metrics:

```bash
oaeval init --interactive
```

### 2. Validate Configuration

```bash
oaeval validate config.yaml
```

Check your configuration without running the evaluation.

### 3. Run Evaluation

```bash
oaeval run config.yaml
```

Or use dry-run mode to preview the evaluation plan:

```bash
oaeval run config.yaml --dry-run
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

### Core Commands

| Command | Description |
|---------|-------------|
| `oaeval init` | Create configuration file (interactive wizard) |
| `oaeval run <config>` | Run evaluation pipeline |
| `oaeval report <id>` | View evaluation reports |
| `oaeval compare <a> <b>` | Compare two experiments |
| `oaeval list` | List previous evaluations |
| `oaeval doctor` | Check environment and dependencies |
| `oaeval validate <config>` | Validate configuration |
| `oaeval delete <id>` | Delete evaluation reports |
| `oaeval completion <shell>` | Generate shell completion scripts |

### Production-Grade Commands (v0.3.0)

| Command | Description |
|---------|-------------|
| `oaeval audit --corpus <path>` | Audit corpus for contradictions, staleness, duplicates |
| `oaeval diagnose --report <id>` | Diagnose failures and attribute blame |
| `oaeval synth --corpus <path>` | Generate synthetic test cases |

### Global Flags

| Flag | Description |
|------|-------------|
| `--quiet`, `-q` | Suppress non-essential output |
| `--json` | Output machine-readable JSON |
| `--no-color` | Disable color output |
| `--verbose`, `-v` | Enable verbose output |
| `--version`, `-V` | Show version and exit |

### Shell Completion

Enable tab completion for your shell:

```bash
# Bash
oaeval completion bash >> ~/.bashrc

# Zsh
oaeval completion zsh >> ~/.zshrc

# Fish
oaeval completion fish > ~/.config/fish/completions/oaeval.fish
```

### Config Auto-Discovery

OpenAgent Eval automatically finds your configuration file:

1. `OAEVAL_CONFIG` environment variable
2. `config.yaml` or `config.yml` in current directory
3. `oaeval.yaml` or `oaeval.yml` in current directory
4. Parent directories up to filesystem root

---

## Usage Examples

### Validate Configuration

```bash
oaeval validate config.yaml
```

Example output:

```
OpenAgent Eval - Configuration Validator
Config: config.yaml

1. Checking YAML syntax...
  OK YAML syntax valid

2. Validating configuration schema...
  OK Configuration schema valid

3. Checking API keys...
  OK All required API keys configured

4. Checking dataset...
  OK Dataset found: data/questions.json
  Size: 12.5 KB

5. Checking output directory...
  OK Output directory exists: ./reports

6. Checking provider configuration...
  LLM: openai (gpt-4o)
  Retriever: chroma

7. Checking metrics...
  Configured: 5 metrics
    Retrieval: context_precision, context_recall, mrr
    Generation: faithfulness, answer_relevancy
    Performance: latency
    Cost: token_count

Summary:
PASSED Configuration is valid

Ready to run: oaeval run <config>
```

### Dry-Run Mode

```bash
oaeval run config.yaml --dry-run
```

Example output:

```
OpenAgent Eval - Dry Run Mode

Configuration Summary:
  Config file: config.yaml
  Dataset: data/questions.json
  LLM: openai (gpt-4o)
  Retriever: chroma
  Output: terminal
  Output dir: ./reports

Metrics (5):
  Retrieval: context_precision, context_recall, mrr
  Generation: faithfulness, answer_relevancy
  Performance: latency
  Cost: token_count

Dataset:
  OK Loaded 500 items

  Sample item:
    question: What is the capital of France?
    answer: Paris is the capital of France.
    ground_truth: Paris

This was a dry run. No evaluations were performed.
Run 'oaeval run <config>' to execute the evaluation.
```

### Run with Metrics Override

```bash
oaeval run config.yaml --metrics faithfulness,answer_relevancy,latency
```

### JSON Output

```bash
oaeval run config.yaml --json
```

Example output:

```json
{
  "status": "success",
  "report_path": "reports/eval_2024_01_15.json",
  "elapsed_seconds": 125.42,
  "summary": {
    "total_items": 500,
    "successful_evaluations": 500,
    "failed_evaluations": 0,
    "metrics_summary": {
      "faithfulness": 0.918,
      "answer_relevancy": 0.892
    }
  }
}
```

### List with Sorting

```bash
oaeval list --sort score --limit 5
```

### Delete Reports

```bash
# Delete a specific report
oaeval delete report_2024_01_15

# Delete all reports
oaeval delete all --force
```

### Check Environment

```bash
oaeval doctor --check-api
```

Example output:

```
OpenAgent Eval - Environment Check

Environment Status
  Component       Status    Details
  Python          OK        v3.11.5
  openagent-eval  OK        v0.1.0
  typer           OK        CLI framework
  rich            OK        Terminal UI
  pydantic        OK        Data validation

API Key Availability
  Provider      Environment Variable    Status
  OpenAI        OPENAI_API_KEY          Available
  Gemini        GEMINI_API_KEY          Not set
  Anthropic     ANTHROPIC_API_KEY       Available

API Connectivity Tests
  OK OpenAI: reachable
  OK Anthropic: reachable

Configuration:
  OK Found config: config.yaml

Summary:
  OK Python version is compatible
  OK Available providers: OpenAI, Anthropic

Recommendations
  - Set GEMINI_API_KEY for Gemini support
```

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

### Corpus-Level (NEW)
- Cross-document contradiction detection
- Stale document detection
- Divergent duplicate detection
- Thematic coverage analysis

### Retrieval
- Context Precision
- Context Recall
- Precision@K
- Recall@K
- Hit Rate
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG)

### Generation
- Faithfulness (NLI-based)
- Answer Relevancy (NLI-based)
- Hallucination Detection
- Semantic Similarity
- Exact Match
- F1 Score
- BLEU
- ROUGE
- BERTScore
- LLM-as-Judge (custom criteria)

### Performance
- Latency (embedding, retrieval, LLM stages)

### Cost
- Token counting (prompt, completion, total)
- Cost estimation per provider

### Diagnosis (NEW)
- Blame attribution (retrieval vs generation vs chunking)
- 8 failure mode detection
- Actionable recommendations

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
│   │   ├── retrieval/       # Retrieval metrics
│   │   ├── generation/      # Generation metrics
│   │   ├── nli/             # NLI-based scoring (NEW)
│   │   ├── performance/     # Performance metrics
│   │   └── cost/            # Cost metrics
│   ├── corpus/              # Corpus Health Auditor (NEW)
│   ├── diagnosis/           # Component Diagnosis (NEW)
│   ├── synthesis/           # Synthetic Test Data (NEW)
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

# Run CLI tests
uv run pytest tests/unit/test_cli/
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

# ⚠️ Instructions for Coding Agents

This document is the single source of truth for the OpenAgent Eval project.

Before writing any code:

1. Read this entire document.
2. Do not skip any section.
3. Follow the architecture described here.
4. Do not invent features outside the current phase.
5. Keep the project modular and plugin-based.
6. If a requirement is ambiguous, ask for clarification instead of making assumptions.
7. Prefer maintainability over clever implementations.

# OpenAgent Eval

## Product Specification (v1.0)

---

# Overview

## Project Name

**OpenAgent Eval**

## Tagline

**Open-source CLI framework for evaluating RAG systems and AI Agents.**

---

# Vision

Modern AI applications are no longer just prompts. They include retrievers, vector databases, tools, memory, and multi-step agent workflows.

Developers can build these systems quickly, but they often have no reliable way to measure quality, compare experiments, detect hallucinations, or identify retrieval failures.

OpenAgent Eval solves this by providing a local-first, developer-friendly evaluation framework that runs entirely from the command line.

The goal is to become the standard evaluation tool for AI developers, similar to how `pytest` became the standard testing framework for Python.

---

# Problem Statement

Building a RAG system is relatively easy.

Knowing whether it actually works is difficult.

Most developers evaluate their applications by manually asking a few questions and checking whether the answers look reasonable.

This approach does not scale.

It cannot detect regressions.

It cannot compare experiments.

It provides no objective metrics.

It cannot explain why failures occur.

Current evaluation platforms often require cloud services, dashboards, expensive subscriptions, or complicated setup.

Many developers simply skip evaluation altogether.

As AI systems become larger and more complex, reliable evaluation becomes essential.

---

# Our Solution

OpenAgent Eval is a local-first CLI tool that evaluates RAG systems and AI agents using standardized metrics.

Instead of manually checking outputs, developers provide a dataset and their application.

OpenAgent Eval automatically executes evaluation pipelines and generates comprehensive reports containing:

* Retrieval quality
* Answer quality
* Hallucination detection
* Latency
* Token usage
* Cost analysis
* Failure analysis
* Experiment comparison

Everything runs from the command line.

No dashboard is required.

---

# Goals

The project should:

* Make AI evaluation simple.
* Work locally.
* Be framework agnostic.
* Require minimal configuration.
* Produce reproducible reports.
* Integrate easily into CI/CD pipelines.
* Help developers improve their applications instead of only producing scores.

---

# Non Goals (Version 1)

The first release will NOT include:

* Web dashboard
* User authentication
* Cloud storage
* Team collaboration
* Hosted evaluation service
* Fine-tuning workflows
* RLHF
* Human annotation interface

These can be future products.

---

# Target Users

* AI Engineers
* RAG Developers
* LangChain Developers
* LangGraph Developers
* LlamaIndex Users
* AI Startups
* Open Source Contributors
* Researchers

---

# Core Philosophy

Developers should be able to evaluate AI systems as easily as they run unit tests.

Example:

```bash
oaeval run config.yaml
```

or

```bash
oaeval evaluate
```

The tool should produce a detailed evaluation report without requiring any manual inspection.

---

# Version 1 Scope

Version 1 focuses entirely on **RAG Evaluation**.

Agent evaluation will be introduced later.

---

# Supported Inputs

The framework should support:

* JSON
* JSONL
* CSV
* Hugging Face datasets

Each dataset entry should contain fields such as:

```json
{
  "question": "...",
  "ground_truth": "...",
  "context": "...",
  "metadata": {}
}
```

Ground truth may be optional depending on the selected metrics.

---

# Evaluation Pipeline

Every evaluation follows the same flow.

```
Dataset

↓

Question

↓

Retriever

↓

Retrieved Documents

↓

LLM

↓

Generated Answer

↓

Evaluation Engine

↓

Metrics

↓

Reports
```

This architecture should remain modular so new metrics can be added without changing the pipeline.

---

# Evaluation Categories

## 1. Retrieval Evaluation

Measure how well the retriever selects relevant context.

Initial metrics:

* Context Precision
* Context Recall
* Recall@K
* Precision@K
* Hit Rate
* Mean Reciprocal Rank (MRR)
* NDCG

---

## 2. Generation Evaluation

Measure answer quality.

Metrics:

* Faithfulness
* Answer Relevancy
* Hallucination Detection
* Semantic Similarity
* Exact Match
* F1 Score
* BLEU
* ROUGE
* BERTScore

---

## 3. Performance Evaluation

Measure runtime performance.

Track:

* Embedding latency
* Retrieval latency
* LLM latency
* Total latency

---

## 4. Cost Evaluation

Track:

* Prompt tokens
* Completion tokens
* Total tokens
* Estimated cost
* Cost per request
* Total experiment cost

Support:

* OpenAI
* Gemini
* Anthropic
* Groq
* OpenRouter
* Ollama (token tracking only)

---

# Reports

The CLI should generate reports in multiple formats.

Supported outputs:

* Terminal summary
* Markdown
* HTML
* JSON

Example:

```
Dataset Summary

Questions: 500

Faithfulness: 91.8%

Answer Relevancy: 89.2%

Hallucination Rate: 3.1%

Average Latency: 612 ms

Total Cost: $2.17

Overall Grade: A
```

---

# Failure Analysis

One of the most important features.

Instead of only reporting metrics, identify why failures occurred.

Possible failure categories:

* Wrong retrieval
* Missing context
* Hallucinated answer
* Prompt issue
* Low similarity
* Empty retrieval
* Slow response
* High token usage

The report should include concrete examples for every failure category.

---

# Experiment Comparison

Developers should compare experiments easily.

Example:

```
Experiment A
Chunk Size: 500
Retriever: BM25

Faithfulness: 83%

Experiment B
Chunk Size: 800
Retriever: Hybrid

Faithfulness: 92%
```

The CLI should clearly show improvements and regressions.

---

# CLI Commands

Initial commands:

```bash
oaeval init
```

Create configuration.

---

```bash
oaeval run config.yaml
```

Run evaluation.

---

```bash
oaeval report latest
```

View latest report.

---

```bash
oaeval compare exp1 exp2
```

Compare experiments.

---

```bash
oaeval list
```

List previous evaluations.

---

```bash
oaeval doctor
```

Check environment and dependencies.

---

# Configuration

The framework should use YAML configuration.

Example:

```yaml
dataset: data/questions.json

retriever:
  provider: chroma

llm:
  provider: openai
  model: gpt-5

metrics:
  - faithfulness
  - answer_relevancy
  - hallucination
  - latency
```

The configuration should be extensible.

---

# Architecture

The project should be modular.

```
openagent_eval/

    cli/
    config/
    dataset/
    evaluators/
    metrics/
    pipeline/
    reports/
    experiments/
    integrations/
    providers/
    utils/
```

Every module should have a single responsibility.

---

# Design Principles

The codebase should prioritize:

* Clean architecture
* Modular design
* Extensibility
* Type safety
* Async execution where appropriate
* Easy testing
* Plugin-friendly structure

Avoid tightly coupling metrics, providers, and report generators.

---

# Future Roadmap

Version 2:

* AI Agent Evaluation
* Tool-call evaluation
* Planning evaluation
* Memory evaluation
* Multi-agent evaluation
* Trace analysis

Version 3:

* CI/CD integration
* GitHub Action
* Cloud synchronization
* Hosted evaluation platform
* Enterprise reporting

---

# Success Criteria

OpenAgent Eval is successful when:

* A developer can install it in under five minutes.
* Running an evaluation requires only one command.
* Reports are understandable without additional tooling.
* Adding a new metric requires minimal code changes.
* The framework integrates easily into existing RAG applications.
* Developers use it in local development and CI pipelines to catch regressions before deployment.

---


Since our goal is **CLI-first**, **plugin-based**, and **framework agnostic**, we should **avoid building on LangChain or any other AI framework**.

Build it as a **pure Python framework** with adapters.

This is exactly how tools like **pytest**, **ruff**, and **uv** became widely adopted.

---

# Recommended Tech Stack

| Component       | Technology                     | Why                                     |
| --------------- | ------------------------------ | --------------------------------------- |
| Language        | Python 3.11+                   | AI ecosystem standard                   |
| Package Manager | uv                             | Fast, modern dependency management      |
| CLI             | Typer                          | Clean, production-ready CLI             |
| Terminal UI     | Rich                           | Beautiful progress bars, tables, colors |
| Async           | asyncio                        | Parallel evaluation for speed           |
| Validation      | Pydantic v2                    | Strong typing and config validation     |
| Config          | YAML (PyYAML)                  | Simple configuration                    |
| Logging         | Loguru                         | Better developer experience             |
| Testing         | pytest                         | Industry standard                       |
| Reports         | Jinja2 + Markdown              | HTML and Markdown report generation     |
| Plugin System   | Python entry points / registry | Extensible architecture                 |

---

# AI Libraries

Don't reinvent evaluation metrics. Wrap the best existing libraries.

### Phase 1

* **Ragas** → Faithfulness, Answer Relevancy
* **DeepEval** → Hallucination, G-Eval metrics
* **Sentence Transformers** → Embeddings & semantic similarity
* **Hugging Face Evaluate** → BLEU, ROUGE, F1, Exact Match
* **scikit-learn** → Precision, Recall, MRR calculations

Our framework orchestrates these tools behind a consistent interface.

---

# Project Architecture

```text
openagent-eval/

├── openagent_eval/
│
├── cli/
│
├── core/
│   ├── pipeline.py
│   ├── registry.py
│   └── executor.py
│
├── datasets/
│
├── metrics/
│
├── providers/
│
├── reports/
│
├── plugins/
│
├── utils/
│
└── config/
```

---

# Very Important Rule

Don't write code like this:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(...)
```

Instead create an abstraction.

```python
class LLMProvider:
    def generate(...)
```

Then implement adapters.

```text
providers/

openai.py

gemini.py

ollama.py

groq.py

langchain.py

llamaindex.py
```

The same idea applies to retrievers.

---

# Plugin Architecture

Everything should implement an interface.

```text
Metric

↓

Faithfulness

Hallucination

BLEU

ROUGE

↓

Register Automatically
```

Then users can even write their own metrics.

```python
class MyMetric(BaseMetric):

    name = "my_metric"

    def evaluate(...):
        ...
```

No core code changes needed.

---

# Why NOT LangChain?

If we build on LangChain:

❌ Locked into one ecosystem

❌ Frequent breaking changes

❌ Hard to support custom RAG implementations

❌ Extra dependency for everyone

Instead:

```text
OpenAgent Eval

↓

Core Engine

↓

Adapters

↓

LangChain
LlamaIndex
Haystack
CrewAI
Custom RAG
Raw OpenAI SDK
```

This keeps OpenAgent Eval independent and much easier to maintain.

---

# CLI Framework

I recommend **Typer + Rich**.

Example:

```bash
oaeval init

oaeval run config.yaml

oaeval compare exp1 exp2

oaeval doctor

oaeval report latest
```

Typer gives a clean CLI, and Rich provides attractive tables, progress bars, and colored output without building a dashboard.

---

# Package Manager

Use **uv** from day one.

```bash
uv init
uv add typer rich pydantic
uv run oaeval run config.yaml
```

This gives faster installs and reproducible environments.

---

# Final Recommendation

I would build OpenAgent Eval with this stack:

```text
Language
├── Python 3.11+

CLI
├── Typer
├── Rich

Core
├── asyncio
├── Pydantic v2
├── PyYAML
├── Loguru

Evaluation
├── Ragas
├── DeepEval
├── Sentence Transformers
├── Hugging Face Evaluate
├── scikit-learn

Reports
├── Markdown
├── HTML (Jinja2)

Testing
├── pytest

Packaging
├── uv
```

## One design decision that will pay off later

Don't think of OpenAgent Eval as a **CLI app**. Think of it as a **Python evaluation SDK with a CLI on top**.

Architecture:

```text
┌──────────────────────────┐
│      CLI (Typer)         │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│   OpenAgent Eval SDK     │
│  (Core Evaluation API)   │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ Metrics • Providers      │
│ Datasets • Reports       │
│ Plugins                  │
└──────────────────────────┘
```

This lets users do both:

```bash
oaeval run config.yaml
```

and

```python
from openagent_eval import Evaluator

evaluator = Evaluator(...)
result = evaluator.evaluate(...)
```

without maintaining two separate codebases. This architecture is scalable and aligns well with the long-term OpenAgentHQ ecosystem.

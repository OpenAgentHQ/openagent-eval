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

## Product Specification (v0.3.0)

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

**Production-Grade Vision:** Go beyond pipeline evaluation to validate the entire RAG stack — from corpus health through retrieval quality to generation faithfulness. Be the only tool that can tell you not just "your RAG scored 0.91" but "your RAG scored 0.91, but 23% of your corpus is stale and 3 documents contradict each other."

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

## The Production Problem

Even with evaluation tools like RAGAS, DeepEval, or TruLens, production RAG systems fail silently:

1. **Corpus degradation** — Documents become stale, contradictory, or duplicated. No tool detects this.
2. **Silent failures** — The system scores 0.91 faithfulness while 23% of the corpus is outdated.
3. **No blame attribution** — When answers are wrong, teams don't know if it's retrieval, generation, or chunking.
4. **Manual evaluation doesn't scale** — Teams review samples by hand, introducing sampling bias.
5. **No regression detection** — Changes to embedding models or prompts aren't automatically tested.

**The gap:** Existing tools measure pipeline quality but never question the corpus itself. OpenAgent Eval will measure both.

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
* **Detect corpus-level issues before they become production failures**
* **Provide blame attribution when things go wrong (retrieval vs generation vs chunking)**
* **Generate synthetic test data to bootstrap evaluation**
* **Score faithfulness with NLI-based methods, not just word overlap**

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

# Production-Grade RAG Evaluation (v0.3.0 - IMPLEMENTED)

## The Problem

Building a RAG system is easy. Knowing whether it actually works in production is hard.

**Key findings from research (2026):**
- 70-80% of enterprise RAG deployments never reach stable production
- 90% of production failures are retrieval problems, not LLM problems
- 67% of "hallucinations" are actually extractive (faithfully reproducing wrong corpus data)
- 38.4% of organizations cite "data that fails to update" as primary failure cause
- Existing tools (RAGAS, DeepEval, TruLens) measure pipeline quality but never question the corpus itself

## The Blind Spot

All existing RAG evaluation frameworks share a critical architectural limitation: they measure pipeline quality *conditional on* retrieved documents — they never question *what* was retrieved.

This means:
- A RAGAS score of 0.97 can coexist with answers built on stale, contradictory information
- Cross-document contradictions go undetected
- Divergent duplicates produce non-deterministic answers
- Unmarked obsolescence silently degrades quality

## Our Solution: Four New Capabilities

### 1. Corpus Health Auditor (THE DIFFERENTIATOR)

**What it does:** Scans the knowledge base *before* connecting to RAG to detect issues that no existing tool can see.

**Checks performed:**
- **Cross-document contradictions** — Two documents covering the same topic provide incompatible information
- **Unmarked obsolescence** — Documents exist and are retrievable but describe states that have changed
- **Divergent duplicates** — Same document exists in two slightly different versions (e.g., SharePoint vs Confluence)
- **Thematic coverage gaps** — Missing topics in the knowledge base

**Why it matters:** This is Step Zero before any serious enterprise RAG deployment. Pipeline evaluation frameworks assume a coherent corpus — they measure quality conditional on corpus health.

### 2. LLM-as-Judge Metrics

**What it does:** Replaces word-overlap fallbacks with proper NLI-based scoring for faithfulness and relevancy.

**Components:**
- NLI Judge using DeBERTa-based Natural Language Inference
- Claim extractor to split answers into atomic claims
- Evidence finder to match claims to supporting context
- Generic LLM-as-Judge for custom quality dimensions

### 3. Component Diagnosis (Blame Attribution)

**What it does:** When something fails, tells the user WHERE it failed — retrieval, generation, or chunking.

**Failure modes detected:**
- Empty retrieval / Low context relevance
- Missing context / Hallucination
- Off-topic answers / Chunking split
- Stale index / Embedding mismatch

**Output:** Root cause breakdown with percentages and actionable recommendations.

### 4. Synthetic Test Data Generator

**What it does:** Auto-generates Q&A test cases and adversarial scenarios from the knowledge base.

**Capabilities:**
- Generate questions from document content
- Create adversarial test cases (tricky questions, edge cases)
- Augment existing datasets with new variations

---

# Updated Feature Matrix

| Feature | v0.1.0 (Foundation) | v0.3.0 (Current) |
|---------|---------------------|-------------------|
| Retrieval Metrics | Context Precision, Recall, MRR, NDCG, Hit Rate | Same + LLM-as-Judge |
| Generation Metrics | Faithfulness, Relevancy, Hallucination (word overlap) | Same + NLI-based scoring |
| Corpus Validation | None | ✅ Contradiction, Staleness, Duplicate detection |
| Component Diagnosis | Basic failure analysis | ✅ Full blame attribution |
| Test Data | Manual datasets only | ✅ Synthetic generation |
| Retriever Providers | ChromaDB only | ✅ 11 providers (Chroma, Qdrant, Pinecone, Weaviate, FAISS, pgvector, Elasticsearch, BM25, HTTP, Memory, Mock) |
| NLI Metrics | None | ✅ DeBERTa-based faithfulness, relevancy scoring |
| CLI Commands | init, run, report, compare, list, doctor | ✅ + validate, delete, diagnose, audit, synth, test, completion |
| CI/CD Integration | None | ✅ Pytest plugin, threshold gating, GitHub Actions workflow |
| Production Monitoring | None | Live traffic sampling (planned) |

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

## 1. Corpus-Level Evaluation (NEW)

**Measure the health of the knowledge base itself — before connecting to RAG.**

Checks:

* Cross-document contradictions
* Unmarked obsolescence (stale documents)
* Divergent duplicates (same doc, different versions)
* Thematic coverage gaps

This is Step Zero. Pipeline evaluation frameworks assume a coherent corpus.

---

## 2. Retrieval Evaluation

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

## 3. Generation Evaluation

Measure answer quality.

Metrics:

* Faithfulness (NLI-based, not just word overlap)
* Answer Relevancy (NLI-based)
* Hallucination Detection
* Semantic Similarity
* Exact Match
* F1 Score
* BLEU
* ROUGE
* BERTScore
* LLM-as-Judge (custom criteria)

---

## 4. Performance Evaluation

Measure runtime performance.

Track:

* Embedding latency
* Retrieval latency
* LLM latency
* Total latency

---

## 5. Cost Evaluation

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

## 6. Component Diagnosis (NEW)

When something fails, attribute blame to the specific component:

* Retrieval failures (empty, low relevance, missing context)
* Generation failures (hallucination, off-topic)
* Chunking failures (info split across chunks)
* Index failures (stale, embedding mismatch)

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

## Production-Grade Commands (v0.3.0 - IMPLEMENTED)

```bash
oaeval audit --corpus ./knowledge_base/
```

Audit corpus for contradictions, staleness, duplicates. Run BEFORE connecting to RAG.

---

```bash
oaeval audit --corpus ./knowledge_base/ --checks contradiction,staleness
```

Audit with specific checks only.

---

```bash
oaeval diagnose --report reports/eval_2024_01_15.json
```

Diagnose failures and attribute blame (retrieval vs generation vs chunking).

---

```bash
oaeval synth --corpus ./knowledge_base/ --count 100
```

Generate synthetic test cases from corpus.

---

```bash
oaeval synth --corpus ./knowledge_base/ --adversarial --count 50
```

Generate adversarial test cases.

---

```bash
oaeval test config.yaml -t faithfulness:gte:0.8
```

Run evaluation as CI/CD test with threshold gating.

---

```bash
oaeval test config.yaml -t faithfulness:gte:0.8 -t answer_relevancy:gte:0.7 --json
```

Run evaluation with multiple thresholds and JSON output.

---

```bash
oaeval ui
```

Launch interactive TUI dashboard (Textual).

---

```bash
oaeval ui --config config.yaml
```

Launch TUI with specific configuration.

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

## Production-Grade Configuration (v0.3.0 - IMPLEMENTED)

```yaml
# Corpus audit (run BEFORE connecting to RAG)
corpus:
  path: ./knowledge_base/
  checks:
    - contradiction
    - staleness
    - duplicate
    - coverage
  llm_provider: openai  # for LLM-as-Judge contradiction detection
  model: gpt-4o-mini

# NLI-based scoring (replaces word overlap)
metrics:
  retrieval:
    - context_precision
    - context_recall
    - mrr
  generation:
    - faithfulness  # now uses NLI when available
    - answer_relevancy  # now uses NLI when available
  performance:
    - latency
  cost:
    - token_count

# Diagnosis (run after evaluation)
diagnosis:
  enabled: true
  blame_attribution: true
  recommendations: true
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

Version 1.0 (Stable Release):

* Generic LLM-as-Judge for custom criteria
* **Hybrid CLI UI** (Rich banner + Textual TUI dashboard)

Version 2.0:

* AI Agent Evaluation
* Tool-call evaluation
* Planning evaluation
* Memory evaluation
* Multi-agent evaluation
* Trace analysis
* Production Monitoring (live traffic sampling)

Version 3.0:

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

### Phase 1 (Implemented)

* **Ragas** → Faithfulness, Answer Relevancy
* **DeepEval** → Hallucination, G-Eval metrics
* **Sentence Transformers** → Embeddings & semantic similarity
* **Hugging Face Evaluate** → BLEU, ROUGE, F1, Exact Match
* **scikit-learn** → Precision, Recall, MRR calculations

### Phase 9-12 (Implemented)

* **transformers + torch** → DeBERTa NLI model for claim verification
* **scikit-learn** → Document clustering for contradiction detection
* **numpy** → Similarity calculations for duplicate detection

Our framework orchestrates these tools behind a consistent interface.

---

# Project Architecture

```text
openagent-eval/

├── openagent_eval/

├── cli/

├── core/
│   ├── pipeline.py
│   ├── registry.py
│   └── executor.py

├── datasets/

├── metrics/
│   ├── retrieval/        # Context precision, recall, MRR, NDCG
│   ├── generation/       # Faithfulness, relevancy, hallucination
│   ├── nli/              # NLI-based scoring (NEW)
│   ├── performance/      # Latency tracking
│   └── cost/             # Token counting

├── corpus/               # NEW: Corpus Health Auditor
│   ├── base.py           # BaseCorpusAnalyzer ABC
│   ├── models.py         # CorpusIssue, AuditReport
│   ├── contradiction.py  # Cross-document contradiction detection
│   ├── staleness.py      # Outdated document detection
│   ├── duplicates.py     # Divergent duplicate detection
│   ├── coverage.py       # Thematic coverage analysis
│   └── auditor.py        # CorpusAuditor orchestrator

├── diagnosis/            # NEW: Component Diagnosis
│   ├── analyzer.py       # DiagnosisAnalyzer
│   ├── blame.py          # BlameAttribution
│   ├── chunking.py       # ChunkingQualityAnalyzer
│   └── models.py         # DiagnosisReport, FailureMode

├── synthesis/            # NEW: Synthetic Test Data
│   ├── generator.py      # SyntheticDataGenerator
│   ├── question_gen.py   # QuestionGenerator
│   ├── adversarial.py    # AdversarialTestCaseGenerator
│   └── models.py         # SyntheticDataset, TestCase

├── providers/

├── reports/

├── plugins/

├── utils/

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

---

# Hybrid CLI UI (v1.0 Planned)

## Design Principle

- **Standard CLI:** All existing commands (`oaeval evaluate`, `oaeval audit`, etc.) use Rich for beautiful output
- **Interactive TUI:** `oaeval ui` launches Textual dashboard for power users
- **Zero Breaking Changes:** Existing workflows continue to work unchanged

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  oaeval evaluate  →  Beautiful Rich output (no TUI)         │
│  oaeval audit     →  Beautiful Rich output (no TUI)         │
│  oaeval ui        →  Full Textual interactive dashboard     │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack Additions

| Component | Technology | Reason |
|-----------|------------|--------|
| ASCII Art Banner | pyfiglet | Professional CLI branding |
| Interactive TUI | Textual | Full keyboard-driven dashboard |

## Dependencies

```toml
[project.optional-dependencies]
ui = ["textual>=0.40", "pyfiglet>=1.0"]
```

## UI Module Structure

```
openagent_eval/
├── cli/
│   ├── banner.py        # ASCII art banner with Rich (NEW)
│   └── commands/
├── ui/                  # Textual TUI application (NEW)
│   ├── __init__.py
│   ├── app.py           # Main Textual App class
│   ├── screens.py       # Dashboard screens (main, audit, evaluate, diagnose)
│   ├── widgets.py       # Custom widgets (banner, results table, progress bars)
│   └── styles.tcss      # Textual CSS for layout
```

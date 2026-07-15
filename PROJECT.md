# PROJECT.md — Product Specification

> Source of truth for what OpenAgent Eval is and does.

---

## What It Is

**OpenAgent Eval** (`oaeval`) — Open-source CLI framework for evaluating RAG systems and AI Agents. Runs entirely from the command line. No cloud, no dashboards, no auth.

**Goal**: Become the `pytest` of AI evaluation.

---

## The Problem

Building RAG systems is easy. Knowing whether they actually works is hard.

- 70-80% of enterprise RAG deployments never reach stable production
- 90% of production failures are retrieval problems, not LLM problems
- 67% of "hallucinations" are actually extractive (wrong corpus data)
- Existing tools (RAGAS, DeepEval, TruLens) measure pipeline quality but never question the corpus

---

## What It Does

1. **Corpus Health Audit** — Scan knowledge base BEFORE connecting to RAG. Detect contradictions, staleness, duplicates, coverage gaps.
2. **Pipeline Evaluation** — Run retrieval + generation + metrics. Score quality objectively.
3. **Blame Attribution** — When answers fail, tell you WHERE: retrieval, generation, or chunking.
4. **Synthetic Data Generation** — Auto-generate test cases from knowledge base.
5. **CI/CD Gating** — Run evaluations as tests with threshold-based pass/fail.

---

## CLI Commands

| Command | Purpose |
|---------|---------|
| `oaeval init` | Scaffold config |
| `oaeval run config.yaml` | Run evaluation |
| `oaeval audit --corpus ./docs/` | Audit corpus health (pre-RAG) |
| `oaeval diagnose --report report.json` | Blame attribution |
| `oaeval synth --corpus ./docs/` | Generate test cases |
| `oaeval test config.yaml -t faithfulness:gte:0.8` | CI/CD gating |
| `oaeval report latest` | View results |
| `oaeval compare exp1 exp2` | Compare experiments |
| `oaeval list` | List past evaluations |
| `oaeval doctor` | System diagnostics |

---

## Evaluation Categories

**Corpus**: Contradiction, staleness, duplicate detection, coverage analysis

**Retrieval**: Context precision, context recall, MRR, NDCG, HitRate, Precision@K, Recall@K

**Generation**: Faithfulness (NLI-based), answer relevancy, hallucination detection, semantic similarity, BLEU, ROUGE, F1, BERTScore, LLM-as-Judge

**Performance**: Latency tracking (embedding, retrieval, LLM, total)

**Cost**: Token counting, cost estimation

---

## Supported Providers

**LLMs**: OpenAI, Anthropic, Gemini, Groq, Ollama, OpenRouter

**Retrievers**: ChromaDB, Qdrant, Pinecone, Weaviate, FAISS, pgvector, Elasticsearch, BM25, HTTP, Memory, Mock

**Datasets**: JSON, JSONL, CSV, HuggingFace, PDF

## Non-Goals (v1)

No dashboard, no auth, no cloud, no team collab, no fine-tuning. Agent eval in v2.

---

## Design Rules

1. **SDK with CLI on top** — core logic is importable Python, CLI is thin shell
2. **Plugin-based** — metrics, providers, reports implement ABCs; users extend via plugins
3. **Local-first** — everything runs from command line
4. **Framework agnostic** — NO LangChain/LlamaIndex dependency; use adapters
5. **Async-native** — all providers and pipeline support asyncio
6. **Typed errors** — every failure is a subclass of `OpenAgentEvalError`

---

## Tech Stack

Python 3.10+ · uv · Typer + Rich · Pydantic v2 · YAML · pytest · Ragas · DeepEval · Sentence Transformers · HF Evaluate · scikit-learn

---

## Related

`ARCHITECTURE.md` · `CONTEXT.md` · `DECISIONS.md`

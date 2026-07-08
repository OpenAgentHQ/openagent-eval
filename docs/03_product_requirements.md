# Product Requirements

## Overview

OpenAgent Eval is a local-first CLI framework for evaluating RAG systems and AI Agents.

---

## Version 1 Scope

Version 1 focuses entirely on **RAG Evaluation**. Agent evaluation will be introduced later.

---

## Supported Inputs

The framework supports:

- JSON
- JSONL
- CSV
- Hugging Face datasets

### Dataset Schema

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

## Evaluation Pipeline

Every evaluation follows the same flow:

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

---

## Evaluation Categories

### 1. Retrieval Evaluation

Measure how well the retriever selects relevant context.

**Metrics:**

- Context Precision
- Context Recall
- Recall@K
- Precision@K
- Hit Rate
- Mean Reciprocal Rank (MRR)
- NDCG

### 2. Generation Evaluation

Measure answer quality.

**Metrics:**

- Faithfulness
- Answer Relevancy
- Hallucination Detection
- Semantic Similarity
- Exact Match
- F1 Score
- BLEU
- ROUGE
- BERTScore

### 3. Performance Evaluation

Measure runtime performance.

**Track:**

- Embedding latency
- Retrieval latency
- LLM latency
- Total latency

### 4. Cost Evaluation

**Track:**

- Prompt tokens
- Completion tokens
- Total tokens
- Estimated cost
- Cost per request
- Total experiment cost

**Supported providers:**

- OpenAI
- Gemini
- Anthropic
- Groq
- OpenRouter
- Ollama (token tracking only)

---

## Reports

The CLI generates reports in multiple formats:

- Terminal summary
- Markdown
- HTML
- JSON

---

## Failure Analysis

Identify why failures occurred:

- Wrong retrieval
- Missing context
- Hallucinated answer
- Prompt issue
- Low similarity
- Empty retrieval
- Slow response
- High token usage

The report includes concrete examples for every failure category.

---

## Experiment Comparison

Developers should compare experiments easily:

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

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `oaeval init` | Create configuration |
| `oaeval run config.yaml` | Run evaluation |
| `oaeval report latest` | View latest report |
| `oaeval compare exp1 exp2` | Compare experiments |
| `oaeval list` | List previous evaluations |
| `oaeval doctor` | Check environment and dependencies |

---

## Non-Goals (Version 1)

The first release will NOT include:

- Web dashboard
- User authentication
- Cloud storage
- Team collaboration
- Hosted evaluation service
- Fine-tuning workflows
- RLHF
- Human annotation interface

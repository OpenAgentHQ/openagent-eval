# QUICKSTART.md — Coding Agent Quick Reference

> Get productive in <60 seconds.

---

## Identity

| Field | Value |
|-------|-------|
| Repo | `openagent-eval` |
| Package | `openagent_eval` |
| CLI | `oaeval` |

---

## First Commands

```bash
uv sync --group dev          # Install deps
pytest                        # Run tests
ruff check .                  # Lint
```

---

## How to Run

```bash
oaeval run config.yaml        # Run evaluation
oaeval audit --corpus ./docs  # Audit corpus
oaeval diagnose --report r.json  # Blame attribution
oaeval synth --corpus ./docs  # Generate test data
oaeval test config.yaml -t faithfulness:gte:0.8  # CI/CD
```

---

## Where to Put Code

| What | Where |
|------|-------|
| New metric | `metrics/{category}/new_metric.py` |
| New LLM | `providers/llm/new_provider.py` |
| New retriever | `providers/retrievers/new_retriever.py` |
| New command | `cli/commands/new_command.py` |

---

## Interfaces

```python
# Metric
from openagent_eval.metrics.base import BaseMetric, MetricResult
class MyMetric(BaseMetric):
    name = "my_metric"
    def evaluate(self, **kwargs) -> MetricResult:
        return MetricResult(score=0.95, reason="Because...", metadata={})

# LLM Provider
from openagent_eval.providers.base.llm import LLMProvider
class MyLLM(LLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        return "response"
    async def get_token_count(self, text: str) -> int:
        return len(text.split())

# Retriever
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document
class MyRetriever(Retriever):
    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        return [Document(content="...", metadata={}, score=0.9)]
```

---

## Testing & Git

```bash
pytest                              # All tests
pytest tests/unit/test_metrics/     # Module
pytest -k "test_faithfulness"       # One test
```

- **Never** develop on `main`
- Branch: `feature/{desc}`, `fix/{desc}`, `docs/{desc}`
- Push → PR → user reviews

---

## Context Files

| File | Purpose |
|------|---------|
| `PROJECT.md` | What we're building |
| `ARCHITECTURE.md` | How it's built |
| `AGENT.md` | Coding rules |
| `DECISIONS.md` | Why we chose this |
| `CONTEXT.md` | Current state |
| `INSTRUCTIONS.md` | Writing rules |

---

## Rules

1. Never develop on `main`
2. Never raise generic `Exception`
3. Never put business logic in CLI
4. Always use typed exceptions
5. Always implement ABCs
6. Always create PR for review

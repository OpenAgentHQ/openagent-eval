# CONTEXT.md — Coding Agent Memory

> Scannable in <30 seconds.

---

## Identity

| Field | Value |
|-------|-------|
| Repo | `openagent-eval` |
| Package | `openagent_eval` |
| CLI | `oaeval` |
| Lang | Python 3.10+ |
| PM | `uv` |
| Test | `pytest` |
| Lint | `ruff` |

---

## What It Is

CLI framework for evaluating RAG systems and AI Agents. No cloud, no dashboards. Goal: become `pytest` of AI evaluation.

---

## Key Modules

| Module | Path | Purpose |
|--------|------|---------|
| CLI | `cli/` | Typer commands |
| Core | `core/` | Engine, pipeline, executor, registry |
| Providers | `providers/` | 6 LLMs, 11 retrievers, 2 embedders |
| Metrics | `metrics/` | Retrieval, generation, NLI, cost, latency |
| Datasets | `datasets/` | JSON, JSONL, CSV, HuggingFace, PDF |
| Reports | `reports/` | Terminal, Markdown, HTML, JSON |
| Corpus | `corpus/` | Health audit (contradiction, staleness, duplicates) |
| Diagnosis | `diagnosis/` | Blame attribution (retrieval vs generation) |
| Synthesis | `synthesis/` | Synthetic test data generation |
| Plugins | `plugins/` | Entry-point discovery |
| Exceptions | `exceptions/` | Typed error hierarchy |

---

## Key Files

| File | Purpose |
|------|---------|
| `PROJECT.md` | Product spec (source of truth) |
| `AGENT.md` | Engineering handbook |
| `DECISIONS.md` | Architectural decisions |
| `ARCHITECTURE.md` | System design (file paths) |
| `INSTRUCTIONS.md` | Writing rules |

---

## Research Stats

- 70-80% enterprise RAG never reach stable production
- 90% of failures are retrieval problems
- 67% of "hallucinations" are extractive (wrong corpus data)
- Existing tools never question the corpus

---

## Git Workflow

- **Never** develop on `main`
- Branch: `feature/{desc}`, `fix/{desc}`, `docs/{desc}`
- Push → PR → user reviews (never merge yourself)

---

## Quick Ref

```bash
uv sync --group dev          # Setup
pytest                        # Test
ruff check .                  # Lint
oaeval run config.yaml        # Run eval
oaeval audit --corpus ./docs  # Corpus audit
oaeval synth --source ./docs  # Generate test data
```

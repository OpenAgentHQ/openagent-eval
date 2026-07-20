# AGENT.md — Engineering Handbook

> Coding standards, architecture rules, execution constraints.

---

## Naming (Critical)

| Context | Name |
|---------|------|
| Repository | `openagent-eval` |
| Package | `openagent_eval` |
| CLI | `oaeval` |

---

## Core Rules

1. **No LangChain** — pure Python with adapters
2. **SDK + CLI** — core logic importable, CLI is thin shell
3. **Plugin-based** — metrics, providers, reports implement ABCs
4. **Local-first** — no cloud, no dashboards, no auth
5. **Async-native** — all providers support asyncio

---

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `cli/` | Parse commands, delegate to core, display output |
| `core/` | Orchestration: engine, pipeline, executor, registry |
| `metrics/` | BaseMetric ABC + retrieval/generation/NLI/cost/latency |
| `providers/` | LLMProvider + Retriever ABCs + 6 LLMs, 11 retrievers, 2 embedders |
| `datasets/` | BaseDatasetLoader ABC + JSON, JSONL, CSV, HuggingFace, PDF |
| `reports/` | ReportGenerator ABC + terminal, markdown, HTML, JSON |
| `corpus/` | Pre-RAG health audit (contradiction, staleness, duplicates, coverage) |
| `diagnosis/` | Blame attribution (retrieval vs generation vs chunking) |
| `synthesis/` | Synthetic test data generation from knowledge base |
| `plugins/` | Entry-point discovery + dynamic loading |
| `exceptions/` | `OpenAgentEvalError` hierarchy |

---

## Dependency Rules

- `cli/` → everything; nothing → `cli/`
- `core/` → `datasets/`, `metrics/`, `providers/`, `reports/`
- `metrics/`, `providers/`, `reports/` → `utils/`, `types/` only
- `exceptions/`, `types/` → nothing (leaf modules)
- **No circular dependencies**

---

## Coding Standards

- Python 3.10+, type hints on all public functions
- Pydantic v2 for all data models
- `snake_case` functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- Functions under 50 lines, single responsibility per module
- No global variables, no business logic in CLI

---

## Exceptions

- NEVER raise generic `Exception` — use typed exceptions
- Always include context in error messages
- All exceptions subclass `OpenAgentEvalError`

---

## Testing

- pytest, 80%+ coverage
- Unit tests per module, integration tests for pipeline
- Mock ALL external dependencies, test success + failure paths

---

## Git Workflow

- **Never** develop on `main`
- Branch: `feature/{desc}`, `fix/{desc}`, `docs/{desc}`, `refactor/{desc}`, `test/{desc}`, `chore/{desc}`
- Push → PR → user reviews (never merge yourself)

---

## Critical Rules

1. NEVER place business logic in CLI commands
2. NEVER raise generic `Exception`
3. NEVER skip approval gate before implementation
4. NEVER assume features not in PROJECT.md
5. ALWAYS communicate through interfaces
6. NEVER develop on `main` — always create PR for review

---

## Package Release Rules

Whenever releasing a new version of any package, ALWAYS follow the workflow in `Release_Guide.md`.

Quick reference: See `Release.md` for the release checklist.

Key rules:
- Never skip tests.
- Never skip CHANGELOG updates.
- Never publish an unverified release.
- Never ignore failed CI or publishing workflows.
- Always verify the published package after release.
- Always use annotated Git tags.
- Always follow the same release workflow for every package.

---

`PROJECT.md` · `ARCHITECTURE.md` · `DECISIONS.md` · `CONTEXT.md`

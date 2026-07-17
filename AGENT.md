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

Whenever releasing a new version of any package, ALWAYS follow this workflow.

### 1. Validate the Project
- Ensure all tests pass.
- Ensure linting and formatting pass.
- Verify CI is green.
- Confirm the package builds successfully.
- Ensure documentation is up to date.

### 2. Update the Release
- Update the package version following Semantic Versioning.
- Update CHANGELOG.md with all user-facing changes.
- Verify README examples and installation instructions.

### 3. Commit Changes
- Create a release commit if needed.

Commit message:

```
release: vX.Y.Z
```

### 4. Create Git Tag
- Create an annotated Git tag.

Tag:

```
vX.Y.Z
```

Push the tag to GitHub.

### 5. GitHub Release
Create a GitHub Release using the same tag.

Release title should be descriptive.

Example:

```
v0.5.0 – New Features & Improvements
```

Generate release notes with the following sections:

- ✨ Features
- 🐛 Bug Fixes
- 📚 Documentation
- ⚙️ Internal Changes
- ❤️ Contributors

Never use the version number alone as the release title.

### 6. Automated Release
If GitHub Actions handles releases:

- Wait for the workflow to finish.
- Verify build success.
- Verify package publishing succeeded.
- Verify GitHub Release was created.
- Stop immediately if any workflow fails.

Never assume a release succeeded without verification.

### 7. Post-Release Verification
Verify:

- Git tag exists.
- GitHub Release exists.
- Package is available on the package registry.
- Fresh installation succeeds.
- The CLI/package reports the correct version.

### 8. Final Report
After every release, provide a summary including:

- Version released
- Release status
- CI status
- Package publish status
- GitHub Release status
- Any warnings or failures

### Semantic Versioning

| Change | Example |
|--------|---------|
| PATCH (bug fixes, docs, internal) | 0.4.5 → 0.4.6 |
| MINOR (backward-compatible features) | 0.4.5 → 0.5.0 |
| MAJOR (breaking changes) | 1.x.x → 2.0.0 |

### Rules
- Never skip tests.
- Never skip CHANGELOG updates.
- Never publish an unverified release.
- Never ignore failed CI or publishing workflows.
- Always verify the published package after release.
- Always use annotated Git tags.
- Always follow the same release workflow for every package.

---

`PROJECT.md` · `ARCHITECTURE.md` · `DECISIONS.md` · `CONTEXT.md`

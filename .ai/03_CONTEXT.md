# CONTEXT.md - Working Memory

> This file tracks project state, milestones, and current progress.
> Update after every milestone.

---

## Current State

| Field | Value |
|-------|-------|
| **Phase** | Phase 5 Complete |
| **Status** | Provider Layer Implemented |
| **Last Updated** | 2026-07-08 |
| **Next Action** | Ready for Phase 6 (Plugin System) |
| **Current Branch** | feature/phase-5-providers |
| **Remote** | https://github.com/OpenAgentHQ/openagent-eval.git |

---

## Project Identity

| Field | Value |
|-------|-------|
| **Repository** | openagent-eval |
| **Package** | openagent_eval |
| **CLI** | oaeval |
| **Source of Truth** | PROJECT.md |

---

## Project Understanding

**OpenAgent Eval** is an open-source CLI framework for evaluating RAG systems and AI Agents.

**Core Problem:** Developers can build RAG systems but cannot reliably measure quality, compare experiments, detect hallucinations, or identify retrieval failures.

**Solution:** A local-first, developer-friendly evaluation framework that runs entirely from the command line.

**Target:** Become the `pytest` of AI evaluation.

---

## Architecture Summary

```
CLI (oaeval - Typer + Rich)
            │
            ▼
SDK (openagent_eval - Core Evaluation API)
            │
            ▼
┌─────────────────────────────────────────┐
│  Metrics • Providers • Datasets • Reports │
│  Plugins • Integrations • Exceptions     │
└─────────────────────────────────────────┘
```

---

## Key Files

| File | Purpose |
|------|---------|
| `.ai/00_PROJECT.md` | Single source of truth (Product Specification) |
| `.ai/02_AGENT.md` | Engineering handbook (coding standards, architecture rules) |
| `.ai/03_CONTEXT.md` | This file (working memory, progress tracking) |
| `.ai/04_DECISIONS.md` | Architectural decisions with rationale |
| `.ai/05_TASKS.md` | Project task list and progress tracking |
| `.ai/01_ARCHITECTURE.md` | System architecture and design |

---

## Milestones

### Milestone 0: Documentation & Architecture
- [x] Read and understand PROJECT.md
- [x] Create AGENT.md
- [x] Create CONTEXT.md
- [x] Create DECISIONS.md
- [x] Create TASKS.md
- [x] Architecture analysis and improvements
- [x] Apply architecture decisions (D011-D016)
- [x] Update all project files
- [x] Create .ai/ directory structure

### Milestone 1: Project Foundation
- [x] Initialize project with uv
- [x] Create pyproject.toml
- [x] Set up directory structure
- [x] Create exception hierarchy
- [x] CLI skeleton (Typer)
- [x] Configuration system (Pydantic v2 + YAML)
- [x] Core module (engine, pipeline, executor, registry)
- [x] Testing infrastructure (pytest)
- [x] Linting and formatting (ruff)

### Milestone 2: Data Layer
- [x] BaseDatasetLoader interface
- [x] JSON loader
- [x] JSONL loader
- [x] CSV loader
- [x] HuggingFace loader
- [x] Dataset validation

### Milestone 3: Metrics
- [x] BaseMetric interface
- [x] MetricResult model
- [x] Retrieval metrics
- [x] Generation metrics
- [x] Classic metrics (BLEU, ROUGE, etc.)

### Milestone 4: Reports
- [x] ReportGenerator interface
- [x] Terminal report (Rich)
- [x] Markdown report
- [x] HTML report (Jinja2)
- [x] JSON report

### Milestone 5: Providers
- [x] LLMProvider interface
- [x] Retriever interface
- [x] OpenAI adapter
- [x] Gemini adapter
- [x] Anthropic adapter
- [x] Groq adapter
- [x] OpenRouter adapter
- [x] Ollama adapter (token tracking only)
- [x] Chroma adapter
- [x] Unit tests (138 tests)

### Milestone 6: Plugin System
- [ ] Plugin registry
- [ ] Entry point discovery
- [ ] User extension examples

---

## Current Questions

None at this time. Phase 5 is complete.

---

## Blockers

None currently.

---

## Architecture Decisions Applied

| ID | Decision | Status |
|----|----------|--------|
| D011 | CLI Naming Convention | ✅ Applied |
| D012 | Core Module Structure | ✅ Applied |
| D013 | Exception Hierarchy | ✅ Applied |
| D014 | Testing Structure | ✅ Applied |
| D015 | Configuration Validation | ✅ Applied |
| D016 | Documentation Workflow | ✅ Applied |

---

## Git Workflow Rules (MANDATORY)

GitHub Flow must be followed throughout the project.

### Rules

- **NEVER** develop directly on the `main` branch
- The `main` branch must always remain stable and production-ready
- For every task:
  1. Create a new Git branch before making any code changes
  2. Perform all work on that branch
  3. Push the branch to the remote repository when complete
  4. Create a Pull Request targeting the `main` branch
  5. **Do NOT merge** - the user will review and merge manually

### Branch Naming Convention

```
feature/{description}      # New features
fix/{description}          # Bug fixes
docs/{description}         # Documentation updates
refactor/{description}     # Code refactoring
test/{description}         # Test additions/updates
chore/{description}        # Maintenance tasks
```

---

## Notes

- Phase 1 is complete - all foundation work done
- Phase 2 is complete - Data Layer implemented
- Phase 3 is complete - Metrics System implemented (86 tests)
- Phase 4 is complete - Reports System implemented (78 tests)
- Phase 5 is complete - Provider Layer implemented (138 tests)
- Total tests: 490+ passing
- Ready to proceed with Phase 6 (Plugin System)

---

## Change Log

| Date | Change |
|------|--------|
| 2026-07-08 | Initial CONTEXT.md created |
| 2026-07-08 | Updated Milestone 0 completion status |
| 2026-07-08 | Added TASKS.md to key files |
| 2026-07-08 | Architecture analysis completed |
| 2026-07-08 | Applied architecture decisions D011-D016 |
| 2026-07-08 | Updated with project identity (repository, package, CLI) |
| 2026-07-08 | Added ARCHITECTURE.md to key files |
| 2026-07-08 | Created .ai/ directory structure |
| 2026-07-08 | Moved all project files to .ai/ |
| 2026-07-08 | Connected to GitHub repository |
| 2026-07-08 | Applied Git workflow rules (GitHub Flow) |
| 2026-07-08 | Corrected all dates from 2025 to 2026 |
| 2026-07-08 | Phase 2 completed - Data Layer implemented |
| 2026-07-08 | Dataset loaders (JSON, JSONL, CSV, HuggingFace) working |
| 2026-07-08 | Ready for Phase 3 (Metrics System) |
| 2026-07-08 | Phase 3 completed - Metrics System implemented |
| 2026-07-08 | Phase 4 completed - Reports System implemented |
| 2026-07-08 | Phase 5 completed - Provider Layer implemented |
| 2026-07-08 | 138 new provider tests added (490+ total) |
| 2026-07-08 | PR #7 created for Phase 5 |

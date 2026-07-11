# CONTEXT.md - Working Memory

> This file tracks project state, milestones, and current progress.
> Update after every milestone.

---

## Current State

| Field | Value |
|-------|-------|
| **Phase** | Phase 13 Complete — CI/CD Integration |
| **Status** | v1.0 complete; production-grade features in progress |
| **Last Updated** | 2026-07-11 |
| **Next Action** | Phase 14 (Hybrid CLI UI) or another feature |
| **Current Branch** | feature/cicd-integration |
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

**Production-Grade Vision:** Go beyond pipeline evaluation to validate the entire RAG stack — from corpus health through retrieval quality to generation faithfulness. Be the only tool that can tell you not just "your RAG scored 0.91" but "your RAG scored 0.91, but 23% of your corpus is stale and 3 documents contradict each other."

## Key Research Findings (2026)

| Finding | Source |
|---------|--------|
| 70-80% of enterprise RAG deployments never reach stable production | Gabriel Anhaia, April 2026 |
| 90% of production failures are retrieval problems | Zartis, March 2026 |
| 67% of "hallucinations" are actually extractive (wrong corpus data) | Renmin University + Tencent, 2025 |
| 38.4% cite "data that fails to update" as primary failure cause | Sinequa, June 2026 |
| Existing tools measure pipeline quality but never question the corpus | K-AI, June 2026 |

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
- [x] Plugin registry extended with entry point discovery
- [x] Entry point discovery mechanism implemented
- [x] Plugin loading mechanism implemented
- [x] Plugin development guide created
- [x] Example custom metric plugin created
- [x] Unit tests for plugin system written (27 tests)

### Milestone 7: Functional Evaluation Pipeline (CORRECTED)
> NOTE: The pipeline (`core/pipeline.py`) was previously a STUB — `_evaluate_item`
> never called a retriever, LLM, or any metric, so `oaeval run` produced empty
> results despite the earlier "complete" status. This was fixed on 2026-07-10.
- [x] `Pipeline._evaluate_item` now runs Retriever → LLM → Metrics end-to-end
- [x] `Engine` wires providers (factory) + metric registry + `Executor`
- [x] `providers/factory.py` maps provider config → adapter instances
- [x] Mock LLM + Mock Retriever for offline dry-run (no API keys)
- [x] `Executor.gather` for bounded parallel item evaluation (D006)
- [x] `recall_at_k` fixed to true recall (was binary, == hit_rate)
- [x] `Pipeline._compute_summary` reports real error count (was hardcoded 0)
- [x] Hallucination metric no longer swallows all errors
- [x] Heavy models (SentenceTransformer/Ragas) cached per metric instance
- [x] Config template + `MetricsConfig` defaults aligned to registry names
- [x] `DatasetItemModel.ground_truth_contexts` added for retrieval eval
- [x] Integration test (mock end-to-end) + recall_at_k unit test added

### Milestone 8: Documentation
- [ ] Phase 8 documentation tasks (see TASKS.md)

### Milestone 9: Corpus Health Auditor (NEW — THE DIFFERENTIATOR)
- [ ] Design `BaseCorpusAnalyzer` ABC
- [ ] Implement `CorpusIssue` and `AuditReport` models
- [ ] Implement `ContradictionDetector` (LLM-as-Judge)
- [ ] Implement `StalenessDetector` (timestamp analysis)
- [ ] Implement `DuplicateDetector` (embedding similarity)
- [ ] Implement `CoverageAnalyzer` (thematic gaps)
- [ ] Implement `CorpusAuditor` orchestrator
- [ ] Add `oaeval audit` CLI command
- [ ] Add `CorpusConfig` to configuration models
- [ ] Write unit tests for all corpus analyzers

### Milestone 10: LLM-as-Judge Metrics (NEW)
- [ ] Implement `NLIJudge` using DeBERTa NLI model
- [ ] Implement `ClaimExtractor` (split answers into atomic claims)
- [ ] Implement `EvidenceFinder` (match claims to supporting context)
- [ ] Upgrade `Faithfulness` metric to use NLI fallback
- [ ] Upgrade `AnswerRelevancy` metric to use NLI fallback
- [ ] Implement generic `LLMJudgeMetric` for custom criteria
- [ ] Write unit tests for NLI scoring

### Milestone 11: Component Diagnosis (NEW)
- [ ] Define `FailureMode` enum (8 failure modes)
- [ ] Implement `BlameAttribution` (retrieval vs generation vs chunking)
- [ ] Implement `ChunkingQualityAnalyzer`
- [ ] Implement `DiagnosisAnalyzer` orchestrator
- [ ] Add `oaeval diagnose` CLI command
- [ ] Write unit tests for blame attribution

### Milestone 12: Synthetic Test Data (NEW) — COMPLETE
- [x] Implement `QuestionGenerator` (generate questions from documents)
- [x] Implement `AdversarialTestCaseGenerator` (tricky edge cases)
- [x] Implement `SyntheticDataGenerator` orchestrator
- [x] Add `oaeval synth` CLI command
- [x] Write unit tests for synthetic generation (49 tests)
- [x] Write integration test for synthetic data pipeline (7 tests)

### Milestone 13: CI/CD Integration (NEW) — COMPLETE
- [x] Implement pytest plugin for RAG evaluation
- [x] Add threshold-based test gating
- [x] Add `oaeval test` CLI command
- [x] Write documentation for CI/CD integration
- [x] Add GitHub Actions workflow example

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
- Phase 6 is complete - Plugin System implemented (27 tests)
- Phase 7 is complete - Evaluation pipeline is now functional (was a stub)
- Phase 8 is pending - Documentation
- **Phase 9-13 are NEW** — Production-grade RAG evaluation features
- **Phase 13 is COMPLETE** — CI/CD Integration (pytest plugin, threshold gating, `oaeval test` command)
- **Phase 12 is COMPLETE** — Synthetic Test Data generator implemented (56 tests)
- CORRECTION: earlier "517+ passing / all phases complete" status was inaccurate —
  the core pipeline did not actually evaluate. That gap is closed.
- `oaeval run` now produces real answers, computed metrics, token usage, and latency.
- Offline dry-run works via `llm.provider: mock` + `retriever.provider: mock`.
- Ready to proceed with Phase 8 (Documentation), Phase 9 (Corpus Auditor), or Phase 14 (Hybrid CLI UI).

## Competitive Advantage

**What makes OpenAgent Eval unique vs RAGAS, DeepEval, TruLens:**

1. **Corpus Health Auditor** — No existing tool validates the knowledge base itself
2. **Blame Attribution** — No existing tool tells you WHERE the failure occurred
3. **NLI-based Scoring** — Word overlap is insufficient for production use
4. **Synthetic Test Data** — Bootstrap evaluation from your corpus
5. **CLI-first, Local-first** — No cloud services, no dashboards, no authentication
6. **Hybrid CLI UI** — Beautiful Rich output + optional Textual TUI dashboard

---

## CLI UI Research Findings

**Key technologies discovered:**

| Technology | Purpose | Integration |
|------------|---------|-------------|
| pyfiglet | ASCII art banners | CLI banner generation |
| Rich Layout | Rows/columns, Panels, Tables | Standard CLI output |
| Textual | Full TUI framework | `oaeval ui` command |
| rich.live.Live | Real-time dashboards | Live updating displays |

**Architecture decision:**
- Hybrid approach: Rich for all commands, Textual for `oaeval ui`
- Zero breaking changes to existing CLI
- Opt-in interactivity for power users

---

## Change Log

| Date | Change |
|------|--------|
| 2026-07-11 | **Phase 13 COMPLETE** — CI/CD Integration implemented (pytest plugin, threshold gating, `oaeval test` command) |
| 2026-07-11 | **Phase 12 COMPLETE** — Synthetic Test Data generator implemented (56 tests) |
| 2026-07-11 | Added Phase 14: Hybrid CLI UI (Rich banner + Textual TUI dashboard) |
| 2026-07-11 | Added CLI UI research findings to context |
| 2026-07-11 | Added Phase 9-13 (production-grade RAG eval): Corpus Auditor, LLM-as-Judge, Diagnosis, Synthetic Data, CI/CD |
| 2026-07-11 | Updated 00_PROJECT.md with production-grade vision and feature matrix |
| 2026-07-11 | Updated 01_ARCHITECTURE.md with new modules (corpus/, diagnosis/, synthesis/) |
| 2026-07-11 | Updated 03_CONTEXT.md with research findings and competitive advantage |
| 2026-07-10 | Pipeline stub fixed: retriever→LLM→metrics wired; mock providers added; recall_at_k/summary/hallucination bugs fixed; config aligned |
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
| 2026-07-08 | Phase 6 completed - Plugin System implemented |
| 2026-07-08 | 27 new plugin tests added (517+ total) |
| 2026-07-08 | Created plugin development guide |
| 2026-07-10 | Added PDF dataset loader (PDFDatasetLoader) with pypdf optional dependency |

# TASKS.md - Project Task List

> Track all project tasks across development phases.
> Update after every major milestone.

---

## TODO

### Phase 8: Documentation
- [ ] Create docs/01_vision.md
- [ ] Create docs/02_problem_statement.md
- [ ] Create docs/03_product_requirements.md
- [ ] Create docs/04_architecture.md
- [ ] Create docs/05_project_structure.md
- [ ] Create docs/06_cli_spec.md
- [ ] Create docs/07_metric_system.md
- [ ] Create docs/08_plugin_system.md
- [ ] Create docs/09_coding_guidelines.md
- [ ] Create docs/10_development_plan.md
- [ ] Create docs/11_future_roadmap.md
- [ ] Create docs/examples.md
- [ ] Create CONTRIBUTING.md
- [ ] Create ROADMAP.md
- [ ] Create CHANGELOG.md

### Phase 9: Corpus Health Auditor (THE DIFFERENTIATOR)
- [ ] Design `BaseCorpusAnalyzer` ABC
- [ ] Implement `CorpusIssue` and `AuditReport` models
- [ ] Implement `ContradictionDetector` (LLM-as-Judge)
- [ ] Implement `StalenessDetector` (timestamp analysis)
- [ ] Implement `DuplicateDetector` (embedding similarity)
- [ ] Implement `CoverageAnalyzer` (thematic gaps)
- [ ] Implement `CorpusAuditor` orchestrator
- [ ] Add `oaeval audit` CLI command
- [ ] Add `CorpusConfig` to configuration models
- [ ] Add `CorpusError` exception hierarchy
- [ ] Write unit tests for all corpus analyzers
- [ ] Write integration test for corpus audit pipeline

### Phase 10: LLM-as-Judge Metrics
- [ ] Implement `NLIJudge` using DeBERTa NLI model
- [ ] Implement `ClaimExtractor` (split answers into atomic claims)
- [ ] Implement `EvidenceFinder` (match claims to supporting context)
- [ ] Upgrade `Faithfulness` metric to use NLI fallback
- [ ] Upgrade `AnswerRelevancy` metric to use NLI fallback
- [ ] Implement generic `LLMJudgeMetric` for custom criteria
- [ ] Add `nli` optional dependency group to pyproject.toml
- [ ] Write unit tests for NLI scoring
- [ ] Write integration test for NLI-based metrics

### Phase 11: Component Diagnosis
- [ ] Define `FailureMode` enum (8 failure modes)
- [ ] Implement `BlameAttribution` (retrieval vs generation vs chunking)
- [ ] Implement `ChunkingQualityAnalyzer`
- [ ] Implement `DiagnosisAnalyzer` orchestrator
- [ ] Add `oaeval diagnose` CLI command
- [ ] Add `DiagnosisError` exception hierarchy
- [ ] Write unit tests for blame attribution
- [ ] Write integration test for diagnosis pipeline

### Phase 12: Synthetic Test Data — COMPLETE
- [x] Implement `QuestionGenerator` (generate questions from documents)
- [x] Implement `AdversarialTestCaseGenerator` (tricky edge cases)
- [x] Implement `SyntheticDataGenerator` orchestrator
- [x] Add `oaeval synth` CLI command
- [x] Write unit tests for synthetic generation (49 tests)
- [x] Write integration test for synthetic data pipeline (7 tests)

### Phase 13: CI/CD Integration — COMPLETE
- [x] Implement pytest plugin for RAG evaluation
- [x] Add threshold-based test gating
- [x] Add `oaeval test` CLI command
- [x] Write documentation for CI/CD integration
- [x] Add GitHub Actions workflow example

---

## IN PROGRESS

*No tasks currently in progress.*

---

## COMPLETED

### Phase 14: Hybrid CLI UI — REMOVED
- [x] TUI removed from codebase, CLI-only interface retained

### Phase 13: CI/CD Integration
- [x] Implement pytest plugin for RAG evaluation
- [x] Add threshold-based test gating
- [x] Add `oaeval test` CLI command
- [x] Write documentation for CI/CD integration
- [x] Add GitHub Actions workflow example

### Phase 12: Synthetic Test Data
- [x] Implement `QuestionGenerator` (generate questions from documents)
- [x] Implement `AdversarialTestCaseGenerator` (tricky edge cases)
- [x] Implement `SyntheticDataGenerator` orchestrator
- [x] Add `oaeval synth` CLI command
- [x] Write unit tests for synthetic generation (49 tests)
- [x] Write integration test for synthetic data pipeline (7 tests)

### Phase 6: Plugin System
- [x] Design plugin registry
- [x] Implement entry point discovery
- [x] Create plugin loading mechanism
- [x] Write plugin development guide
- [x] Create example custom metric
- [x] Write unit tests for plugin system

### Phase 5: Providers
- [x] Define LLMProvider interface
- [x] Define Retriever interface
- [x] Implement OpenAI adapter
- [x] Implement Gemini adapter
- [x] Implement Anthropic adapter
- [x] Implement Groq adapter
- [x] Implement OpenRouter adapter
- [x] Implement Ollama adapter (token tracking only)
- [x] Implement Chroma retriever adapter
- [x] Write unit tests for all providers (138 tests)

### Phase 4: Reports
- [x] Define ReportGenerator interface
- [x] Implement terminal report (Rich)
- [x] Implement Markdown report
- [x] Implement HTML report (Jinja2)
- [x] Implement JSON report
- [x] Create failure analysis reporting
- [x] Implement experiment comparison reports
- [x] Write unit tests for all reporters (78 tests)

### Phase 1: Project Foundation
- [x] Initialize project with `uv init`
- [x] Create `pyproject.toml` with all dependencies
- [x] Set up directory structure (openagent_eval/*)
- [x] Create `__init__.py` files for all modules
- [x] Create exception hierarchy (exceptions/*)
- [x] Implement CLI skeleton with Typer
- [x] Create configuration system (Pydantic v2 + YAML)
- [x] Implement core module (engine.py, pipeline.py, executor.py, registry.py)
- [x] Set up pytest and testing infrastructure
- [x] Set up linting (ruff) and formatting

### Milestone 0: Documentation & Architecture
- [x] Read and understand PROJECT.md
- [x] Create AGENT.md (engineering handbook)
- [x] Create CONTEXT.md (working memory)
- [x] Create DECISIONS.md (architectural decisions)
- [x] Create TASKS.md (this file)
- [x] Architecture analysis and improvements
- [x] Apply architecture decisions (D011-D016)
- [x] Update all project files
- [x] Create .ai/ directory structure
- [x] Move all project files to .ai/

### Phase 2: Data Layer
- [x] Define BaseDatasetLoader interface
- [x] Implement JSON dataset loader
- [x] Implement JSONL dataset loader
- [x] Implement CSV dataset loader
- [x] Implement HuggingFace dataset loader
- [x] Implement PDF dataset loader (pypdf, optional `pdf` extra)
- [x] Create dataset validation (Pydantic models)
- [x] Implement dataset schema enforcement
- [x] Write unit tests for all loaders

### Phase 3: Metrics System
- [x] Define BaseMetric interface
- [x] Create MetricResult model
- [x] Implement retrieval metrics:
  - [x] Context Precision
  - [x] Context Recall
  - [x] Recall@K
  - [x] Precision@K
  - [x] Hit Rate
  - [x] Mean Reciprocal Rank (MRR)
  - [x] NDCG
- [x] Implement generation metrics:
  - [x] Faithfulness (Ragas integration stub)
  - [x] Answer Relevancy (Ragas integration stub)
  - [x] Hallucination Detection (DeepEval integration stub)
  - [x] Semantic Similarity (Sentence Transformers)
  - [x] Exact Match
  - [x] F1 Score
  - [x] BLEU (HF Evaluate)
  - [x] ROUGE (HF Evaluate)
  - [x] BERTScore
- [x] Implement performance metrics:
  - [x] Latency tracking
- [x] Implement cost metrics:
  - [x] Token counting
  - [x] Cost estimation
- [x] Write unit tests for all metrics (86 tests)

---

## BLOCKED

*No tasks currently blocked.*

---

## Task Dependencies

```
Phase 1 (Foundation) ✓ COMPLETE
    ↓
Phase 2 (Data Layer) ← depends on Phase 1
    ↓
Phase 3 (Metrics) ← depends on Phase 1
    ↓
Phase 4 (Reports) ← depends on Phase 1
    ↓
Phase 5 (Providers) ← depends on Phase 1
    ↓
Phase 6 (Plugins) ← depends on Phases 2-5
    ↓
Phase 7 (CLI) ← depends on Phases 1-6
    ↓
Phase 8 (Documentation) ← can run in parallel with Phase 7
    ↓
Phase 9 (Corpus Auditor) ← depends on Phase 1 (new module, independent)
    ↓
Phase 10 (LLM-as-Judge) ← depends on Phase 3 (metrics upgrade)
    ↓
Phase 11 (Diagnosis) ← depends on Phase 3 (uses metric results)
    ↓
Phase 12 (Synthetic Data) ← depends on Phase 5 (uses LLM providers)
    ↓
Phase 13 (CI/CD) ← depends on Phases 7, 9-12
```

---

## Notes

- Phase 1 is complete - all foundation work done
- Phases 2-5 can be developed in parallel
- Phase 6 requires interfaces from Phases 2-5
- Phase 7 is complete - CLI works and the evaluation pipeline is now functional
- Phase 8 can start early and run in parallel
- **Phase 9-14 are NEW** — Production-grade RAG evaluation features
- Exception hierarchy is part of Phase 1 (required foundation)
- Core module (engine, pipeline, executor, registry) is part of Phase 1
- CORRECTION: the earlier "all phases complete / 517+ passing" claim was inaccurate;
  the core pipeline was a stub that produced empty results. Fixed 2026-07-10.
- `oaeval run` now retrieves, generates, and scores; offline dry-run via mock providers.
- Phase 9 (Corpus Auditor) is the key differentiator — no existing tool does this
- Phase 10 (LLM-as-Judge) fixes the faithfulness metric weakness
- Phase 11 (Diagnosis) solves the "where did it fail" problem
- Phase 12 (Synthetic Data) solves the "not enough test cases" problem
- Phase 13 (CI/CD) enables regression gating in pipelines
- **Phase 14 is COMPLETE** — TUI removed, CLI-only interface retained

---

## Task Priority Legend

| Priority | Description |
|----------|-------------|
| 🔴 High | Must complete before next phase |
| 🟡 Medium | Important but can wait |
| 🟢 Low | Nice to have, can be deferred |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-07-12 | **TUI REMOVED** — Textual TUI dashboard removed, CLI-only interface retained |
| 2026-07-11 | **Phase 14 COMPLETE** — Hybrid CLI UI implemented (Rich banner, Textual TUI dashboard, 15 tests) |
| 2026-07-11 | **Phase 13 COMPLETE** — CI/CD Integration implemented (pytest plugin, threshold gating, `oaeval test` command) |
| 2026-07-11 | **Phase 12 COMPLETE** — Synthetic Test Data generator implemented (56 tests) |
| 2026-07-11 | Added Phase 14: Hybrid CLI UI (Rich banner + Textual TUI dashboard) |
| 2026-07-11 | Added Phase 9-13: Corpus Auditor, LLM-as-Judge, Diagnosis, Synthetic Data, CI/CD |
| 2026-07-10 | Pipeline stub fixed; mock providers added; recall_at_k/summary/hallucination bugs fixed; config aligned to registry; Phase 7 marked complete |
| 2026-07-08 | Initial TASKS.md created |
| 2026-07-08 | Updated with architecture decisions (D011-D016) |
| 2026-07-08 | Added exception hierarchy to Phase 1 |
| 2026-07-08 | Added core module to Phase 1 |
| 2026-07-08 | Added ARCHITECTURE.md to Phase 1 |
| 2026-07-08 | Created .ai/ directory structure |
| 2026-07-08 | Moved all project files to .ai/ |
| 2026-07-08 | Phase 1 completed - all foundation work done |
| 2026-07-08 | Phase 2 completed - Data Layer implemented |
| 2026-07-08 | Phase 3 completed - Metrics System implemented |
| 2026-07-08 | 136 tests passing (50 existing + 86 new metrics tests) |
| 2026-07-08 | Phase 4 completed - Reports System implemented (78 new tests) |
| 2026-07-08 | Phase 5 completed - Provider Layer implemented (138 new tests) |
| 2026-07-08 | PR #7 created for Phase 5 |
| 2026-07-08 | Phase 6 completed - Plugin System implemented (27 new tests) |
| 2026-07-08 | Created plugin development guide |
| 2026-07-10 | Added PDF dataset loader (PDFDatasetLoader) with pypdf optional dependency |

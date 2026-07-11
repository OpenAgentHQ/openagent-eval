# Development Plan

## Overview

OpenAgent Eval follows a phased development approach. Each phase builds on the previous one, ensuring a solid foundation before adding complexity.

---

## Phase Overview

```
Phase 1:  Foundation ─────────────────────────────────┐
    ↓                                                   │
Phase 2:  Data Layer ─────────────────────────────────┤
    ↓                                                   │
Phase 3:  Metrics ────────────────────────────────────┤
    ↓                                                   │
Phase 4:  Reports ────────────────────────────────────┤
    ↓                                                   │
Phase 5:  Providers ──────────────────────────────────┤
    ↓                                                   │
Phase 6:  Plugin System ──────────────────────────────┤
    ↓                                                   │
Phase 7:  CLI Commands ───────────────────────────────┤
    ↓                                                   │
Phase 8:  Documentation ──────────────────────────────┤
    ↓                                                   │
Phase 9:  Corpus Health Auditor ──────────────────────┤
    ↓                                                   │
Phase 10: Component Diagnosis ────────────────────────┤
    ↓                                                   │
Phase 11: Synthetic Test Data ────────────────────────┤
    ↓                                                   │
Phase 12: Advanced Providers & NLI Metrics ───────────┘
```

---

## Phase 1: Foundation ✅

**Status:** Complete

**Objectives:**

- Initialize project with `uv`
- Create `pyproject.toml` with all dependencies
- Set up directory structure
- Create exception hierarchy
- Implement CLI skeleton with Typer
- Create configuration system (Pydantic v2 + YAML)
- Implement core module (engine, pipeline, executor, registry)
- Set up testing infrastructure
- Set up linting and formatting

**Deliverables:**

- [x] Project structure
- [x] Exception hierarchy
- [x] CLI skeleton
- [x] Configuration system
- [x] Core module
- [x] Testing infrastructure

---

## Phase 2: Data Layer ✅

**Status:** Complete

**Objectives:**

- Define `BaseDatasetLoader` interface
- Implement JSON, JSONL, CSV, HuggingFace loaders
- Create dataset validation (Pydantic models)
- Implement dataset schema enforcement

**Deliverables:**

- [x] Base interface
- [x] JSON loader
- [x] JSONL loader
- [x] CSV loader
- [x] HuggingFace loader
- [x] Validation models

---

## Phase 3: Metrics ✅

**Status:** Complete

**Objectives:**

- Define `BaseMetric` interface
- Create `MetricResult` model
- Implement retrieval metrics
- Implement generation metrics
- Implement classic metrics
- Implement performance and cost metrics

**Deliverables:**

- [x] Base interface
- [x] MetricResult model
- [x] Retrieval metrics (7)
- [x] Generation metrics (9)
- [x] Classic metrics (4)
- [x] Performance metrics (1)
- [x] Cost metrics (1)

---

## Phase 4: Reports ✅

**Status:** Complete

**Objectives:**

- Define `ReportGenerator` interface
- Implement terminal report (Rich)
- Implement Markdown report
- Implement HTML report (Jinja2)
- Implement JSON report
- Create failure analysis reporting
- Implement experiment comparison reports

**Deliverables:**

- [x] Base interface
- [x] Terminal report
- [x] Markdown report
- [x] HTML report
- [x] JSON report
- [x] Failure analysis
- [x] Experiment comparison

---

## Phase 5: Providers ✅

**Status:** Complete

**Objectives:**

- Define `LLMProvider` interface
- Define `Retriever` interface
- Implement LLM adapters (OpenAI, Gemini, Anthropic, Groq, OpenRouter, Ollama)
- Implement Chroma retriever adapter

**Deliverables:**

- [x] LLM interface
- [x] Retriever interface
- [x] OpenAI adapter
- [x] Gemini adapter
- [x] Anthropic adapter
- [x] Groq adapter
- [x] OpenRouter adapter
- [x] Ollama adapter
- [x] Chroma adapter

---

## Phase 6: Plugin System ✅

**Status:** Complete

**Objectives:**

- Design plugin registry
- Implement entry point discovery
- Create plugin loading mechanism
- Write plugin development guide
- Create example custom metric

**Deliverables:**

- [x] Plugin registry
- [x] Entry point discovery
- [x] Plugin loading
- [x] Development guide
- [x] Example plugins

---

## Phase 7: CLI Commands ✅

**Status:** Complete

**Objectives:**

- Implement `oaeval init`
- Implement `oaeval run`
- Implement `oaeval report`
- Implement `oaeval compare`
- Implement `oaeval list`
- Implement `oaeval doctor`
- Implement `oaeval validate`
- Implement `oaeval delete`
- Implement `oaeval diagnose`
- Implement `oaeval audit`
- Implement `oaeval synth`
- Implement shell completion (bash, zsh, fish)
- Write CLI integration tests

**Deliverables:**

- [x] `oaeval init` command (interactive wizard)
- [x] `oaeval run` command (dry-run, metrics override)
- [x] `oaeval report` command
- [x] `oaeval compare` command
- [x] `oaeval list` command (sorting, search filtering)
- [x] `oaeval doctor` command (API connectivity tests)
- [x] `oaeval validate` command
- [x] `oaeval delete` command
- [x] `oaeval diagnose` command
- [x] `oaeval audit` command
- [x] `oaeval synth` command
- [x] Shell completion (bash, zsh, fish)
- [x] Global flags (`--quiet`, `--json`, `--no-color`, `--verbose`)
- [x] Config auto-discovery
- [x] Integration tests

---

## Phase 8: Documentation ✅

**Status:** Complete

**Objectives:**

- Create comprehensive documentation
- Write contributor guidelines
- Create project roadmap
- Initialize changelog

**Deliverables:**

- [x] Vision documentation
- [x] Problem statement
- [x] Product requirements
- [x] Architecture documentation
- [x] Project structure
- [x] CLI specification
- [x] Metric system documentation
- [x] Plugin system documentation
- [x] Coding guidelines
- [x] Development plan
- [x] Future roadmap
- [x] Retriever providers documentation
- [x] Examples
- [x] CONTRIBUTING.md
- [x] ROADMAP.md
- [x] CHANGELOG.md
- [x] CODE_OF_CONDUCT.md
- [x] SECURITY.md
- [x] SUPPORT.md
- [x] DEVELOPMENT.md

---

## Phase 9: Corpus Health Auditor ✅

**Status:** Complete

**Objectives:**

- Build corpus health auditor to scan knowledge bases BEFORE connecting to RAG
- Detect cross-document contradictions
- Detect unmarked obsolescence (stale documents)
- Detect divergent duplicates
- Analyze thematic coverage
- Create `oaeval audit` CLI command
- Generate corpus health reports

**Deliverables:**

- [x] `BaseCorpusAnalyzer` interface
- [x] `ContradictionDetector` — cross-document contradiction detection
- [x] `StalenessDetector` — unmarked obsolescence detection
- [x] `DuplicateDetector` — divergent duplicate detection
- [x] `CoverageAnalyzer` — thematic coverage analysis
- [x] `CorpusAuditor` — orchestrates all analyzers
- [x] `CorpusIssue`, `AuditReport`, `IssueType`, `IssueSeverity` models
- [x] `oaeval audit` CLI command
- [x] Unit tests (test_auditor, test_contradiction, test_staleness, test_models, test_base, test_exceptions)
- [x] Integration tests (test_corpus_audit)

---

## Phase 10: Component Diagnosis ✅

**Status:** Complete

**Objectives:**

- Build blame attribution system to identify WHERE evaluations fail
- Attribute failures to retrieval, generation, or chunking
- Detect 8 failure modes
- Generate actionable recommendations
- Create `oaeval diagnose` CLI command

**Deliverables:**

- [x] `DiagnosisAnalyzer` — orchestrates diagnosis
- [x] `BlameAttribution` — blame attribution engine
- [x] `ChunkingQualityAnalyzer` — chunking quality analysis
- [x] `BlameResult`, `BlameTarget`, `ChunkingIssue`, `ComponentScores` models
- [x] `DiagnosisReport`, `FailureInstance`, `FailureMode` models
- [x] `oaeval diagnose` CLI command
- [x] Unit tests (test_analyzer, test_blame, test_chunking, test_models, test_integration)
- [x] Integration tests

---

## Phase 11: Synthetic Test Data ✅

**Status:** Complete

**Objectives:**

- Build synthetic test data generation from knowledge bases
- Generate questions from documents
- Generate adversarial test cases
- Augment existing datasets
- Create `oaeval synth` CLI command

**Deliverables:**

- [x] `SyntheticDataGenerator` — main generator orchestrator
- [x] `QuestionGenerator` — question generation from documents
- [x] `AdversarialTestCaseGenerator` — adversarial test case generation
- [x] `SyntheticDataset`, `TestCase`, `TestCaseType` models
- [x] `oaeval synth` CLI command
- [x] Unit tests (test_generator, test_question_gen, test_adversarial, test_models, test_integration)

---

## Phase 12: Advanced Providers & NLI Metrics ✅

**Status:** Complete

**Objectives:**

- Expand retriever provider ecosystem beyond Chroma
- Implement NLI-based metrics for more accurate faithfulness/relevancy scoring
- Add embedder abstraction for vector retrievers
- Implement score normalization across backends

**Deliverables:**

- [x] **Retriever Providers (11 total):**
  - [x] ChromaDB
  - [x] Qdrant
  - [x] Pinecone
  - [x] Weaviate
  - [x] FAISS
  - [x] pgvector
  - [x] Elasticsearch
  - [x] BM25 (lexical baseline)
  - [x] HTTP (generic REST)
  - [x] Memory (in-memory vector store)
  - [x] Mock (offline/testing)
- [x] **Embedder Abstraction:**
  - [x] `Embedder` base interface
  - [x] Sentence Transformers embedder
  - [x] Mock embedder
- [x] **Score Normalization:**
  - [x] `normalize_distance`, `minmax_normalize`, `rank_based_normalize` helpers
  - [x] Unified `[0.0, 1.0]` score range across all backends
- [x] **NLI Metrics:**
  - [x] `NLIJudge` — DeBERTa-based NLI scoring
  - [x] `ClaimExtractor` — split answers into atomic claims
  - [x] `EvidenceFinder` — match claims to supporting context via NLI
- [x] **PDF Dataset Loader** — PDF document loading support
- [x] Unit tests (test_factory_retrievers, test_embedders, test_scoring, test_nli)
- [x] Provider-specific tests (test_bm25, test_chroma, test_memory, test_http, etc.)

---

## Future Phases

### Version 2.0: Agent Evaluation

- AI Agent evaluation
- Tool-call evaluation
- Planning evaluation
- Memory evaluation
- Multi-agent evaluation
- Trace analysis

### Version 3.0: Enterprise Features

- CI/CD integration
- GitHub Action
- Cloud synchronization
- Hosted evaluation platform
- Enterprise reporting

---

## Development Principles

1. **Test-Driven Development** - Write tests before code
2. **Incremental Delivery** - Ship working code frequently
3. **Code Review** - All changes reviewed before merge
4. **Documentation** - Update docs with code changes
5. **Backward Compatibility** - Avoid breaking changes
6. **Performance** - Consider performance from the start
7. **Security** - Follow security best practices

---

## Quality Gates

Before completing any phase:

1. All tests passing
2. Code coverage >= 80%
3. No linting errors
4. Type hints on all public APIs
5. Documentation updated
6. Code reviewed
7. PR created and approved

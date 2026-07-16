# Changelog

All notable changes to OpenAgent Eval will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Fixed

- Add consistent `--version` flag to all CLI commands (#125).

---

## [0.4.5] - 2026-07-15

### Added

- **Issue Claim System** — production-ready issue claim workflow replacing broken auto-assign
- **PR Congratulations Workflow** — automated congratulations on merged PRs
- **Reports Output Formats Documentation** — new docs page covering report output formats

### Fixed

- **JSONL Corpus Loading** — JSONL files now load as one document per line in corpus auditor
- **Unused Imports** — removed unused imports across the codebase

### Changed

- **README Rewrite** — professional layout with GitHub badges (Stars, Forks, Contributors)

---

## [0.4.4] - 2026-07-12

### Fixed

- **Synthesis JSON Parsing** — add individual JSON object parsing for malformed responses
- **Synthesis Notebook** — update notebook with v0.4.4 and no hardcoded API key

---

## [0.4.3] - 2026-07-12

### Fixed

- **Synthesis JSON Parsing** — simplify JSON parsing with multi-strategy fallback

---

## [0.4.2] - 2026-07-12

### Fixed

- **Synthesis JSON Parsing** — add regex fallback for JSON parsing in synthesis module

---

## [0.4.1] - 2026-07-12

### Fixed

- **Synthesis JSON Parsing** — improve JSON parsing resilience in question_gen

---

## [0.4.0] - 2026-07-12

### Added

- **Phase 13: CI/CD Integration**
  - CI/CD module with workflow management
  - Unit tests for CI/CD module (35 tests)

- **Phase 14: TUI Redesign (Partial)**
  - Claude Code-inspired TUI components
  - Rich command input with autocomplete
  - Virtual scrolling message list
  - OAEVAL block-style ASCII art banner

### Changed

- **TUI Removal** — removed TUI dashboard, keeping CLI-only interface
- **README Badges** — updated badges and uv.lock dependencies
- **Documentation** — removed all TUI/Textual references

### Fixed

- **ChromaDB Tests** — resolve ChromaDB test mock setup and normalize_distance tests
- **CLI Tests** — fix CLI test assertions and eval workflow audit command

---

## [0.3.0] - 2026-07-11

### Added

- **Phase 7: CLI Commands (Complete)**
  - `oaeval init` — interactive wizard for provider/model selection
  - `oaeval run` — evaluation pipeline with dry-run mode and metrics override
  - `oaeval report` — view evaluation reports
  - `oaeval compare` — compare two experiments
  - `oaeval list` — list evaluations with sorting (date/score/cost) and search filtering
  - `oaeval doctor` — environment check with API connectivity tests
  - `oaeval validate` — config validation without running evaluation
  - `oaeval delete` — remove old reports
  - `oaeval diagnose` — diagnose failures and attribute blame
  - `oaeval audit` — audit corpus health
  - `oaeval synth` — generate synthetic test cases
  - Shell completion for bash, zsh, and fish
  - Global flags: `--quiet`, `--json`, `--no-color`, `--verbose`
  - Config auto-discovery (config.yaml/oaeval.yaml in cwd, OAEVAL_CONFIG env var)

- **Phase 8: Documentation (Complete)**
  - Vision documentation (docs/01_vision.md)
  - Problem statement (docs/02_problem_statement.md)
  - Product requirements (docs/03_product_requirements.md)
  - Architecture documentation (docs/04_architecture.md)
  - Project structure (docs/05_project_structure.md)
  - CLI specification (docs/06_cli_spec.md)
  - Metric system documentation (docs/07_metric_system.md)
  - Plugin system documentation (docs/08_plugin_system.md)
  - Coding guidelines (docs/09_coding_guidelines.md)
  - Development plan (docs/10_development_plan.md)
  - Future roadmap (docs/11_future_roadmap.md)
  - Retriever providers documentation (docs/12_retrievers.md)
  - CONTRIBUTING.md, ROADMAP.md, CHANGELOG.md
  - CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, DEVELOPMENT.md
  - GitHub issue templates (bug report, feature request)
  - GitHub pull request template

- **Phase 9: Corpus Health Auditor**
  - `CorpusAuditor` — orchestrates all corpus health analyzers
  - `ContradictionDetector` — cross-document contradiction detection
  - `StalenessDetector` — unmarked obsolescence detection
  - `DuplicateDetector` — divergent duplicate detection
  - `CoverageAnalyzer` — thematic coverage analysis
  - `CorpusIssue`, `AuditReport`, `IssueType`, `IssueSeverity` models
  - `oaeval audit` CLI command with configurable checks
  - Unit and integration tests

- **Phase 10: Component Diagnosis**
  - `DiagnosisAnalyzer` — orchestrates failure diagnosis
  - `BlameAttribution` — blame attribution engine (retrieval vs generation vs chunking)
  - `ChunkingQualityAnalyzer` — chunking quality analysis
  - 8 failure mode detection
  - Actionable recommendations
  - `BlameResult`, `BlameTarget`, `ChunkingIssue`, `ComponentScores` models
  - `DiagnosisReport`, `FailureInstance`, `FailureMode` models
  - `oaeval diagnose` CLI command
  - Unit and integration tests

- **Phase 11: Synthetic Test Data**
  - `SyntheticDataGenerator` — main generator orchestrator
  - `QuestionGenerator` — question generation from documents
  - `AdversarialTestCaseGenerator` — adversarial test case generation
  - `SyntheticDataset`, `TestCase`, `TestCaseType` models
  - `oaeval synth` CLI command
  - Unit and integration tests

- **Phase 12: Advanced Providers & NLI Metrics**
  - **Retriever Providers (11 total):**
    - ChromaDB, Qdrant, Pinecone, Weaviate, FAISS, pgvector
    - Elasticsearch, BM25 (lexical), HTTP (generic REST), Memory (in-memory), Mock
  - **Embedder Abstraction:**
    - `Embedder` base interface
    - Sentence Transformers embedder (all-MiniLM-L6-v2)
    - Mock embedder for offline testing
  - **Score Normalization:**
    - `normalize_distance`, `minmax_normalize`, `rank_based_normalize` helpers
    - Unified `[0.0, 1.0]` score range across all backends
  - **NLI Metrics:**
    - `NLIJudge` — DeBERTa-based NLI scoring
    - `ClaimExtractor` — split answers into atomic claims
    - `EvidenceFinder` — match claims to supporting context via NLI
  - **PDF Dataset Loader** — PDF document loading support
  - Provider factory with lazy loading
  - Unit tests for all providers and embedders

---

## [0.2.0] - 2026-07-10

### Added

- **CLI Improvements**
  - Global error handler with friendly Rich output for `OpenAgentEvalError` subclasses
  - Global flags: `--quiet`, `--json`, `--no-color`, `--verbose`
  - Config auto-discovery (config.yaml/oaeval.yaml in cwd, OAEVAL_CONFIG env var)
  - New `validate` command to check config without running evaluation
  - Dry-run mode (`--dry-run` flag on run command)
  - Shell completion support for bash, zsh, and fish
  - Enhanced `doctor` command with API connectivity tests
  - New `delete` command for removing old reports
  - Enhanced `list` command with sorting (date/score/cost) and search filtering
  - Enhanced `init` command with interactive wizard for provider/model selection
  - JSON output support for all commands (`--json` flag)

- Phase 8: Documentation
  - Vision documentation
  - Problem statement
  - Product requirements
  - Architecture documentation
  - Project structure
  - CLI specification (updated with new commands and features)
  - Metric system documentation
  - Plugin system documentation
  - Coding guidelines
  - Development plan
  - Future roadmap
  - Examples
  - CONTRIBUTING.md
  - ROADMAP.md
  - CHANGELOG.md
- CONTRIBUTING.md with contribution guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant v2.0)
- SECURITY.md with vulnerability reporting process
- SUPPORT.md with support channels
- DEVELOPMENT.md with development guide
- GitHub issue templates (bug report, feature request)
- GitHub pull request template

### Changed

- Improved README.md with badges and comprehensive documentation
- Updated CLI documentation with new commands and features
- Enhanced `init` command with interactive wizard
- Enhanced `run` command with dry-run mode and metrics override
- Enhanced `doctor` command with API connectivity tests
- Enhanced `list` command with sorting and filtering
- Improved error handling across all CLI commands

### Fixed

- Fixed error chaining in CLI commands (raise from)
- Fixed unused imports and variables

---

## [0.1.0] - 2026-07-08

### Added

- **Phase 1: Foundation**
  - Project initialization with `uv`
  - `pyproject.toml` with all dependencies
  - Directory structure (`openagent_eval/*`)
  - Exception hierarchy (`exceptions/*`)
  - CLI skeleton with Typer
  - Configuration system (Pydantic v2 + YAML)
  - Core module (`engine.py`, `pipeline.py`, `executor.py`, `registry.py`)
  - Testing infrastructure (pytest)
  - Linting and formatting (ruff)

- **Phase 2: Data Layer**
  - `BaseDatasetLoader` interface
  - JSON dataset loader
  - JSONL dataset loader
  - CSV dataset loader
  - HuggingFace dataset loader
  - Dataset validation (Pydantic models)
  - Dataset schema enforcement

- **Phase 3: Metrics System**
  - `BaseMetric` interface
  - `MetricResult` model
  - Retrieval metrics:
    - Context Precision
    - Context Recall
    - Recall@K
    - Precision@K
    - Hit Rate
    - Mean Reciprocal Rank (MRR)
    - NDCG
  - Generation metrics:
    - Faithfulness (Ragas integration)
    - Answer Relevancy (Ragas integration)
    - Hallucination Detection (DeepEval integration)
    - Semantic Similarity (Sentence Transformers)
    - Exact Match
    - F1 Score
    - BLEU (HF Evaluate)
    - ROUGE (HF Evaluate)
    - BERTScore
  - Performance metrics:
    - Latency tracking
  - Cost metrics:
    - Token counting
    - Cost estimation
  - Unit tests (86 tests)

- **Phase 4: Reports System**
  - `ReportGenerator` interface
  - Terminal report (Rich)
  - Markdown report
  - HTML report (Jinja2)
  - JSON report
  - Failure analysis reporting
  - Experiment comparison reports
  - Unit tests (78 tests)

- **Phase 5: Providers**
  - `LLMProvider` interface
  - `Retriever` interface
  - OpenAI adapter
  - Gemini adapter
  - Anthropic adapter
  - Groq adapter
  - OpenRouter adapter
  - Ollama adapter (token tracking only)
  - Chroma retriever adapter
  - Unit tests (138 tests)

- **Phase 6: Plugin System**
  - Plugin registry
  - Entry point discovery
  - Plugin loading mechanism
  - Plugin development guide
  - Example custom metric plugin
  - Unit tests (27 tests)

- Initial release
- CLI interface with Typer (`oaeval init`, `run`, `report`, `compare`, `list`, `doctor`)
- SDK for programmatic usage
- Configuration system with Pydantic models and YAML support
- Plugin architecture for custom metrics, providers, and report generators
- Retrieval metrics: Context Precision, Context Recall, Recall@K, Precision@K, Hit Rate, MRR, NDCG
- Generation metrics: Faithfulness, Answer Relevancy, Hallucination Detection, Semantic Similarity, Exact Match, F1, BLEU, ROUGE, BERTScore
- Performance metrics: Embedding latency, Retrieval latency, LLM latency, Total latency
- Cost metrics: Token counting, Cost estimation
- LLM providers: OpenAI, Google Gemini, Anthropic, Groq, OpenRouter, Ollama
- Retriever providers: Chroma
- Report formats: Terminal, Markdown, HTML, JSON
- Dataset loaders for JSON and CSV formats
- Custom exception hierarchy
- Comprehensive test suite with pytest

### Technical Details

- Python 3.11+ required
- Built with Typer + Rich for CLI
- Pydantic v2 for validation
- asyncio for parallel execution
- Plugin-based architecture
- 517+ tests passing

---

## [0.0.1] - 2026-07-08

### Added

- Initial project structure
- Basic documentation
- Architecture decisions (D001-D016)

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible new functionality
- **PATCH**: Backward-compatible bug fixes

## Links

[Unreleased]: https://github.com/openagenthq/openagent-eval/compare/v0.4.5...HEAD
[0.4.5]: https://github.com/openagenthq/openagent-eval/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/openagenthq/openagent-eval/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/openagenthq/openagent-eval/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/openagenthq/openagent-eval/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/openagenthq/openagent-eval/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/openagenthq/openagent-eval/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/openagenthq/openagent-eval/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/openagenthq/openagent-eval/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/openagenthq/openagent-eval/releases/tag/v0.1.0

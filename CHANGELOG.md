# Changelog

All notable changes to OpenAgent Eval will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]
### Added
- Added `oaeval doctor` warnings for configured providers whose optional extras are not installed.
- Created `scripts/changelog_validator.py` to automatically verify Keep a Changelog formatting.
- Added a section to `CONTRIBUTING.md` documenting the changelog update process for future contributors.
- Added `EvalPortReport` (`openagent_eval/reports/evalport.py`), a `ReportGenerator` that exports an `EvaluationReport` as an [EvalPort](https://github.com/adhabnr-ux/evalport) `ResultSet` for interop with other EvalPort-speaking evaluation tools; install with the new optional `evalport` extra (design agreed in Discussion #296).

---

## [0.4.10] - 2026-08-24

### Fixed

- **Report Version Metadata** — use package version in report metadata instead of hardcoded value (#292)
- **CLI Test Command** — add missing `EvaluationResult` import in CI/CD test command
- **Exception Chaining** — add proper `raise ... from` in exception handlers across codebase
- **pgvector Availability Check** — use `importlib.util.find_spec` for psycopg availability check

### Changed

- **Opencode Model** — update opencode model to MiMo V2.5 Free (#293)
- **Opencode Model ID** — correct MiMo model ID format in opencode workflow (#294)

### Testing

- **Audit Path Test** — fix path assertion in audit error message test for Windows path wrapping
- **CLI Help Test** — fix encoding issue in pytest-import regression test on Windows

---

## [0.4.9] - 2026-08-17

### Added

- **EvaluationReport Type Hints** — add `EvaluationReport` type hints to report generators for better IDE support (#239)
- **Common Evaluation Workflow Examples** — add example workflows documentation for common RAG evaluation patterns (#289)
- **Config Reference Documentation** — new `config-reference.md` documenting the full YAML schema
- **CLI Exit Code Documentation** — document CLI exit codes for programmatic usage (#107)
- **LLM API Key Setup Guide** — new docs page for configuring API keys
- **Plugin Development Guide** — comprehensive guide for building custom plugins
- **End-to-End Tutorial** — tutorial with free APIs and local embeddings
- **Colab Tutorial Notebook** — zero-setup Colab tutorial for quick onboarding

### Fixed

- **ROUGE Recall Fallback** — compute occurrence-based ROUGE recall fallback when standard ROUGE fails (#288)
- **LatencyMetric None Crash** — handle `None` latency_ms in `LatencyMetric` without crashing (#286)
- **Exact Match Whitespace** — normalize internal whitespace in exact match (#281)
- **Falsy Exception Details** — record explicitly-supplied falsy details instead of dropping them (#280)
- **Short Answer False Positives** — require low relevancy to flag short answers as off-topic (#66)
- **Silent Retrieval Failures** — surface retrieval failures in logs and run errors (#256)
- **CICD Gate Metrics Summary** — populate `metrics_summary` in `run_evaluation` gate summary (#228)
- **CICD Event Loop** — make `run_evaluation` independent of event-loop policy state
- **CICD Lazy pytest** — lazy-load pytest in plugin.py (#227)
- **Config SecretStr** — store `LLMConfig.api_key` as `SecretStr` for security
- **Config Exports** — export `CorpusConfig`, `ReportConfig`, and `OutputFormat`
- **Pipeline Ground Truth** — detect `ground_truth_contexts` support for backward compatibility
- **Pipeline Retriever Contract** — pass `ground_truth_contexts` through public retriever contract
- **Pipeline LLM Model** — read LLM model through public `model_name` contract
- **CLI Config Loading** — load config exactly once in `run_command`
- **Executor Async** — async `run_in_thread`, cancel siblings on timeout, lazy thread pool
- **Corpus Unknown Checks** — raise `CorpusValidationError` for unknown audit checks
- **Corpus Timestamp UTC** — make `AuditReport.timestamp` UTC-aware
- **Corpus Concurrency** — limit contradiction detector concurrency
- **Diagnosis Content Gaps** — use whole-word matching for content gaps
- **NDCG Off-by-One** — fix off-by-one DCG position discount (#223)
- **JSONL max_documents** — enforce `max_documents` cumulatively across `.jsonl` files (#224)
- **Synthesis Config Migration** — fix legacy config migration bugs in `loader.py`

### Changed

- **Retrieval Failure Surfacing** — make retrieval-failure surfacing log-only for non-critical cases (#256)
- **Synthesis Response Parser** — use shared response parser in `question_gen` and `adversarial`

### Removed

- **Dead Executor Methods** — remove `Executor.execute_parallel()` and `Executor.execute_sequential()`, which had no production callers (the pipeline uses `Executor.gather()`); their only in-tree references were two dedicated unit tests (#52)

### Documentation

- **MkDocs Theme Redesign** — dark-first, org brand, hero + cards (#239)
- **README Banner** — professional README banner for social sharing (#236)
- **README Rewrite** — community-focused README with OpenAgentHQ branding
- **Notebook Refresh** — refresh notebooks to v0.4.8 and wire tutorials into docs site
- **CLI Wizard Screenshot** — add interactive CLI wizard screenshot to README
- **ExactMatch Docs** — align documentation with actual behavior

### Testing

- **Diagnose Command Tests** — add unit tests for diagnose command
- **CICD Regression Tests** — strengthen regression tests for gate metrics_summary (#228)
- **Synthesis Parser Tests** — add characterization tests for question_gen and adversarial parsers
- **Short-Answer Regression Tests** — regression tests for short-answer false positives (#66)
- **Retrieval Failure Tests** — regression test for silent retrieval-failure swallow (#256)
- **Corpus Concurrency Tests** — strengthen concurrency limit assertion
- **Exception Falsy Tests** — cover falsy original errors

### Contributors

- ❤️ @Nitjsefnie
- ❤️ @Nithyaviswak
- ❤️ @PrinceThummar011
- ❤️ @himanshu231204

---

## [0.4.8] - 2026-07-24

### Fixed

- **Missing Reports Subpackage in sdist** — anchor `reports/` in `.gitignore` to root-only and add explicit sdist include for `openagent_eval/reports/`; 0.4.7 wheel/sdist shipped without the `reports` subpackage, making all CLI commands fail at import (#233)

---

## [0.4.7] - 2026-07-24

### Fixed

- **Mock Provider Regression Test** — add regression test verifying that `--llm-provider mock` never falls back to `OpenAIProvider` (#40)
- **Chunking Metadata Usage** — `ChunkingQualityAnalyzer.analyze()` now uses the `metadata` parameter to perform more informed analysis: checks chunk size deviation from expected, detects excessive character overlap, and adjusts empty chunk thresholds (#65)

---

## [0.4.6] - 2026-07-17

### Added

- **Retriever Settings Validation** — validate retriever settings keys to catch typos early (#172)
- **Standardized Provider Errors** — standardize provider error `__str__` format for better debugging (#167)
- **Environment Variables Reference** — new docs page covering all environment variables (#176)
- **Package Release Rules** — add release workflow documentation to AGENT.md (#183)

### Fixed

- **pgvector Async Connection** — use async psycopg connection in pgvector retriever (#182)
- **Report max_examples Respect** — HTML and JSON generators now respect `ReportConfig.max_examples` (#181)
- **Synthesis Duplicate Functions** — extract duplicate inner generation functions (#180)
- **Synthesis Parallel Generation** — parallelize adversarial test case generation with `asyncio.gather` (#178)
- **Synthesis Premature Return** — fix Strategy 0 in `_parse_response` returning prematurely (#175)
- **Synthesis Corpus Errors** — `_read_corpus` no longer silently swallows file reading errors (#149)
- **CLI Version Flag** — add consistent `--version` flag to all CLI commands (#157)
- **CLI Export Commands** — export all CLI commands (#147)
- **CLI Dry-run Warning** — interpolate timeout in dry-run warning (#145)
- **CLI Mock Provider** — use configured provider for synth (#148)
- **Progress Bar Reset** — fix progress bar reset to 1/total_items on completion (#162)
- **Context Variable Shadowing** — rename ctx variables to avoid shadowing CLIContext and click.Context (#153, #162)
- **Report max_examples Hardcoded** — use `ReportConfig.max_examples` instead of hardcoded limits (#161)
- **Comparison Winner Logic** — use common metrics only in comparison report (#159)
- **Dataset Input Validation** — add input validation for dataset path with helpful error message (#158)
- **Non-ASCII Keywords** — support non-ASCII characters in content gap analysis (#156)
- **Failure Analysis Metrics** — pass `metric_scores` from error entries in `_compute_failure_analysis` (#155)
- **Synthesis Curly Braces** — escape curly braces in context before `str.format()` in synthesis (#152)
- **Report Config Validation** — validate config key in `ReportManager.reconstruct()` (#150)
- **Metrics Zero Timeout** — preserve zero timeout details (#146)
- **Missing Command Imports** — add missing imports and `__all__` entries for 6 commands (#168)
- **Orphan LLMResponse** — remove orphan LLMResponse construction in anthropic generate() (#166)
- **Dead Regex** — remove dead `_SIMPLE_PATTERNS` regex (#165)
- **Corpus Naive Timestamps** — normalize naive staleness timestamps (#170)
- **Configuration Validation** — enhance error messages for missing required config fields (#140)

### Changed

- **Env-var Documentation** — correct env-var and config claims in docs (#179)

### Documentation

- **Quickstart Guide** — add QUICKSTART.md for coding agents (#144)
- **Context Files Compressed** — compress context files to <100 lines for coding agent efficiency (#142)
- **AI Files Reorganized** — move .ai/ files to root, add INSTRUCTIONS.md writing rules (#139)

### Testing

- **Synth CLI Unit Tests** — add unit tests for the synth CLI command (#174)
- **Report Edge Cases** — cover `ReportManager.reconstruct()` edge cases (#173)
- **Pipeline Integration Test** — add full-pipeline e2e test with mock providers (#171)

### Internal

- **Ignore Local Configs** — ignore local config files in git (#143)
- **Remove Local Artifacts** — remove local artifacts from tracking (#141)

### Contributors

- ❤️ @himanshu231204
- ❤️ @Nitjsefnie
- ❤️ @fazalpsinfo-cmyk
- ❤️ @Sanjays2402
- ❤️ @lesbass
- ❤️ @PrinceThummar011
- ❤️ @Silvren
- ❤️ @hkJerryLeung
- ❤️ @1-gokul

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

[Unreleased]: https://github.com/openagenthq/openagent-eval/compare/v0.4.10...HEAD
[0.4.10]: https://github.com/openagenthq/openagent-eval/compare/v0.4.9...v0.4.10
[0.4.9]: https://github.com/openagenthq/openagent-eval/compare/v0.4.8...v0.4.9
[0.4.8]: https://github.com/openagenthq/openagent-eval/compare/v0.4.7...v0.4.8
[0.4.7]: https://github.com/openagenthq/openagent-eval/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/openagenthq/openagent-eval/compare/v0.4.5...v0.4.6
[0.4.5]: https://github.com/openagenthq/openagent-eval/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/openagenthq/openagent-eval/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/openagenthq/openagent-eval/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/openagenthq/openagent-eval/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/openagenthq/openagent-eval/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/openagenthq/openagent-eval/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/openagenthq/openagent-eval/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/openagenthq/openagent-eval/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/openagenthq/openagent-eval/releases/tag/v0.1.0

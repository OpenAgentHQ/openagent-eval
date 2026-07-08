# Changelog

All notable changes to OpenAgent Eval will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- Phase 8: Documentation
  - Vision documentation
  - Problem statement
  - Product requirements
  - Architecture documentation
  - Project structure
  - CLI specification
  - Metric system documentation
  - Plugin system documentation
  - Coding guidelines
  - Development plan
  - Future roadmap
  - Examples
  - CONTRIBUTING.md
  - ROADMAP.md
  - CHANGELOG.md

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

This project follows [Semantic Versioning](https://semver.org/).

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality
- **PATCH** version for backwards-compatible bug fixes

---

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/OpenAgentHQ/openagent-eval/issues)
- **Discord:** [Join our community](https://discord.gg/openagent-eval)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

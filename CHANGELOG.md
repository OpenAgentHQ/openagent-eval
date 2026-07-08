# Changelog

All notable changes to OpenAgent Eval will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- CONTRIBUTING.md with contribution guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant v2.0)
- SECURITY.md with vulnerability reporting process
- SUPPORT.md with support channels
- DEVELOPMENT.md with development guide
- GitHub issue templates (bug report, feature request)
- GitHub pull request template

### Changed

- Improved README.md with badges and comprehensive documentation

### Fixed

- (No fixes yet)

## [0.1.0] - 2026-07-08

### Added

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

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible new functionality
- **PATCH**: Backward-compatible bug fixes

## Links

[Unreleased]: https://github.com/openagenthq/openagent-eval/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/openagenthq/openagent-eval/releases/tag/v0.1.0

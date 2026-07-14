# AGENT.md - Engineering Handbook

> Your engineering handbook for OpenAgent Eval.
> This is your single source of truth for coding standards, architecture rules, and execution constraints.

---

## Project Identity

| Field | Value |
|-------|-------|
| **Project** | OpenAgent Eval |
| **Repository** | openagent-eval |
| **Package** | openagent_eval |
| **CLI** | oaeval |
| **Purpose** | Open-source CLI framework for evaluating RAG systems and AI Agents |
| **Phase** | v0.3.0 - Phases 1-14 Complete |
| **Status** | Active Development |
| **Source of Truth** | PROJECT.md |

---

## Naming Convention (CRITICAL)

| Context | Name | Example |
|---------|------|---------|
| Repository | `openagent-eval` | `git clone https://github.com/org/openagent-eval` |
| Python package | `openagent_eval` | `from openagent_eval import Evaluator` |
| CLI command | `oaeval` | `oaeval run config.yaml` |
| Documentation | Always use `oaeval` | `oaeval init`, `oaeval doctor` |

**NEVER mix CLI names.** Always use `oaeval` in documentation and commands.

---

## Core Principles

### 1. Framework Agnostic

- Do NOT build on LangChain, LlamaIndex, or Haystack
- Build as a pure Python framework with adapters
- Users should bring their own frameworks, not be forced into one

### 2. CLI-First, SDK-Second

- CLI (`oaeval` via Typer + Rich) is the primary interface
- SDK (`from openagent_eval import Evaluator`) must also work
- Single codebase, two entry points

### 3. Plugin-Based Everything

- Metrics: Implement `BaseMetric`
- Providers: Implement `LLMProvider`
- Retrievers: Implement `Retriever`
- Dataset Loaders: Implement `DatasetLoader`
- Report Generators: Implement `ReportGenerator`

### 4. Local-First

- No cloud services required
- No dashboards
- No authentication
- Everything runs from the command line

---

## Tech Stack (Mandatory)

| Component | Technology | Reason |
|-----------|------------|--------|
| Language | Python 3.11+ | AI ecosystem standard |
| Package Manager | uv | Fast, modern dependency management |
| CLI | Typer | Clean, production-ready CLI |
| Terminal UI | Rich | Beautiful progress bars, tables, colors |
| Async | asyncio | Parallel evaluation for speed |
| Validation | Pydantic v2 | Strong typing and config validation |
| Config | YAML (PyYAML) | Simple configuration |
| Logging | Loguru | Better developer experience |
| Testing | pytest | Industry standard |
| Reports | Jinja2 + Markdown | HTML and Markdown report generation |
| Plugin System | Python entry points / registry | Extensible architecture |

---

## Architecture Rules

### Directory Structure (Authoritative)

```
openagent-eval/
├── openagent_eval/
│   ├── cli/              # CLI commands (Typer)
│   │   ├── main.py       # Main CLI entry point
│   │   ├── context.py    # CLI context
│   │   └── commands/     # Individual commands
│   │       ├── init.py
│   │       ├── run.py
│   │       ├── report.py
│   │       ├── compare.py
│   │       ├── list_evaluations.py
│   │       ├── doctor.py
│   │       ├── validate.py
│   │       ├── delete.py
│   │       ├── diagnose.py
│   │       ├── audit.py
│   │       └── synth.py
│   ├── config/           # Configuration management
│   ├── core/             # Core orchestration layer
│   │   ├── engine.py     # Main evaluation engine
│   │   ├── pipeline.py   # Evaluation pipeline
│   │   ├── executor.py   # Task execution
│   │   └── registry.py   # Plugin/component registry
│   ├── datasets/         # Dataset loaders (JSON, JSONL, CSV, HuggingFace, PDF)
│   ├── metrics/          # All evaluation metrics
│   │   ├── retrieval/    # Context precision, recall, MRR, NDCG, hit rate
│   │   ├── generation/   # Faithfulness, relevancy, hallucination, BLEU, ROUGE, F1
│   │   ├── nli/          # NLI-based scoring (DeBERTa)
│   │   ├── performance/  # Latency tracking
│   │   └── cost/         # Token counting
│   ├── corpus/           # Corpus Health Auditor
│   │   ├── auditor.py    # CorpusAuditor orchestrator
│   │   ├── contradiction.py  # Cross-document contradiction detection
│   │   ├── staleness.py      # Outdated document detection
│   │   ├── duplicates.py     # Divergent duplicate detection
│   │   └── coverage.py       # Thematic coverage analysis
│   ├── diagnosis/        # Component Diagnosis
│   │   ├── analyzer.py   # DiagnosisAnalyzer
│   │   ├── blame.py      # BlameAttribution
│   │   ├── chunking.py   # ChunkingQualityAnalyzer
│   │   └── models.py     # DiagnosisReport, FailureMode
│   ├── synthesis/        # Synthetic Test Data
│   │   ├── generator.py  # SyntheticDataGenerator
│   │   ├── question_gen.py   # QuestionGenerator
│   │   ├── adversarial.py    # AdversarialTestCaseGenerator
│   │   └── models.py     # SyntheticDataset, TestCase
│   ├── providers/        # LLM/Retriever adapters
│   │   ├── factory.py    # Provider factory with lazy loading
│   │   ├── llm/          # OpenAI, Gemini, Anthropic, Groq, OpenRouter, Ollama
│   │   ├── retrievers/   # 11 providers: Chroma, Qdrant, Pinecone, Weaviate, FAISS, pgvector, Elasticsearch, BM25, HTTP, Memory, Mock
│   │   └── embedders/    # Sentence Transformers, Mock
│   ├── reports/          # Report generation (Terminal, Markdown, HTML, JSON)
│   ├── plugins/          # External extensions
│   ├── exceptions/       # Custom exception hierarchy
│   ├── types/            # Shared type definitions
│   └── utils/            # Shared utilities
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── sample_data/
├── docs/                 # 12 numbered design docs + provider docs + examples
├── pyproject.toml
├── README.md
├── ROADMAP.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `cli/` | Parse commands, delegate to core, display output |
| `config/` | Load, validate, and manage YAML configuration |
| `core/` | Orchestration layer (engine, pipeline, executor, registry) |
| `datasets/` | Load evaluation data from JSON, JSONL, CSV, HuggingFace, PDF |
| `metrics/` | Implement BaseMetric for all evaluation metrics |
| `metrics/nli/` | NLI-based scoring (DeBERTa faithfulness, relevancy) |
| `corpus/` | Corpus Health Auditor (contradiction, staleness, duplicates, coverage) |
| `diagnosis/` | Component Diagnosis (blame attribution, failure modes) |
| `synthesis/` | Synthetic Test Data (question generation, adversarial cases) |
| `providers/` | Adapter pattern for LLMs (6) and Retrievers (11) + Embedders |
| `reports/` | Generate Markdown, HTML, JSON, Terminal reports |
| `plugins/` | User extensions via entry points |
| `exceptions/` | Custom exception hierarchy |
| `types/` | Shared type definitions and protocols |
| `utils/` | Shared utilities, logging, helpers |

### Core Module Responsibilities

| File | Responsibility |
|------|----------------|
| `engine.py` | Main evaluation engine - orchestrates the entire evaluation |
| `pipeline.py` | Evaluation pipeline - Dataset → Retriever → LLM → Metrics |
| `executor.py` | Task execution - manages async execution and parallelism |
| `registry.py` | Plugin/component registry - discovers and manages plugins |

### Dependency Rules

1. `cli/` depends on everything, nothing depends on `cli/`
2. `core/` depends on `datasets/`, `metrics/`, `providers/`, `reports/`
3. `metrics/` depends on nothing except `utils/` and `types/`
4. `providers/` depends on nothing except `utils/` and `types/`
5. `reports/` depends on nothing except `utils/` and `types/`
6. `exceptions/` depends on nothing
7. `types/` depends on nothing
8. No circular dependencies

---

## Exception Hierarchy (CRITICAL)

All custom exceptions MUST inherit from `OpenAgentEvalError`.

```
exceptions/
├── __init__.py
├── base.py          # OpenAgentEvalError (base class)
├── config.py        # Configuration errors
├── dataset.py       # Dataset loading/validation errors
├── metric.py        # Metric execution errors
├── provider.py      # Provider connection/execution errors
├── plugin.py        # Plugin discovery/registration errors
└── cli.py           # CLI-specific errors
```

### Exception Rules

- NEVER raise generic `Exception` in production code
- ALWAYS use meaningful error messages
- ALWAYS include context in error messages
- Use specific exception types for each module

### Example

```python
# WRONG
raise Exception("Invalid config")

# CORRECT
from openagent_eval.exceptions import ConfigurationError

raise ConfigurationError(
    message="Missing required field 'llm.provider'",
    config_path="config.yaml",
    field="llm.provider"
)
```

---

## Testing Strategy (CRITICAL)

### Test Structure

```
tests/
├── unit/
│   ├── test_cli/
│   ├── test_config/
│   ├── test_core/
│   ├── test_datasets/
│   ├── test_metrics/
│   ├── test_providers/
│   ├── test_reports/
│   └── test_plugins/
├── integration/
│   ├── test_pipeline/
│   └── test_cli_integration/
├── fixtures/
│   └── conftest.py
└── sample_data/
    ├── valid_dataset.json
    ├── invalid_dataset.json
    └── config.yaml
```

### Testing Rules

- pytest for all tests
- Unit tests for every module
- Integration tests for pipeline
- Test coverage target: 80%+
- Mock ALL external dependencies (LLMs, APIs)
- Use fixtures for common test data
- Test both success and failure paths
- Test edge cases and error handling

---

## Coding Standards

### Language Requirements

- Python 3.11+ required
- Type hints on ALL public functions
- Use `typing` module for complex types
- Pydantic v2 for data models and validation

### Code Quality Rules

- No global variables
- Functions under 50 lines
- Single responsibility per module
- Dependency injection for all external dependencies
- Follow SOLID principles
- No business logic in CLI layer
- No tight coupling between metrics, providers, and report generators

### Naming Conventions

- `snake_case` for variables and functions
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Module files: `snake_case.py`

### Async Rules

- Use `asyncio` for parallel evaluation
- Provider adapters should support async operations
- Pipeline execution should be async-compatible

---

## Configuration System

### Requirements

- YAML format
- Environment variable support
- Pydantic validation
- Default values
- Helpful validation errors

### Required Fields

- `dataset`: Path to dataset file
- `llm.provider`: LLM provider name
- `llm.model`: Model identifier

### Optional Fields

- `metrics`: List of metrics (default: all)
- `output`: Report format (default: terminal)
- `output_dir`: Output directory (default: ./reports)

### Environment Variables

- `OPENAI_API_KEY`: Required for OpenAI
- `GEMINI_API_KEY`: Required for Gemini
- `ANTHROPIC_API_KEY`: Required for Anthropic
- `GROQ_API_KEY`: Required for Groq

---

## Implementation Constraints

### v1 Scope (RAG Evaluation Only)

**Include:**
- Retrieval evaluation metrics
- Generation evaluation metrics
- Performance tracking (latency)
- Cost tracking (tokens, estimated cost)
- Report generation (Terminal, Markdown, HTML, JSON)
- Experiment comparison
- Failure analysis

**Exclude (Future Versions):**
- AI Agent evaluation
- Tool-call evaluation
- Planning evaluation
- Memory evaluation
- Multi-agent evaluation
- Trace analysis
- Web dashboard
- User authentication
- Cloud storage
- Team collaboration
- Hosted evaluation service
- Fine-tuning workflows
- RLHF
- Human annotation interface

### Supported Input Formats

- JSON
- JSONL
- CSV
- Hugging Face datasets

### Dataset Schema

```json
{
  "question": "...",
  "ground_truth": "...",
  "context": "...",
  "metadata": {}
}
```

Note: `ground_truth` may be optional depending on metrics.

---

## Evaluation Pipeline

```
Dataset
    ↓
Question
    ↓
Retriever
    ↓
Retrieved Documents
    ↓
LLM
    ↓
Generated Answer
    ↓
Evaluation Engine
    ↓
Metrics
    ↓
Reports
```

---

## Metrics System

### Metric Interface

```python
class BaseMetric:
    name: str
    description: str

    def evaluate(self, ...) -> MetricResult:
        ...

class MetricResult:
    score: float
    reason: str
    metadata: dict
```

### Phase 1 Metrics

**Retrieval:**
- Context Precision
- Context Recall
- Recall@K
- Precision@K
- Hit Rate
- Mean Reciprocal Rank (MRR)
- NDCG

**Generation:**
- Faithfulness (Ragas)
- Answer Relevancy (Ragas)
- Hallucination Detection (DeepEval)
- Semantic Similarity (Sentence Transformers)
- Exact Match (HF Evaluate)
- F1 Score (HF Evaluate)
- BLEU (HF Evaluate)
- ROUGE (HF Evaluate)
- BERTScore

**Performance:**
- Embedding latency
- Retrieval latency
- LLM latency
- Total latency

**Cost:**
- Prompt tokens
- Completion tokens
- Total tokens
- Estimated cost
- Cost per request
- Total experiment cost

### Supported LLM Providers

- OpenAI
- Gemini
- Anthropic
- Groq
- OpenRouter
- Ollama (token tracking only)

---

## Report Formats

1. **Terminal summary** - Quick overview with Rich
2. **Markdown** - Detailed report in Markdown
3. **HTML** - Styled report via Jinja2
4. **JSON** - Machine-readable output

---

## Failure Analysis Categories

- Wrong retrieval
- Missing context
- Hallucinated answer
- Prompt issue
- Low similarity
- Empty retrieval
- Slow response
- High token usage

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `oaeval init` | Create configuration (interactive wizard) |
| `oaeval run config.yaml` | Run evaluation (dry-run, metrics override) |
| `oaeval report latest` | View latest report |
| `oaeval compare exp1 exp2` | Compare experiments |
| `oaeval list` | List previous evaluations (sorting, search) |
| `oaeval doctor` | Check environment and dependencies (API tests) |
| `oaeval validate config.yaml` | Validate configuration |
| `oaeval delete <id>` | Delete evaluation reports |
| `oaeval audit --corpus ./kb/` | Audit corpus for contradictions, staleness |
| `oaeval diagnose --report report.json` | Diagnose failures and attribute blame |
| `oaeval synth --corpus ./kb/ --count 100` | Generate synthetic test cases |
| `oaeval test config.yaml -t faithfulness:gte:0.8` | Run evaluation as CI/CD test with threshold gating |
| `oaeval completion <shell>` | Generate shell completion (bash, zsh, fish) |

---

## Development Phases

### Phase 1: Foundation ✅
- Project setup (uv, pyproject.toml)
- Directory structure
- Exception hierarchy
- CLI skeleton (Typer)
- Configuration system (Pydantic v2 + YAML)
- Basic pipeline architecture

### Phase 2: Data Layer ✅
- Dataset loaders (JSON, JSONL, CSV, HuggingFace)
- Dataset validation
- Data schema enforcement

### Phase 3: Metrics ✅
- BaseMetric interface
- Retrieval metrics (precision, recall, MRR, NDCG, etc.)
- Generation metrics (faithfulness, relevancy, hallucination)
- Classic metrics (BLEU, ROUGE, F1, Exact Match)

### Phase 4: Reports ✅
- Report generator interface
- Terminal report (Rich)
- Markdown report
- HTML report (Jinja2)
- JSON report

### Phase 5: Providers ✅
- LLM provider interface
- OpenAI, Gemini, Anthropic, Groq, OpenRouter, Ollama adapters
- Retriever adapter interface
- Chroma adapter

### Phase 6: Plugin System ✅
- Plugin registry
- Entry point discovery
- User metric examples
- Documentation

### Phase 7: CLI Commands ✅
- `oaeval init` (interactive wizard)
- `oaeval run` (dry-run, metrics override)
- `oaeval report`, `compare`, `list`, `doctor`
- `oaeval validate`, `delete`
- `oaeval diagnose`, `audit`, `synth`
- Shell completion (bash, zsh, fish)
- Global flags (`--quiet`, `--json`, `--no-color`, `--verbose`)
- Config auto-discovery

### Phase 8: Documentation ✅
- 12 numbered design docs (vision → retrievers)
- CONTRIBUTING.md, ROADMAP.md, CHANGELOG.md
- CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, DEVELOPMENT.md
- Provider-specific documentation
- Examples and tutorials

### Phase 9: Corpus Health Auditor ✅
- `CorpusAuditor` orchestrator
- `ContradictionDetector` — cross-document contradiction detection
- `StalenessDetector` — unmarked obsolescence detection
- `DuplicateDetector` — divergent duplicate detection
- `CoverageAnalyzer` — thematic coverage analysis
- `oaeval audit` CLI command

### Phase 10: Component Diagnosis ✅
- `DiagnosisAnalyzer` orchestrator
- `BlameAttribution` — retrieval vs generation vs chunking
- `ChunkingQualityAnalyzer` — chunking quality analysis
- 8 failure mode detection
- Actionable recommendations
- `oaeval diagnose` CLI command

### Phase 11: Synthetic Test Data ✅
- `SyntheticDataGenerator` orchestrator
- `QuestionGenerator` — question generation from documents
- `AdversarialTestCaseGenerator` — adversarial test cases
- `oaeval synth` CLI command

### Phase 12: Advanced Providers & NLI Metrics ✅
- 11 retriever providers (Chroma, Qdrant, Pinecone, Weaviate, FAISS, pgvector, Elasticsearch, BM25, HTTP, Memory, Mock)
- Embedder abstraction (Sentence Transformers, Mock)
- Score normalization (`_scoring.py`)
- NLI metrics (NLIJudge, ClaimExtractor, EvidenceFinder)
- PDF dataset loader

### Phase 13: CI/CD Integration ✅
- [x] Implement pytest plugin for RAG evaluation
- [x] Add threshold-based test gating
- [x] Add `oaeval test` CLI command
- [x] Write documentation for CI/CD integration
- [x] Add GitHub Actions workflow example

---

## AI Library Dependencies

| Library | Purpose |
|---------|---------|
| Ragas | Faithfulness, Answer Relevancy |
| DeepEval | Hallucination, G-Eval metrics |
| Sentence Transformers | Embeddings & semantic similarity |
| Hugging Face Evaluate | BLEU, ROUGE, F1, Exact Match |
| scikit-learn | Precision, Recall, MRR calculations |

---

## Engineering Principles (Always Follow)

- Clean Architecture
- SOLID Principles
- Dependency Injection
- Plugin-first Architecture
- Type Safety
- Async where appropriate
- Modular Design
- Production-ready code
- Comprehensive type hints
- Clear docstrings
- High test coverage

---

## Critical Rules

1. **NEVER** place business logic inside CLI commands
2. **NEVER** raise generic `Exception` in production code
3. **NEVER** skip the approval gate before implementation
4. **NEVER** assume features not documented in PROJECT.md
5. **ALWAYS** communicate through interfaces
6. **ALWAYS** use meaningful error messages
7. **ALWAYS** update project files after major milestones
8. **NEVER** develop directly on the `main` branch
9. **ALWAYS** create a new branch for every feature/task
10. **ALWAYS** create a Pull Request for review (never merge yourself)

---

## Writing & GitHub Content Standards

All generated GitHub content — issues, pull requests, PR reviews, comments, discussions, release notes, changelogs, commit messages, documentation, README updates, and wiki pages — must follow the rules in `INSTRUCTIONS.md` at the project root.

### Quick Reference

- **Markdown**: Always use GitHub Flavored Markdown (GFM)
- **File paths**: Forward slashes only, wrapped in backticks: `openagent_eval/diagnosis/chunking.py`
- **Code**: Fenced code blocks with language identifiers
- **Commands**: Fenced bash blocks
- **Headings**: Proper Markdown headings (`##`), never bold text as headings
- **Checklists**: GitHub task lists (`- [ ]`)
- **Tone**: Professional maintainer, clear, concise, technically accurate
- **Emoji**: At most one per section, avoid unnecessary emojis

### Required Templates

See `INSTRUCTIONS.md` for authoritative templates for issues, pull requests, release notes, and comments.

---

## Git Workflow Rules (MANDATORY)

GitHub Flow must be followed throughout the project.

### Branch Rules

- **NEVER** develop directly on the `main` branch
- The `main` branch must always remain stable and production-ready
- For every new feature, enhancement, bug fix, refactor, documentation update, test, or any other development task:
  1. Create a new Git branch before making any code changes
  2. Perform all work on that branch
  3. Push the branch to the remote repository when the task is complete
  4. Create a Pull Request targeting the `main` branch
  5. **Do NOT merge the Pull Request** - the user will review and merge manually

### Branch Naming Convention

```
feature/{description}      # New features
fix/{description}          # Bug fixes
docs/{description}         # Documentation updates
refactor/{description}     # Code refactoring
test/{description}         # Test additions/updates
chore/{description}        # Maintenance tasks
```

Examples:
- `feature/initial-scaffolding`
- `fix/config-validation-error`
- `docs/add-cli-specification`
- `refactor/metric-interface`
- `test/add-unit-tests-metrics`

### Pull Request Requirements

Every Pull Request must include a clear and professional description:

```markdown
## Summary

[Clear description of what was implemented]

## Motivation

[Why this change was needed]

## Files Modified

- `file1.py` - Description of changes
- `file2.py` - Description of changes

## Architectural Decisions

[Any important design decisions made]

## Breaking Changes

[Any breaking changes, or "None"]

## Testing

[What testing was performed]

## Remaining TODOs

[Any remaining work, or "None"]

## Assumptions & Limitations

[Any assumptions or limitations]
```

### PR Workflow

```
1. Create branch from main
   git checkout -b feature/initial-scaffolding

2. Make changes and commit
   git add .
   git commit -m "feat: Description"

3. Push to remote
   git push origin feature/initial-scaffolding

4. Create Pull Request (via GitHub CLI or web)
   gh pr create --title "Feature: Description" --body "..."

5. WAIT for review (do NOT merge)
```

---

## Date & Time Rules (MANDATORY)

### Verification Requirement

**NEVER guess or hardcode dates.** Always verify the current date and time before making any changes.

### How to Verify

1. **If internet access is available:** Verify using a reliable online source
2. **Otherwise:** Use the operating system's local date and time
3. **Never** assume the year or reuse dates from previous sessions

### When to Use Verified Dates

Always use the verified current date and time when creating or updating:
- Architecture Decision Records (ADRs)
- Changelog entries
- Documentation
- Task updates
- Context updates
- Milestone logs
- Any generated project files

### Date Format

Use ISO 8601 format: `YYYY-MM-DD`

Example: `2026-07-08`

### Rules

1. **ALWAYS** verify the current date before writing any date
2. **ALWAYS** use the verified date, not a guessed or hardcoded date
3. **NEVER** assume the year is the same as previous sessions
4. **ALWAYS** check the system date or online source
5. **ALWAYS** use consistent date format (YYYY-MM-DD)

---

## What NOT to Do

- Do NOT build on LangChain or other AI frameworks
- Do NOT add cloud services
- Do NOT add dashboards
- Do NOT add authentication
- Do NOT add features not in v1 scope
- Do NOT assume features not documented in PROJECT.md
- Do NOT skip the approval gate before implementation

---

## When Stuck

1. Re-read PROJECT.md
2. Check this file (AGENT.md)
3. Review DECISIONS.md for architectural rationale
4. Review ARCHITECTURE.md for system design
5. Ask questions if requirements are unclear
6. Never assume - always clarify

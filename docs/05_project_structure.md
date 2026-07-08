# Project Structure

## Directory Layout

```
openagent-eval/
├── openagent_eval/
│   ├── cli/                    # CLI commands (Typer)
│   │   ├── __init__.py
│   │   ├── main.py            # Main CLI entry point
│   │   ├── commands/          # Individual commands
│   │   │   ├── __init__.py
│   │   │   ├── init.py        # oaeval init
│   │   │   ├── run.py         # oaeval run
│   │   │   ├── report.py      # oaeval report
│   │   │   ├── compare.py     # oaeval compare
│   │   │   ├── list.py        # oaeval list
│   │   │   └── doctor.py      # oaeval doctor
│   │   └── utils/             # CLI utilities
│   │       ├── __init__.py
│   │       └── display.py     # Rich display helpers
│   │
│   ├── config/                 # Configuration management
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic configuration models
│   │   ├── loader.py          # YAML loading
│   │   └── validator.py       # Configuration validation
│   │
│   ├── core/                   # Core orchestration layer
│   │   ├── __init__.py
│   │   ├── engine.py          # Main evaluation engine
│   │   ├── pipeline.py        # Evaluation pipeline
│   │   ├── executor.py        # Async task execution
│   │   └── registry.py        # Plugin/component registry
│   │
│   ├── datasets/               # Dataset loaders
│   │   ├── __init__.py
│   │   ├── base.py            # BaseDatasetLoader interface
│   │   ├── json_loader.py     # JSON dataset loader
│   │   ├── jsonl_loader.py    # JSONL dataset loader
│   │   ├── csv_loader.py      # CSV dataset loader
│   │   ├── hf_loader.py       # HuggingFace dataset loader
│   │   └── models.py          # Dataset models
│   │
│   ├── metrics/                # Evaluation metrics
│   │   ├── __init__.py
│   │   ├── base.py            # BaseMetric interface
│   │   ├── models.py          # MetricResult model
│   │   ├── retrieval/         # Retrieval metrics
│   │   │   ├── __init__.py
│   │   │   ├── precision.py
│   │   │   ├── recall.py
│   │   │   ├── mrr.py
│   │   │   ├── ndcg.py
│   │   │   └── hit_rate.py
│   │   ├── generation/        # Generation metrics
│   │   │   ├── __init__.py
│   │   │   ├── faithfulness.py
│   │   │   ├── relevancy.py
│   │   │   ├── hallucination.py
│   │   │   ├── similarity.py
│   │   │   ├── bleu.py
│   │   │   ├── rouge.py
│   │   │   └── f1.py
│   │   ├── performance/       # Performance metrics
│   │   │   ├── __init__.py
│   │   │   └── latency.py
│   │   └── cost/              # Cost metrics
│   │       ├── __init__.py
│   │       └── tokens.py
│   │
│   ├── providers/              # LLM/Retriever adapters
│   │   ├── __init__.py
│   │   ├── base/
│   │   │   ├── __init__.py
│   │   │   ├── llm.py         # LLMProvider interface
│   │   │   └── retriever.py   # Retriever interface
│   │   ├── llm/               # LLM providers
│   │   │   ├── __init__.py
│   │   │   ├── openai.py
│   │   │   ├── gemini.py
│   │   │   ├── anthropic.py
│   │   │   ├── groq.py
│   │   │   ├── openrouter.py
│   │   │   └── ollama.py
│   │   └── retrievers/        # Retriever providers
│   │       ├── __init__.py
│   │       └── chroma.py
│   │
│   ├── reports/                # Report generation
│   │   ├── __init__.py
│   │   ├── base.py            # ReportGenerator interface
│   │   ├── terminal.py        # Terminal report (Rich)
│   │   ├── markdown.py        # Markdown report
│   │   ├── html.py            # HTML report (Jinja2)
│   │   └── json_report.py     # JSON report
│   │
│   ├── plugins/                # Plugin system
│   │   ├── __init__.py
│   │   ├── loader.py          # Plugin loading
│   │   ├── discovery.py       # Entry point discovery
│   │   └── manager.py         # Plugin management
│   │
│   ├── integrations/           # Third-party integrations
│   │   ├── __init__.py
│   │   └── ...                # Framework adapters
│   │
│   ├── exceptions/             # Custom exception hierarchy
│   │   ├── __init__.py
│   │   ├── base.py            # OpenAgentEvalError
│   │   ├── config.py          # Configuration errors
│   │   ├── dataset.py         # Dataset errors
│   │   ├── metric.py          # Metric errors
│   │   ├── provider.py        # Provider errors
│   │   ├── plugin.py          # Plugin errors
│   │   └── cli.py             # CLI errors
│   │
│   ├── types/                  # Shared type definitions
│   │   ├── __init__.py
│   │   └── protocols.py       # Type protocols
│   │
│   └── utils/                  # Shared utilities
│       ├── __init__.py
│       ├── logging.py         # Loguru setup
│       ├── async_utils.py     # Async helpers
│       └── validators.py      # Common validators
│
├── tests/
│   ├── unit/                  # Unit tests by module
│   │   ├── test_cli/
│   │   ├── test_config/
│   │   ├── test_core/
│   │   ├── test_datasets/
│   │   ├── test_metrics/
│   │   ├── test_providers/
│   │   ├── test_reports/
│   │   └── test_plugins/
│   ├── integration/           # Integration tests
│   │   ├── test_pipeline/
│   │   └── test_cli/
│   ├── fixtures/              # Test fixtures
│   │   └── conftest.py
│   └── sample_data/           # Sample datasets
│       ├── valid_dataset.json
│       └── config.yaml
│
├── docs/                       # Documentation
│   ├── 01_vision.md
│   ├── 02_problem_statement.md
│   ├── 03_product_requirements.md
│   ├── 04_architecture.md
│   ├── 05_project_structure.md
│   ├── 06_cli_spec.md
│   ├── 07_metric_system.md
│   ├── 08_plugin_system.md
│   ├── 09_coding_guidelines.md
│   ├── 10_development_plan.md
│   ├── 11_future_roadmap.md
│   └── examples.md
│
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── ROADMAP.md
├── CHANGELOG.md
├── ARCHITECTURE.md
├── AGENT.md
├── CONTEXT.md
├── DECISIONS.md
└── TASKS.md
```

---

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `cli/` | Parse commands, delegate to core, display output |
| `config/` | Load, validate, and manage YAML configuration |
| `core/` | Orchestration layer (engine, pipeline, executor, registry) |
| `datasets/` | Load evaluation data from JSON, JSONL, CSV, HuggingFace |
| `metrics/` | Implement BaseMetric for all evaluation metrics |
| `providers/` | Adapter pattern for LLMs (OpenAI, Gemini, Anthropic, etc.) |
| `reports/` | Generate Markdown, HTML, JSON, Terminal reports |
| `plugins/` | User extensions via entry points |
| `integrations/` | Third-party framework adapters |
| `exceptions/` | Custom exception hierarchy |
| `types/` | Shared type definitions and protocols |
| `utils/` | Shared utilities, logging, helpers |

---

## Key Design Decisions

### Why This Structure?

1. **Separation of concerns** - Each module has a single responsibility
2. **Dependency inversion** - Core depends on abstractions, not implementations
3. **Plugin-friendly** - Easy to add new metrics, providers, or report formats
4. **Testable** - Clear boundaries make mocking and testing straightforward
5. **Scalable** - New features can be added without modifying existing code

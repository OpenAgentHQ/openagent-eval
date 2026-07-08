# ARCHITECTURE.md - System Architecture

> This document explains HOW OpenAgent Eval is built.
> For WHAT we are building, see PROJECT.md.

---

## Overview

OpenAgent Eval is designed as a **Python evaluation SDK with a CLI on top**.

This architecture enables:
- CLI usage: `oaeval run config.yaml`
- SDK usage: `from openagent_eval import Evaluator`
- Single codebase, two entry points
- Extensible plugin-based design

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                    CLI Layer                         │
│               (oaeval - Typer + Rich)                │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                   SDK Layer                          │
│            (openagent_eval - Core API)               │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                 Core Orchestration                   │
│            (engine, pipeline, executor)              │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                    Components                        │
│  ┌───────────┬───────────┬───────────┬───────────┐  │
│  │  Metrics  │ Providers │ Datasets  │  Reports  │  │
│  └───────────┴───────────┴───────────┴───────────┘  │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  Plugin System                       │
│           (Registry + Entry Points)                  │
└─────────────────────────────────────────────────────┘
```

---

## Package Structure

```
openagent_eval/
├── cli/                    # CLI commands (Typer)
│   ├── __init__.py
│   ├── main.py            # Main CLI entry point
│   ├── commands/          # Individual commands
│   │   ├── __init__.py
│   │   ├── init.py        # oaeval init
│   │   ├── run.py         # oaeval run
│   │   ├── report.py      # oaeval report
│   │   ├── compare.py     # oaeval compare
│   │   ├── list.py        # oaeval list
│   │   └── doctor.py      # oaeval doctor
│   └── utils/             # CLI utilities
│       ├── __init__.py
│       └── display.py     # Rich display helpers
│
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── models.py          # Pydantic configuration models
│   ├── loader.py          # YAML loading
│   └── validator.py       # Configuration validation
│
├── core/                   # Core orchestration layer
│   ├── __init__.py
│   ├── engine.py          # Main evaluation engine
│   ├── pipeline.py        # Evaluation pipeline
│   ├── executor.py        # Async task execution
│   └── registry.py        # Plugin/component registry
│
├── datasets/               # Dataset loaders
│   ├── __init__.py
│   ├── base.py            # BaseDatasetLoader interface
│   ├── json_loader.py     # JSON dataset loader
│   ├── jsonl_loader.py    # JSONL dataset loader
│   ├── csv_loader.py      # CSV dataset loader
│   ├── hf_loader.py       # HuggingFace dataset loader
│   └── models.py          # Dataset models
│
├── metrics/                # Evaluation metrics
│   ├── __init__.py
│   ├── base.py            # BaseMetric interface
│   ├── models.py          # MetricResult model
│   ├── retrieval/         # Retrieval metrics
│   │   ├── __init__.py
│   │   ├── precision.py
│   │   ├── recall.py
│   │   ├── mrr.py
│   │   ├── ndcg.py
│   │   └── hit_rate.py
│   ├── generation/        # Generation metrics
│   │   ├── __init__.py
│   │   ├── faithfulness.py
│   │   ├── relevancy.py
│   │   ├── hallucination.py
│   │   ├── similarity.py
│   │   ├── bleu.py
│   │   ├── rouge.py
│   │   └── f1.py
│   ├── performance/       # Performance metrics
│   │   ├── __init__.py
│   │   └── latency.py
│   └── cost/              # Cost metrics
│       ├── __init__.py
│       └── tokens.py
│
├── providers/              # LLM/Retriever adapters
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   ├── llm.py         # LLMProvider interface
│   │   └── retriever.py   # Retriever interface
│   ├── llm/               # LLM providers
│   │   ├── __init__.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   ├── anthropic.py
│   │   ├── groq.py
│   │   ├── openrouter.py
│   │   └── ollama.py
│   └── retrievers/        # Retriever providers
│       ├── __init__.py
│       └── chroma.py
│
├── reports/                # Report generation
│   ├── __init__.py
│   ├── base.py            # ReportGenerator interface
│   ├── terminal.py        # Terminal report (Rich)
│   ├── markdown.py        # Markdown report
│   ├── html.py            # HTML report (Jinja2)
│   └── json_report.py     # JSON report
│
├── plugins/                # Plugin system
│   ├── __init__.py
│   ├── loader.py          # Plugin loading
│   ├── discovery.py       # Entry point discovery
│   └── manager.py         # Plugin management
│
├── integrations/           # Third-party integrations
│   ├── __init__.py
│   └── ...                # Framework adapters
│
├── exceptions/             # Custom exception hierarchy
│   ├── __init__.py
│   ├── base.py            # OpenAgentEvalError
│   ├── config.py          # Configuration errors
│   ├── dataset.py         # Dataset errors
│   ├── metric.py          # Metric errors
│   ├── provider.py        # Provider errors
│   ├── plugin.py          # Plugin errors
│   └── cli.py             # CLI errors
│
├── types/                  # Shared type definitions
│   ├── __init__.py
│   └── protocols.py       # Type protocols
│
└── utils/                  # Shared utilities
    ├── __init__.py
    ├── logging.py         # Loguru setup
    ├── async_utils.py     # Async helpers
    └── validators.py      # Common validators
```

---

## Core Components

### 1. CLI Layer (`cli/`)

**Responsibility:** Parse commands, delegate to core, display output.

**Rules:**
- NO business logic in CLI
- Only command parsing and output display
- Delegate all work to core modules

**Example:**
```python
@app.command()
def run(config_path: str):
    """Run evaluation."""
    # Load configuration
    config = load_config(config_path)
    
    # Delegate to core engine
    engine = Engine(config)
    result = engine.run()
    
    # Display results
    display_results(result)
```

### 2. Core Orchestration (`core/`)

**Responsibility:** Orchestrate the evaluation pipeline.

**Components:**

| File | Responsibility |
|------|----------------|
| `engine.py` | Main evaluation engine - orchestrates entire evaluation |
| `pipeline.py` | Evaluation pipeline - Dataset → Retriever → LLM → Metrics |
| `executor.py` | Task execution - manages async execution and parallelism |
| `registry.py` | Plugin/component registry - discovers and manages plugins |

**Example:**
```python
class Engine:
    def __init__(self, config: Config):
        self.config = config
        self.pipeline = Pipeline(config)
        self.registry = Registry()
    
    async def run(self) -> EvaluationResult:
        # Load dataset
        dataset = self.registry.get_dataset_loader(self.config.dataset)
        
        # Run pipeline
        results = await self.pipeline.execute(dataset)
        
        # Generate reports
        report = self.generate_report(results)
        
        return report
```

### 3. Metrics System (`metrics/`)

**Responsibility:** Implement evaluation metrics.

**Interface:**
```python
class BaseMetric(ABC):
    name: str
    description: str
    
    @abstractmethod
    def evaluate(self, ...) -> MetricResult:
        ...

@dataclass
class MetricResult:
    score: float
    reason: str
    metadata: dict
```

**Rules:**
- Every metric implements `BaseMetric`
- Return `MetricResult` with score, reason, metadata
- No side effects
- Pure functions where possible

### 4. Providers (`providers/`)

**Responsibility:** Adapter pattern for LLMs and retrievers.

**Interfaces:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        ...
    
    @abstractmethod
    async def get_token_count(self, text: str) -> int:
        ...

class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, k: int = 5) -> List[Document]:
        ...
```

**Rules:**
- Support async operations
- Implement token counting for cost tracking
- Handle errors gracefully
- Never raise generic exceptions

### 5. Datasets (`datasets/`)

**Responsibility:** Load evaluation data from various formats.

**Interface:**
```python
class BaseDatasetLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> Dataset:
        ...
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        ...
```

**Supported Formats:**
- JSON
- JSONL
- CSV
- HuggingFace datasets

### 6. Reports (`reports/`)

**Responsibility:** Generate evaluation reports.

**Interface:**
```python
class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, results: EvaluationResult) -> str:
        ...
```

**Formats:**
- Terminal (Rich)
- Markdown
- HTML (Jinja2)
- JSON

### 7. Plugin System (`plugins/`)

**Responsibility:** Enable extensibility.

**Mechanism:**
- Python entry points
- Registry pattern
- Discovery at runtime

**Example:**
```python
# User creates custom metric
class MyMetric(BaseMetric):
    name = "my_metric"
    def evaluate(self, ...) -> MetricResult:
        ...

# Register via entry point
# pyproject.toml
[project.entry-points."openagent_eval.metrics"]
my_metric = "my_package.metrics:MyMetric"
```

---

## Dependency Flow

```
cli/ → core/ → datasets/
             → metrics/
             → providers/
             → reports/
             → plugins/
```

**Rules:**
1. `cli/` depends on everything
2. `core/` depends on `datasets/`, `metrics/`, `providers/`, `reports/`
3. `metrics/`, `providers/`, `reports/` depend only on `utils/` and `types/`
4. `exceptions/` depends on nothing
5. `types/` depends on nothing
6. No circular dependencies

---

## Evaluation Pipeline

```
┌─────────────┐
│   Dataset   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Question   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Retriever  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Retrieved Docs  │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│     LLM     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│Generated Answer │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Evaluation     │
│ Engine         │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│   Metrics   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Reports   │
└─────────────┘
```

---

## Exception Hierarchy

```
OpenAgentEvalError (base)
├── ConfigurationError
├── DatasetError
│   ├── DatasetNotFoundError
│   ├── InvalidDatasetError
│   └── DatasetValidationError
├── MetricError
│   ├── MetricNotFoundError
│   ├── MetricExecutionError
│   └── MetricTimeoutError
├── ProviderError
│   ├── ProviderNotFoundError
│   ├── ProviderConnectionError
│   └── ProviderExecutionError
├── PluginError
│   ├── PluginNotFoundError
│   └── PluginLoadError
└── CLIError
    ├── CommandError
    └── ValidationError
```

---

## Configuration System

**Format:** YAML

**Example:**
```yaml
dataset: data/questions.json

retriever:
  provider: chroma
  settings:
    collection_name: my_docs

llm:
  provider: openai
  model: gpt-4o

metrics:
  - faithfulness
  - answer_relevancy
  - hallucination
  - latency

output: terminal
output_dir: ./reports
```

**Validation:**
- Pydantic v2 models
- Required fields enforced
- Environment variables for secrets
- Helpful error messages

---

## Testing Strategy

**Structure:**
```
tests/
├── unit/                  # Unit tests by module
│   ├── test_cli/
│   ├── test_config/
│   ├── test_core/
│   ├── test_datasets/
│   ├── test_metrics/
│   ├── test_providers/
│   ├── test_reports/
│   └── test_plugins/
├── integration/           # Integration tests
│   ├── test_pipeline/
│   └── test_cli/
├── fixtures/              # Test fixtures
│   └── conftest.py
└── sample_data/           # Sample datasets
    ├── valid_dataset.json
    └── config.yaml
```

**Rules:**
- 80%+ coverage target
- Mock all external dependencies
- Test both success and failure paths
- Use pytest fixtures

---

## Async Architecture

**Why Async:**
- Parallel evaluation for speed
- Better resource utilization
- Compatible with async LLM clients

**Implementation:**
- All provider adapters support async
- Pipeline execution is async
- Executor manages parallelism

**Example:**
```python
async def evaluate_dataset(dataset: Dataset) -> List[MetricResult]:
    tasks = []
    for item in dataset:
        task = evaluate_item(item)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

---

## Plugin Architecture

**Discovery:**
- Python entry points
- Registry pattern
- Runtime loading

**Extension Points:**
- Metrics: `openagent_eval.metrics`
- Providers: `openagent_eval.providers`
- Reports: `openagent_eval.reports`
- Datasets: `openagent_eval.datasets`

**Example:**
```python
# Register custom metric
[project.entry-points."openagent_eval.metrics"]
my_metric = "my_package.metrics:MyMetric"
```

---

## Design Principles

1. **Clean Architecture** - Clear separation of concerns
2. **SOLID Principles** - Single responsibility, dependency inversion
3. **Plugin-first** - Everything extensible via interfaces
4. **Type Safety** - Pydantic v2, type hints everywhere
5. **Async where appropriate** - Parallel execution
6. **Modular Design** - Loose coupling, high cohesion
7. **Production-ready** - Error handling, logging, testing

---

## Related Documents

- `PROJECT.md` - Product specification (WHAT)
- `AGENT.md` - Engineering handbook (rules)
- `DECISIONS.md` - Architectural decisions (WHY)
- `CONTEXT.md` - Working memory (status)
- `TASKS.md` - Task tracking (progress)

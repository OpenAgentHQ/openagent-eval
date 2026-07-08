# Architecture

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
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  Plugin System                       │
│           (Registry + Entry Points)                  │
└─────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. CLI Layer (`cli/`)

**Responsibility:** Parse commands, delegate to core, display output.

**Rules:**

- NO business logic in CLI
- Only command parsing and output display
- Delegate all work to core modules

### 2. Core Orchestration (`core/`)

**Responsibility:** Orchestrate the evaluation pipeline.

| File | Responsibility |
|------|----------------|
| `engine.py` | Main evaluation engine - orchestrates entire evaluation |
| `pipeline.py` | Evaluation pipeline - Dataset → Retriever → LLM → Metrics |
| `executor.py` | Task execution - manages async execution and parallelism |
| `registry.py` | Plugin/component registry - discovers and manages plugins |

### 3. Metrics System (`metrics/`)

**Responsibility:** Implement evaluation metrics.

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

### 4. Providers (`providers/`)

**Responsibility:** Adapter pattern for LLMs and retrievers.

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

### 5. Datasets (`datasets/`)

**Responsibility:** Load evaluation data from various formats.

```python
class BaseDatasetLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> Dataset:
        ...
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        ...
```

### 6. Reports (`reports/`)

**Responsibility:** Generate evaluation reports.

```python
class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, results: EvaluationResult) -> str:
        ...
```

### 7. Plugin System (`plugins/`)

**Responsibility:** Enable extensibility via entry points.

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

## Design Principles

1. **Clean Architecture** - Clear separation of concerns
2. **SOLID Principles** - Single responsibility, dependency inversion
3. **Plugin-first** - Everything extensible via interfaces
4. **Type Safety** - Pydantic v2, type hints everywhere
5. **Async where appropriate** - Parallel execution
6. **Modular Design** - Loose coupling, high cohesion
7. **Production-ready** - Error handling, logging, testing

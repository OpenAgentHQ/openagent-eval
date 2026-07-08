# Plugin System

## Overview

OpenAgent Eval uses a plugin-based architecture to enable extensibility. Users can add custom metrics, providers, dataset loaders, and report generators without modifying the core codebase.

---

## Architecture

```
┌─────────────────────────────────────────┐
│            Plugin Manager               │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │   Loader    │  │   Discovery     │  │
│  │  (load)     │  │  (entry points) │  │
│  └─────────────┘  └─────────────────┘  │
└─────────────────────┬───────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────┐
│              Registry                   │
│  ┌───────────┬───────────┬───────────┐  │
│  │  Metrics  │ Providers │  Reports  │  │
│  └───────────┴───────────┴───────────┘  │
└─────────────────────────────────────────┘
```

---

## Extension Points

### 1. Metrics

Add custom evaluation metrics.

**Interface:** `BaseMetric`

```python
from openagent_eval.metrics import BaseMetric, MetricResult

class CustomMetric(BaseMetric):
    name = "custom_metric"
    description = "My custom evaluation metric"
    
    def evaluate(self, **kwargs) -> MetricResult:
        # Implementation
        score = 0.95
        return MetricResult(
            score=score,
            reason="Custom evaluation complete",
            metadata={"details": "..."}
        )
```

**Register:**

```toml
# pyproject.toml
[project.entry-points."openagent_eval.metrics"]
custom_metric = "my_package.metrics:CustomMetric"
```

### 2. LLM Providers

Add custom LLM provider adapters.

**Interface:** `LLMProvider`

```python
from openagent_eval.providers.base.llm import LLMProvider

class CustomLLM(LLMProvider):
    name = "custom_llm"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Call your LLM API
        response = await call_custom_api(prompt)
        return response
    
    async def get_token_count(self, text: str) -> int:
        # Return token count
        return len(text.split())
```

**Register:**

```toml
[project.entry-points."openagent_eval.providers.llm"]
custom_llm = "my_package.providers:CustomLLM"
```

### 3. Retriever Providers

Add custom retriever adapters.

**Interface:** `Retriever`

```python
from openagent_eval.providers.base.retriever import Retriever

class CustomRetriever(Retriever):
    name = "custom_retriever"
    
    async def retrieve(self, query: str, k: int = 5) -> List[Document]:
        # Your retrieval logic
        documents = await search(query, k=k)
        return documents
```

**Register:**

```toml
[project.entry-points."openagent_eval.providers.retriever"]
custom_retriever = "my_package.retrievers:CustomRetriever"
```

### 4. Dataset Loaders

Add custom dataset format support.

**Interface:** `BaseDatasetLoader`

```python
from openagent_eval.datasets.base import BaseDatasetLoader

class CustomLoader(BaseDatasetLoader):
    name = "custom_loader"
    
    def load(self, path: str) -> Dataset:
        # Load your custom format
        data = read_custom_format(path)
        return Dataset(items=data)
    
    def validate(self, data: Any) -> bool:
        # Validate data structure
        return isinstance(data, list)
```

**Register:**

```toml
[project.entry-points."openagent_eval.datasets"]
custom_loader = "my_package.loaders:CustomLoader"
```

### 5. Report Generators

Add custom report formats.

**Interface:** `ReportGenerator`

```python
from openagent_eval.reports.base import ReportGenerator

class CustomReport(ReportGenerator):
    name = "custom_report"
    
    def generate(self, results: EvaluationResult) -> str:
        # Generate your custom report
        report = format_custom(results)
        return report
```

**Register:**

```toml
[project.entry-points."openagent_eval.reports"]
custom_report = "my_package.reports:CustomReport"
```

---

## Plugin Discovery

Plugins are discovered via Python entry points. The plugin manager scans:

1. Built-in plugins (in `openagent_eval/`)
2. Installed packages with entry points
3. Local plugins (if configured)

### Discovery Process

```
1. Scan entry point groups
   └── openagent_eval.metrics
   └── openagent_eval.providers.llm
   └── openagent_eval.providers.retriever
   └── openagent_eval.datasets
   └── openagent_eval.reports

2. Load plugin classes
   └── Import module
   └── Get class from entry point

3. Register in registry
   └── Validate interface
   └── Store in registry
```

---

## Plugin Loading

```python
from openagent_eval.plugins import PluginManager

manager = PluginManager()

# Discover all plugins
manager.discover()

# Get a specific metric
faithfulness = manager.get_metric("faithfulness")

# Get all available metrics
all_metrics = manager.list_metrics()

# Get a provider
openai = manager.get_provider("llm", "openai")
```

---

## Creating a Plugin Package

### 1. Create Package Structure

```
my-oaeval-plugin/
├── pyproject.toml
├── README.md
└── my_package/
    ├── __init__.py
    ├── metrics/
    │   ├── __init__.py
    │   └── custom_metric.py
    └── providers/
        ├── __init__.py
        └── custom_llm.py
```

### 2. Configure Entry Points

```toml
# pyproject.toml
[project]
name = "my-oaeval-plugin"
version = "0.1.0"
dependencies = ["openagent-eval>=0.1.0"]

[project.entry-points."openagent_eval.metrics"]
custom_metric = "my_package.metrics.custom_metric:CustomMetric"

[project.entry-points."openagent_eval.providers.llm"]
custom_llm = "my_package.providers.custom_llm:CustomLLM"
```

### 3. Install Plugin

```bash
pip install -e .
# or
uv add -e .
```

### 4. Use Plugin

```bash
oaeval run config.yaml
# Plugin automatically discovered and available
```

---

## Plugin Development Guide

### Best Practices

1. **Follow interfaces** - Always implement the base interface
2. **Return proper types** - Use `MetricResult`, `Document`, etc.
3. **Handle errors gracefully** - Never raise generic exceptions
4. **Add type hints** - All public functions must have type hints
5. **Write tests** - Include tests for your plugin
6. **Document** - Add docstrings and README

### Testing Plugins

```python
import pytest
from my_package.metrics import CustomMetric

def test_custom_metric():
    metric = CustomMetric()
    result = metric.evaluate(answer="test", context="test context")
    
    assert 0.0 <= result.score <= 1.0
    assert result.reason is not None
    assert isinstance(result.metadata, dict)
```

### Error Handling

```python
from openagent_eval.exceptions import MetricExecutionError

class CustomMetric(BaseMetric):
    def evaluate(self, **kwargs) -> MetricResult:
        try:
            # Your logic
            score = calculate_score(kwargs)
            return MetricResult(score=score, reason="Success")
        except ValueError as e:
            raise MetricExecutionError(
                message=f"Failed to evaluate: {e}",
                metric_name=self.name
            )
```

---

## Built-in Plugins

OpenAgent Eval includes the following built-in plugins:

### Metrics

- `faithfulness` - LLM-based faithfulness evaluation
- `answer_relevancy` - LLM-based relevancy evaluation
- `hallucination` - Hallucination detection
- `semantic_similarity` - Sentence transformer similarity
- `exact_match` - Exact string matching
- `f1_score` - Token-level F1
- `bleu` - BLEU score
- `rouge` - ROUGE score
- `context_precision` - Retrieval precision
- `context_recall` - Retrieval recall
- `hit_rate` - Hit rate
- `mrr` - Mean Reciprocal Rank
- `ndcg` - NDCG
- `latency` - Execution time
- `token_usage` - Token counting and cost

### LLM Providers

- `openai` - OpenAI GPT models
- `gemini` - Google Gemini
- `anthropic` - Anthropic Claude
- `groq` - Groq
- `openrouter` - OpenRouter
- `ollama` - Ollama (local)

### Retriever Providers

- `chroma` - ChromaDB

### Report Generators

- `terminal` - Rich terminal output
- `markdown` - Markdown files
- `html` - HTML with Jinja2
- `json` - JSON output

---

## Troubleshooting

### Plugin Not Found

```
Error: Plugin 'my_metric' not found
```

**Solutions:**

1. Ensure plugin is installed: `pip install -e .`
2. Check entry points in `pyproject.toml`
3. Verify module path is correct

### Plugin Load Error

```
Error: Failed to load plugin 'my_metric'
```

**Solutions:**

1. Check import paths
2. Verify dependencies are installed
3. Check for syntax errors in plugin code

### Interface Error

```
Error: Plugin 'my_metric' does not implement BaseMetric
```

**Solutions:**

1. Ensure class inherits from `BaseMetric`
2. Implement all required methods
3. Return proper types (`MetricResult`)

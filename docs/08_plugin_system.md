# Plugin System Guide

## Overview

OpenAgent Eval supports a plugin system that allows you to extend the framework with custom metrics, providers, retrievers, dataset loaders, and report generators. Plugins are discovered automatically via Python entry points.

## Plugin Types

OpenAgent Eval supports five types of plugins:

1. **Metrics** - Custom evaluation metrics
2. **Providers** - LLM and retriever adapters
3. **Retriever** - Document retrieval providers
4. **Dataset Loaders** - Custom dataset formats
5. **Report Generators** - Custom report formats

## Creating a Plugin

### 1. Create a Python Package

Create a new Python package for your plugin:

```bash
mkdir my-oaeval-plugin
cd my-oaeval-plugin
```

### 2. Define Your Plugin

#### Custom Metric Example

```python
# my_oaeval_plugin/metrics.py
from openagent_eval.metrics.base import BaseMetric, MetricResult


class MyCustomMetric(BaseMetric):
    """A custom evaluation metric."""
    
    name = "my_custom_metric"
    description = "Evaluates something custom"
    
    def evaluate(self, **kwargs) -> MetricResult:
        # Your evaluation logic here
        score = 0.85
        
        return MetricResult(
            score=score,
            reason="Custom evaluation completed",
            metadata={"custom_data": "value"}
        )
```

#### Custom Provider Example

```python
# my_oaeval_plugin/providers.py
from openagent_eval.providers.base.llm import LLMProvider


class MyCustomProvider(LLMProvider):
    """A custom LLM provider."""
    
    name = "my_custom_provider"
    description = "A custom LLM provider"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your LLM integration here
        return "Generated response"
    
    async def get_token_count(self, text: str) -> int:
        # Your token counting logic here
        return len(text.split())
```

### 3. Configure Entry Points

Add entry points to your `pyproject.toml`:

```toml
[project]
name = "my-oaeval-plugin"
version = "0.1.0"
description = "Custom plugin for OpenAgent Eval"
requires-python = ">=3.11"
dependencies = [
    "openagent-eval>=0.1.0",
]

[project.entry-points."openagent_eval.metrics"]
my_custom_metric = "my_oaeval_plugin.metrics:MyCustomMetric"

[project.entry-points."openagent_eval.providers"]
my_custom_provider = "my_oaeval_plugin.providers:MyCustomProvider"
```

### 4. Install Your Plugin

```bash
pip install -e .
```

Or with uv:

```bash
uv pip install -e .
```

## Using Plugins

Once installed, plugins are automatically discovered when you import OpenAgent Eval:

```python
from openagent_eval.core.registry import Registry

# Create registry and load plugins
registry = Registry()

# Your custom metric is now available
metric = registry.get_metric("my_custom_metric")
```

## Plugin Interface Requirements

All plugins must implement:

1. `name` attribute - Unique identifier string
2. `description` attribute - Human-readable description
3. Required methods for their type

### Metric Interface

```python
class BaseMetric:
    name: str
    description: str
    
    def evaluate(self, **kwargs) -> MetricResult:
        ...
```

### Provider Interface

```python
class LLMProvider:
    name: str
    description: str
    
    async def generate(self, prompt: str, **kwargs) -> str:
        ...
    
    async def get_token_count(self, text: str) -> int:
        ...
```

## Testing Your Plugin

Create tests for your plugin:

```python
# tests/test_my_metric.py
import pytest
from my_oaeval_plugin.metrics import MyCustomMetric


def test_my_metric():
    metric = MyCustomMetric()
    result = metric.evaluate(question="test", answer="test")
    
    assert 0.0 <= result.score <= 1.0
    assert result.reason != ""
```

## Best Practices

1. **Keep plugins focused** - One plugin per functionality
2. **Follow naming conventions** - Use snake_case for names
3. **Provide clear descriptions** - Help users understand what your plugin does
4. **Handle errors gracefully** - Use appropriate exception types
5. **Write tests** - Ensure your plugin works correctly
6. **Document usage** - Provide examples in your plugin's README

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

## Troubleshooting

### Plugin Not Discovered

1. Ensure entry points are correctly configured in `pyproject.toml`
2. Reinstall the plugin: `pip install -e .`
3. Check that the plugin class has `name` and `description` attributes

### Import Errors

1. Ensure all dependencies are installed
2. Check that the plugin module is importable
3. Verify the entry point path is correct

### Plugin Loading Fails

1. Check the plugin class implements required methods
2. Ensure the plugin class inherits from the correct base class
3. Look at logs for detailed error messages

## Example Plugin Structure

```
my-oaeval-plugin/
├── my_oaeval_plugin/
│   ├── __init__.py
│   ├── metrics.py
│   └── providers.py
├── tests/
│   └── test_metrics.py
├── pyproject.toml
└── README.md
```

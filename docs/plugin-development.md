# Plugin Development Guide

## Overview

OpenAgent Eval provides a plugin system that allows developers to extend the framework without modifying the core codebase. Plugins are discovered through Python entry points, making it easy to add new functionality such as custom metrics, LLM providers, dataset loaders, retrievers, and report generators.

This guide walks through creating a plugin from scratch using the included `WordCountMetric` example and explains how to register, test, and use your own plugins.

## Plugin Architecture

The plugin system is based on Python entry points. When OpenAgent Eval starts, it discovers registered plugins automatically and makes them available inside the framework.

The framework currently supports:

- Custom Metrics
- LLM Providers
- Retriever Providers
- Dataset Loaders
- Report Generators

Each plugin should inherit from the appropriate base class and expose a unique `name` and `description`.

## Creating a Custom Metric

This example demonstrates how to create a custom metric using the `WordCountMetric` example included with OpenAgent Eval.

### Step 1: Create a Metric Class

Create a Python file for your metric and inherit from `BaseMetric`.

```python
from openagent_eval.metrics.base import BaseMetric, MetricResult

class WordCountMetric(BaseMetric):
    name = "word_count"
    description = "Counts the number of words in the answer"
```

### Step 2: Implement the `evaluate()` Method

The `evaluate()` method contains the logic used to calculate the metric score.

```python
def evaluate(self, **kwargs) -> MetricResult:
    answer = kwargs.get("answer", "")
    words = answer.split()
    word_count = len(words)

    return MetricResult(
        score=min(word_count / 100.0, 1.0),
        reason=f"Answer contains {word_count} words",
        metadata={"word_count": word_count},
    )
```

### Step 3: Validate Inputs

Optionally validate user inputs before evaluation.

```python
def validate_inputs(self, **kwargs):
    answer = kwargs.get("answer")
    if answer is not None and not isinstance(answer, str):
        raise ValueError("Answer must be a string")
```

After registering the plugin, the metric becomes available automatically when OpenAgent Eval loads plugins.

## Registering a Custom LLM Provider

To create a custom LLM provider, inherit from the appropriate provider base class and implement the required methods such as `generate()` and `get_token_count()`.

Each provider should define a unique `name` and `description`. Once registered through Python entry points, the provider will be discovered automatically by OpenAgent Eval.

## Configuring Entry Points

OpenAgent Eval discovers plugins using Python entry points defined in the package configuration.

Add your plugin entry point inside `pyproject.toml`:

```toml
[project.entry-points."openagent_eval.plugins"]
word_count = "my_plugin.metrics:WordCountMetric"
```

The entry point contains:

- A unique plugin name
- The Python import path to the plugin class
- The class that implements the required plugin interface

After installing the package, OpenAgent Eval automatically detects the plugin during startup.

## Testing Your Plugin Locally

Before publishing a plugin, test it locally to ensure that it works correctly with OpenAgent Eval.

### Step 1: Install the Plugin Locally

Install your plugin package in editable mode:

```bash
pip install -e .
```

This allows you to make changes to the plugin code without reinstalling the package.

### Step 2: Verify Plugin Discovery

Start OpenAgent Eval and check whether the plugin is discovered successfully.

You can verify that:

- The plugin name appears in the available plugins list
- The plugin loads without import errors
- The metric or provider behaves as expected

### Step 3: Run Tests

Create tests for your plugin functionality and run them using:

```bash
pytest
```

Testing helps ensure that plugin behavior remains stable when the framework changes.

## Best Practices

Follow these practices when developing plugins for OpenAgent Eval:

- Keep plugins independent from the core framework code.
- Use clear and unique names for plugins, metrics, and providers.
- Provide meaningful descriptions explaining the purpose of the plugin.
- Validate inputs before processing data.
- Add tests to verify plugin behavior.
- Handle errors gracefully and provide useful error messages.
- Keep plugin dependencies minimal to avoid compatibility issues.
- Follow the existing coding style and project conventions.

## Common Pitfalls

While developing plugins, avoid these common issues:

- Forgetting to register the plugin through Python entry points.
- Using duplicate plugin names that conflict with existing plugins.
- Incorrect import paths in the plugin configuration.
- Missing required methods from the base plugin class.
- Not validating inputs before processing data.
- Adding unnecessary dependencies that make installation difficult.
- Not writing tests before integrating the plugin with OpenAgent Eval.
- Ignoring error handling, which can make debugging difficult.
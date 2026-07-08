# Examples

## Overview

This document provides practical examples of using OpenAgent Eval.

---

## Quick Start

### 1. Install OpenAgent Eval

```bash
pip install openagent-eval
# or
uv add openagent-eval
```

### 2. Create Configuration

```bash
oaeval init
```

This creates a `config.yaml` file:

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

output: terminal
```

### 3. Prepare Dataset

Create `data/questions.json`:

```json
[
  {
    "question": "What is the capital of France?",
    "ground_truth": "Paris",
    "context": "Paris is the capital city of France. It is known for the Eiffel Tower."
  },
  {
    "question": "What is machine learning?",
    "ground_truth": "Machine learning is a subset of AI that enables systems to learn from data.",
    "context": "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data."
  }
]
```

### 4. Run Evaluation

```bash
oaeval run config.yaml
```

**Output:**

```
Loading dataset: data/questions.json (2 questions)
Running evaluation...

Retrieval Metrics:
  Context Precision: 0.95
  Context Recall: 0.90
  Hit Rate: 1.00

Generation Metrics:
  Faithfulness: 0.92
  Answer Relevancy: 0.88
  Hallucination Rate: 0.05

Performance:
  Average Latency: 450ms
  Total Time: 2.1s

Cost:
  Total Tokens: 1,234
  Estimated Cost: $0.002

Overall Grade: A
```

---

## SDK Usage

### Basic Evaluation

```python
from openagent_eval import Evaluator
from openagent_eval.config import Config

# Load configuration
config = Config.from_yaml("config.yaml")

# Create evaluator
evaluator = Evaluator(config)

# Run evaluation
result = evaluator.evaluate()

# Access results
print(f"Overall Score: {result.overall_score}")
for metric in result.metrics:
    print(f"{metric.name}: {metric.score}")
```

### Custom Metrics

```python
from openagent_eval.metrics import BaseMetric, MetricResult

class WordCountMetric(BaseMetric):
    name = "word_count"
    description = "Count words in answer"
    
    def evaluate(self, answer: str, **kwargs) -> MetricResult:
        word_count = len(answer.split())
        return MetricResult(
            score=float(word_count),
            reason=f"{word_count} words"
        )

# Use custom metric
from openagent_eval import Evaluator

evaluator = Evaluator(config)
result = evaluator.evaluate(metrics=[WordCountMetric()])
```

### Custom Provider

```python
from openagent_eval.providers.base.llm import LLMProvider

class MyCustomLLM(LLMProvider):
    name = "my_llm"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your custom LLM logic
        response = await call_my_api(prompt)
        return response
    
    async def get_token_count(self, text: str) -> int:
        return len(text.split())

# Register and use
from openagent_eval.plugins import PluginManager

manager = PluginManager()
manager.register_provider("llm", "my_llm", MyCustomLLM)
```

---

## CLI Examples

### Compare Experiments

```bash
oaeval compare exp_a exp_b --diff
```

**Output:**

```
Experiment Comparison

| Metric           | Experiment A | Experiment B | Delta |
|------------------|--------------|--------------|-------|
| Faithfulness     | 83.2%        | 92.1%        | +8.9% |
| Answer Relevancy | 81.5%        | 89.7%        | +8.2% |
| Latency          | 450ms        | 612ms        | +162ms|
| Cost             | $1.82        | $2.17        | +$0.35|

Winner: Experiment B (Faithfulness +8.9%)
```

### View Reports

```bash
oaeval report latest --format markdown
```

**Output:**

```markdown
# Evaluation Report

**Date:** 2026-07-09
**Dataset:** data/questions.json (500 questions)

## Summary

| Metric | Score |
|--------|-------|
| Faithfulness | 91.8% |
| Answer Relevancy | 89.2% |
| Hallucination Rate | 3.1% |

## Failure Analysis

### Hallucinated Answers (15 failures)

1. Question: "What is X?"
   - Answer: "X is Y" (not in context)
   - Context: "X is Z"

### Wrong Retrieval (8 failures)

1. Question: "What is Y?"
   - Retrieved: Document about Z
   - Expected: Document about Y
```

### Check Environment

```bash
oaeval doctor
```

**Output:**

```
Environment Check

✓ Python 3.11.5
✓ openagent-eval 0.1.0
✓ PyYAML installed
✓ Pydantic v2.4.0

Provider Status
✓ OpenAI API key configured
✗ Gemini API key not found
✓ Anthropic API key configured

Recommendations
- Set GEMINI_API_KEY for Gemini support
```

---

## Advanced Usage

### Batch Evaluation

```python
import asyncio
from openagent_eval import Evaluator

async def batch_evaluate():
    config = Config.from_yaml("config.yaml")
    evaluator = Evaluator(config)
    
    # Evaluate multiple datasets
    datasets = ["data/train.json", "data/val.json", "data/test.json"]
    
    tasks = [evaluator.evaluate(dataset=d) for d in datasets]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(f"{result.dataset}: {result.overall_score}")

asyncio.run(batch_evaluate())
```

### Custom Report Template

```python
from openagent_eval.reports.base import ReportGenerator

class CustomReport(ReportGenerator):
    name = "custom_report"
    
    def generate(self, results) -> str:
        report = f"""
# Custom Report

## Metrics
"""
        for metric in results.metrics:
            report += f"- **{metric.name}**: {metric.score:.2%}\n"
        
        report += f"""
## Summary
Overall Score: {results.overall_score:.2%}
"""
        return report
```

### Plugin Development

```python
# my_package/metrics/custom.py
from openagent_eval.metrics import BaseMetric, MetricResult

class MyMetric(BaseMetric):
    name = "my_metric"
    description = "My custom metric"
    
    def evaluate(self, answer: str, context: str, **kwargs) -> MetricResult:
        # Your evaluation logic
        score = calculate_my_score(answer, context)
        return MetricResult(
            score=score,
            reason=f"My score: {score:.2f}",
            metadata={"details": "..."}
        )
```

```toml
# pyproject.toml
[project.entry-points."openagent_eval.metrics"]
my_metric = "my_package.metrics.custom:MyMetric"
```

---

## Common Patterns

### Pattern: A/B Testing

```python
from openagent_eval import Evaluator

evaluator = Evaluator(config)

# Test two different prompts
result_a = evaluator.evaluate(prompt_version="v1")
result_b = evaluator.evaluate(prompt_version="v2")

if result_b.overall_score > result_a.overall_score:
    print("Prompt v2 is better!")
```

### Pattern: Regression Testing

```python
from openagent_eval import Evaluator

evaluator = Evaluator(config)

# Run evaluation
result = evaluator.evaluate()

# Check against thresholds
assert result.metrics["faithfulness"].score >= 0.9, "Faithfulness regression!"
assert result.metrics["latency"].score <= 1000, "Latency regression!"
```

### Pattern: Continuous Evaluation

```python
# In CI/CD pipeline
import subprocess
import sys

result = subprocess.run(
    ["oaeval", "run", "config.yaml", "--output", "json"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("Evaluation failed!")
    sys.exit(1)

# Parse results and check thresholds
import json
results = json.loads(result.stdout)

if results["overall_score"] < 0.8:
    print("Quality below threshold!")
    sys.exit(1)
```

---

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'openagent_eval'`

**Solution:**

```bash
pip install -e .
# or
uv add -e .
```

**Issue:** `ConfigurationError: Missing required field`

**Solution:**

Check your `config.yaml` has all required fields:

```yaml
dataset: data/questions.json  # Required
llm:
  provider: openai  # Required
  model: gpt-4o     # Required
```

**Issue:** `ProviderError: API key not found`

**Solution:**

Set environment variable:

```bash
export OPENAI_API_KEY="your-api-key"
```

### Getting Help

- Check the [Documentation](docs/)
- Search [GitHub Issues](https://github.com/OpenAgentHQ/openagent-eval/issues)
- Join our [Discord](https://discord.gg/openagent-eval)

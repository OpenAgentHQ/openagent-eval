# Examples

Practical, copy-paste examples for common OpenAgent Eval workflows.

## Minimal CLI evaluation

```bash
oaeval init
oaeval run config.yaml
oaeval report latest
```

## Dataset formats

### JSON

```json title="data/questions.json"
[
  {
    "question": "What is RAG?",
    "reference": "Retrieval-Augmented Generation.",
    "context": ["RAG combines retrieval with generation."]
  }
]
```

### JSONL

```json title="data/questions.jsonl"
{"question": "What is RAG?", "reference": "Retrieval-Augmented Generation.", "context": ["RAG combines retrieval with generation."]}
```

### CSV

```csv title="data/questions.csv"
question,reference,context
What is RAG?,Retrieval-Augmented Generation.,"RAG combines retrieval with generation."
```

### Hugging Face dataset

```yaml title="config.yaml"
dataset:
  type: hf
  name: my-org/rag-eval
  split: test
```

## SDK: evaluate in a pytest suite

```python title="tests/test_eval.py"
import pytest
from openagent_eval import Evaluator

@pytest.fixture(scope="module")
def evaluator():
    return Evaluator(config_path="config.yaml")

def test_faithfulness(evaluator):
    result = evaluator.evaluate("data/questions.json")
    assert result.summary["faithfulness"] >= 0.8

def test_no_hallucination(evaluator):
    result = evaluator.evaluate("data/questions.json")
    assert result.summary["hallucination"] <= 0.1
```

## SDK: custom metric

```python title="my_metric.py"
from openagent_eval.metrics.base import BaseMetric

class LengthMetric(BaseMetric):
    name = "length"

    def score(self, *, answer, **kwargs) -> float:
        return min(len(answer) / 500.0, 1.0)
```

Register it:

```python
from openagent_eval.plugins import PluginManager
from my_metric import LengthMetric

PluginManager().register("metric", LengthMetric)
```

See the full template at `openagent_eval/plugins/examples/custom_metric.py`.

## Comparing experiments

```bash
oaeval run config-a.yaml --output json
oaeval run config-b.yaml --output json
oaeval compare exp-001 exp-002
```

## Generating an HTML report

```bash
oaeval run config.yaml --output html
```

Reports are written to `output_dir` (default `./reports`).

## Using a local model (Ollama)

```yaml title="config.yaml"
llm:
  provider: ollama
  model: llama3.1
```

No API key is required.

## Next steps

- Reference the [API Reference](api.md) for every class.
- Run the commands from the [CLI Reference](cli.md).

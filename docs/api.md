# API Reference

OpenAgent Eval exposes a small, stable public API for embedding evaluations in Python code and tests.

## Top-level entry point

### `Evaluator`

```python
from openagent_eval import Evaluator

evaluator = Evaluator(config_path="config.yaml")
result = evaluator.evaluate(dataset)
```

| Parameter | Type | Description |
| --- | --- | --- |
| `config_path` | `str` | Path to a `config.yaml` file |
| `config` | `dict` \| `ConfigModel` | In-memory configuration (alternative to `config_path`) |

`evaluate(dataset)` accepts a dataset path or a list of `DatasetItem` objects and returns a
`EvaluationResult` with a `.summary` dictionary of metric scores.

## Configuration models

Located in `openagent_eval.config.models`:

```python
from openagent_eval.config.models import ConfigModel, LLMConfig, RetrieverConfig

config = ConfigModel(
    dataset="data/questions.json",
    llm=LLMConfig(provider="openai", model="gpt-4o"),
    retriever=RetrieverConfig(provider="chroma", settings={"collection_name": "docs"}),
    metrics=["faithfulness", "answer_relevancy"],
)
```

## Datasets

`openagent_eval.datasets` normalizes inputs into `DatasetItem`:

```python
from openagent_eval.datasets import DatasetItem

item = DatasetItem(
    question="What is RAG?",
    reference="Retrieval-Augmented Generation.",
    context=["RAG combines retrieval with generation."],
)
```

Loaders: `json_loader`, `jsonl_loader`, `csv_loader`, `hf_loader`, `pdf_loader`, selected automatically
by the `factory`.

## Providers

### LLM base class

```python
from openagent_eval.providers.base import BaseLLMProvider

class MyLLM(BaseLLMProvider):
    def complete(self, prompt: str) -> str:
        ...
```

Built-in implementations live under `openagent_eval.providers.llm` (openai, gemini, anthropic, groq,
openrouter, ollama).

### Retriever base class

```python
from openagent_eval.providers.base import BaseRetrieverProvider

class MyRetriever(BaseRetrieverProvider):
    def retrieve(self, query: str, k: int) -> list[str]:
        ...
```

Built-in implementations live under `openagent_eval.providers.retrievers` (chroma).

## Metrics

All metrics implement `openagent_eval.metrics.base.BaseMetric`:

```python
from openagent_eval.metrics.base import BaseMetric

class MyMetric(BaseMetric):
    name = "my_metric"

    def score(self, *, question, answer, context, reference, **kwargs) -> float:
        ...
```

Available groups:

- `openagent_eval.metrics.retrieval` — precision, recall, recall_at_k, precision_at_k, hit_rate, mrr, ndcg
- `openagent_eval.metrics.generation` — faithfulness, relevancy, hallucination, similarity, exact_match, f1, bleu, rouge, bertscore
- `openagent_eval.metrics.performance` — latency
- `openagent_eval.metrics.cost` — tokens

## Reports

`openagent_eval.reports.ReportManager` renders results:

```python
from openagent_eval.reports import ReportManager

ReportManager().render(result, format="html", output_dir="./reports")
```

Formats: `terminal`, `markdown`, `html`, `json`, `comparison`.

## Plugins

Register custom components through the plugin manager:

```python
from openagent_eval.plugins import PluginManager

PluginManager().register("metric", MyMetric)
```

See `openagent_eval/plugins/examples/custom_metric.py` for a complete template.

## Exceptions

All errors derive from `openagent_eval.exceptions.base.OpenAgentEvalError`:

```python
from openagent_eval.exceptions import (
    ConfigurationError,
    DatasetError,
    MetricError,
    ProviderError,
    PluginError,
)
```

## Next steps

- Put it together in [Examples](examples.md).
- Understand the moving parts in [Architecture](architecture.md).

# Examples

Practical, copy-paste examples for common OpenAgent Eval workflows.

## Minimal CLI evaluation

```bash
oaeval init
oaeval run config.yaml
oaeval report latest
```

## Quick start: evaluate from Python

`Engine.run` is `async`. This minimal script uses the built-in `mock` providers so it runs offline with no API keys:

```python title="quick_eval.py"
import asyncio

from openagent_eval.config.models import Config
from openagent_eval.core.engine import Engine

# A tiny dataset you can inline. To load a file instead, use
# load_dataset(DatasetConfig(path="data/questions.json")).
dataset = [
    {
        "question": "What is RAG?",
        "ground_truth": "Retrieval-Augmented Generation.",
        "context": "RAG combines retrieval with generation.",
    },
]

config = Config(
    dataset={"path": "data/questions.json"},  # required; unused when items are passed directly
    llm={"provider": "mock", "model": "mock"},
    retriever={"provider": "mock"},
    metrics={"generation": ["faithfulness"]},
)


async def main() -> None:
    engine = Engine(config)
    try:
        report = await engine.run(dataset)
    finally:
        engine.shutdown()
    print(report.summary)


if __name__ == "__main__":
    asyncio.run(main())
```

Swap `llm.provider: mock` for `openai`, `anthropic`, `gemini`, `groq`, or `ollama` (with a real model ID) and the same script calls your model. API keys are read from the matching environment variable (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, ...) when `api_key` is omitted.

## Dataset formats

### JSON

```json title="data/questions.json"
[
  {
    "question": "What is RAG?",
    "ground_truth": "Retrieval-Augmented Generation.",
    "context": "RAG combines retrieval with generation."
  }
]
```

### JSONL

```json title="data/questions.jsonl"
{"question": "What is RAG?", "ground_truth": "Retrieval-Augmented Generation.", "context": "RAG combines retrieval with generation."}
```

### CSV

```csv title="data/questions.csv"
question,ground_truth,context
What is RAG?,Retrieval-Augmented Generation.,"RAG combines retrieval with generation."
```

Format is auto-detected from the file extension (`json`, `jsonl`, `csv`, `pdf`).

## SDK: evaluate in a pytest suite

`Engine.run` is `async`, so wrap it in `asyncio.run`:

```python title="tests/test_eval.py"
import asyncio

from openagent_eval.config.models import Config
from openagent_eval.core.engine import Engine
from openagent_eval.datasets.factory import load_dataset


def test_faithfulness():
    config = Config(
        dataset={"path": "data/questions.json"},
        llm={"provider": "openai", "model": "gpt-4o-mini"},
        retriever={"provider": "chroma", "settings": {"collection_name": "my_collection"}},
        metrics={"generation": ["faithfulness"], "retrieval": ["context_precision"]},
    )
    engine = Engine(config)
    dataset = load_dataset(config.dataset)
    report = asyncio.run(engine.run(dataset))

    assert report.summary["metrics_summary"]["faithfulness"] >= 0.8
    assert report.summary["failed_evaluations"] == 0
```

## SDK: custom metric

Subclass `BaseMetric` and register it in `METRIC_REGISTRY`:

```python title="my_metric.py"
from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.metrics import METRIC_REGISTRY


class LengthMetric(BaseMetric):
    name = "length"
    description = "Normalized answer length"

    def evaluate(self, **kwargs) -> MetricResult:
        answer = kwargs.get("answer", "")
        score = min(len(answer.split()) / 100.0, 1.0)
        return MetricResult(score=score, reason=f"{len(answer.split())} words")


METRIC_REGISTRY["length"] = LengthMetric
```

Then reference it in your config: `metrics.generation: [faithfulness, length]`.

See the full template at `openagent_eval/plugins/examples/custom_metric.py`.

## Comparing experiments

```bash
oaeval run config-a.yaml --output json
oaeval run config-b.yaml --output json
oaeval compare exp-001 exp-002
```

## SDK: compare two models

Evaluate the same dataset with two different LLMs (here GPT-4o vs Claude) and pick the model with the stronger score. Set `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` before running:

```python title="compare_models.py"
import asyncio

from openagent_eval.config.models import Config, DatasetConfig
from openagent_eval.core.engine import Engine
from openagent_eval.datasets.factory import load_dataset


async def score_model(config: Config, dataset: list) -> dict:
    engine = Engine(config)
    try:
        report = await engine.run(dataset)
    finally:
        engine.shutdown()
    return report.summary["metrics_summary"]


async def main() -> None:
    dataset = load_dataset(DatasetConfig(path="data/questions.json", format="json"))

    candidates = [
        ("gpt-4o", "openai"),
        ("claude-3-5-sonnet", "anthropic"),
    ]

    scores = {}
    for name, provider in candidates:
        config = Config(
            dataset={"path": "data/questions.json"},
            llm={"provider": provider, "model": name},
            retriever={"provider": "mock"},
            metrics={"generation": ["faithfulness", "answer_relevancy"]},
        )
        scores[name] = await score_model(config, dataset)
        print(f"{name}: {scores[name]}")

    winner = max(scores, key=lambda name: scores[name].get("faithfulness", 0.0))
    print(f"\nWinner on faithfulness: {winner}")


if __name__ == "__main__":
    asyncio.run(main())
```

To keep a permanent record of each run for later `oaeval compare`, point `report.output` at `json` in the config, or save reports to disk from the SDK.

## Generating an HTML report

```bash
oaeval run config.yaml --output html
```

Reports are written to `report.output_dir` (default `./reports`).

## Offline dry-run (no API keys)

Use the built-in `mock` providers for CI or local experimentation:

```yaml title="config.yaml"
llm:
  provider: mock
retriever:
  provider: mock
```

## Using a local model (Ollama)

```yaml title="config.yaml"
llm:
  provider: ollama
  model: llama3.1
```

No API key is required.

## Local vector retrieval

Memory/BM25/FAISS retrievers embed locally via an embedder:

```yaml title="config.yaml"
retriever:
  provider: memory
  embedder:
    provider: sentence_transformers
    model: all-MiniLM-L6-v2
```

## CI/CD integration

Gate merges on evaluation scores with `oaeval test`. It runs your config and exits non-zero if any threshold fails, so a workflow step (and thus the whole job) fails when quality drops:

```yaml title=".github/workflows/eval.yml"
name: evaluation
on:
  pull_request:
  push:
    branches: [main]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install "openagent-eval[evaluation]"
      - name: Run evaluation with thresholds
        run: oaeval test config.yaml -t faithfulness:gte:0.8 -t answer_relevancy:gte:0.7 --json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Threshold format is `metric:operator:value` with operators `gt`, `gte`, `lt`, `lte`, `eq`, `neq`. For offline CI runs (no external APIs), use the `mock` providers from the [offline dry-run](#offline-dry-run-no-api-keys) section.

If you prefer pytest, the built-in plugin gives the same gating as a test:

```python title="tests/test_eval_gate.py"
from openagent_eval.cicd import OAEvalPlugin


def test_rag_gate():
    result = OAEvalPlugin.run_evaluation(
        "config.yaml",
        thresholds=["faithfulness:gte:0.8", "answer_relevancy:gte:0.7"],
    )
    assert result.passed, result.summary
```

## Batch evaluation

Run several configs programmatically and compare their summaries to pick the best combination:

```python title="batch_eval.py"
import asyncio

from openagent_eval.config.loader import load_config
from openagent_eval.config.models import DatasetConfig
from openagent_eval.core.engine import Engine
from openagent_eval.datasets.factory import load_dataset


async def evaluate(config_path: str, dataset: list) -> dict:
    engine = Engine(load_config(config_path))
    try:
        report = await engine.run(dataset)
    finally:
        engine.shutdown()
    return report.summary["metrics_summary"]


async def main() -> None:
    dataset = load_dataset(DatasetConfig(path="data/questions.json", format="json"))

    configs = [
        "configs/retriever-a.yaml",
        "configs/retriever-b.yaml",
        "configs/retriever-c.yaml",
    ]

    scores = {}
    for path in configs:
        scores[path] = await evaluate(path, dataset)
        print(f"{path}: {scores[path]}")

    best = max(scores, key=lambda path: scores[path].get("faithfulness", 0.0))
    print(f"\nBest config on faithfulness: {best}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Next steps

- Reference the [API Reference](api.md) for every class.
- Run the commands from the [CLI Reference](cli.md).

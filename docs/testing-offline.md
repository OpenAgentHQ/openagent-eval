# Testing Offline

OpenAgent Eval includes deterministic mock LLM and retriever providers. Use
them to exercise configuration loading, dataset ingestion, metrics, and report
generation without API keys, network calls, or a vector database.

This mode is useful for:

- checking a new installation before configuring credentials;
- running fast smoke tests in CI;
- developing report and metric integrations locally;
- learning the evaluation workflow without incurring provider costs.

Mock scores only prove that the evaluation pipeline works. They do not measure
the quality of a production model or retriever.

## Run an offline evaluation

Create a small dataset whose rows include both `ground_truth` and
`ground_truth_contexts`:

```json title="data/offline-smoke.json"
[
  {
    "question": "What does RAG combine?",
    "ground_truth": "RAG combines retrieval with generation.",
    "ground_truth_contexts": [
      "Retrieval-Augmented Generation combines retrieval with generation."
    ]
  }
]
```

Configure both mock providers:

```yaml title="offline.yaml"
dataset:
  path: data/offline-smoke.json

llm:
  provider: mock
  model: mock-model

retriever:
  provider: mock

metrics:
  retrieval:
    - context_precision
    - context_recall
  generation:
    - exact_match
  performance:
    - latency

report:
  output: terminal
  output_dir: ./reports
```

Validate and run it with no provider environment variables set:

```bash
oaeval validate offline.yaml
oaeval run offline.yaml
```

The mock LLM returns each row's `ground_truth`. The mock retriever returns its
`ground_truth_contexts` as retrieved documents. Exact-match and retrieval
scores should therefore be perfect for this fixture; that is an assertion
about the harness, not a quality benchmark.

## Use it from Python

The same path can be embedded in a test without loading a configuration file:

```python title="test_offline_eval.py"
import asyncio

from openagent_eval.config.models import Config
from openagent_eval.core.engine import Engine


def test_evaluation_pipeline_offline() -> None:
    config = Config(
        dataset={"path": "data/offline-smoke.json"},
        llm={"provider": "mock", "model": "mock-model"},
        retriever={"provider": "mock"},
        metrics={
            "retrieval": ["context_precision", "context_recall"],
            "generation": ["exact_match"],
        },
    )
    dataset = [
        {
            "question": "What does RAG combine?",
            "ground_truth": "RAG combines retrieval with generation.",
            "ground_truth_contexts": [
                "Retrieval-Augmented Generation combines retrieval with generation."
            ],
        }
    ]

    engine = Engine(config)
    try:
        report = asyncio.run(engine.run(dataset))
    finally:
        engine.shutdown()

    assert report.summary["failed_evaluations"] == 0
    assert report.summary["metrics_summary"]["exact_match"] == 1.0
```

## Add a CI smoke test

Keep the offline dataset and configuration in the repository, then run the
same commands after installing the package:

```yaml title=".github/workflows/eval-smoke.yml"
name: Evaluation smoke test

on:
  pull_request:

jobs:
  offline-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install openagent-eval
      - run: oaeval validate offline.yaml
      - run: oaeval run offline.yaml
```

No secrets are required for this job. Keep the fixture small so it remains a
fast pipeline check, and run real-provider evaluations separately when model or
retrieval quality is the subject under test.

## Move to real providers

When the offline path is green, replace one mock at a time. Point `llm.provider`
at a supported model provider to evaluate generation, or replace
`retriever.provider` to evaluate a real retrieval system. See the
[Mock LLM](providers/llm/mock.md) and
[Mock retriever](providers/retrievers/mock.md) pages for provider behavior and
configuration details.

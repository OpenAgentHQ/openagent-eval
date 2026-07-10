# Mock LLM

The Mock LLM provider is a **fully offline, deterministic** provider. It returns
the dataset's `ground_truth` (when available) instead of calling any model. It
needs no API key and installs nothing extra.

## When should you use this?

- **Your very first run** — verify the whole pipeline works before spending money.
- **CI / automated tests** — evaluate without credentials or network.
- **Learning the workflow** — focus on metrics and reports, not model output.

## Prerequisites

None. It is built in.

```bash
pip install openagent-eval
```

## Step 1 — Configure

```yaml title="config.yaml"
llm:
  provider: mock
  model: mock-model
  temperature: 0.0
```

Because the mock returns `ground_truth`, generation metrics (faithfulness,
answer relevancy, semantic similarity) will score near perfect — that is expected
and useful for testing the harness itself.

## Step 2 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_mock.py"
import asyncio

from openagent_eval.config.models import Config, LLMConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm=LLMConfig(provider="mock", model="mock-model", temperature=0.0),
    retriever={"provider": "mock"},
    metrics={"generation": ["faithfulness", "answer_relevancy"]},
)

engine = Engine(config)
report = asyncio.run(engine.run(dataset))
print(report.summary["metrics_summary"])
```

## All configuration options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `provider` | `str` | — | Must be `mock`. |
| `model` | `str` | `mock-model` | Informational only. |
| `temperature` | `float` | `0.0` | Ignored. |
| `api_key` | `str \| null` | `null` | Ignored. |
| `max_tokens` | `int \| null` | `null` | Ignored. |

## How it behaves

- `generate(prompt, ground_truth=...)` → returns `ground_truth` if given, else a
  deterministic echo of the prompt.
- Token usage and latency are approximated locally (whitespace token count,
  sub-millisecond timing).

## Troubleshooting

- Scores look "too good"? That is correct for the mock — it echoes ground truth.
  Swap in a real provider (e.g. [openai](openai.md)) for realistic scores.

## Related

- Pair with the [mock retriever](../retrievers/mock.md) for a 100% offline run.
- See all LLMs in [index.md](index.md).

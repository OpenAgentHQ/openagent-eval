# Groq

The Groq provider uses the `groq` SDK (async) to evaluate with fast open-weight
models (Llama, Mixtral, Gemma) served by Groq's high-throughput infrastructure.

## When should you use this?

Use it when you want **very low-latency** inference or prefer open-weight models
without running them yourself.

## Prerequisites

- Install the provider extra:
  ```bash
  pip install "openagent-eval[providers]"
  ```
  (installs the `groq` SDK)
- A Groq API key.

## Step 1 — Install

```bash
pip install "openagent-eval[providers]"
```

## Step 2 — Set your API key

```bash
export GROQ_API_KEY=gsk_...
```

## Step 3 — Configure

```yaml title="config.yaml"
llm:
  provider: groq
  model: llama-3.3-70b-versatile
  temperature: 0.0
```

## Step 4 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_groq.py"
import asyncio

from openagent_eval.config.models import Config, LLMConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm=LLMConfig(provider="groq", model="llama-3.3-70b-versatile", temperature=0.0),
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
| `provider` | `str` | — | Must be `groq`. |
| `model` | `str` | `llama-3.3-70b-versatile` | Any Groq-served model id. |
| `temperature` | `float` | `0.0` | `0.0`–`2.0`. |
| `api_key` | `str \| null` | `null` | Falls back to `GROQ_API_KEY`. |
| `max_tokens` | `int \| null` | `null` | Caps completion length. |

## Troubleshooting

- **`ProviderConnectionError: Groq API key not provided`** — set `GROQ_API_KEY`
  or pass `api_key`.
- **`ProviderError: ... groq ...`** — the `groq` package is missing; run
  `pip install "openagent-eval[providers]"`.

## Related

- Compare with other LLMs in [index.md](index.md).
- Pair with any retriever from [../retrievers/index.md](../retrievers/index.md).

# OpenAI

The OpenAI provider uses the official `openai` SDK (async) and is the easiest
cloud LLM to start with. `gpt-4o-mini` is cheap, fast, and great for evaluation.

## When should you use this?

Use it when you already use OpenAI models, or want the smoothest first evaluation.
It is the recommended **first real provider** for beginners.

## Prerequisites

- Install the provider extra:
  ```bash
  pip install "openagent-eval[providers]"
  ```
  (installs `openai` + `tiktoken`; `tiktoken` powers accurate token counting)
- An OpenAI API key.

## Step 1 — Install

```bash
pip install "openagent-eval[providers]"
```

## Step 2 — Set your API key

```bash
export OPENAI_API_KEY=sk-...
```

You can also put the key directly in `config.yaml` (`llm.api_key`), but the env
var is safer.

## Step 3 — Configure

```yaml title="config.yaml"
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0
  # api_key: sk-...   # optional; falls back to OPENAI_API_KEY
```

## Step 4 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_openai.py"
import asyncio

from openagent_eval.config.models import Config, LLMConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm=LLMConfig(provider="openai", model="gpt-4o-mini", temperature=0.0),
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
| `provider` | `str` | — | Must be `openai`. |
| `model` | `str` | `gpt-4o` | Any OpenAI chat model, e.g. `gpt-4o-mini`, `gpt-4o`. |
| `temperature` | `float` | `0.0` | `0.0`–`2.0`. Use `0.0` for reproducible eval. |
| `api_key` | `str \| null` | `null` | Falls back to `OPENAI_API_KEY`. |
| `max_tokens` | `int \| null` | `null` | Caps completion length. |

## Troubleshooting

- **`ProviderConnectionError: OpenAI API key not provided`** — set `OPENAI_API_KEY`
  or pass `api_key`.
- **`ProviderError: ... openai ...`** — the `openai` package is missing; run
  `pip install "openagent-eval[providers]"`.
- **Wrong token counts** — ensure `tiktoken` is installed so counting uses the
  correct tokenizer instead of a rough estimate.

## Related

- Compare with other LLMs in [index.md](index.md).
- Pair with any retriever from [../retrievers/index.md](../retrievers/index.md).

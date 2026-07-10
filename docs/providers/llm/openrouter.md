# OpenRouter

The OpenRouter provider is a **single gateway** to hundreds of models (OpenAI,
Anthropic, Meta, Mistral, and more) through one OpenAI-compatible API. It only
needs `httpx` — no provider-specific SDK.

## When should you use this?

Use it to **compare many models with one key**, or to access models that aren't
directly supported by the other providers.

## Prerequisites

- No extra package needed (`httpx` is already a dependency).
- An OpenRouter API key.

## Step 1 — Install

OpenRouter needs nothing beyond the base install:

```bash
pip install openagent-eval
```

## Step 2 — Set your API key

```bash
export OPENROUTER_API_KEY=sk-or-...
```

## Step 3 — Configure

Model names use the `provider/model` form (see OpenRouter's model catalog):

```yaml title="config.yaml"
llm:
  provider: openrouter
  model: openai/gpt-4o-mini
  temperature: 0.0
```

Other examples: `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct`.

## Step 4 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_openrouter.py"
import asyncio

from openagent_eval.config.models import Config, LLMConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm=LLMConfig(provider="openrouter", model="openai/gpt-4o-mini", temperature=0.0),
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
| `provider` | `str` | — | Must be `openrouter`. |
| `model` | `str` | `openai/gpt-4o-mini` | `provider/model` id from OpenRouter. |
| `temperature` | `float` | `0.0` | `0.0`–`2.0`. |
| `api_key` | `str \| null` | `null` | Falls back to `OPENROUTER_API_KEY`. |
| `max_tokens` | `int \| null` | `null` | Caps completion length. |
| `base_url` | `str` | `https://openrouter.ai/api/v1` | Override only via direct instantiation. |

!!! warning "`base_url` is not settable via config"
    The factory builds the provider with only the `LLMConfig`, so `base_url`
    always uses the default. To customize it, instantiate the class directly:

    ```python
    from openagent_eval.providers.llm.openrouter import OpenRouter
    llm = OpenRouter(api_key="sk-or-...", model="openai/gpt-4o-mini",
                     base_url="https://your-proxy/v1")
    ```

## Troubleshooting

- **`ProviderConnectionError: OpenRouter API key not provided`** — set
  `OPENROUTER_API_KEY`.
- **Model not found** — double-check the `provider/model` spelling on the
  OpenRouter dashboard.

## Related

- Compare with other LLMs in [index.md](index.md).
- Pair with any retriever from [../retrievers/index.md](../retrievers/index.md).

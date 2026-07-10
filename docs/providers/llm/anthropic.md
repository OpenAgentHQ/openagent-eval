# Anthropic

The Anthropic provider uses the official `anthropic` SDK (async) to evaluate with
Claude models.

## When should you use this?

Use it if you run Claude in production or want to compare Claude against other
LLMs in your evaluations.

## Prerequisites

- Install the provider extra:
  ```bash
  pip install "openagent-eval[providers]"
  ```
  (installs the `anthropic` SDK)
- An Anthropic API key.

## Step 1 — Install

```bash
pip install "openagent-eval[providers]"
```

## Step 2 — Set your API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Step 3 — Configure

```yaml title="config.yaml"
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.0
  max_tokens: 1024
```

!!! warning "`max_tokens` is required by the API"
    Unlike most providers, Anthropic's Messages API **requires** a max output
    length. OpenAgent Eval defaults it to `4096`, but you should set it
    explicitly (e.g. `1024`) so long answers are not truncated mid-evaluation.

## Step 4 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_anthropic.py"
import asyncio

from openagent_eval.config.models import Config, LLMConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm=LLMConfig(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        temperature=0.0,
        max_tokens=1024,
    ),
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
| `provider` | `str` | — | Must be `anthropic`. |
| `model` | `str` | `claude-sonnet-4-20250514` | Any Claude model id. |
| `temperature` | `float` | `0.0` | `0.0`–`2.0`. |
| `api_key` | `str \| null` | `null` | Falls back to `ANTHROPIC_API_KEY`. |
| `max_tokens` | `int` | `4096` | **Required by the API.** Caps completion length. |

## Troubleshooting

- **`ProviderConnectionError: Anthropic API key not provided`** — set
  `ANTHROPIC_API_KEY` or pass `api_key`.
- **Truncated answers / low scores** — raise `max_tokens`; the default `4096`
  may cut long generations.
- **Token counts look off** — Anthropic counts tokens with its own endpoint
  (not tiktoken), which is the correct count for Claude.

## Related

- Compare with other LLMs in [index.md](index.md).
- Pair with any retriever from [../retrievers/index.md](../retrievers/index.md).

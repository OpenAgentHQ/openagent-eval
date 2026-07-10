# Gemini

The Gemini provider uses Google's `google-genai` SDK (async) to evaluate with
Gemini models.

## When should you use this?

Use it if you run Gemini in production or want Google's models in your eval mix.

## Prerequisites

- Install the provider extra:
  ```bash
  pip install "openagent-eval[providers]"
  ```
  (installs `google-genai`)
- A Gemini API key.

## Step 1 — Install

```bash
pip install "openagent-eval[providers]"
```

## Step 2 — Set your API key

```bash
export GEMINI_API_KEY=...
```

!!! danger "Use `GEMINI_API_KEY`, not `GOOGLE_API_KEY`"
    OpenAgent Eval reads the key from **`GEMINI_API_KEY`**. The older
    `GOOGLE_API_KEY` name is **not** recognized by this provider.

## Step 3 — Configure

```yaml title="config.yaml"
llm:
  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
```

## Step 4 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_gemini.py"
import asyncio

from openagent_eval.config.models import Config, LLMConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm=LLMConfig(provider="gemini", model="gemini-2.5-flash", temperature=0.0),
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
| `provider` | `str` | — | Must be `gemini`. |
| `model` | `str` | `gemini-2.5-flash` | Any Gemini model id. |
| `temperature` | `float` | `0.0` | `0.0`–`2.0`. |
| `api_key` | `str \| null` | `null` | Falls back to `GEMINI_API_KEY`. |
| `max_tokens` | `int \| null` | `null` | Caps completion length. |

## Troubleshooting

- **`ProviderConnectionError: Gemini API key not provided`** — set
  `GEMINI_API_KEY` (not `GOOGLE_API_KEY`).
- **`ProviderError: ... google-genai ...`** — the `google-genai` package is
  missing; run `pip install "openagent-eval[providers]"`.

## Related

- Compare with other LLMs in [index.md](index.md).
- Pair with any retriever from [../retrievers/index.md](../retrievers/index.md).

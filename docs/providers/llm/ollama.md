# Ollama

The Ollama provider runs models **locally** on your machine — no API key, no
cloud, fully private. Great for offline evaluation and cost-free experimentation.

## When should you use this?

Use it when you want **local, private, free** inference, or to evaluate open-weight
models you already serve with Ollama.

## Prerequisites

- [Ollama](https://ollama.com) installed and running (`ollama serve`).
- A model pulled, e.g. `ollama pull llama3.2`.
- No extra Python package needed (`httpx` is already a dependency).

## Step 1 — Install & start Ollama

```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2
ollama list            # confirm it is available
```

OpenAgent Eval connects to `http://localhost:11434` by default.

## Step 2 — Configure

No API key required:

```yaml title="config.yaml"
llm:
  provider: ollama
  model: llama3.2
  temperature: 0.0
```

## Step 3 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_ollama.py"
import asyncio

from openagent_eval.config.models import Config, LLMConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm=LLMConfig(provider="ollama", model="llama3.2", temperature=0.0),
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
| `provider` | `str` | — | Must be `ollama`. |
| `model` | `str` | `llama3.2` | Any pulled Ollama model. |
| `temperature` | `float` | `0.7` | **Note:** defaults to `0.7` (not `0.0` like other providers). |
| `max_tokens` | `int \| null` | `null` | Caps completion length. |
| `base_url` | `str` | `http://localhost:11434` | **Not settable via config** — see warning. |
| `timeout` | `float` | `120.0` | **Not settable via config** — see warning. |

!!! warning "Defaults differ from other providers"
    - `temperature` defaults to **`0.7`** here (set `0.0` for reproducible eval).
    - `base_url` and `timeout` are **ignored when set via config** — the factory
      only passes the `LLMConfig`, so Ollama always uses
      `http://localhost:11434`. To point at a different host/port, instantiate
      directly:

      ```python
      from openagent_eval.providers.llm.ollama import Ollama
      llm = Ollama(model="llama3.2", base_url="http://192.168.1.10:11434")
      ```

!!! warning "Different return type"
    Ollama's `generate_with_usage(...)` returns a **`tuple[str, TokenUsage]`**
    (not the `LLMResponse` that other providers return). The Engine handles this
    internally, but be aware of it if you call the provider directly.

## Troubleshooting

- **Connection refused** — make sure `ollama serve` is running and the model is
  pulled (`ollama list`).
- **Non-deterministic scores** — set `temperature: 0.0` (default is `0.7`).

## Related

- Compare with other LLMs in [index.md](index.md).
- Pair with any retriever from [../retrievers/index.md](../retrievers/index.md).

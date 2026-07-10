# LLM Providers

LLM providers generate the answers that OpenAgent Eval scores. Choose the one you
already use in production, set its API key, and you are ready to evaluate.

## Which one should a beginner pick?

- **Never used one before?** Start with [`mock`](mock.md) — zero setup, runs offline.
- **Want the easiest real cloud LLM?** Use [`openai`](openai.md) (`gpt-4o-mini` is cheap and fast).
- **Prefer open-weight models, fully local?** Use [`ollama`](ollama.md) — no API key.
- **Want many models through one key?** Use [`openrouter`](openrouter.md).

## Comparison matrix

| Provider | Install extra | API key env var | Default model | Needs key? |
|----------|---------------|----------------|---------------|-----------|
| [OpenAI](openai.md) | `openagent-eval[providers]` | `OPENAI_API_KEY` | `gpt-4o` | ✅ |
| [Anthropic](anthropic.md) | `openagent-eval[providers]` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` | ✅ |
| [Gemini](gemini.md) | `openagent-eval[providers]` | `GEMINI_API_KEY` | `gemini-2.5-flash` | ✅ |
| [Groq](groq.md) | `openagent-eval[providers]` | `GROQ_API_KEY` | `llama-3.3-70b-versatile` | ✅ |
| [OpenRouter](openrouter.md) | *(none — uses `httpx`)* | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` | ✅ |
| [Ollama](ollama.md) | *(none — uses `httpx`)* | — (local) | `llama3.2` | ❌ |
| [Mock](mock.md) | *(built-in)* | — | `mock-model` | ❌ |

## Common configuration

All LLM providers share the same four settings:

```yaml title="config.yaml"
llm:
  provider: openai          # one of the names above
  model: gpt-4o-mini        # any model the provider supports
  temperature: 0.0          # 0.0 disables randomness (recommended for eval)
  api_key: sk-...           # optional; falls back to the env var
```

| Setting | Type | Default | Notes |
|---------|------|---------|-------|
| `provider` | `str` | — | Required. One of the names in the matrix. |
| `model` | `str` | provider-specific | Model id, e.g. `gpt-4o-mini`, `claude-sonnet-4-20250514`. |
| `temperature` | `float` | `0.0` | Range `0.0`–`2.0`. Use `0.0` for reproducible eval. |
| `api_key` | `str \| null` | `null` | If omitted, read from the env var. Must be ≥ 10 chars if set. |
| `max_tokens` | `int \| null` | provider-specific | Caps completion length. Anthropic requires it (default 4096). |

## Next steps

- Pick a provider above and open its page for a full walkthrough.
- Pair your LLM with a retriever from [../retrievers/index.md](../retrievers/index.md).
- Need embeddings? See [../embedders/index.md](../embedders/index.md).

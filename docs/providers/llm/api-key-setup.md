---
tags:
  - guide
  - providers
  - configuration
---

# LLM API key setup

Hosted LLM providers need an API key before `oaeval run` can call them. This page
lists the exact environment variable each provider reads, where to get a key, and a
minimal `config.yaml` snippet you can use.

!!! tip "Prefer environment variables"
    Put keys in the environment rather than `config.yaml`. If you do set
    `llm.api_key`, it takes priority over the environment variable.

## Quick reference

| Provider | Environment variable | Required | Default model | Where it is read |
|----------|----------------------|----------|---------------|------------------|
| [OpenAI](#openai) | `OPENAI_API_KEY` | Yes | `gpt-4o` | `openagent_eval/providers/llm/openai.py:114`, `:120` |
| [Anthropic](#anthropic) | `ANTHROPIC_API_KEY` | Yes | `claude-sonnet-4-20250514` | `openagent_eval/providers/llm/anthropic.py:121` |
| [Gemini](#gemini) | `GEMINI_API_KEY` | Yes | `gemini-2.5-flash` | `openagent_eval/providers/llm/gemini.py:128` |
| [Groq](#groq) | `GROQ_API_KEY` | Yes | `llama-3.3-70b-versatile` | `openagent_eval/providers/llm/groq.py:113`, `:120` |
| [OpenRouter](#openrouter) | `OPENROUTER_API_KEY` | Yes | `openai/gpt-4o-mini` | `openagent_eval/providers/llm/openrouter.py:117` |
| [Ollama](#ollama) | — | No | `llama3.2` | No key is read |
| [Mock](#mock) | — | No | `mock-model` | No key is read |

## Setting variables

OpenAgent Eval reads keys straight from the process environment (`os.environ` /
`os.getenv`). Export the variable for the provider you plan to use:

```bash
export OPENAI_API_KEY="sk-..."
```

!!! warning "The CLI does not auto-load `.env` files"
    `oaeval` does not load a `.env` file automatically. To use one, export it
    into your shell first, for example:
    ```bash
    set -a; . ./.env; set +a
    ```

## Provider details

### OpenAI

- **Environment variable:** `OPENAI_API_KEY`
- **Read in code:** `openagent_eval/providers/llm/openai.py:114` and `:120`
- **Default model:** `gpt-4o` (`openagent_eval/providers/llm/openai.py:94`)
- **Get a key:** [OpenAI Platform](https://platform.openai.com/api-keys)
- **Install:** `pip install "openagent-eval[providers]"`

```yaml title="config.yaml"
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0
```

### Anthropic

- **Environment variable:** `ANTHROPIC_API_KEY`
- **Read in code:** `openagent_eval/providers/llm/anthropic.py:121`
- **Default model:** `claude-sonnet-4-20250514` (`openagent_eval/providers/llm/anthropic.py:81`)
- **Get a key:** [Anthropic Console](https://console.anthropic.com/settings/keys)
- **Install:** `pip install "openagent-eval[providers]"`

```yaml title="config.yaml"
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.0
  max_tokens: 1024
```

### Gemini

- **Environment variable:** `GEMINI_API_KEY`
- **Read in code:** `openagent_eval/providers/llm/gemini.py:128`
- **Default model:** `gemini-2.5-flash` (`openagent_eval/providers/llm/gemini.py:91`)
- **Get a key:** [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Install:** `pip install "openagent-eval[providers]"`

```yaml title="config.yaml"
llm:
  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
```

### Groq

- **Environment variable:** `GROQ_API_KEY`
- **Read in code:** `openagent_eval/providers/llm/groq.py:113` and `:120`
- **Default model:** `llama-3.3-70b-versatile` (`openagent_eval/providers/llm/groq.py:83`)
- **Get a key:** [Groq Console](https://console.groq.com/keys)
- **Install:** `pip install "openagent-eval[providers]"`

```yaml title="config.yaml"
llm:
  provider: groq
  model: llama-3.3-70b-versatile
  temperature: 0.0
```

### OpenRouter

- **Environment variable:** `OPENROUTER_API_KEY`
- **Read in code:** `openagent_eval/providers/llm/openrouter.py:117`
- **Default model:** `openai/gpt-4o-mini` (`openagent_eval/providers/llm/openrouter.py:78`)
- **Default base URL:** `https://openrouter.ai/api/v1` (`openagent_eval/providers/llm/openrouter.py:81`)
- **Get a key:** [OpenRouter Keys](https://openrouter.ai/keys)
- **Install:** no extra needed; uses `httpx`, which is a core dependency

```yaml title="config.yaml"
llm:
  provider: openrouter
  model: openai/gpt-4o-mini
  temperature: 0.0
```

### Ollama

- **Environment variable:** none
- **Key required:** No
- **Default server URL:** `http://localhost:11434` (`openagent_eval/providers/llm/ollama.py:108`)
- **Default model:** `llama3.2` (`openagent_eval/providers/llm/ollama.py:109`)
- **Install:** no extra needed; uses `httpx`, which is a core dependency

Start the Ollama server locally, then use:

```yaml title="config.yaml"
llm:
  provider: ollama
  model: llama3.2
  temperature: 0.0
```

### Mock

- **Environment variable:** none
- **Key required:** No
- **Use for:** offline smoke tests and CI

```yaml title="config.yaml"
llm:
  provider: mock
```

## Run

After exporting the right variable:

```bash
oaeval run config.yaml
```

## See also

- [LLM providers overview](index.md)
- [Environment variables reference](../../environment-variables.md)
- [OpenAI provider walkthrough](openai.md)

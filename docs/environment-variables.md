---
tags:
  - reference
  - configuration
---

# Environment Variables

OpenAgent Eval reads a small, fixed set of environment variables. None are
required to import or install the package — they are consulted at runtime, and
only for the provider or feature you actually use. Every variable listed here is
read directly by OpenAgent Eval's own code; the file and line where each one is
consumed is cited so you can trace the behaviour to source.

Variables fall into two groups:

- **[Provider API keys](#provider-api-keys)** — credentials for the hosted LLM
  providers.
- **[Configuration](#configuration)** — where OpenAgent Eval looks for your
  config file.

## Provider API keys

Each hosted LLM provider reads its credential from a single environment
variable. There is **no built-in default** for any key: if the key is neither
passed explicitly (via the `api_key` config field or constructor argument) nor
present in the environment, the provider raises `ProviderConnectionError` at
initialisation.

| Variable | Controls | Default | Example |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | API key for the `openai` LLM provider. | *unset* (no default) | `sk-proj-abc123…` |
| `GEMINI_API_KEY` | API key for the `gemini` LLM provider (Google Gemini). | *unset* (no default) | `AIzaSy…` |
| `ANTHROPIC_API_KEY` | API key for the `anthropic` LLM provider. | *unset* (no default) | `sk-ant-api03-…` |
| `GROQ_API_KEY` | API key for the `groq` LLM provider. | *unset* (no default) | `gsk_…` |
| `OPENROUTER_API_KEY` | API key for the `openrouter` LLM provider. | *unset* (no default) | `sk-or-v1-…` |

**Precedence.** An `api_key` supplied in your `config.yaml` (or passed
programmatically) takes priority; the environment variable is the fallback used
only when no key is configured. For example, the OpenAI adapter resolves
`config.api_key or os.getenv("OPENAI_API_KEY")`.

**Where these are read:**

| Variable | Consumed at |
| --- | --- |
| `OPENAI_API_KEY` | `openagent_eval/providers/llm/openai.py:111`, `:116` |
| `GEMINI_API_KEY` | `openagent_eval/providers/llm/gemini.py:123` |
| `ANTHROPIC_API_KEY` | `openagent_eval/providers/llm/anthropic.py:116` |
| `GROQ_API_KEY` | `openagent_eval/providers/llm/groq.py:105`, `:111` |
| `OPENROUTER_API_KEY` | `openagent_eval/providers/llm/openrouter.py:112` |

The same five keys are also checked (without being consumed) by two
diagnostics:

- `oaeval doctor` reports each key's availability —
  `openagent_eval/cli/commands/doctor.py:87–92`.
- Config validation lists missing keys for the selected provider —
  `openagent_eval/config/validator.py:74–79`.

!!! note "No key required for local models"
    The `ollama` and `mock` providers need no API key. Ollama's server URL is a
    configuration/constructor value (`base_url`, default
    `http://localhost:11434`), not an environment variable.

## Configuration

| Variable | Controls | Default | Example |
| --- | --- | --- | --- |
| `OAEVAL_CONFIG` | Absolute or relative path to the configuration file. When set and pointing at an existing file, it is used ahead of any auto-discovered `config.yaml`/`oaeval.yaml`. | *unset* (falls back to config auto-discovery) | `/etc/oaeval/config.yaml` |

`OAEVAL_CONFIG` is the first entry in the config-discovery order (see
[Config auto-discovery](cli.md#config-auto-discovery)). If it is set but the
path does not exist, discovery returns no config rather than falling through to
the directory search.

**Where it is read:**

- `openagent_eval/cli/utils/discovery.py:15`, `:33` (the resolution logic).
- `openagent_eval/cli/commands/doctor.py:190` (reported by `oaeval doctor`).

## How variables reach the process

OpenAgent Eval reads variables straight from the process environment
(`os.environ` / `os.getenv`). A few points worth knowing:

!!! warning "The CLI does not auto-load `.env` files"
    OpenAgent Eval does **not** depend on `python-dotenv`, and neither the
    library nor the `oaeval` CLI loads a `.env` file automatically. To use a
    `.env` file, export it into your shell first (for example
    `set -a; . ./.env; set +a`) or rely on a runner that loads it for you.
    The only place in the repository that parses `.env` directly is the
    developer smoke-test script `scripts/run_real_eval.py:20–25`, which is not
    part of the installed package.

!!! warning "`${VAR}` in `config.yaml` is not expanded"
    Values such as `api_key: ${OPENAI_API_KEY}` in a config file are **not**
    interpolated — the config loader (`openagent_eval/config/loader.py`)
    performs no environment-variable substitution, so the literal string
    `${OPENAI_API_KEY}` would be used as the key. To read a key from the
    environment, omit the `api_key` field entirely and let the provider fall
    back to its environment variable.

## Example: exporting keys

```bash
# Hosted providers — export only the ones you use.
export OPENAI_API_KEY="sk-proj-abc123…"
export ANTHROPIC_API_KEY="sk-ant-api03-…"

# Point OpenAgent Eval at a specific config file.
export OAEVAL_CONFIG="/etc/oaeval/config.yaml"

oaeval doctor        # verify which keys are visible
oaeval run           # config resolved via OAEVAL_CONFIG
```

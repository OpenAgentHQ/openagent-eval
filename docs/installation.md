# Installation

This page covers installing OpenAgent Eval, both as a user and as a contributor.

## Requirements

| Requirement | Version |
| --- | --- |
| Python | >= 3.11 |
| pip | latest |
| (Recommended) uv | >= 0.4 |

OpenAgent Eval is local-first: no external services or accounts are required.

## Install from PyPI

The fastest way to get started is via `pip`:

```bash
pip install openagent-eval
```

Verify the installation:

```bash
oaeval --version
oaeval --help
```

You can also use [uv](https://github.com/astral-sh/uv):

```bash
uv pip install openagent-eval
```

Some retrievers and embedders require extra dependencies (e.g. `chromadb`, `sentence-transformers`,
`faiss-cpu`, `qdrant-client`). Install the full set with:

```bash
pip install "openagent-eval[all]"
```

## Install with uvx (no persistent environment)

```bash
uvx openagent-eval --help
```

## Install from source (development)

Use this workflow if you want to contribute or run the latest unreleased changes.

```bash
# Clone the repository
git clone https://github.com/OpenAgentHQ/openagent-eval.git
cd openagent-eval

# Create a virtual environment and install dependencies
uv sync

# The CLI is now available inside the environment
uv run oaeval --help
```

## Setting up API keys

OpenAgent Eval reads provider credentials from environment variables. Create a `.env`
file in your project root (or export them in your shell):

```bash
# .env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
GROQ_API_KEY=...
OPENROUTER_API_KEY=...
```

!!! tip "No keys? Use Ollama"
    OpenAgent Eval supports fully local models through [Ollama](https://ollama.com).
    Set `provider: ollama` in your config and no API key is required.

See the [Environment Variables](environment-variables.md) reference for every
variable OpenAgent Eval reads, including how keys are resolved and how they
reach the process.

## Next steps

- Follow the [Quickstart](quickstart.md) to run your first evaluation.
- Browse the [CLI Reference](cli.md) for every command.
- Explore the [API Reference](api.md) to embed evaluations in your test suite.

## Troubleshooting

If `oaeval` is not found after install, ensure the install location is on your `PATH`:

```bash
python -m openagent_eval --help
```

Running `oaeval doctor` checks your environment and dependency versions:

```bash
oaeval doctor
```

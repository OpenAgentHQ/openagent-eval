# Contributing

Thanks for your interest in improving OpenAgent Eval! This guide explains how to set up a development
environment and submit changes.

## Code of conduct

All contributors are expected to follow our [Code of Conduct](https://github.com/OpenAgentHQ/openagent-eval/blob/main/CODE_OF_CONDUCT.md).
Be respectful, inclusive, and constructive.

## Development setup

```bash
# Fork and clone
git clone https://github.com/<your-username>/openagent-eval.git
cd openagent-eval

# Install dependencies with uv
uv sync

# Create a feature branch
git checkout -b feat/my-change
```

## Running the test suite

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=openagent_eval

# A single file
uv run pytest tests/unit/test_exceptions.py
```

## Linting and formatting

```bash
uv run ruff check .
uv run ruff format .
```

## Project layout

```
openagent-eval/
├── openagent_eval/      # Main package
│   ├── cli/             # CLI commands (Typer)
│   ├── config/          # Configuration (Pydantic)
│   ├── core/            # Core orchestration
│   ├── datasets/        # Dataset loaders
│   ├── metrics/         # Evaluation metrics
│   ├── providers/       # LLM / Retriever adapters
│   ├── reports/         # Report generators
│   ├── plugins/         # Plugin system
│   └── exceptions/      # Custom exceptions
├── tests/               # Test suite
├── docs/                # Documentation (this site)
└── pyproject.toml
```

## Adding a metric

1. Create a class implementing `openagent_eval.metrics.base.BaseMetric`.
2. Place it under `openagent_eval/metrics/<category>/`.
3. Export it from the category's `__init__.py`.
4. Add unit tests under `tests/`.
5. Document it in [API Reference](api.md).

## Adding a provider

Implement `BaseLLMProvider` or `BaseRetrieverProvider` from
`openagent_eval.providers.base` and register it via the plugin system.

## Documentation

Documentation lives in `docs/` and is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).
To preview locally:

```bash
pip install mkdocs-material
mkdocs serve
```

When you change docs, make sure all cross-links resolve and run `mkdocs build --strict` before opening
a pull request.

## Submitting a pull request

1. Keep changes focused and well-tested.
2. Update documentation where relevant.
3. Use a clear, conventional commit message (e.g. `feat:`, `fix:`, `docs:`).
4. Open the PR against `main` and fill in the template.

## Reporting issues

- Bugs: [GitHub Issues](https://github.com/OpenAgentHQ/openagent-eval/issues)
- Ideas: [GitHub Discussions](https://github.com/OpenAgentHQ/openagent-eval/discussions)

## Next steps

- See what's planned in the [Roadmap](roadmap.md).
- Check the [FAQ](faq.md) for common questions.

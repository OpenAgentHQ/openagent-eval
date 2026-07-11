# Development Guide

This guide explains how to set up and work on OpenAgent Eval for development.

## Prerequisites

Before you begin, ensure you have:

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/{your-username}/openagent-eval.git
cd openagent-eval
```

### 2. Add Upstream Remote

```bash
git remote add upstream https://github.com/openagenthq/openagent-eval.git
```

### 3. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

### 4. Verify Setup

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy openagent_eval/
```

## Project Structure

```
openagent-eval/
├── openagent_eval/          # Main package
│   ├── cli/                 # CLI commands (Typer)
│   │   └── main.py         # Entry point: oaeval command
│   ├── config/              # Configuration system (Pydantic)
│   │   ├── models.py       # Config models
│   │   ├── loader.py       # YAML loader
│   │   └── validator.py    # Config validation
│   ├── core/                # Core orchestration
│   │   ├── engine.py       # Main evaluation engine
│   │   ├── pipeline.py     # Evaluation pipeline
│   │   ├── executor.py     # Task executor
│   │   └── registry.py     # Plugin registry
│   ├── datasets/            # Dataset loaders
│   ├── metrics/             # Evaluation metrics
│   │   ├── retrieval/      # Retrieval metrics
│   │   ├── generation/     # Generation metrics
│   │   ├── performance/    # Performance metrics
│   │   └── cost/           # Cost metrics
│   ├── providers/           # LLM/Retriever adapters
│   │   ├── llm/            # LLM providers
│   │   ├── retrievers/     # Retriever providers
│   │   └── base/           # Base interfaces
│   ├── reports/             # Report generators
│   ├── plugins/             # Plugin system
│   ├── integrations/        # External integrations
│   ├── exceptions/          # Custom exceptions
│   ├── types/               # Type definitions
│   └── utils/               # Utility functions
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── fixtures/           # Test fixtures
│   └── sample_data/        # Sample datasets
├── pyproject.toml           # Project configuration
└── README.md
```

## Development Workflow

### Creating a Branch

```bash
git fetch upstream
git checkout -b feature/your-feature upstream/main
```

### Making Changes

1. Make your changes
2. Write or update tests
3. Run tests: `uv run pytest`
4. Run linter: `uv run ruff check .`
5. Format code: `uv run ruff format .`
6. Type check: `uv run mypy openagent_eval/`
7. Commit your changes

### Committing

Follow the commit convention:

```
type(scope): description
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Submitting a Pull Request

1. Push your branch
2. Create a pull request on GitHub
3. Fill out the PR template
4. Wait for review

## Coding Standards

### General

- Follow PEP 8 conventions
- Use type hints for all function signatures
- Write clear, readable code
- Add docstrings for public APIs
- Keep functions small and focused

### Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for formatting.

```bash
# Format code
uv run ruff format .

# Check formatting without changes
uv run ruff format --check .
```

### Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting.

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Type Checking

This project uses [mypy](https://mypy.readthedocs.io/) for static type checking.

```bash
uv run mypy openagent_eval/
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=openagent_eval

# Run specific test file
uv run pytest tests/unit/test_exceptions.py

# Run specific test function
uv run pytest tests/unit/test_exceptions.py::test_function_name

# Run slow tests
uv run pytest -m slow

# Run integration tests
uv run pytest -m integration
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies (LLM providers, APIs)

## Debugging

### Common Issues

1. **Import errors after install**: Ensure you're using the editable install (`pip install -e ".[dev]"` or `uv sync`)
2. **mypy errors**: Run `uv run mypy openagent_eval/` to see all type errors
3. **Ruff errors**: Run `uv run ruff check .` to see all lint issues
4. **Test collection errors**: Check that test files follow `test_*.py` naming convention

### Using loguru for Debugging

OpenAgent Eval uses [loguru](https://github.com/Delgan/loguru) for logging:

```python
from loguru import logger

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
```

## IDE Setup

### VS Code

Recommended extensions:
- Python (ms-python.python)
- Ruff (charliermarsh.ruff)
- Pylance (ms-python.vscode-pylance)

Settings:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/openagenthq/openagent-eval/issues)
- **Discussions**: [GitHub Discussions](https://github.com/openagenthq/openagent-eval/discussions)

See [SUPPORT.md](SUPPORT.md) for more options.

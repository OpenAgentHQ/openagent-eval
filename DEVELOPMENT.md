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
│   ├── ui/                  # TUI dashboard (Textual)
│   │   ├── app.py          # Main app with ChatScreen
│   │   ├── screens.py      # Dashboard screens
│   │   ├── widgets.py      # Custom widgets
│   │   ├── styles.tcss     # Textual CSS
│   │   ├── theme.py        # Theme system (70+ tokens)
│   │   ├── streaming.py    # Streaming manager
│   │   ├── components/     # Reusable components
│   │   │   ├── spinner.py  # Animated spinner
│   │   │   ├── footer.py   # Status footer
│   │   │   ├── message_list.py  # Virtual scrolling
│   │   │   └── command_input.py # Rich input
│   │   └── tools/          # Tool renderers
│   │       ├── eval.py     # Eval results
│   │       ├── audit.py    # Audit results
│   │       └── diagnose.py # Diagnose results
│   └── utils/               # Utility functions
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── fixtures/           # Test fixtures
│   └── sample_data/        # Sample datasets
├── pyproject.toml           # Project configuration
└── README.md
```

## TUI Development

### Overview

The TUI dashboard is built with [Textual](https://textual.textualize.io/) and provides a Claude Code-inspired interface for interacting with OpenAgent Eval.

### Key Components

| Component | File | Description |
|-----------|------|-------------|
| Theme System | `ui/theme.py` | 70+ semantic color tokens |
| Streaming Manager | `ui/streaming.py` | 6-state machine for streaming output |
| Spinner Widget | `ui/components/spinner.py` | Animated spinner with rotating tips |
| Status Footer | `ui/components/footer.py` | Model, cost, time, tokens display |
| Message List | `ui/components/message_list.py` | Virtual scrolling (O(visible)) |
| Command Input | `ui/components/command_input.py` | Autocomplete, vim mode, history |
| Tool Renderers | `ui/tools/` | Eval, audit, diagnose panels |

### Running the TUI

```bash
# Launch the TUI dashboard
oaeval ui

# Launch with config file
oaeval ui --config config.yaml
```

### TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Dashboard |
| `2` | Evaluate |
| `3` | Audit |
| `4` | Diagnose |
| `5` | Chat |
| `D` | Toggle dark mode |
| `F1` | Help |
| `Ctrl+P` | Command palette |
| `Ctrl+L` | Clear messages |
| `Escape` | Back/Quit |

### Testing TUI Components

```bash
# Run TUI-specific tests
uv run pytest tests/unit/test_cli/test_phase14_redesign.py -v

# Run all tests
uv run pytest
```

### TUI Architecture

```
┌─────────────────────────────────────────────────┐
│  Header                                         │
├─────────────────────────────────────────────────┤
│                                                 │
│  MessageList (Virtual Scrolling)                │
│  ┌─────────────────────────────────────────┐   │
│  │ > User message                          │   │
│  │ ✓ Assistant response                    │   │
│  │ [tool] Tool result                      │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
├─────────────────────────────────────────────────┤
│  StatusFooter │ Model │ Cost │ Time │ Tokens   │
└─────────────────────────────────────────────────┘
```

### Adding New Components

1. Create component in `ui/components/`
2. Add CSS styles in `ui/styles.tcss`
3. Write tests in `tests/unit/test_cli/test_phase14_redesign.py`
4. Export in `ui/components/__init__.py`

### Theme Customization

The theme system uses frozen dataclasses with 70+ semantic tokens:

```python
from openagent_eval.ui.theme import get_theme, ThemeName

# Get dark theme
theme = get_theme(ThemeName.DARK)

# Access tokens
print(theme.brand)  # "rgb(79,140,255)"
print(theme.metric_excellent)  # "rgb(80,200,120)"
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

### TUI-Specific Issues

1. **"No module named 'textual'"**: Install Textual in your virtual environment:
   ```bash
   uv pip install textual
   ```

2. **CSS syntax errors**: Textual CSS doesn't support `:dark`/`:light` pseudo-selectors. Use default theme colors instead.

3. **`Rule()` errors**: Textual 8.x doesn't support `style` parameter. Use `Rule()` without arguments.

4. **`register_screen()` errors**: Textual 8.x doesn't have `register_screen()`. Use `push_screen()` with screen instances.

5. **UI not launching**: Run tests first to verify components:
   ```bash
   uv run pytest tests/unit/test_cli/test_phase14_redesign.py -v
   ```

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

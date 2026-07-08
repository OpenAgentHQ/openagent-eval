# Contributing to OpenAgent Eval

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

### Finding Something to Work On

- **Good First Issues**: Look for issues labeled `good first issue`
- **Help Wanted**: Check issues labeled `help wanted`
- **Documentation**: Help improve documentation
- **Tests**: Add or improve test coverage

## Development Setup

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

### 4. Create a Branch

```bash
git fetch upstream
git checkout -b {type}/{description} upstream/main
```

### 5. Verify Setup

```bash
uv run pytest
uv run ruff check .
```

## Making Changes

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/{description}` | `feature/add-oauth` |
| Bug Fix | `fix/{description}` | `fix/null-pointer` |
| Documentation | `docs/{description}` | `docs/update-readme` |
| Refactor | `refactor/{description}` | `refactor/extract-utils` |
| Test | `test/{description}` | `test/add-unit-tests` |

### Coding Standards

- Follow PEP 8 conventions
- Use type hints for all function signatures
- Write clear, readable code
- Add docstrings for public APIs
- Keep functions small and focused
- No hardcoded values

### Formatting and Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for formatting and linting.

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Type Checking

This project uses [mypy](https://mypy.readthedocs.io/) for static type checking.

```bash
uv run mypy openagent_eval/
```

### Testing

- Write tests for new features
- Maintain or improve test coverage
- Use descriptive test names
- Test edge cases

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=openagent_eval

# Run specific test file
uv run pytest tests/unit/test_exceptions.py

# Run slow tests
uv run pytest -m slow
```

## Commit Guidelines

### Commit Message Format

```
type(scope): description

optional body

optional footer
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(metrics): add BERTScore metric` |
| `fix` | Bug fix | `fix(config): handle missing yaml key` |
| `docs` | Documentation | `docs(readme): add installation steps` |
| `style` | Formatting | `style: fix indentation` |
| `refactor` | Code refactoring | `refactor(utils): extract helpers` |
| `test` | Tests | `test(metrics): add faithfulness tests` |
| `chore` | Maintenance | `chore: update dependencies` |
| `perf` | Performance | `perf(query): add caching` |
| `ci` | CI/CD | `ci: add release workflow` |
| `build` | Build | `build: configure hatch` |

### Rules

- Use imperative mood ("add feature" not "added feature")
- Keep subject line under 72 characters
- Reference issues when applicable
- Use body for complex changes
- Do not use a period at the end of the subject line

## Pull Request Process

### Before Submitting

1. Update your branch:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Run all checks:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run mypy openagent_eval/
   ```

3. Update documentation if needed

### Submitting

1. Push your branch
2. Create a pull request on GitHub
3. Fill out the PR template completely
4. Add appropriate labels
5. Request review from maintainers

### Review Process

1. Maintainers will review your PR
2. Address feedback promptly
3. Make requested changes
4. Push updates to the same branch

### After Merge

1. Delete your feature branch
2. Pull the latest main

## Reporting Issues

### Bug Reports

When reporting bugs, include:
1. Clear description of the bug
2. Steps to reproduce
3. Expected vs actual behavior
4. Environment details
5. Screenshots (if applicable)

### Feature Requests

When requesting features, include:
1. Clear description of the feature
2. Use case
3. Alternatives considered
4. Additional context

### Security Issues

For security issues, see [SECURITY.md](SECURITY.md). Do not create public issues for security vulnerabilities.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).

## Questions?

If you have questions about contributing, feel free to open a discussion or create an issue with the `question` label.

Thank you for contributing to OpenAgent Eval!

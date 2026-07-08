# Contributing to OpenAgent Eval

Thank you for your interest in contributing to OpenAgent Eval! This document provides guidelines and information for contributors.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/). Please be respectful and inclusive in all interactions.

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (package manager)
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/openagent-eval.git
cd openagent-eval

# Add upstream remote
git remote add upstream https://github.com/OpenAgentHQ/openagent-eval.git
```

---

## Development Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Set Up Pre-commit Hooks

```bash
uv run pre-commit install
```

### 3. Verify Setup

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy openagent_eval/
```

---

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/OpenAgentHQ/openagent-eval/issues)
2. Create a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details

### Suggesting Features

1. Check [existing issues](https://github.com/OpenAgentHQ/openagent-eval/issues)
2. Create a new issue with:
   - Clear title
   - Problem description
   - Proposed solution
   - Alternatives considered

### Contributing Code

1. Find an issue to work on (or create one)
2. Comment on the issue to claim it
3. Create a branch from `main`
4. Make your changes
5. Write tests
6. Update documentation
7. Submit a pull request

---

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
# or
git checkout -b docs/your-documentation
```

### 2. Make Changes

- Follow coding standards
- Write tests for new functionality
- Update documentation as needed

### 3. Commit

```bash
git add .
git commit -m "feat: Add new metric implementation"
```

**Commit Message Format:**

```
type: Short description

Optional longer description

Closes #123
```

**Types:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

### 4. Push

```bash
git push origin feature/your-feature-name
```

### 5. Create Pull Request

- Go to GitHub and create a new PR
- Fill out the PR template
- Link the related issue
- Request review

### 6. Code Review

- Address review comments
- Make requested changes
- Get approval from maintainer

### 7. Merge

- Maintainer will merge your PR
- Delete your branch

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints on all public functions
- Keep functions under 50 lines
- Single responsibility per function/class

### Naming

```python
# Variables and functions
user_name = "John"
def calculate_score():

# Classes
class BaseMetric:

# Constants
MAX_RETRIES = 3
```

### Imports

```python
# Standard library
import os
from typing import List

# Third-party
import yaml
from pydantic import BaseModel

# Local
from openagent_eval.metrics import BaseMetric
```

### Docstrings

```python
def calculate_score(answer: str, ground_truth: str) -> float:
    """Calculate similarity score between answer and ground truth.
    
    Args:
        answer: The generated answer
        ground_truth: The expected answer
        
    Returns:
        Similarity score between 0 and 1
        
    Example:
        >>> calculate_score("hello", "hello world")
        0.75
    """
```

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_metrics/test_faithfulness.py

# Run with coverage
uv run pytest --cov=openagent_eval --cov-report=html
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock

class TestMyMetric:
    @pytest.fixture
    def metric(self):
        return MyMetric()
    
    def test_evaluate_success(self, metric):
        result = metric.evaluate(answer="test", context="context")
        assert result.score >= 0.0
        assert result.score <= 1.0
    
    def test_evaluate_edge_case(self, metric):
        result = metric.evaluate(answer="", context="")
        assert result.score == 0.0
```

### Test Coverage

- Target: 80%+ coverage
- Mock all external dependencies
- Test both success and failure paths

---

## Documentation

### Types of Documentation

1. **Code Documentation** - Docstrings in code
2. **API Documentation** - Generated from docstrings
3. **User Guides** - In `docs/` directory
4. **Developer Guides** - In `docs/` directory

### Updating Documentation

- Update docs when adding features
- Add examples for new functionality
- Keep README.md up to date

---

## Community

### Getting Help

- **GitHub Issues** - For bugs and feature requests
- **Discord** - For questions and discussions
- **Discussions** - For general topics

### Staying Updated

- Watch the repository
- Follow us on Twitter
- Join our newsletter

---

## Recognition

Contributors will be recognized in:

- README.md
- CHANGELOG.md
- Release notes

Thank you for contributing to OpenAgent Eval!

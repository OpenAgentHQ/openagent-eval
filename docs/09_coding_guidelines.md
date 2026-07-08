# Coding Guidelines

## Overview

This document outlines the coding standards and conventions for OpenAgent Eval.

---

## Language Requirements

- **Python 3.11+** required
- Type hints on ALL public functions
- Use `typing` module for complex types
- Pydantic v2 for data models and validation

---

## Naming Conventions

| Context | Convention | Example |
|---------|------------|---------|
| Variables | `snake_case` | `user_name`, `retry_count` |
| Functions | `snake_case` | `load_dataset()`, `calculate_score()` |
| Classes | `PascalCase` | `BaseMetric`, `LLMProvider` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Module files | `snake_case.py` | `faithfulness.py`, `json_loader.py` |
| Package dirs | `snake_case/` | `metrics/`, `providers/` |

---

## Code Quality Rules

### Functions

- Keep functions under 50 lines
- Single responsibility per function
- Maximum 3-4 parameters (use dataclasses for more)
- Use keyword arguments for optional parameters

**Good:**

```python
def calculate_score(
    answer: str,
    ground_truth: str,
    threshold: float = 0.5
) -> MetricResult:
    """Calculate similarity score between answer and ground truth."""
    score = compute_similarity(answer, ground_truth)
    return MetricResult(
        score=score,
        reason=f"Similarity: {score:.3f}"
    )
```

**Bad:**

```python
def calculate_score(answer, ground_truth, threshold=0.5, normalize=True, 
                    strip_whitespace=True, lowercase=True, max_length=1000,
                    min_length=10):
    # 50+ lines of logic
    pass
```

### Classes

- Single responsibility per class
- Prefer composition over inheritance
- Use abstract base classes for interfaces
- Keep public API minimal

**Good:**

```python
class FaithfulnessMetric(BaseMetric):
    """Evaluate faithfulness of answer to context."""
    
    name = "faithfulness"
    description = "Whether the answer is faithful to the context"
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
    
    def evaluate(self, answer: str, context: str) -> MetricResult:
        """Evaluate faithfulness."""
        prompt = self._build_prompt(answer, context)
        result = self.llm.generate(prompt)
        return self._parse_result(result)
    
    def _build_prompt(self, answer: str, context: str) -> str:
        """Build evaluation prompt."""
        return f"..."
    
    def _parse_result(self, result: str) -> MetricResult:
        """Parse LLM response into MetricResult."""
        ...
```

### Error Handling

- NEVER raise generic `Exception`
- ALWAYS use custom exception hierarchy
- ALWAYS include context in error messages
- Use specific exception types

**Good:**

```python
from openagent_eval.exceptions import ConfigurationError

def load_config(path: str) -> Config:
    if not os.path.exists(path):
        raise ConfigurationError(
            message=f"Configuration file not found: {path}",
            config_path=path
        )
```

**Bad:**

```python
def load_config(path: str) -> Config:
    if not os.path.exists(path):
        raise Exception("File not found")
```

---

## Type Hints

### Required On

- All public function parameters
- All public function return values
- All class attributes
- All module-level variables

**Example:**

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class EvaluationResult(BaseModel):
    """Result of an evaluation run."""
    
    metrics: List[MetricResult]
    dataset_info: Dict[str, Any]
    config: Config
    duration_ms: float
    
    @property
    def overall_score(self) -> float:
        """Calculate overall score from metrics."""
        if not self.metrics:
            return 0.0
        return sum(m.score for m in self.metrics) / len(self.metrics)

def evaluate_dataset(
    dataset: Dataset,
    metrics: List[BaseMetric],
    config: Optional[Config] = None
) -> EvaluationResult:
    """Evaluate a dataset with specified metrics."""
    ...
```

---

## Async Rules

- Use `asyncio` for parallel evaluation
- Provider adapters should support async operations
- Pipeline execution should be async-compatible
- Never block the event loop

**Good:**

```python
async def evaluate_item(item: DatasetItem) -> List[MetricResult]:
    """Evaluate a single dataset item."""
    tasks = [metric.evaluate(**item.to_dict()) for metric in metrics]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, MetricResult)]
```

**Bad:**

```python
def evaluate_item(item: DatasetItem) -> List[MetricResult]:
    results = []
    for metric in metrics:
        # Blocking call in async context
        result = metric.evaluate(**item.to_dict())
        results.append(result)
    return results
```

---

## Import Order

Follow this order for imports:

```python
# 1. Standard library
import os
import json
from typing import List, Optional
from dataclasses import dataclass

# 2. Third-party packages
import yaml
from pydantic import BaseModel
from loguru import logger

# 3. Local imports
from openagent_eval.metrics.base import BaseMetric
from openagent_eval.metrics.models import MetricResult
from openagent_eval.exceptions import MetricError
```

---

## Documentation

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def calculate_score(
    answer: str,
    ground_truth: str,
    threshold: float = 0.5
) -> MetricResult:
    """Calculate similarity score between answer and ground truth.
    
    Args:
        answer: The generated answer
        ground_truth: The expected answer
        threshold: Minimum threshold for passing
        
    Returns:
        MetricResult with score and reason
        
    Raises:
        ValueError: If inputs are empty
        
    Example:
        >>> result = calculate_score("hello", "hello world")
        >>> result.score
        0.75
    """
```

### Comments

**Good:**

```python
# Calculate discount by tier (Bronze: 5%, Silver: 10%, Gold: 15%)
discount = get_discount_byTier(customer.tier)

# HACK: API returns null instead of [], normalize it
items = response.items or []

# TODO: Use async/await when Node 18+ is minimum
```

**Bad:**

```python
# Increment i
i++

# Get user
user = getUser()
```

---

## Testing

### Test Structure

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestFaithfulnessMetric:
    """Tests for FaithfulnessMetric."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        llm = Mock(spec=LLMProvider)
        llm.generate = AsyncMock(return_value="yes")
        return llm
    
    @pytest.fixture
    def metric(self, mock_llm):
        """Create metric instance."""
        return FaithfulnessMetric(llm_provider=mock_llm)
    
    @pytest.mark.asyncio
    async def test_evaluate_faithful(self, metric):
        """Test evaluation with faithful answer."""
        result = metric.evaluate(
            answer="Paris is the capital of France",
            context="Paris, the capital city of France..."
        )
        
        assert result.score == 1.0
        assert "faithful" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_evaluate_unfaithful(self, metric):
        """Test evaluation with unfaithful answer."""
        metric.llm.generate = AsyncMock(return_value="no")
        
        result = metric.evaluate(
            answer="London is the capital of France",
            context="Paris, the capital city of France..."
        )
        
        assert result.score == 0.0
```

### Test Coverage

- Target: 80%+ coverage
- Mock ALL external dependencies
- Test both success and failure paths
- Test edge cases and error handling

---

## Git Workflow

### Branch Naming

```
feature/{description}      # New features
fix/{description}          # Bug fixes
docs/{description}         # Documentation updates
refactor/{description}     # Code refactoring
test/{description}         # Test additions/updates
chore/{description}        # Maintenance tasks
```

### Commit Messages

```
feat: Add new metric implementation
fix: Fix config validation error
docs: Update CLI specification
refactor: Simplify metric interface
test: Add unit tests for plugins
chore: Update dependencies
```

### Pull Requests

Every PR must include:

1. Clear description of changes
2. Motivation for the change
3. List of files modified
4. Architectural decisions (if any)
5. Testing performed
6. Breaking changes (if any)

---

## Code Review Checklist

### Before Submitting

- [ ] Type hints on all public functions
- [ ] Docstrings on all public APIs
- [ ] No generic `Exception` raised
- [ ] Custom exceptions used
- [ ] Tests written and passing
- [ ] No circular dependencies
- [ ] Follows naming conventions
- [ ] Functions under 50 lines
- [ ] Single responsibility per function/class

### During Review

- [ ] Code is readable and maintainable
- [ ] Error handling is comprehensive
- [ ] Tests cover edge cases
- [ ] Documentation is clear
- [ ] No security vulnerabilities
- [ ] Performance is acceptable

# CI/CD Integration Guide

This guide explains how to integrate OpenAgent Eval into your CI/CD pipelines for automated RAG evaluation.

## Overview

OpenAgent Eval provides CI/CD integration through:

1. **`oaeval test` CLI command** — Run evaluations as CI/CD tests with threshold gating
2. **pytest plugin** — Write RAG evaluation tests using pytest
3. **GitHub Actions workflow** — Ready-to-use workflow for GitHub repositories

## Quick Start

### Using `oaeval test`

The simplest way to add RAG evaluation to your CI/CD pipeline:

```bash
# Run evaluation with a threshold gate
oaeval test config.yaml -t faithfulness:gte:0.8

# Multiple thresholds
oaeval test config.yaml \
  -t faithfulness:gte:0.8 \
  -t answer_relevancy:gte:0.7 \
  -t latency:lte:5000

# JSON output for CI/CD parsing
oaeval test config.yaml -t faithfulness:gte:0.8 --json
```

### Exit Codes

- **0** — All thresholds passed
- **1** — One or more required thresholds failed
- **2** — Configuration error

## Threshold Configuration

### Format

Thresholds follow the format: `metric:operator:value`

**Operators:**
- `gt` — Greater than
- `gte` — Greater than or equal
- `lt` — Less than
- `lte` — Less than or equal
- `eq` — Equal to
- `neq` — Not equal to

**Examples:**
```bash
# Faithfulness must be at least 80%
-t faithfulness:gte:0.8

# Latency must be under 5 seconds
-t latency:lte:5000

# Hallucination rate must be below 5%
-t hallucination:lt:0.05
```

### Available Metrics

| Category | Metrics |
|----------|---------|
| **Retrieval** | `context_precision`, `context_recall`, `mrr`, `ndcg`, `hit_rate`, `precision_at_k`, `recall_at_k` |
| **Generation** | `faithfulness`, `answer_relevancy`, `hallucination`, `semantic_similarity`, `exact_match`, `f1_score`, `bleu`, `rouge`, `bertscore` |
| **Performance** | `latency` |
| **Cost** | `token_count` |

## GitHub Actions Integration

### Basic Workflow

Create `.github/workflows/eval.yml`:

```yaml
name: RAG Evaluation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  evaluate:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install openagent-eval[evaluation]

      - name: Run evaluation
        run: |
          oaeval test config.yaml \
            -t faithfulness:gte:0.8 \
            -t answer_relevancy:gte:0.7 \
            --json > eval-results.json

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-results
          path: eval-results.json
```

### Advanced Workflow with Multiple Stages

```yaml
name: RAG Evaluation Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Stage 1: Corpus Audit
  corpus-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install openagent-eval[corpus]
      
      - name: Audit corpus
        run: |
          oaeval audit --corpus ./knowledge_base/ \
            --checks contradiction,staleness,duplicate \
            --output json > corpus-audit.json
      
      - name: Check corpus health
        run: |
          # Fail if critical issues found
          python -c "
          import json
          with open('corpus-audit.json') as f:
              report = json.load(f)
          if report.get('critical_issues', 0) > 0:
              print('Corpus has critical issues!')
              exit(1)
          "

  # Stage 2: Evaluation
  evaluate:
    needs: corpus-audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install openagent-eval[evaluation]
      
      - name: Run evaluation
        run: |
          oaeval test config.yaml \
            -t faithfulness:gte:0.85 \
            -t answer_relevancy:gte:0.75 \
            -t hallucination:lt:0.05 \
            --json > eval-results.json
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-results
          path: eval-results.json

  # Stage 3: Report
  report:
    needs: evaluate
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Download results
        uses: actions/download-artifact@v4
        with:
          name: evaluation-results
      
      - name: Post summary
        run: |
          python -c "
          import json
          with open('eval-results.json') as f:
              result = json.load(f)
          
          status = '✅ Passed' if result['status'] == 'passed' else '❌ Failed'
          print(f'## RAG Evaluation {status}')
          print()
          print('### Threshold Results')
          for gate in result.get('gates', []):
              for t in gate.get('thresholds', []):
                  icon = '✅' if t['passed'] else '❌'
                  print(f\"{icon} {t['message']}\")
          "
```

## pytest Integration

### Using the Plugin

Add the OpenAgent Eval plugin to your pytest configuration:

**pyproject.toml:**
```toml
[tool.pytest.ini_options]
addopts = "-p openagent_eval.cicd.plugin"
```

**pytest.ini:**
```ini
[pytest]
addopts = -p openagent_eval.cicd.plugin
```

### Writing Evaluation Tests

```python
"""RAG evaluation tests."""

import pytest
from openagent_eval.cicd import OAEvalPlugin


def test_rag_faithfulness():
    """Test that RAG faithfulness meets threshold."""
    result = OAEvalPlugin.run_evaluation(
        config_path="config.yaml",
        thresholds=["faithfulness:gte:0.8"],
    )
    assert result.passed, f"Faithfulness check failed: {result.summary}"


def test_rag_comprehensive():
    """Comprehensive RAG evaluation test."""
    result = OAEvalPlugin.run_evaluation(
        config_path="config.yaml",
        thresholds=[
            "faithfulness:gte:0.8",
            "answer_relevancy:gte:0.7",
            "hallucination:lt:0.05",
            "latency:lte:5000",
        ],
    )
    
    # Print detailed results
    for gate in result.gate_results:
        for tr in gate.threshold_results:
            print(f"{tr.metric}: {tr.actual_value:.4f} {tr.operator.value} {tr.threshold_value:.4f} -> {'PASS' if tr.passed else 'FAIL'}")
    
    assert result.passed, "RAG evaluation failed threshold checks"
```

### Running pytest Tests

```bash
# Run all evaluation tests
pytest tests/test_rag_evaluation.py -v

# Run with custom thresholds
pytest tests/test_rag_evaluation.py -v \
  --oaeval-threshold "faithfulness:gte:0.8" \
  --oaeval-threshold "answer_relevancy:gte:0.7"
```

## GitLab CI Integration

```yaml
stages:
  - evaluate

rag-evaluation:
  stage: evaluate
  image: python:3.11
  script:
    - pip install openagent-eval[evaluation]
    - |
      oaeval test config.yaml \
        -t faithfulness:gte:0.8 \
        -t answer_relevancy:gte:0.7 \
        --json > eval-results.json
  artifacts:
    paths:
      - eval-results.json
    when: always
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

## CircleCI Integration

```yaml
version: 2.1

orbs:
  python: circleci/python@2.0

jobs:
  evaluate:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - python/install-packages:
          pkg-manager: pip
          args: openagent-eval[evaluation]
      - run:
          name: Run RAG evaluation
          command: |
            oaeval test config.yaml \
              -t faithfulness:gte:0.8 \
              -t answer_relevancy:gte:0.7 \
              --json > eval-results.json
      - store_artifacts:
          path: eval-results.json
          destination: evaluation-results

workflows:
  evaluate-rag:
    jobs:
      - evaluate:
          filters:
            branches:
              only: main
```

## Best Practices

### 1. Start with Soft Gates

Initially, use warnings instead of failures to avoid blocking your pipeline:

```bash
oaeval test config.yaml -t faithfulness:gte:0.8 --no-fail-on-error
```

### 2. Set Realistic Thresholds

- Start with lower thresholds and gradually increase
- Monitor your baseline metrics before setting gates
- Consider different thresholds for different environments

### 3. Use Multiple Metrics

Don't rely on a single metric. Check multiple aspects:

```bash
oaeval test config.yaml \
  -t faithfulness:gte:0.8 \
  -t answer_relevancy:gte:0.7 \
  -t hallucination:lt:0.05 \
  -t latency:lte:5000
```

### 4. Cache Dependencies

Cache model downloads and dependencies:

```yaml
- name: Cache models
  uses: actions/cache@v4
  with:
    path: ~/.cache/huggingface
    key: ${{ runner.os }}-models-${{ hashFiles('**/requirements.txt') }}
```

### 5. Run on Schedule

Run evaluations regularly to catch regressions:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

## Troubleshooting

### Common Issues

**1. "Config file not found"**
- Ensure the config path is correct
- Use absolute paths in CI/CD environments

**2. "Metric not found"**
- Check that the metric name is correct
- Ensure required dependencies are installed

**3. "Timeout exceeded"**
- Increase the timeout: `--timeout 600`
- Optimize your RAG pipeline

**4. "API key not found"**
- Set environment variables in your CI/CD platform
- Use secrets management (GitHub Secrets, GitLab CI Variables)

### Debug Mode

Run with verbose output to debug issues:

```bash
oaeval test config.yaml -t faithfulness:gte:0.8 -v --json
```

## Further Reading

- [CLI Reference](./06_cli_spec.md)
- [Metrics Reference](./07_metric_system.md)

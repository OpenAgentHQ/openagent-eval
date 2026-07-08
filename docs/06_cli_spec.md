# CLI Specification

## Overview

OpenAgent Eval provides a CLI interface via `oaeval` built with Typer and Rich.

---

## Installation

```bash
pip install openagent-eval
```

or with uv:

```bash
uv add openagent-eval
```

---

## Commands

### `oaeval init`

Create a new evaluation configuration.

**Usage:**

```bash
oaeval init
```

**Behavior:**

- Interactively prompts for configuration options
- Creates `config.yaml` in the current directory
- Sets up default metrics and output settings

**Example output:**

```
✓ Configuration created: config.yaml
✓ Default metrics: faithfulness, answer_relevancy, hallucination
✓ Output format: terminal
```

---

### `oaeval run`

Run an evaluation.

**Usage:**

```bash
oaeval run <config_path>
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Report format (terminal, markdown, html, json) | terminal |
| `--output-dir` | Output directory for reports | ./reports |
| `--metrics` | Comma-separated list of metrics | all configured |
| `--verbose` | Enable verbose output | false |
| `--parallel` | Number of parallel evaluations | 4 |

**Example:**

```bash
oaeval run config.yaml --output markdown --output-dir ./reports
```

**Example output:**

```
Loading dataset: data/questions.json (500 questions)
Running evaluation...

Retrieval Metrics:
  Context Precision: 0.87
  Context Recall: 0.92
  Hit Rate: 0.95

Generation Metrics:
  Faithfulness: 0.918
  Answer Relevancy: 0.892
  Hallucination Rate: 0.031

Performance:
  Average Latency: 612ms
  Total Time: 5m 12s

Cost:
  Total Tokens: 1,234,567
  Estimated Cost: $2.17

Overall Grade: A
```

---

### `oaeval report`

View evaluation reports.

**Usage:**

```bash
oaeval report <report_id|latest>
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--format` | Output format (terminal, markdown, html) | terminal |
| `--save` | Save report to file | false |

**Example:**

```bash
oaeval report latest
oaeval report exp_2024_01_15 --format markdown
```

---

### `oaeval compare`

Compare two or more experiments.

**Usage:**

```bash
oaeval compare <experiment1> <experiment2> [...]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--format` | Output format (terminal, markdown, html) | terminal |
| `--diff` | Show only differences | false |

**Example:**

```bash
oaeval compare exp_a exp_b --diff
```

**Example output:**

```
Experiment Comparison

| Metric           | Experiment A | Experiment B | Delta |
|------------------|--------------|--------------|-------|
| Faithfulness     | 83.2%        | 92.1%        | +8.9% |
| Answer Relevancy | 81.5%        | 89.7%        | +8.2% |
| Latency          | 450ms        | 612ms        | +162ms|
| Cost             | $1.82        | $2.17        | +$0.35|

Winner: Experiment B (Faithfulness +8.9%)
```

---

### `oaeval list`

List previous evaluations.

**Usage:**

```bash
oaeval list
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--limit` | Number of results | 10 |
| `--sort` | Sort by (date, score, cost) | date |

**Example:**

```bash
oaeval list --limit 5 --sort score
```

**Example output:**

```
Recent Evaluations

| ID                  | Date       | Score | Cost   |
|---------------------|------------|-------|--------|
| exp_2024_01_15_001  | 2024-01-15 | 92.1% | $2.17  |
| exp_2024_01_14_003  | 2024-01-14 | 89.7% | $1.82  |
| exp_2024_01_13_002  | 2024-01-13 | 83.2% | $1.95  |
```

---

### `oaeval doctor`

Check environment and dependencies.

**Usage:**

```bash
oaeval doctor
```

**Example output:**

```
Environment Check

✓ Python 3.11.5
✓ openagent-eval 0.1.0
✓ PyYAML installed
✓ Pydantic v2.4.0

Provider Status
✓ OpenAI API key configured
✗ Gemini API key not found
✓ Anthropic API key configured

Recommendations
- Set GEMINI_API_KEY for Gemini support
```

---

## Configuration File

### Example `config.yaml`

```yaml
dataset: data/questions.json

retriever:
  provider: chroma
  settings:
    collection_name: my_docs
    persist_directory: ./chroma_db

llm:
  provider: openai
  model: gpt-4o
  temperature: 0.0

metrics:
  - faithfulness
  - answer_relevancy
  - hallucination
  - latency

output: terminal
output_dir: ./reports

parallel: 4
timeout: 300
```

### Configuration Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `dataset` | string | Yes | - | Path to dataset file |
| `retriever.provider` | string | Yes | - | Retriever provider name |
| `retriever.settings` | object | No | {} | Provider-specific settings |
| `llm.provider` | string | Yes | - | LLM provider name |
| `llm.model` | string | Yes | - | Model identifier |
| `llm.temperature` | float | No | 0.0 | Sampling temperature |
| `metrics` | list | No | all | List of metrics to run |
| `output` | string | No | terminal | Report format |
| `output_dir` | string | No | ./reports | Output directory |
| `parallel` | int | No | 4 | Parallel evaluations |
| `timeout` | int | No | 300 | Timeout in seconds |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | For OpenAI |
| `GEMINI_API_KEY` | Google Gemini API key | For Gemini |
| `ANTHROPIC_API_KEY` | Anthropic API key | For Anthropic |
| `GROQ_API_KEY` | Groq API key | For Groq |

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Dataset error |
| 4 | Provider error |
| 5 | Metric error |

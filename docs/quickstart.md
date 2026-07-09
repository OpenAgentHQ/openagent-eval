# Quickstart

This guide takes you from a fresh install to your first evaluation report in a few minutes.

## 1. Initialize a configuration

```bash
oaeval init
```

This creates a `config.yaml` file with sensible defaults:

```yaml title="config.yaml"
dataset: data/questions.json

retriever:
  provider: chroma
  settings:
    collection_name: my_docs

llm:
  provider: openai
  model: gpt-4o

metrics:
  - faithfulness
  - answer_relevancy
  - hallucination
  - latency

output: terminal
output_dir: ./reports
```

## 2. Prepare a dataset

OpenAgent Eval supports several dataset formats. The simplest is a JSON list of questions, each with
a reference answer and the retrieved context:

```json title="data/questions.json"
[
  {
    "question": "What is the capital of France?",
    "reference": "The capital of France is Paris.",
    "context": ["France is a country in Western Europe. Its capital is Paris."]
  }
]
```

See [Examples](examples.md) for CSV, JSONL, and Hugging Face dataset loaders.

## 3. Run the evaluation

```bash
oaeval run config.yaml
```

You can override the output format from the command line:

```bash
oaeval run config.yaml --output html
```

## 4. View the report

```bash
oaeval report latest
```

Other report commands:

```bash
# List all stored evaluations
oaeval list

# Compare two experiments
oaeval compare exp-001 exp-002
```

## 5. Use the Python SDK

The same pipeline is available as a library so you can embed it in `pytest`:

```python title="test_eval.py"
from openagent_eval import Evaluator

evaluator = Evaluator(config_path="config.yaml")
result = evaluator.evaluate(dataset)

assert result.summary["faithfulness"] >= 0.8
```

## Configuration reference

| Key | Description | Default |
| --- | --- | --- |
| `dataset` | Path or loader spec for the evaluation dataset | — |
| `retriever.provider` | Retriever backend (`chroma`, ...) | `chroma` |
| `llm.provider` | LLM backend (`openai`, `gemini`, `anthropic`, `groq`, `openrouter`, `ollama`) | `openai` |
| `llm.model` | Model identifier | — |
| `metrics` | List of metric names to compute | — |
| `output` | Report format: `terminal`, `markdown`, `html`, `json` | `terminal` |
| `output_dir` | Directory for persisted reports | `./reports` |

## Next steps

- Understand the internals on the [Architecture](architecture.md) page.
- Learn every flag in the [CLI Reference](cli.md).
- Discover advanced metrics and plugins in the [API Reference](api.md).

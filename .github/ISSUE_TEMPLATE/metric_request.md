---
name: Metric Request
about: Propose a new evaluation metric for OpenAgent Eval
title: "[METRIC] "
labels: enhancement, metric
assignees: ''
---

## Metric Details

- **Metric Name**: [e.g., Answer Consistency, Latency Percentile, Tool Call Accuracy]
- **Category**:
  - [ ] Retrieval (`metrics/retrieval/`)
  - [ ] Generation (`metrics/generation/`)
  - [ ] NLI / Entailment (`metrics/nli/`)
  - [ ] Safety / Hallucination / Agentic
- **Computation Mode**:
  - [ ] Deterministic / rule-based
  - [ ] Model-based (embedding / cross-encoder / NLI)
  - [ ] LLM-as-Judge (`LLMProvider`)

## Required Inputs

Check which evaluation fields this metric requires:

- [ ] `question` / `query`
- [ ] `answer` / `response`
- [ ] `contexts` / `retrieved_documents`
- [ ] `ground_truth` / `expected_answer`
- [ ] Trace / tool calls / custom fields (describe below)

## Formula & Scoring Definition

Describe the scoring formula, range (e.g., `[0.0, 1.0]`), aggregation rules, and reference paper or benchmark (if any):

- **Score range & direction**: [e.g., `0.0` to `1.0`, higher is better]
- **Formula / algorithm**: [mathematical definition or step-by-step rubric]
- **Edge cases**: [e.g., empty response, missing contexts, divide-by-zero behavior]

## Use Case & Example Configuration

```yaml
# Example metric configuration in config.yaml
metrics:
  - name: my_metric
    threshold: 0.8
```

## Would you be willing to contribute this metric?

- [ ] Yes, I'd like to implement this metric
- [ ] I can help with testing
- [ ] No, I'm just suggesting

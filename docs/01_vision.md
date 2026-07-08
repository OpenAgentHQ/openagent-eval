# Vision

## Why OpenAgent Eval Exists

Modern AI applications are no longer just prompts. They include retrievers, vector databases, tools, memory, and multi-step agent workflows.

Developers can build these systems quickly, but they often have no reliable way to:

- Measure quality
- Compare experiments
- Detect hallucinations
- Identify retrieval failures

**OpenAgent Eval** solves this by providing a local-first, developer-friendly evaluation framework that runs entirely from the command line.

---

## Our Goal

Become the standard evaluation tool for AI developers, similar to how `pytest` became the standard testing framework for Python.

---

## Core Belief

Developers should be able to evaluate AI systems as easily as they run unit tests.

```bash
oaeval run config.yaml
```

One command. No dashboard required. No cloud services. No subscriptions.

---

## What Makes Us Different

| Feature | OpenAgent Eval | Other Tools |
|---------|----------------|-------------|
| Local-first | ✅ | ❌ Often cloud-only |
| CLI-native | ✅ | ❌ Dashboard-focused |
| Framework agnostic | ✅ | ⚠️ Often tied to one framework |
| Free & open source | ✅ | ⚠️ Often paid |
| Plugin-based | ✅ | ❌ Limited extensibility |

---

## Success Criteria

OpenAgent Eval is successful when:

- A developer can install it in under five minutes
- Running an evaluation requires only one command
- Reports are understandable without additional tooling
- Adding a new metric requires minimal code changes
- The framework integrates easily into existing RAG applications
- Developers use it in local development and CI pipelines to catch regressions before deployment

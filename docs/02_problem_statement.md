# Problem Statement

## The Core Problem

Building a RAG system is relatively easy.

**Knowing whether it actually works is difficult.**

---

## Why Current Approaches Fail

Most developers evaluate their applications by manually asking a few questions and checking whether the answers look reasonable.

This approach:

- Does not scale
- Cannot detect regressions
- Cannot compare experiments
- Provides no objective metrics
- Cannot explain why failures occur

---

## The Evaluation Gap

Current evaluation platforms often require:

- Cloud services
- Dashboards
- Expensive subscriptions
- Complicated setup

Many developers simply skip evaluation altogether.

As AI systems become larger and more complex, reliable evaluation becomes essential.

---

## Real-World Consequences

Without proper evaluation:

| Problem | Impact |
|---------|--------|
| Hallucinations go undetected | Users lose trust |
| Retrieval failures invisible | Wrong context passed to LLM |
| No regression testing | Quality degrades over time |
| Manual comparison only | Slow, error-prone experiments |
| No cost tracking | Surprising API bills |

---

## Our Solution

OpenAgent Eval is a local-first CLI tool that evaluates RAG systems and AI agents using standardized metrics.

Instead of manually checking outputs, developers provide a dataset and their application.

OpenAgent Eval automatically executes evaluation pipelines and generates comprehensive reports containing:

- Retrieval quality
- Answer quality
- Hallucination detection
- Latency
- Token usage
- Cost analysis
- Failure analysis
- Experiment comparison

**Everything runs from the command line. No dashboard is required.**

# RAG Evaluation Tutorial

A hands-on Jupyter notebook that walks through a complete RAG evaluation using
OpenAgent Eval's offline **mock** providers — no API keys required:

- Building a minimal RAG pipeline (chunking, a local keyword retriever, a mock LLM)
- Configuring an evaluation both from YAML and programmatically
- Running all 18 retrieval, generation, performance and cost metrics
- Diagnosing failures and interpreting the report output
- Writing a custom metric and comparing experiments

**Download:** [`rag_evaluation_tutorial.ipynb`](https://github.com/OpenAgentHQ/openagent-eval/blob/main/examples/rag_evaluation_tutorial.ipynb)

### What you'll learn

| Section | Topic |
|---------|-------|
| 1 | Introduction: what OpenAgent Eval is |
| 2 | Installing and verifying the package |
| 3 | Building a minimal RAG pipeline (retriever + mock LLM) |
| 4 | Evaluating the pipeline (YAML and programmatic config) |
| 5 | A deep dive on all 18 metrics |
| 6 | Interpreting results and diagnosing failures |
| 7 | Advanced usage: custom metrics, batch comparison, LLM judges |
| 8 | Best practices for production RAG evaluation |

### Prerequisites

```bash
pip install openagent-eval jupyter
```

### Quick start

```bash
cd examples/
jupyter notebook rag_evaluation_tutorial.ipynb
```

The notebook runs entirely offline with the `mock` providers, so you can work through
every cell without an API key.

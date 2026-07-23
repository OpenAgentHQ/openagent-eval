# Examples

Worked examples showing how to use OpenAgent Eval in practice. Each tutorial is a
runnable Jupyter notebook in the
[`examples/`](https://github.com/OpenAgentHQ/openagent-eval/tree/main/examples)
directory of the repository.

| Tutorial | What it covers | Run it |
|----------|----------------|--------|
| [Colab Quickstart](colab.md) | Zero-setup, end-to-end evaluation that runs in the browser — no API keys required | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OpenAgentHQ/openagent-eval/blob/main/examples/openagent_eval_colab_tutorial.ipynb) |
| [RAG Evaluation](rag.md) | A complete RAG pipeline scored with all 18 retrieval, generation, performance and cost metrics | Local Jupyter |
| [Corpus Health Auditor](corpus.md) | Corpus health checks (staleness, duplicates, coverage, contradiction), failure diagnosis and synthetic test-case generation | Local Jupyter |

## Running the notebooks locally

```bash
pip install openagent-eval jupyter
git clone https://github.com/OpenAgentHQ/openagent-eval
cd openagent-eval/examples
jupyter notebook
```

The [Colab Quickstart](colab.md) needs no local setup at all — open it directly in
your browser.

## More examples

For copy-paste snippets covering common workflows, see the
[Quickstart](../quickstart.md). The
[`scripts/`](https://github.com/OpenAgentHQ/openagent-eval/tree/main/scripts)
directory in the repository holds additional runnable examples.

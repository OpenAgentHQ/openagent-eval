# Colab Quickstart Tutorial

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OpenAgentHQ/openagent-eval/blob/main/examples/openagent_eval_colab_tutorial.ipynb)

A zero-setup, end-to-end tour of OpenAgent Eval that runs entirely in your browser.
It uses the built-in **mock** LLM and retriever providers, so it needs **no API keys**
and makes no network calls — click the badge above and run every cell.

## What you'll learn

- Installing OpenAgent Eval and verifying it with `oaeval doctor`
- Building a fully offline evaluation config with the `mock` providers
- Running an evaluation from both the CLI (`oaeval run`) and the Python SDK (`Engine`)
- Reading the terminal, Markdown, HTML and JSON reports
- Generating synthetic test cases with `oaeval synth`
- Optionally plugging in a real provider (OpenAI) through a guarded, key-optional cell

## Run it

- **In the browser:** [open in Google Colab](https://colab.research.google.com/github/OpenAgentHQ/openagent-eval/blob/main/examples/openagent_eval_colab_tutorial.ipynb)
  and choose *Runtime → Run all*.
- **Locally:** download
  [`openagent_eval_colab_tutorial.ipynb`](https://github.com/OpenAgentHQ/openagent-eval/blob/main/examples/openagent_eval_colab_tutorial.ipynb)
  and open it with `jupyter notebook`.

## Prerequisites

None for the offline walkthrough — the notebook installs its own dependencies in the
first cell:

```bash
pip install -q openagent-eval pytest
```

The optional final section runs against a real provider when an `OPENAI_API_KEY` is
present (via Colab Secrets or an environment variable); without a key it skips itself
and the notebook stays fully offline.

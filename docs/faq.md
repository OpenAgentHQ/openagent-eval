# FAQ

Frequently asked questions about OpenAgent Eval.

??? question "What is OpenAgent Eval?"
    An open-source, local-first CLI framework for evaluating RAG systems and AI Agents. Our goal is to
    become the `pytest` of AI evaluation — a familiar, composable way to measure quality.

??? question "Do I need an API key?"
    Only if you use a hosted LLM provider (OpenAI, Gemini, Anthropic, Groq, OpenRouter). You can run
    fully locally with [Ollama](https://ollama.com) — no API key required.

??? question "Which LLM providers are supported?"
    OpenAI, Google Gemini, Anthropic, Groq, OpenRouter, and Ollama (local). See
    [Architecture](architecture.md#providers-openagent_evalproviders) for the base classes and how to
    add your own.

??? question "Which retrievers are supported?"
    Chroma today, with more (FAISS, Weaviate, Pinecone) planned. Implement `BaseRetrieverProvider` to
    add one.

??? question "Can I use OpenAgent Eval inside pytest?"
    Yes. Import `Evaluator` from `openagent_eval` and assert on `result.summary`. See
    [Examples](examples.md#sdk-evaluate-in-a-pytest-suite).

??? question "How do I add a custom metric?"
    Subclass `openagent_eval.metrics.base.BaseMetric`, implement `score(...)`, and register it via the
    plugin manager. A template lives at `openagent_eval/plugins/examples/custom_metric.py`.

??? question "Which report formats are available?"
    Terminal, Markdown, HTML, and JSON, plus a side-by-side `comparison` report for
    `oaeval compare`.

??? question "Does it send my data anywhere?"
    No. OpenAgent Eval is local-first. The only network calls are to the LLM/retriever providers you
    configure. We do not collect telemetry.

??? question "What Python versions are supported?"
    Python >= 3.11.

??? question "How do I deploy the documentation?"
    Push to `main` — GitHub Actions builds and deploys the site to GitHub Pages automatically. See
    [Contributing](contributing.md#documentation) for local preview.

??? question "Where do I get help?"
    - [GitHub Issues](https://github.com/OpenAgentHQ/openagent-eval/issues) for bugs
    - [GitHub Discussions](https://github.com/OpenAgentHQ/openagent-eval/discussions) for questions
    - [Discord](https://discord.gg/openagenthq) for community chat

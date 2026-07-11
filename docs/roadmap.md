# Roadmap

OpenAgent Eval is evolving from a RAG evaluation tool into a full AI agent evaluation framework.
The roadmap below reflects our current plans — priorities may shift based on community feedback.

## v0.3.0 — Current

- [x] RAG evaluation pipeline
- [x] CLI (`oaeval`) and Python SDK
- [x] Plugin architecture
- [x] Multiple report formats (terminal, markdown, html, json)
- [x] Retrieval, generation, performance, and cost metrics
- [x] 11 retriever providers (Chroma, Qdrant, Pinecone, Weaviate, FAISS, pgvector, Elasticsearch, BM25, HTTP, Memory, Mock)
- [x] Corpus Health Auditor (contradiction, staleness, duplicates, coverage)
- [x] Component Diagnosis (blame attribution, failure modes)
- [x] Synthetic Test Data (question generation, adversarial cases)
- [x] NLI-based metrics (DeBERTa faithfulness, relevancy scoring)
- [x] Comprehensive documentation

## v1.0 — Stable Release (planned)

- [ ] Generic LLM-as-Judge for custom criteria
- [ ] Pytest plugin for RAG evaluation
- [ ] Threshold-based test gating
- [ ] GitHub Actions workflow example
- [ ] Documentation site (this site) and GitHub Pages deployment

## v2.0 — AI Agent Evaluation (planned)

- [ ] Tool-call evaluation
- [ ] Planning / reasoning evaluation
- [ ] Memory evaluation
- [ ] Multi-agent evaluation
- [ ] Dataset versioning and experiment tracking

## v3.0 — Platform & Integration (future)

- [ ] CI/CD integration and native GitHub Action
- [ ] Cloud synchronization of evaluation runs
- [ ] Hosted evaluation dashboard
- [ ] Team collaboration and shared baselines

## How we prioritize

1. **Community requests** raised in [Discussions](https://github.com/OpenAgentHQ/openagent-eval/discussions).
2. **Contributor interest** — the fastest path is an open PR.
3. **Ecosystem gaps** — providers and metrics the community needs most.

## Get involved

- Propose a feature in [Discussions](https://github.com/OpenAgentHQ/openagent-eval/discussions).
- Pick up a planned item and open a PR — see [Contributing](contributing.md).
- Ask questions in the [FAQ](faq.md).

!!! note "Subject to change"
    This roadmap is indicative. Items may be reordered, merged, or deferred as the project matures.

# Roadmap

## Overview

OpenAgent Eval is an open-source CLI framework for evaluating RAG systems and AI Agents. This roadmap outlines our planned features and improvements.

---

## Current Status

**Version:** 0.3.0 (Development)
**Phase:** Phase 12 - Advanced Providers & NLI Metrics (Complete)
**Status:** Active Development

---

## Version 1.0 - RAG Evaluation Core

**Target:** Q3 2026

### Features

- [x] RAG evaluation pipeline
- [x] Retrieval metrics (precision, recall, MRR, NDCG, hit rate)
- [x] Generation metrics (faithfulness, relevancy, hallucination)
- [x] Classic metrics (BLEU, ROUGE, F1, exact match)
- [x] Performance tracking (latency)
- [x] Cost tracking (tokens, estimated cost)
- [x] Report generation (Terminal, Markdown, HTML, JSON)
- [x] Experiment comparison
- [x] Failure analysis
- [x] Plugin system
- [x] CLI commands (init, run, report, compare, list, doctor, validate, delete, diagnose, audit, synth)
- [x] Comprehensive documentation

### Supported Providers

- OpenAI
- Gemini
- Anthropic
- Groq
- OpenRouter
- Ollama

### Supported Retrievers

- ChromaDB
- Qdrant
- Pinecone
- Weaviate
- FAISS
- pgvector
- Elasticsearch
- BM25
- Memory
- HTTP
- Mock

---

## Version 1.1 - Production-Grade RAG Evaluation

**Target:** Q3 2026 (after v1.0)

### Corpus Health Auditor (THE DIFFERENTIATOR)

- [x] Cross-document contradiction detection
- [x] Unmarked obsolescence detection
- [x] Divergent duplicate detection
- [x] Thematic coverage analysis
- [x] `oaeval audit` CLI command
- [x] Corpus health reports

### LLM-as-Judge Metrics

- [x] NLI-based faithfulness scoring (DeBERTa)
- [x] NLI-based answer relevancy scoring
- [x] Claim extraction for atomic verification
- [x] Evidence finding for claim support
- [ ] Generic LLM-as-Judge for custom criteria

### Component Diagnosis

- [x] Blame attribution (retrieval vs generation vs chunking)
- [x] 8 failure mode detection
- [x] Actionable recommendations
- [x] `oaeval diagnose` CLI command

### Synthetic Test Data

- [x] Question generation from documents
- [x] Adversarial test case generation
- [x] Dataset augmentation
- [x] `oaeval synth` CLI command

### CI/CD Integration

- [ ] Pytest plugin for RAG evaluation
- [ ] Threshold-based test gating
- [ ] GitHub Actions workflow example

---

## Version 1.x - Enhancements

**Target:** Q4 2026

### Planned Features

- [ ] Additional LLM providers
- [ ] More retrieval metrics
- [ ] Streaming support
- [ ] Batch evaluation mode
- [ ] Configuration templates
- [ ] Dataset generators
- [ ] Custom report templates
- [ ] Webhook notifications
- [ ] Production monitoring (live traffic sampling)

---

## Version 2.0 - Agent Evaluation

**Target:** Q2 2027

### Agent Capabilities

- [ ] Tool-call evaluation
- [ ] Planning evaluation
- [ ] Memory evaluation
- [ ] Multi-agent evaluation
- [ ] Trace analysis

### Advanced Metrics

- [ ] LLM-as-judge metrics
- [ ] Custom metric builder
- [ ] Metric composition
- [ ] A/B testing support
- [ ] Statistical significance testing

---

## Version 3.0 - Enterprise & Integration

**Target:** Q4 2027

### CI/CD Integration

- [ ] GitHub Action
- [ ] GitLab CI integration
- [ ] Jenkins plugin
- [ ] Azure DevOps extension

### Cloud Features

- [ ] Cloud synchronization
- [ ] Hosted evaluation platform
- [ ] Team collaboration
- [ ] Shared datasets
- [ ] Result sharing

### Enterprise Reporting

- [ ] Dashboard (optional)
- [ ] Custom report builder
- [ ] Scheduled evaluations
- [ ] Alert system
- [ ] SLA monitoring

---

## Version 4.0 - AI-Native Evaluation

**Target:** 2028

### Self-Improving Systems

- [ ] Automated metric selection
- [ ] Adaptive thresholds
- [ ] Intelligent dataset generation
- [ ] Auto-optimization suggestions

### Advanced Agent Evaluation

- [ ] Autonomous agent evaluation
- [ ] Agent comparison framework
- [ ] Agent evolution tracking
- [ ] Multi-modal agent evaluation

---

## Contributing

We welcome community contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Priority Areas

1. **CI/CD Integration** - Pytest plugin, GitHub Actions workflow
2. **Generic LLM-as-Judge** - Custom criteria evaluation
3. **Tests** - Increase test coverage
4. **Providers** - Add new LLM/retriever adapters
5. **Metrics** - Add new evaluation metrics

---

## Release Schedule

| Version | Target Date | Focus |
|---------|-------------|-------|
| v0.1.0 | 2026-07-08 | Foundation, Data, Metrics, Reports, Providers, Plugins |
| v0.2.0 | 2026-07-10 | CLI Commands, Documentation |
| v0.3.0 | 2026-07-11 | Corpus Health, Diagnosis, Synthesis, Advanced Providers, NLI |
| v1.0 | Q3 2026 | RAG Evaluation Core (stable) |
| v1.1 | Q4 2026 | CI/CD Integration, Generic LLM-as-Judge |
| v2.0 | Q2 2027 | Agent Evaluation |
| v3.0 | Q4 2027 | Enterprise Features |
| v4.0 | 2028 | AI-Native Evaluation |

*Dates are approximate and subject to change.*

---

## Follow Us

- **GitHub:** [OpenAgentHQ/openagent-eval](https://github.com/OpenAgentHQ/openagent-eval)
- **Twitter:** @OpenAgentdev
- **Discord:** [Join our community](https://discord.gg/openagent-eval)

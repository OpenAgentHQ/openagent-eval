# TASKS.md - Project Task List

> Track all project tasks across development phases.
> Update after every major milestone.

---

## TODO

### Phase 1: Project Foundation
- [ ] Initialize project with `uv init`
- [ ] Create `pyproject.toml` with all dependencies
- [ ] Set up directory structure (openagent_eval/*)
- [ ] Create `__init__.py` files for all modules
- [ ] Create exception hierarchy (exceptions/*)
- [ ] Implement CLI skeleton with Typer
- [ ] Create configuration system (Pydantic v2 + YAML)
- [ ] Implement core module (engine.py, pipeline.py, executor.py, registry.py)
- [ ] Set up pytest and testing infrastructure
- [ ] Create initial README.md
- [ ] Set up linting (ruff) and formatting
- [ ] Create ARCHITECTURE.md

### Phase 2: Data Layer
- [ ] Define BaseDatasetLoader interface
- [ ] Implement JSON dataset loader
- [ ] Implement JSONL dataset loader
- [ ] Implement CSV dataset loader
- [ ] Implement HuggingFace dataset loader
- [ ] Create dataset validation (Pydantic models)
- [ ] Implement dataset schema enforcement
- [ ] Write unit tests for all loaders

### Phase 3: Metrics System
- [ ] Define BaseMetric interface
- [ ] Create MetricResult model
- [ ] Implement retrieval metrics:
  - [ ] Context Precision
  - [ ] Context Recall
  - [ ] Recall@K
  - [ ] Precision@K
  - [ ] Hit Rate
  - [ ] Mean Reciprocal Rank (MRR)
  - [ ] NDCG
- [ ] Implement generation metrics:
  - [ ] Faithfulness (Ragas integration)
  - [ ] Answer Relevancy (Ragas integration)
  - [ ] Hallucination Detection (DeepEval integration)
  - [ ] Semantic Similarity (Sentence Transformers)
  - [ ] Exact Match (HF Evaluate)
  - [ ] F1 Score (HF Evaluate)
  - [ ] BLEU (HF Evaluate)
  - [ ] ROUGE (HF Evaluate)
  - [ ] BERTScore
- [ ] Implement performance metrics:
  - [ ] Embedding latency
  - [ ] Retrieval latency
  - [ ] LLM latency
  - [ ] Total latency
- [ ] Implement cost metrics:
  - [ ] Token counting
  - [ ] Cost estimation
- [ ] Write unit tests for all metrics

### Phase 4: Reports
- [ ] Define ReportGenerator interface
- [ ] Implement terminal report (Rich)
- [ ] Implement Markdown report
- [ ] Implement HTML report (Jinja2)
- [ ] Implement JSON report
- [ ] Create failure analysis reporting
- [ ] Implement experiment comparison reports
- [ ] Write unit tests for all reporters

### Phase 5: Providers
- [ ] Define LLMProvider interface
- [ ] Define Retriever interface
- [ ] Implement OpenAI adapter
- [ ] Implement Gemini adapter
- [ ] Implement Anthropic adapter
- [ ] Implement Groq adapter
- [ ] Implement OpenRouter adapter
- [ ] Implement Ollama adapter (token tracking only)
- [ ] Implement Chroma retriever adapter
- [ ] Write unit tests for all providers

### Phase 6: Plugin System
- [ ] Design plugin registry
- [ ] Implement entry point discovery
- [ ] Create plugin loading mechanism
- [ ] Write plugin development guide
- [ ] Create example custom metric
- [ ] Write unit tests for plugin system

### Phase 7: CLI Commands
- [ ] Implement `oaeval init`
- [ ] Implement `oaeval run`
- [ ] Implement `oaeval report`
- [ ] Implement `oaeval compare`
- [ ] Implement `oaeval list`
- [ ] Implement `oaeval doctor`
- [ ] Write CLI integration tests

### Phase 8: Documentation
- [ ] Create docs/01_vision.md
- [ ] Create docs/02_problem_statement.md
- [ ] Create docs/03_product_requirements.md
- [ ] Create docs/04_architecture.md
- [ ] Create docs/05_project_structure.md
- [ ] Create docs/06_cli_spec.md
- [ ] Create docs/07_metric_system.md
- [ ] Create docs/08_plugin_system.md
- [ ] Create docs/09_coding_guidelines.md
- [ ] Create docs/10_development_plan.md
- [ ] Create docs/11_future_roadmap.md
- [ ] Create docs/examples.md
- [ ] Create CONTRIBUTING.md
- [ ] Create ROADMAP.md
- [ ] Create CHANGELOG.md

---

## IN PROGRESS

*No tasks currently in progress.*

---

## COMPLETED

### Milestone 0: Documentation & Architecture
- [x] Read and understand PROJECT.md
- [x] Create AGENT.md (engineering handbook)
- [x] Create CONTEXT.md (working memory)
- [x] Create DECISIONS.md (architectural decisions)
- [x] Create TASKS.md (this file)
- [x] Architecture analysis and improvements
- [x] Apply architecture decisions (D011-D016)
- [x] Update all project files
- [x] Create .ai/ directory structure
- [x] Move all project files to .ai/

---

## BLOCKED

*No tasks currently blocked.*

---

## Task Dependencies

```
Phase 1 (Foundation)
    ↓
Phase 2 (Data Layer) ← depends on Phase 1
    ↓
Phase 3 (Metrics) ← depends on Phase 1
    ↓
Phase 4 (Reports) ← depends on Phase 1
    ↓
Phase 5 (Providers) ← depends on Phase 1
    ↓
Phase 6 (Plugins) ← depends on Phases 2-5
    ↓
Phase 7 (CLI) ← depends on Phases 1-6
    ↓
Phase 8 (Documentation) ← can run in parallel with Phase 7
```

---

## Notes

- Phases 2-5 can be developed in parallel after Phase 1
- Phase 6 requires interfaces from Phases 2-5
- Phase 7 is integration work
- Phase 8 can start early and run in parallel
- Exception hierarchy is part of Phase 1 (required foundation)
- Core module (engine, pipeline, executor, registry) is part of Phase 1

---

## Task Priority Legend

| Priority | Description |
|----------|-------------|
| 🔴 High | Must complete before next phase |
| 🟡 Medium | Important but can wait |
| 🟢 Low | Nice to have, can be deferred |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-07-08 | Initial TASKS.md created |
| 2026-07-08 | Updated with architecture decisions (D011-D016) |
| 2026-07-08 | Added exception hierarchy to Phase 1 |
| 2026-07-08 | Added core module to Phase 1 |
| 2026-07-08 | Added ARCHITECTURE.md to Phase 1 |
| 2026-07-08 | Created .ai/ directory structure |
| 2026-07-08 | Moved all project files to .ai/ |

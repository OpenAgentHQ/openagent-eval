# TASKS.md - Project Task List

> Track all project tasks across development phases.
> Update after every major milestone.

---

## TODO

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

### Phase 1: Project Foundation
- [x] Initialize project with `uv init`
- [x] Create `pyproject.toml` with all dependencies
- [x] Set up directory structure (openagent_eval/*)
- [x] Create `__init__.py` files for all modules
- [x] Create exception hierarchy (exceptions/*)
- [x] Implement CLI skeleton with Typer
- [x] Create configuration system (Pydantic v2 + YAML)
- [x] Implement core module (engine.py, pipeline.py, executor.py, registry.py)
- [x] Set up pytest and testing infrastructure
- [x] Set up linting (ruff) and formatting

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

### Phase 2: Data Layer
- [x] Define BaseDatasetLoader interface
- [x] Implement JSON dataset loader
- [x] Implement JSONL dataset loader
- [x] Implement CSV dataset loader
- [x] Implement HuggingFace dataset loader
- [x] Create dataset validation (Pydantic models)
- [x] Implement dataset schema enforcement
- [x] Write unit tests for all loaders

### Phase 3: Metrics System
- [x] Define BaseMetric interface
- [x] Create MetricResult model
- [x] Implement retrieval metrics:
  - [x] Context Precision
  - [x] Context Recall
  - [x] Recall@K
  - [x] Precision@K
  - [x] Hit Rate
  - [x] Mean Reciprocal Rank (MRR)
  - [x] NDCG
- [x] Implement generation metrics:
  - [x] Faithfulness (Ragas integration stub)
  - [x] Answer Relevancy (Ragas integration stub)
  - [x] Hallucination Detection (DeepEval integration stub)
  - [x] Semantic Similarity (Sentence Transformers)
  - [x] Exact Match
  - [x] F1 Score
  - [x] BLEU (HF Evaluate)
  - [x] ROUGE (HF Evaluate)
  - [x] BERTScore
- [x] Implement performance metrics:
  - [x] Latency tracking
- [x] Implement cost metrics:
  - [x] Token counting
  - [x] Cost estimation
- [x] Write unit tests for all metrics (86 tests)

---

## BLOCKED

*No tasks currently blocked.*

---

## Task Dependencies

```
Phase 1 (Foundation) ✓ COMPLETE
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

- Phase 1 is complete - all foundation work done
- Phases 2-5 can be developed in parallel
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
| 2026-07-08 | Phase 1 completed - all foundation work done |
| 2026-07-08 | Phase 2 completed - Data Layer implemented |
| 2026-07-08 | Phase 3 completed - Metrics System implemented |
| 2026-07-08 | 136 tests passing (50 existing + 86 new metrics tests) |

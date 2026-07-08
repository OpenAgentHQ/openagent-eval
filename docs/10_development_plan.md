# Development Plan

## Overview

OpenAgent Eval follows a phased development approach. Each phase builds on the previous one, ensuring a solid foundation before adding complexity.

---

## Phase Overview

```
Phase 1: Foundation ──────────────────────────────────┐
    ↓                                                  │
Phase 2: Data Layer ──────────────────────────────────┤
    ↓                                                  │
Phase 3: Metrics ─────────────────────────────────────┤
    ↓                                                  │
Phase 4: Reports ─────────────────────────────────────┤
    ↓                                                  │
Phase 5: Providers ───────────────────────────────────┤
    ↓                                                  │
Phase 6: Plugin System ───────────────────────────────┤
    ↓                                                  │
Phase 7: CLI Commands ────────────────────────────────┤
    ↓                                                  │
Phase 8: Documentation ───────────────────────────────┘
```

---

## Phase 1: Foundation ✅

**Status:** Complete

**Objectives:**

- Initialize project with `uv`
- Create `pyproject.toml` with all dependencies
- Set up directory structure
- Create exception hierarchy
- Implement CLI skeleton with Typer
- Create configuration system (Pydantic v2 + YAML)
- Implement core module (engine, pipeline, executor, registry)
- Set up testing infrastructure
- Set up linting and formatting

**Deliverables:**

- [x] Project structure
- [x] Exception hierarchy
- [x] CLI skeleton
- [x] Configuration system
- [x] Core module
- [x] Testing infrastructure

---

## Phase 2: Data Layer ✅

**Status:** Complete

**Objectives:**

- Define `BaseDatasetLoader` interface
- Implement JSON, JSONL, CSV, HuggingFace loaders
- Create dataset validation (Pydantic models)
- Implement dataset schema enforcement

**Deliverables:**

- [x] Base interface
- [x] JSON loader
- [x] JSONL loader
- [x] CSV loader
- [x] HuggingFace loader
- [x] Validation models

---

## Phase 3: Metrics ✅

**Status:** Complete

**Objectives:**

- Define `BaseMetric` interface
- Create `MetricResult` model
- Implement retrieval metrics
- Implement generation metrics
- Implement classic metrics
- Implement performance and cost metrics

**Deliverables:**

- [x] Base interface
- [x] MetricResult model
- [x] Retrieval metrics (7)
- [x] Generation metrics (9)
- [x] Classic metrics (4)
- [x] Performance metrics (1)
- [x] Cost metrics (1)

---

## Phase 4: Reports ✅

**Status:** Complete

**Objectives:**

- Define `ReportGenerator` interface
- Implement terminal report (Rich)
- Implement Markdown report
- Implement HTML report (Jinja2)
- Implement JSON report
- Create failure analysis reporting
- Implement experiment comparison reports

**Deliverables:**

- [x] Base interface
- [x] Terminal report
- [x] Markdown report
- [x] HTML report
- [x] JSON report
- [x] Failure analysis
- [x] Experiment comparison

---

## Phase 5: Providers ✅

**Status:** Complete

**Objectives:**

- Define `LLMProvider` interface
- Define `Retriever` interface
- Implement LLM adapters (OpenAI, Gemini, Anthropic, Groq, OpenRouter, Ollama)
- Implement Chroma retriever adapter

**Deliverables:**

- [x] LLM interface
- [x] Retriever interface
- [x] OpenAI adapter
- [x] Gemini adapter
- [x] Anthropic adapter
- [x] Groq adapter
- [x] OpenRouter adapter
- [x] Ollama adapter
- [x] Chroma adapter

---

## Phase 6: Plugin System ✅

**Status:** Complete

**Objectives:**

- Design plugin registry
- Implement entry point discovery
- Create plugin loading mechanism
- Write plugin development guide
- Create example custom metric

**Deliverables:**

- [x] Plugin registry
- [x] Entry point discovery
- [x] Plugin loading
- [x] Development guide
- [x] Example plugins

---

## Phase 7: CLI Commands

**Status:** Pending

**Objectives:**

- Implement `oaeval init`
- Implement `oaeval run`
- Implement `oaeval report`
- Implement `oaeval compare`
- Implement `oaeval list`
- Implement `oaeval doctor`
- Write CLI integration tests

**Deliverables:**

- [ ] `oaeval init` command
- [ ] `oaeval run` command
- [ ] `oaeval report` command
- [ ] `oaeval compare` command
- [ ] `oaeval list` command
- [ ] `oaeval doctor` command
- [ ] Integration tests

---

## Phase 8: Documentation

**Status:** In Progress

**Objectives:**

- Create comprehensive documentation
- Write contributor guidelines
- Create project roadmap
- Initialize changelog

**Deliverables:**

- [x] Vision documentation
- [x] Problem statement
- [x] Product requirements
- [x] Architecture documentation
- [x] Project structure
- [x] CLI specification
- [x] Metric system documentation
- [x] Plugin system documentation
- [x] Coding guidelines
- [x] Development plan
- [x] Future roadmap
- [x] Examples
- [ ] CONTRIBUTING.md
- [ ] ROADMAP.md
- [ ] CHANGELOG.md

---

## Future Phases

### Version 2: Agent Evaluation

- AI Agent evaluation
- Tool-call evaluation
- Planning evaluation
- Memory evaluation
- Multi-agent evaluation
- Trace analysis

### Version 3: Enterprise Features

- CI/CD integration
- GitHub Action
- Cloud synchronization
- Hosted evaluation platform
- Enterprise reporting

---

## Development Principles

1. **Test-Driven Development** - Write tests before code
2. **Incremental Delivery** - Ship working code frequently
3. **Code Review** - All changes reviewed before merge
4. **Documentation** - Update docs with code changes
5. **Backward Compatibility** - Avoid breaking changes
6. **Performance** - Consider performance from the start
7. **Security** - Follow security best practices

---

## Quality Gates

Before completing any phase:

1. All tests passing
2. Code coverage >= 80%
3. No linting errors
4. Type hints on all public APIs
5. Documentation updated
6. Code reviewed
7. PR created and approved

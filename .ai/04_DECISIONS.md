# DECISIONS.md - Architectural Decisions

> Record every architectural decision with reasons.
> This helps future developers understand why the codebase is shaped the way it is.

---

## Decision Log

### D001: No LangChain Dependency

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Building an evaluation framework that needs to support multiple AI frameworks.

**Decision:** Build as a pure Python framework with adapters, not on top of LangChain or any other AI framework.

**Rationale:**
- Locked into one ecosystem if we build on LangChain
- Frequent breaking changes in AI frameworks
- Hard to support custom RAG implementations
- Extra dependency for everyone

**Consequences:**
- More work upfront to build adapters
- Longer-term maintainability
- Framework agnostic design
- Easier adoption by developers using different frameworks

**Alternatives Considered:**
- Build on LangChain: Rejected due to ecosystem lock-in
- Build on LlamaIndex: Rejected for same reasons
- Build on Haystack: Rejected for same reasons

---

### D002: SDK + CLI Dual Interface

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need both CLI for quick usage and SDK for programmatic access.

**Decision:** Design as Python evaluation SDK with CLI on top, not just a CLI app.

**Rationale:**
- Users can use CLI for quick evaluations
- Users can use SDK for custom integrations
- Single codebase, two entry points
- Scalable architecture aligned with OpenAgentHQ ecosystem

**Consequences:**
- CLI layer must be thin (no business logic)
- Core logic must be importable
- API must be clean and documented

**Alternatives Considered:**
- CLI-only: Rejected, limits adoption
- SDK-only: Rejected, reduces usability for quick evaluations

---

### D003: Plugin-Based Architecture

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need extensibility for metrics, providers, and other components.

**Decision:** Everything should implement an interface. Users can extend via plugins.

**Rationale:**
- Users can add custom metrics without core changes
- Easy to support new LLM providers
- Community can contribute extensions
- Clean separation of concerns

**Consequences:**
- Must define clear interfaces (BaseMetric, LLMProvider, etc.)
- Plugin discovery mechanism needed
- Documentation for plugin development required

**Alternatives Considered:**
- Hardcoded metrics: Rejected, not extensible
- Configuration-only extension: Rejected, too limiting

---

### D004: Local-First Design

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Developers want simple evaluation without complex setup.

**Decision:** No cloud services, no dashboards, no authentication. Everything runs from the command line.

**Rationale:**
- Most evaluation platforms require cloud services, dashboards, expensive subscriptions
- Many developers skip evaluation because of complexity
- Local-first is simpler, faster, and more private
- Aligns with developer preferences

**Consequences:**
- No team collaboration features in v1
- No cloud storage
- Reports are local files
- No centralized dashboards

**Alternatives Considered:**
- Cloud-first: Rejected, adds complexity
- Hybrid: Rejected for v1, can be added in v3

---

### D005: YAML Configuration

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need simple, readable configuration format.

**Decision:** Use YAML for configuration files.

**Rationale:**
- Human-readable
- Supports comments
- Common in Python ecosystem
- Simple to parse with PyYAML

**Consequences:**
- Requires PyYAML dependency
- Need YAML validation with Pydantic
- Must handle YAML syntax errors gracefully

**Alternatives Considered:**
- JSON: Rejected, no comments, less readable
- TOML: Rejected, less common in Python ecosystem
- Python config files: Rejected, security concerns

---

### D006: Async Pipeline Execution

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Evaluations need to process many questions efficiently.

**Decision:** Use asyncio for parallel evaluation execution.

**Rationale:**
- Parallel evaluation for speed
- Better resource utilization
- Modern Python async support
- Compatible with async LLM clients

**Consequences:**
- All provider adapters must support async
- Pipeline must be async-compatible
- Need async testing patterns

**Alternatives Considered:**
- Threading: Rejected, GIL limitations
- Multiprocessing: Rejected, too heavy for I/O-bound tasks
- Synchronous: Rejected, too slow for large datasets

---

### D007: Pydantic v2 for Validation

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need strong typing and configuration validation.

**Decision:** Use Pydantic v2 for all data models and validation.

**Rationale:**
- Strong typing
- Excellent validation
- Fast performance (Rust core)
- Industry standard for Python data models

**Consequences:**
- All data models must use Pydantic
- Configuration validation automatic
- Need to handle Pydantic v2 migration if upgrading

**Alternatives Considered:**
- Dataclasses: Rejected, less validation support
- Marshmallow: Rejected, slower
- attrs: Rejected, less popular

---

### D008: v1 Scope - RAG Evaluation Only

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need to focus on core functionality for first release.

**Decision:** Version 1 focuses entirely on RAG Evaluation. Agent evaluation comes in v2.

**Rationale:**
- RAG evaluation is the core use case
- Agent evaluation is more complex
- Better to do one thing well than many things poorly
- Clear roadmap for future versions

**Consequences:**
- No agent evaluation features in v1
- No tool-call, planning, or memory evaluation
- Future versions have clear scope

**Alternatives Considered:**
- Include agent evaluation: Rejected, scope too large
- Skip RAG evaluation: Rejected, core value proposition

---

### D009: Rich for Terminal UI

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need beautiful terminal output without building a dashboard.

**Decision:** Use Rich for progress bars, tables, and colored output.

**Rationale:**
- Beautiful output without dashboard
- Easy to implement
- Good developer experience
- Compatible with Typer

**Consequences:**
- Rich dependency
- Need to design terminal-friendly reports
- Color support varies by terminal

**Alternatives Considered:**
- Colorama: Rejected, too basic
- Custom terminal UI: Rejected, too much work
- No terminal UI: Rejected, poor developer experience

---

### D010: uv as Package Manager

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need fast, modern dependency management.

**Decision:** Use uv from day one for dependency management.

**Rationale:**
- Faster installs than pip
- Reproducible environments
- Modern tooling
- Growing adoption in Python ecosystem

**Consequences:**
- Need uv installed
- Different workflow from pip
- May have compatibility issues with some packages

**Alternatives Considered:**
- pip: Rejected, slower
- Poetry: Rejected, heavier
- pdm: Rejected, less popular

---

### D011: CLI Naming Convention

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need consistent naming across repository, package, and CLI.

**Decision:** Use the following naming convention:
- Repository: `openagent-eval`
- Python package: `openagent_eval`
- CLI command: `oaeval`
- Documentation: Always use `oaeval`

**Rationale:**
- Consistency across all contexts
- Clear distinction between repository and package
- CLI name is short and memorable
- Avoids confusion in documentation

**Consequences:**
- All documentation must use `oaeval`
- All CLI references must use `oaeval`
- Package imports use `openagent_eval`
- Repository name uses `openagent-eval`

**Alternatives Considered:**
- `openagent-eval` as CLI: Rejected, too long
- `oa-eval`: Rejected, inconsistent
- `eval`: Rejected, too generic

---

### D012: Core Module Structure

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need clear separation of orchestration concerns.

**Decision:** Use `core/` module with four files:
- `engine.py` - Main evaluation engine
- `pipeline.py` - Evaluation pipeline
- `executor.py` - Task execution
- `registry.py` - Plugin/component registry

**Rationale:**
- Clear separation of orchestration concerns
- Each file has single responsibility
- Easy to test and maintain
- Avoids monolithic orchestrator

**Consequences:**
- No `evaluators/` directory (removed)
- `core/` is the orchestration layer
- All orchestration logic goes in `core/`

**Alternatives Considered:**
- Single `orchestrator.py`: Rejected, too monolithic
- `evaluators/` directory: Rejected, redundant with `core/`
- Split across multiple modules: Rejected, too fragmented

---

### D013: Exception Hierarchy

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need structured error handling across the framework.

**Decision:** Create dedicated exception hierarchy:
- `exceptions/base.py` - `OpenAgentEvalError` (base class)
- `exceptions/config.py` - Configuration errors
- `exceptions/dataset.py` - Dataset errors
- `exceptions/metric.py` - Metric errors
- `exceptions/provider.py` - Provider errors
- `exceptions/plugin.py` - Plugin errors
- `exceptions/cli.py` - CLI errors

**Rationale:**
- Structured error handling
- Easy to catch specific errors
- Better debugging experience
- Professional error handling

**Consequences:**
- All custom exceptions inherit from `OpenAgentEvalError`
- Never raise generic `Exception`
- Always use meaningful error messages
- Always include context in errors

**Alternatives Considered:**
- Generic exceptions: Rejected, unprofessional
- Single exception class: Rejected, too broad
- No custom exceptions: Rejected, poor debugging

---

### D014: Testing Structure

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need proper testing structure for maintainability.

**Decision:** Use testing structure:
- `tests/unit/` - Unit tests by module
- `tests/integration/` - Integration tests
- `tests/fixtures/` - Test fixtures
- `tests/sample_data/` - Sample datasets

**Rationale:**
- Clear separation of test types
- Easy to find and maintain tests
- Proper fixture management
- Sample data for testing

**Consequences:**
- All tests go in appropriate directory
- Use pytest fixtures for common data
- Mock all external dependencies
- Target 80%+ coverage

**Alternatives Considered:**
- Flat test structure: Rejected, hard to maintain
- Tests next to source: Rejected, mixes concerns
- No fixtures directory: Rejected, poor test organization

---

### D015: Configuration Validation Requirements

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need robust configuration validation.

**Decision:** Configuration system must support:
- YAML format
- Environment variables
- Pydantic validation
- Default values
- Helpful validation errors

**Rationale:**
- User-friendly configuration
- Flexible environment variable support
- Strong validation with Pydantic
- Good developer experience

**Consequences:**
- Must validate all configuration on load
- Must provide helpful error messages
- Must support environment variables for secrets
- Must have sensible defaults

**Alternatives Considered:**
- JSON configuration: Rejected, no comments
- No validation: Rejected, poor UX
- Manual validation: Rejected, error-prone

---

### D016: Documentation Workflow

**Date:** 2025-07-08
**Status:** Accepted
**Context:** Need to maintain project documentation automatically.

**Decision:** Maintain project files automatically:
- Update `AGENT.md` when project-wide knowledge changes
- Update `CONTEXT.md` after every major milestone
- Update `TASKS.md` after every major milestone
- Update `DECISIONS.md` when architectural decisions are made
- Create `ARCHITECTURE.md` for system design

**Rationale:**
- Documentation stays current
- No manual reminders needed
- Clear project state tracking
- Historical decision record

**Consequences:**
- Must update files after major milestones
- Must track all architectural decisions
- Must maintain task list
- Must keep working memory current

**Alternatives Considered:**
- Manual updates: Rejected, forgetful
- No documentation: Rejected, unprofessional
- Separate documentation process: Rejected, too heavy

---

## Pending Decisions

None at this time.

---

## Decision Template

```markdown
### DXXX: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Rejected | Superseded
**Context:** [Why this decision was needed]

**Decision:** [What was decided]

**Rationale:** [Why this decision was made]

**Consequences:** [What this decision implies]

**Alternatives Considered:** [What else was considered]
```

---

## Related Documents

- `.ai/00_PROJECT.md` - Product specification
- `.ai/02_AGENT.md` - Engineering handbook
- `.ai/03_CONTEXT.md` - Working memory

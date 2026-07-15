# DECISIONS.md — Architectural Decisions

> Why the codebase is shaped the way it is.

---

## Decision Log

| ID | Decision | Date |
|----|----------|------|
| D001 | No LangChain dependency — pure Python with adapters | 2026-07-08 |
| D002 | SDK + CLI dual interface — two entry points, one codebase | 2026-07-08 |
| D003 | Plugin-based architecture — everything implements ABCs | 2026-07-08 |
| D004 | Local-first — no cloud, no dashboards, no auth | 2026-07-08 |
| D005 | YAML configuration — human-readable with comments | 2026-07-08 |
| D006 | Async pipeline — asyncio for parallel evaluation | 2026-07-08 |
| D007 | Pydantic v2 — all models use Pydantic | 2026-07-08 |
| D008 | v1 scope: RAG only — agent eval in v2 | 2026-07-08 |
| D009 | Rich for terminal UI — beautiful output without dashboard | 2026-07-08 |
| D010 | uv as package manager — fast, modern | 2026-07-08 |
| D011 | CLI naming: `oaeval` (not `openagent-eval` or `eval`) | 2026-07-08 |
| D012 | Core module: `engine.py`, `pipeline.py`, `executor.py`, `registry.py` | 2026-07-08 |
| D013 | Exception hierarchy — every error subclasses `OpenAgentEvalError` | 2026-07-08 |
| D014 | Testing: `tests/unit/` by module, `tests/integration/`, 80%+ coverage | 2026-07-08 |
| D015 | Config validation: Pydantic v2 + YAML + env vars | 2026-07-08 |
| D016 | Documentation workflow: update files after milestones | 2026-07-08 |
| D017 | Corpus audit as step zero — run BEFORE connecting to RAG | 2026-07-11 |
| D018 | NLI-based scoring — DeBERTa faithfulness, not just word overlap | 2026-07-11 |
| D019 | Blame attribution — tell WHERE failures occur (retrieval vs generation) | 2026-07-11 |
| D020 | Synthetic test data — auto-generate from knowledge base | 2026-07-11 |
| D021 | Separate corpus audit from pipeline — different execution models | 2026-07-11 |
| D022 | MVI for docs — <200 lines, scannable in <30 seconds | 2026-07-15 |
| D023 | File-path architecture — real paths, not ASCII diagrams | 2026-07-15 |
| D024 | Compact working memory — milestones/changelog in git log | 2026-07-15 |

---

## Key Rationale

**Why no LangChain**: Ecosystem lock-in, breaking changes, extra dependency for users.

**Why plugin-based**: Users extend metrics/providers without core changes.

**Why corpus audit first**: 67% of hallucinations are extractive (wrong corpus data). No existing tool validates corpus.

**Why NLI scoring**: Word overlap is surface-level. NLI verifies entailment properly.

---

## Pending

None.

---

`PROJECT.md` · `AGENT.md` · `ARCHITECTURE.md` · `CONTEXT.md`

# ARCHITECTURE.md — System Architecture

> HOW OpenAgent Eval is built. See `PROJECT.md` for WHAT.

---

## Entry Points

| Entry | File | How to Invoke |
|-------|------|---------------|
| CLI | `openagent_eval/cli/main.py` | `oaeval <command>` |
| SDK | `openagent_eval/core/engine.py` | `from openagent_eval.core import Engine` |

CLI is thin shell — zero business logic, only parse + delegate + display.

---

## Module Map

| Module | Key Files | Responsibility |
|--------|-----------|----------------|
| `cli/` | `main.py`, `commands/*.py` | Typer CLI (12 subcommands) |
| `config/` | `models.py`, `loader.py`, `validator.py` | YAML/JSON config, Pydantic v2 |
| `core/` | `engine.py`, `pipeline.py`, `executor.py`, `registry.py` | Orchestration |
| `metrics/` | `base.py`, `retrieval/`, `generation/`, `nli/` | BaseMetric ABC + implementations |
| `providers/` | `base/`, `factory.py`, `llm/`, `retrievers/`, `embedders/` | Adapter interfaces + implementations |
| `datasets/` | `base.py`, `factory.py`, `json_loader.py`, etc. | BaseDatasetLoader ABC + loaders |
| `reports/` | `base.py`, `terminal.py`, `html.py`, `markdown.py`, `json_report.py` | ReportGenerator ABC + formats |
| `corpus/` | `auditor.py`, `contradiction.py`, `staleness.py`, `duplicates.py`, `coverage.py` | Pre-RAG corpus health check |
| `diagnosis/` | `analyzer.py`, `blame.py`, `chunking.py` | Blame attribution for failures |
| `synthesis/` | `generator.py`, `question_gen.py`, `adversarial.py` | Synthetic test data generation |
| `plugins/` | `discovery.py`, `loader.py`, `manager.py` | Entry-point plugin system |
| `cicd/` | `plugin.py`, `thresholds.py` | Pytest plugin for CI/CD gating |
| `exceptions/` | `base.py` + 9 domain files | `OpenAgentEvalError` hierarchy |

---

## ABCs (Interfaces to Implement)

| File | ABC | Abstract Methods |
|------|-----|-----------------|
| `metrics/base.py` | `BaseMetric` | `evaluate()` |
| `providers/base/llm.py` | `LLMProvider` | `generate()`, `get_token_count()` |
| `providers/base/retriever.py` | `Retriever` | `retrieve()` |
| `providers/embedders/base.py` | `Embedder` | `embed()` |
| `datasets/base.py` | `BaseDatasetLoader` | `load()`, `validate()` |
| `reports/base.py` | `ReportGenerator` | `generate()`, `generate_to_file()` |
| `corpus/base.py` | `BaseCorpusAnalyzer` | `analyze()` |

---

## Dependency Rules

```
cli/ → core/ → datasets/, metrics/, providers/, reports/
     → corpus/, diagnosis/, synthesis/

metrics/ → providers/ (for LLM-as-Judge)
corpus/ → providers/ (for LLM-as-Judge)
diagnosis/ → metrics/ (for MetricResult)
synthesis/ → providers/ (for generation)

exceptions/ → nothing (leaf)
types/ → nothing (leaf)
```

**Rule**: No circular dependencies. CLI is the only module that imports across all domains.

---

## Public API Imports

```python
from openagent_eval.core import Engine, Pipeline, Executor, Registry
from openagent_eval.config import Config, load_config
from openagent_eval.metrics import BaseMetric, MetricResult, faithfulness
from openagent_eval.providers import LLMProvider, Retriever, Document
from openagent_eval.datasets import Dataset, JSONDatasetLoader
from openagent_eval.reports import ReportGenerator, HTMLReport
from openagent_eval.corpus import CorpusAuditor
from openagent_eval.diagnosis import DiagnosisAnalyzer, FailureMode
from openagent_eval.synthesis import SyntheticDataGenerator
from openagent_eval.cicd import ThresholdEvaluator, OAEvalPlugin
from openagent_eval.plugins import PluginManager
```

---

## Design Principles

1. CLI as thin shell — no business logic in `cli/`
2. Typed errors — every failure is `OpenAgentEvalError` subclass
3. Async-native — all providers and pipeline are async
4. Lazy imports — heavy deps imported lazily from adapter files
5. Plugin-first — new implementations register via entry points
6. Pydantic v2 — all config/models/data structures validated

---

`PROJECT.md` · `AGENT.md` · `DECISIONS.md` · `CONTEXT.md`

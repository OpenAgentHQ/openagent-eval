"""End-to-end pipeline integration test: JSON dataset -> mocks -> metrics -> reports.

This test exercises the full evaluation pipeline described in issue #106:

1. Load a small sample dataset from a JSON file (via ``JSONDatasetLoader``).
2. Configure a mock LLM and a mock retriever (the project's own offline
   providers, no API keys required).
3. Run the full pipeline through ``core/engine.py`` (``Engine``).
4. Render the resulting report in every format (terminal, markdown, HTML, JSON).
5. Verify each report contains the expected data.

Crucially, the assertions prove the mock providers were *actually exercised*
rather than the pipeline silently falling back to an empty/default path:
``_SpyMockLLM`` / ``_SpyMockRetriever`` record their calls, and each mock answer
carries a unique sentinel that must reappear in the rendered reports. A pipeline
that never called the mocks would leave the call logs empty and the sentinels
absent, failing the test instead of passing vacuously.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    ReportConfig,
    RetrieverConfig,
)
from openagent_eval.core.engine import Engine
from openagent_eval.datasets.json_loader import JSONDatasetLoader
from openagent_eval.providers.llm.mock import MockLLMProvider
from openagent_eval.providers.retrievers.mock import MockRetriever
from openagent_eval.reports.html import HTMLReport
from openagent_eval.reports.json_report import JSONReport
from openagent_eval.reports.markdown import MarkdownReport
from openagent_eval.reports.terminal import TerminalReport

# Unique sentinels embedded in each item's ground truth. The mock LLM echoes the
# ground truth as its answer, so these strings can only appear in the results /
# reports if the mock actually generated them.
SENTINEL_0 = "ZZAlphaSentinel RAG combines retrieval with generation."
SENTINEL_1 = "ZZBetaSentinel a vector store indexes embeddings."


class _SpyMockLLM(MockLLMProvider):
    """Repo mock LLM that also records every prompt / ground truth it sees."""

    def __init__(self) -> None:
        super().__init__()
        self.prompts: list[str] = []
        self.ground_truths: list[str | None] = []

    async def generate_with_usage(self, prompt: str, **kwargs: object):  # type: ignore[override]
        self.prompts.append(prompt)
        self.ground_truths.append(kwargs.get("ground_truth"))  # type: ignore[arg-type]
        return await super().generate_with_usage(prompt, **kwargs)


class _SpyMockRetriever(MockRetriever):
    """Repo mock retriever that also records every query it is asked for."""

    def __init__(self) -> None:
        super().__init__()
        self.queries: list[str] = []

    async def retrieve(self, query: str, k: int = 5, **kwargs: object):  # type: ignore[override]
        self.queries.append(query)
        return await super().retrieve(query, k=k, **kwargs)


@pytest.fixture
def dataset_file(tmp_path: Path) -> Path:
    """Write a small sample dataset to a JSON file and return its path."""
    items = [
        {
            "question": "What is RAG?",
            "ground_truth": SENTINEL_0,
            "context": SENTINEL_0,
            "ground_truth_contexts": [SENTINEL_0],
        },
        {
            "question": "What is a vector store?",
            "ground_truth": SENTINEL_1,
            "context": SENTINEL_1,
            "ground_truth_contexts": [SENTINEL_1],
        },
    ]
    path = Path(tmp_path) / "sample_dataset.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    return path


@pytest.fixture
def dataset_dicts(dataset_file: Path) -> list[dict]:
    """Load the sample dataset from the JSON file via the project's loader."""
    dataset = JSONDatasetLoader().load(dataset_file)
    return dataset.to_dicts()


@pytest.fixture
def mock_config(dataset_file: Path) -> Config:
    return Config(
        dataset=DatasetConfig(path=str(dataset_file)),
        llm=LLMConfig(provider="mock", model="mock-model"),
        retriever=RetrieverConfig(provider="mock", settings={"collection_name": "c"}),
        metrics=MetricsConfig(
            retrieval=["context_precision", "context_recall", "recall_at_k"],
            generation=["faithfulness", "answer_relevancy", "exact_match", "f1_score"],
            performance=["latency"],
            cost=["token_count"],
        ),
        report=ReportConfig(output="json", output_dir="./test_reports"),
        parallel=False,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_generates_all_report_formats(
    mock_config: Config, dataset_dicts: list[dict]
) -> None:
    """Load -> run engine -> render every report format -> verify expected data."""
    # The dataset was loaded from the JSON file (two items survived the round-trip).
    assert len(dataset_dicts) == 2
    assert dataset_dicts[0]["question"] == "What is RAG?"

    engine = Engine(mock_config)
    report = await engine.run(dataset_dicts)

    # --- Summary reflects a real, fully successful run ------------------------
    assert report.summary["total_items"] == 2
    assert report.summary["successful_evaluations"] == 2
    assert report.summary["failed_evaluations"] == 0

    # --- Real-mock-path proof #1: mock output drives the metrics -------------
    # The mock LLM echoes the ground truth, so exact_match is perfect; the mock
    # retriever returns the ground-truth contexts, so retrieval metrics are
    # perfect. A silent fallback to an empty answer / no retrieval would drop
    # these to 0.0 and fail here.
    metrics_summary = report.summary["metrics_summary"]
    assert metrics_summary["exact_match"] == 1.0
    assert metrics_summary["context_precision"] == 1.0
    assert metrics_summary["context_recall"] == 1.0
    assert metrics_summary["recall_at_k"] == 1.0

    # --- Real-mock-path proof #2: sentinel answers made it into the results --
    answers = [r.answer for r in report.result.results]
    assert answers == [SENTINEL_0, SENTINEL_1]

    # --- Terminal report (summary + metrics, no per-item answers) ------------
    terminal_out = TerminalReport().generate(report)
    assert "OpenAgent Eval Report" in terminal_out
    assert "Total items:" in terminal_out
    assert "exact_match" in terminal_out

    # --- Markdown report -----------------------------------------------------
    markdown_out = MarkdownReport().generate(report)
    assert markdown_out.startswith("# ")
    assert "## Summary" in markdown_out
    assert "exact_match" in markdown_out
    assert SENTINEL_0 in markdown_out
    assert SENTINEL_1 in markdown_out

    # --- HTML report ---------------------------------------------------------
    html_out = HTMLReport().generate(report)
    assert "<html" in html_out.lower()
    assert SENTINEL_0 in html_out
    assert SENTINEL_1 in html_out

    # --- JSON report ---------------------------------------------------------
    json_out = JSONReport().generate(report)
    payload = json.loads(json_out)
    assert payload["summary"]["total_items"] == 2
    assert payload["summary"]["successful_evaluations"] == 2
    assert payload["summary"]["failed_evaluations"] == 0
    assert payload["summary"]["metrics_summary"]["exact_match"] == 1.0
    json_answers = [item["answer"] for item in payload["results"]]
    assert json_answers == [SENTINEL_0, SENTINEL_1]

    engine.shutdown()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mock_providers_are_actually_invoked(
    mock_config: Config, dataset_dicts: list[dict]
) -> None:
    """Inject spying mocks and assert they were called with the real inputs.

    This is the explicit call-count proof that the pipeline drives the mock LLM
    and mock retriever for every dataset item, forwarding the question and
    ground truth through to them.
    """
    spy_llm = _SpyMockLLM()
    spy_retriever = _SpyMockRetriever()

    engine = Engine(mock_config, retriever=spy_retriever, llm=spy_llm)
    report = await engine.run(dataset_dicts)

    # The mock LLM was called exactly once per item, with prompts derived from
    # each question and the item's ground truth forwarded for echoing.
    assert len(spy_llm.prompts) == 2
    assert "What is RAG?" in spy_llm.prompts[0]
    assert "What is a vector store?" in spy_llm.prompts[1]
    assert spy_llm.ground_truths == [SENTINEL_0, SENTINEL_1]

    # The mock retriever was called exactly once per item, with the question.
    assert spy_retriever.queries == ["What is RAG?", "What is a vector store?"]

    # And the mock output propagated end-to-end into the results.
    assert [r.answer for r in report.result.results] == [SENTINEL_0, SENTINEL_1]

    engine.shutdown()

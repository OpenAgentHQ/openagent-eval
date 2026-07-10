"""Tests for the hallucination metric (C4: score direction must not invert)."""

from __future__ import annotations

import sys
import types

import pytest

from openagent_eval.metrics.generation.hallucination import HallucinationDetection


class _FakeHallucinationMetric:
    """Stand-in for deepeval.metrics.HallucinationMetric.

    Mirrors DeepEval's contract: ``score`` is the degree of hallucination,
    0.0 = no hallucination, 1.0 = fully hallucinated (lower is better).
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold
        self.score = 0.0

    def measure(self, test_case: object) -> None:  # noqa: ARG002 - signature parity
        # Simulate DeepEval reporting a fully faithful answer as 0.0.
        self.score = 0.0


def _install_fake_deepeval() -> None:
    """Inject fake deepeval modules so the DeepEval branch can run offline."""
    fake_metrics = types.ModuleType("deepeval.metrics")
    fake_metrics.HallucinationMetric = _FakeHallucinationMetric
    fake_tc = types.ModuleType("deepeval.test_case")

    class _FakeLLMTestCase:
        def __init__(self, **kwargs: object) -> None:  # noqa: D107
            self.__dict__.update(kwargs)

    fake_tc.LLMTestCase = _FakeLLMTestCase
    fake_root = types.ModuleType("deepeval")
    fake_root.metrics = fake_metrics
    fake_root.test_case = fake_tc
    sys.modules.setdefault("deepeval", fake_root)
    sys.modules.setdefault("deepeval.metrics", fake_metrics)
    sys.modules.setdefault("deepeval.test_case", fake_tc)


@pytest.fixture
def fake_deepeval(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_deepeval()
    yield
    for mod in ("deepeval", "deepeval.metrics", "deepeval.test_case"):
        monkeypatch.undo()
        sys.modules.pop(mod, None)


def test_deepeval_path_does_not_invert_score(fake_deepeval: None) -> None:
    """C4: a faithful answer (DeepEval score 0.0) must report 0.0, not 1.0."""
    metric = HallucinationDetection()
    result = metric.evaluate(
        answer="Python is a programming language.",
        contexts=["Python is a programming language."],
    )
    assert result.score == 0.0
    assert result.metadata["method"] == "deepeval"


def test_simple_fallback_no_hallucination_is_zero() -> None:
    """The simple fallback must also report 0.0 when the answer is supported."""
    metric = HallucinationDetection()
    result = metric.evaluate(
        answer="Python is a programming language.",
        contexts=["Python is a programming language."],
    )
    assert result.score == 0.0


def test_simple_fallback_unsupported_words_score_above_zero() -> None:
    """Unsupported words should yield a positive hallucination score."""
    metric = HallucinationDetection()
    result = metric.evaluate(
        answer="The moon is made of green cheese.",
        contexts=["Python is a programming language."],
    )
    assert result.score > 0.0

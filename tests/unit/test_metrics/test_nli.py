"""Unit tests for NLI-based scoring module.

Tests NLIJudge, ClaimExtractor, EvidenceFinder, and LLMJudgeMetric.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from openagent_eval.metrics.nli import (
    Claim,
    ClaimExtractor,
    EvidenceFinder,
    EvidenceMatch,
    NLIJudge,
    NLIResult,
    NLILabel,
)
from openagent_eval.metrics.generation.llm_judge import (
    LLMJudgeMetric,
    FAITHFULNESS_CRITERIA,
    RELEVANCY_CRITERIA,
)


# ============================================================
# NLIResult Tests
# ============================================================


class TestNLIResult:
    """Tests for NLIResult dataclass."""

    def test_valid_result(self):
        result = NLIResult(
            label=NLILabel.ENTAILMENT,
            score=0.95,
            entailed_score=0.95,
        )
        assert result.label == NLILabel.ENTAILMENT
        assert result.score == 0.95
        assert result.entailed_score == 0.95

    def test_invalid_score_too_high(self):
        with pytest.raises(ValueError, match="Score must be between"):
            NLIResult(
                label=NLILabel.ENTAILMENT,
                score=1.5,
                entailed_score=0.9,
            )

    def test_invalid_score_too_low(self):
        with pytest.raises(ValueError, match="Score must be between"):
            NLIResult(
                label=NLILabel.ENTAILMENT,
                score=-0.1,
                entailed_score=0.9,
            )

    def test_invalid_entailed_score(self):
        with pytest.raises(ValueError, match="Entailed score must be between"):
            NLIResult(
                label=NLILabel.ENTAILMENT,
                score=0.9,
                entailed_score=1.5,
            )


# ============================================================
# Claim Tests
# ============================================================


class TestClaim:
    """Tests for Claim dataclass."""

    def test_valid_claim(self):
        claim = Claim(text="Python is open source", index=0)
        assert claim.text == "Python is open source"
        assert claim.index == 0

    def test_claim_immutable(self):
        claim = Claim(text="Test", index=0)
        with pytest.raises(AttributeError):
            claim.text = "Changed"  # type: ignore[misc]


# ============================================================
# ClaimExtractor Tests
# ============================================================


class TestClaimExtractor:
    """Tests for ClaimExtractor."""

    def setup_method(self):
        self.extractor = ClaimExtractor()

    def test_extract_empty_answer(self):
        claims = self.extractor.extract("")
        assert claims == []

    def test_extract_whitespace_only(self):
        claims = self.extractor.extract("   ")
        assert claims == []

    def test_extract_single_sentence(self):
        claims = self.extractor.extract("Python was created in 1991.")
        assert len(claims) >= 1
        assert "1991" in claims[0].text

    def test_extract_multiple_sentences(self):
        text = "Python was created in 1991. It is open source. It supports multiple paradigms."
        claims = self.extractor.extract(text)
        assert len(claims) >= 2

    def test_extract_compound_sentence(self):
        text = "Python is popular, and it is easy to learn."
        claims = self.extractor.extract(text)
        # Should split on ", and"
        assert len(claims) >= 1

    def test_extract_claims_have_indices(self):
        text = "First claim. Second claim. Third claim."
        claims = self.extractor.extract(text)
        for i, claim in enumerate(claims):
            assert claim.index == i

    def test_extract_with_context(self):
        answer = "Python is open source."
        contexts = ["Python is a programming language.", "Java is compiled."]
        paired = self.extractor.extract_with_context(answer, contexts)
        assert len(paired) >= 1
        assert paired[0][0].text  # Claim text not empty
        assert paired[0][1]  # Context not empty


# ============================================================
# EvidenceFinder Tests (with mocked NLI)
# ============================================================


class TestEvidenceFinder:
    """Tests for EvidenceFinder with mocked NLI judge."""

    def setup_method(self):
        self.mock_judge = MagicMock(spec=NLIJudge)
        self.finder = EvidenceFinder(judge=self.mock_judge)

    def test_find_evidence_empty_contexts(self):
        claim = Claim(text="Test claim", index=0)
        result = self.finder.find_evidence(claim, [])
        assert result is None

    def test_find_evidence_best_match(self):
        claim = Claim(text="Python is open source", index=0)
        contexts = [
            "Python is a compiled language.",
            "Python is open source and free.",
        ]

        # Mock NLI results: second context entails better
        self.mock_judge.evaluate.side_effect = [
            NLIResult(label=NLILabel.NEUTRAL, score=0.6, entailed_score=0.3),
            NLIResult(label=NLILabel.ENTAILMENT, score=0.9, entailed_score=0.9),
        ]

        result = self.finder.find_evidence(claim, contexts)
        assert result is not None
        assert result.evidence == contexts[1]
        assert result.nli_result.entailed_score == 0.9

    def test_score_faithfulness_all_supported(self):
        claims = [
            Claim(text="Claim 1", index=0),
            Claim(text="Claim 2", index=1),
        ]
        contexts = ["Context 1", "Context 2"]

        self.mock_judge.evaluate.return_value = NLIResult(
            label=NLILabel.ENTAILMENT, score=0.95, entailed_score=0.95
        )

        score, matches = self.finder.score_faithfulness(claims, contexts)
        assert score == 1.0
        assert len(matches) == 2

    def test_score_faithfulness_none_supported(self):
        claims = [
            Claim(text="Claim 1", index=0),
            Claim(text="Claim 2", index=1),
        ]
        contexts = ["Context 1"]

        self.mock_judge.evaluate.return_value = NLIResult(
            label=NLILabel.CONTRADICTION, score=0.9, entailed_score=0.05
        )

        score, matches = self.finder.score_faithfulness(claims, contexts, threshold=0.5)
        assert score == 0.0

    def test_score_faithfulness_empty_claims(self):
        score, matches = self.finder.score_faithfulness([], ["context"])
        assert score == 0.0
        assert matches == []


# ============================================================
# NLIJudge Tests (with mocked pipeline)
# ============================================================


class TestNLIJudge:
    """Tests for NLIJudge with mocked pipeline."""

    def setup_method(self):
        self.judge = NLIJudge(model_name="test-model")

    def test_empty_premise(self):
        result = self.judge.evaluate(premise="", hypothesis="test")
        assert result.label == NLILabel.NEUTRAL
        assert result.entailed_score == 0.0

    def test_empty_hypothesis(self):
        result = self.judge.evaluate(premise="test", hypothesis="")
        assert result.label == NLILabel.NEUTRAL
        assert result.entailed_score == 0.0

    def test_evaluate_entailment(self):
        mock_pipe = MagicMock()
        mock_pipe.return_value = [[
            {"label": "entailment", "score": 0.95},
            {"label": "neutral", "score": 0.03},
            {"label": "contradiction", "score": 0.02},
        ]]

        judge = NLIJudge()
        judge._pipeline = mock_pipe

        result = judge.evaluate(
            premise="The sky is blue.",
            hypothesis="The sky has a color."
        )
        assert result.label == NLILabel.ENTAILMENT
        assert result.entailed_score == 0.95

    def test_evaluate_contradiction(self):
        mock_pipe = MagicMock()
        mock_pipe.return_value = [[
            {"label": "entailment", "score": 0.05},
            {"label": "neutral", "score": 0.1},
            {"label": "contradiction", "score": 0.85},
        ]]

        judge = NLIJudge()
        judge._pipeline = mock_pipe

        result = judge.evaluate(
            premise="The sky is blue.",
            hypothesis="The sky is red."
        )
        assert result.label == NLILabel.CONTRADICTION
        assert result.score == 0.85

    def test_batch_evaluate(self):
        with patch.object(NLIJudge, 'evaluate') as mock_eval:
            mock_eval.return_value = NLIResult(
                label=NLILabel.ENTAILMENT, score=0.9, entailed_score=0.9
            )
            judge = NLIJudge()
            results = judge.batch_evaluate([
                ("premise1", "hyp1"),
                ("premise2", "hyp2"),
            ])
            assert len(results) == 2
            assert all(r.label == NLILabel.ENTAILMENT for r in results)


# ============================================================
# LLMJudgeMetric Tests (with mocked provider)
# ============================================================


class TestLLMJudgeMetric:
    """Tests for LLMJudgeMetric with mocked LLM provider."""

    def setup_method(self):
        self.mock_provider = MagicMock()
        self.mock_provider.name = "test_provider"
        self.mock_provider.generate = MagicMock(return_value="0.85")

    def test_judge_criteria_defaults(self):
        criteria = FAITHFULNESS_CRITERIA
        assert criteria.name == "faithfulness"
        assert criteria.passing_threshold == 0.7

    def test_llm_judge_metric_name(self):
        metric = LLMJudgeMetric(
            provider=self.mock_provider,
            criteria=RELEVANCY_CRITERIA,
        )
        assert metric.name == "llm_judge_relevancy"

    def test_llm_judge_missing_inputs(self):
        metric = LLMJudgeMetric(provider=self.mock_provider)
        result = metric.evaluate(premise="", hypothesis="test")
        assert result.score == 0.0
        assert "Missing" in result.reason

    def test_llm_judge_parse_score_decimal(self):
        metric = LLMJudgeMetric(provider=self.mock_provider)
        score = metric._parse_score("The score is 0.85")
        assert score == 0.85

    def test_llm_judge_parse_score_percentage(self):
        metric = LLMJudgeMetric(provider=self.mock_provider)
        score = metric._parse_score("85%")
        assert score == 0.85  # 85 / 100

    def test_llm_judge_parse_score_keyword_yes(self):
        metric = LLMJudgeMetric(provider=self.mock_provider)
        score = metric._parse_score("Yes, the answer is excellent")
        assert score == 1.0

    def test_llm_judge_parse_score_keyword_no(self):
        metric = LLMJudgeMetric(provider=self.mock_provider)
        score = metric._parse_score("No, not at all")
        assert score == 0.0

    def test_llm_judge_parse_score_neutral(self):
        metric = LLMJudgeMetric(provider=self.mock_provider)
        score = metric._parse_score("some random text")
        assert score == 0.5

    def test_llm_judge_evaluate_success(self):
        self.mock_provider.generate.return_value = "0.92"
        metric = LLMJudgeMetric(provider=self.mock_provider)
        result = metric.evaluate(premise="context", hypothesis="answer")
        assert result.score == 0.92
        assert result.metadata["method"] == "llm_judge"

    def test_llm_judge_evaluate_failure(self):
        self.mock_provider.generate.side_effect = Exception("API error")
        metric = LLMJudgeMetric(provider=self.mock_provider)
        result = metric.evaluate(premise="context", hypothesis="answer")
        assert result.score == 0.0
        assert "failed" in result.reason.lower()


# ============================================================
# MetricResult Integration Tests
# ============================================================


class TestMetricResultNLI:
    """Test that NLI-based metrics return proper MetricResult."""

    def test_nli_result_is_frozen(self):
        result = NLIResult(
            label=NLILabel.ENTAILMENT,
            score=0.9,
            entailed_score=0.9,
        )
        with pytest.raises(AttributeError):
            result.score = 0.5  # type: ignore[misc]

    def test_claim_is_frozen(self):
        claim = Claim(text="test", index=0)
        with pytest.raises(AttributeError):
            claim.text = "changed"  # type: ignore[misc]

    def test_evidence_match_is_frozen(self):
        match = EvidenceMatch(
            claim=Claim(text="test", index=0),
            evidence="context",
            nli_result=NLIResult(
                label=NLILabel.ENTAILMENT,
                score=0.9,
                entailed_score=0.9,
            ),
            all_scores=(),
        )
        with pytest.raises(AttributeError):
            match.evidence = "changed"  # type: ignore[misc]

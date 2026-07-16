"""Tests for contradiction detector."""

from __future__ import annotations

import pytest

from openagent_eval.corpus.contradiction import ContradictionDetector
from openagent_eval.corpus.models import CorpusDocument, IssueType


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response: str = "") -> None:
        self.response = response
        self.calls: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response


class TestContradictionDetector:
    """Tests for ContradictionDetector."""

    @pytest.fixture
    def detector_no_llm(self):
        """Create detector without LLM provider."""
        return ContradictionDetector(llm_provider=None)

    @pytest.fixture
    def mock_contradiction_response(self):
        """JSON response indicating contradiction."""
        return '{"contradicts": true, "confidence": 0.95, "topic": "API version", "explanation": "Doc A says v1, Doc B says v2"}'

    @pytest.fixture
    def mock_no_contradiction_response(self):
        """JSON response indicating no contradiction."""
        return '{"contradicts": false, "confidence": 0.1, "topic": "API version", "explanation": "Both discuss the same version"}'

    @pytest.mark.asyncio
    async def test_no_llm_returns_info_report(self, detector_no_llm):
        """Test that detector without LLM returns informational report."""
        docs = [
            CorpusDocument(doc_id="a.txt", content="Content A"),
            CorpusDocument(doc_id="b.txt", content="Content B"),
        ]

        report = await detector_no_llm.analyze(docs)

        assert len(report.issues) == 0
        assert report.metadata.get("requires_llm") is True

    @pytest.mark.asyncio
    async def test_detects_contradiction(self, mock_contradiction_response):
        """Test that contradictions are detected."""
        llm = MockLLMProvider(response=mock_contradiction_response)
        detector = ContradictionDetector(llm_provider=llm)

        docs = [
            CorpusDocument(
                doc_id="a.txt",
                content="The API version is 1.0 and supports basic features including authentication and rate limiting.",
            ),
            CorpusDocument(
                doc_id="b.txt",
                content="The API version is 2.0 and supports advanced features including batch processing and webhooks.",
            ),
        ]

        report = await detector.analyze(docs)

        assert len(report.issues) >= 1
        assert report.issues[0].issue_type == IssueType.CONTRADICTION
        assert "a.txt" in report.issues[0].document_ids
        assert "b.txt" in report.issues[0].document_ids

    @pytest.mark.asyncio
    async def test_no_contradiction(self, mock_no_contradiction_response):
        """Test when documents don't contradict."""
        llm = MockLLMProvider(response=mock_no_contradiction_response)
        detector = ContradictionDetector(llm_provider=llm)

        docs = [
            CorpusDocument(
                doc_id="a.txt",
                content="The API version is 1.0 and supports basic features including authentication and rate limiting.",
            ),
            CorpusDocument(
                doc_id="b.txt",
                content="The API version is 1.0 and supports advanced features including batch processing and webhooks.",
            ),
        ]

        report = await detector.analyze(docs)

        assert len(report.issues) == 0

    @pytest.mark.asyncio
    async def test_empty_corpus(self, detector_no_llm):
        """Test empty corpus raises error."""
        with pytest.raises(ValueError, match="empty"):
            await detector_no_llm.analyze([])

    @pytest.mark.asyncio
    async def test_single_document_no_pairs(self, detector_no_llm):
        """Test single document produces no pairs."""
        docs = [CorpusDocument(doc_id="a.txt", content="Unique content here")]

        report = await detector_no_llm.analyze(docs)
        assert len(report.issues) == 0

    @pytest.mark.asyncio
    async def test_pairs_generation_heuristic(self, detector_no_llm):
        """Test that pairs are generated based on shared words."""
        docs = [
            CorpusDocument(
                doc_id="related.txt",
                content="Python programming language is great for machine learning and data science applications",
            ),
            CorpusDocument(
                doc_id="related2.txt",
                content="Python programming language is used for machine learning and data science projects",
            ),
            CorpusDocument(
                doc_id="unrelated.txt",
                content="The weather today is sunny with clear skies and warm temperatures",
            ),
        ]

        pairs = detector_no_llm._generate_pairs(docs)
        # The two Python docs should be paired
        assert len(pairs) >= 1

    @pytest.mark.asyncio
    async def test_summary_generation(self, mock_contradiction_response):
        """Test summary text generation."""
        llm = MockLLMProvider(response=mock_contradiction_response)
        detector = ContradictionDetector(llm_provider=llm)

        docs = [
            CorpusDocument(
                doc_id="a.txt",
                content="The API uses REST architecture for all endpoints including authentication and data processing",
            ),
            CorpusDocument(
                doc_id="b.txt",
                content="The API uses GraphQL architecture for all endpoints including authentication and data processing",
            ),
        ]

        report = await detector.analyze(docs)
        assert "contradiction" in report.summary.lower() or "no contradictions" in report.summary.lower()

    @pytest.mark.asyncio
    async def test_health_score_computation(self, detector_no_llm):
        """Test health score computation."""
        # No issues = perfect score
        score = detector_no_llm._compute_health_score(10, 0)
        assert score == 1.0

        # Single doc = perfect score
        score = detector_no_llm._compute_health_score(1, 0)
        assert score == 1.0

        # Some issues = reduced score
        score = detector_no_llm._compute_health_score(10, 5)
        assert score < 1.0

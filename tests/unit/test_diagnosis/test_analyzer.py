"""Tests for the DiagnosisAnalyzer orchestrator."""

from __future__ import annotations

from openagent_eval.diagnosis.analyzer import DiagnosisAnalyzer
from openagent_eval.diagnosis.models import DiagnosisReport


class TestDiagnosisAnalyzer:
    """Tests for DiagnosisAnalyzer."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = DiagnosisAnalyzer()

    def test_empty_results(self) -> None:
        """Empty results should produce a valid but empty report."""
        report = self.analyzer.analyze([])
        assert isinstance(report, DiagnosisReport)
        assert report.total_items == 0
        assert report.overall_health == 1.0
        assert report.blame_summary == {}
        assert report.failure_summary == {}
        assert report.failures == []

    def test_healthy_items(self) -> None:
        """Items with good scores should produce healthy report."""
        results = [
            {
                "question": f"Question {i}?",
                "answer": "A good answer.",
                "contexts": ["Context 1", "Context 2"],
                "metrics": {
                    "context_precision": 0.9,
                    "context_recall": 0.85,
                    "faithfulness": 0.92,
                    "answer_relevancy": 0.88,
                },
                "metadata": {"latency_ms": 100.0},
            }
            for i in range(5)
        ]
        report = self.analyzer.analyze(results)
        assert report.total_items == 5
        assert report.overall_health == 1.0  # All healthy
        assert report.blame_summary == {}

    def test_retrieval_failure_blamed(self) -> None:
        """Items with empty retrieval should blame retrieval."""
        results = [
            {
                "question": "What is AI?",
                "answer": "",  # No answer because no context
                "contexts": [],  # Empty retrieval
                "metrics": {},
                "metadata": {},
            }
        ]
        report = self.analyzer.analyze(results)
        assert report.blame_summary.get("retrieval", 0) == 1
        assert report.overall_health == 0.0

    def test_generation_failure_blamed(self) -> None:
        """Items with low faithfulness should blame generation."""
        results = [
            {
                "question": "What is AI?",
                "answer": "Some answer that is wrong.",
                "contexts": ["Good context."],
                "metrics": {
                    "context_precision": 0.9,
                    "faithfulness": 0.2,  # Very low
                },
                "metadata": {},
            }
        ]
        report = self.analyzer.analyze(results)
        assert report.blame_summary.get("generation", 0) == 1

    def test_mixed_results(self) -> None:
        """Mixed results should produce correct blame distribution."""
        results = [
            # Healthy item
            {
                "question": "Good question?",
                "answer": "Good answer.",
                "contexts": ["Context 1", "Context 2"],
                "metrics": {
                    "context_precision": 0.9,
                    "faithfulness": 0.9,
                },
                "metadata": {},
            },
            # Retrieval failure
            {
                "question": "Bad retrieval?",
                "answer": "",
                "contexts": [],
                "metrics": {},
                "metadata": {},
            },
            # Generation failure
            {
                "question": "Bad generation?",
                "answer": "Wrong answer.",
                "contexts": ["Good context."],
                "metrics": {
                    "context_precision": 0.9,
                    "faithfulness": 0.1,  # Very low
                },
                "metadata": {},
            },
        ]
        report = self.analyzer.analyze(results)
        assert report.total_items == 3
        assert report.blame_summary.get("retrieval", 0) == 1
        assert report.blame_summary.get("generation", 0) == 1
        assert report.overall_health == 1 / 3  # Only 1 healthy out of 3

    def test_recommendations_generated(self) -> None:
        """Report should include recommendations when failures exist."""
        results = [
            {
                "question": "What is AI?",
                "answer": "",
                "contexts": [],
                "metrics": {},
                "metadata": {},
            }
        ]
        report = self.analyzer.analyze(results)
        assert len(report.recommendations) > 0
        # Should contain retrieval-specific recommendation
        assert any("retrieval" in r.lower() or "RETRIEVAL" in r for r in report.recommendations)

    def test_no_recommendations_when_healthy(self) -> None:
        """Healthy report should have generic recommendation."""
        results = [
            {
                "question": "Explain Python programming",
                "answer": "Python is a popular programming language for many applications.",
                "contexts": [
                    "Python is a high-level programming language.",
                    "Python is used for web development and data science.",
                ],
                "metrics": {"context_precision": 0.9, "faithfulness": 0.9},
                "metadata": {},
            }
        ]
        report = self.analyzer.analyze(results)
        assert len(report.recommendations) == 1
        assert "healthy" in report.recommendations[0].lower()

    def test_max_recommendations_limit(self) -> None:
        """Recommendations should respect max_recommendations limit."""
        analyzer = DiagnosisAnalyzer(max_recommendations=2)
        results = [
            {
                "question": "What is AI?",
                "answer": "",
                "contexts": [],
                "metrics": {},
                "metadata": {},
            }
        ]
        report = analyzer.analyze(results)
        assert len(report.recommendations) <= 2

    def test_custom_blame_threshold(self) -> None:
        """Custom threshold should filter low-confidence failures."""
        # With high threshold, borderline failures should be excluded
        high_threshold_analyzer = DiagnosisAnalyzer(blame_threshold=0.95)
        results = [
            {
                "question": "Question?",
                "answer": "Answer.",
                "contexts": ["Context."],
                "metrics": {
                    "context_precision": 0.35,  # Just above LOW_CONTEXT_PRECISION (0.3)
                    "faithfulness": 0.9,
                },
                "metadata": {},
            }
        ]
        report = high_threshold_analyzer.analyze(results)
        # With 0.95 threshold, the 0.8 confidence failure should be excluded
        assert len(report.failures) == 0

    def test_to_dict_is_json_serializable(self) -> None:
        """Report.to_dict() should produce JSON-serializable output."""
        import json

        results = [
            {
                "question": "Test?",
                "answer": "Answer.",
                "contexts": ["Context"],
                "metrics": {"context_precision": 0.9, "faithfulness": 0.9},
                "metadata": {},
            },
            {
                "question": "Bad?",
                "answer": "",
                "contexts": [],
                "metrics": {},
                "metadata": {},
            },
        ]
        report = self.analyzer.analyze(results)
        d = report.to_dict()
        # Should not raise
        json.dumps(d)

    def test_extract_scores_from_pipeline_format(self) -> None:
        """Should handle Pipeline-style evaluation result dicts."""
        results = [
            {
                "question": "What is Python?",
                "answer": "Python is a popular programming language used for many applications.",
                "contexts": [
                    "Python is a high-level programming language.",
                    "Python was created by Guido van Rossum.",
                ],
                "metrics": {
                    "context_precision": 0.85,
                    "context_recall": 0.7,
                    "mrr": 0.9,
                    "faithfulness": 0.95,
                    "answer_relevancy": 0.88,
                },
                "metadata": {
                    "latency_ms": 150.0,
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                },
            }
        ]
        report = self.analyzer.analyze(results)
        assert report.total_items == 1
        # Should be healthy
        assert report.overall_health == 1.0

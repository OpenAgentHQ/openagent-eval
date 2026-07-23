"""Integration tests for the diagnosis pipeline.

Tests the full flow from evaluation results through blame attribution
and chunking analysis to a final DiagnosisReport.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from openagent_eval.diagnosis import DiagnosisAnalyzer
from openagent_eval.diagnosis.blame import BlameAttribution
from openagent_eval.diagnosis.chunking import ChunkingQualityAnalyzer
from openagent_eval.diagnosis.models import (
    BlameTarget,
    ComponentScores,
)


class TestDiagnosisPipeline:
    """End-to-end tests for the diagnosis pipeline."""

    def test_full_pipeline_with_mixed_results(self) -> None:
        """Full pipeline should correctly diagnose mixed healthy/failing items."""
        analyzer = DiagnosisAnalyzer()

        results = [
            # Healthy item
            {
                "question": "What is Python?",
                "answer": "Python is a programming language.",
                "contexts": [
                    "Python is a high-level programming language.",
                    "Python was created by Guido van Rossum.",
                ],
                "metrics": {
                    "context_precision": 0.92,
                    "context_recall": 0.88,
                    "faithfulness": 0.95,
                    "answer_relevancy": 0.90,
                },
                "metadata": {"latency_ms": 120.0},
            },
            # Retrieval failure - empty retrieval
            {
                "question": "What is quantum entanglement?",
                "answer": "",
                "contexts": [],
                "metrics": {},
                "metadata": {"latency_ms": 50.0},
            },
            # Generation failure - low faithfulness
            {
                "question": "Explain machine learning.",
                "answer": "Machine learning is about aliens learning to code.",
                "contexts": [
                    "Machine learning is a subset of AI that enables systems to learn from data.",
                    "Machine learning algorithms build models based on training data.",
                ],
                "metrics": {
                    "context_precision": 0.85,
                    "faithfulness": 0.15,
                    "answer_relevancy": 0.20,
                },
                "metadata": {"latency_ms": 200.0},
            },
            # Another healthy item
            {
                "question": "What is Docker?",
                "answer": "Docker is a containerization platform for developers.",
                "contexts": [
                    "Docker enables containerized application deployment.",
                    "Docker packages applications with their dependencies.",
                ],
                "metrics": {
                    "context_precision": 0.88,
                    "faithfulness": 0.92,
                },
                "metadata": {"latency_ms": 95.0},
            },
        ]

        report = analyzer.analyze(results)

        # Verify basic counts
        assert report.total_items == 4
        assert len(report.failures) >= 2  # At least the retrieval + generation failures
        assert report.blame_summary.get("retrieval", 0) >= 1
        assert report.blame_summary.get("generation", 0) >= 1

        # Verify healthy items count (2 healthy out of 4)
        assert report.overall_health >= 0.4  # At least 2 healthy items

        # Verify recommendations exist
        assert len(report.recommendations) > 0

        # Verify report is serializable
        d = report.to_dict()
        serialized = json.dumps(d)
        assert len(serialized) > 0

    def test_pipeline_with_chunking_issues(self) -> None:
        """Pipeline should detect chunking issues."""
        analyzer = DiagnosisAnalyzer()

        results = [
            {
                "question": "What is AI?",
                "answer": "AI is artificial intelligence.",
                "contexts": [
                    "The",  # Very short context
                    "A" * 2000,  # Very long context
                ],
                "metrics": {
                    "context_precision": 0.7,
                    "faithfulness": 0.85,
                },
                "metadata": {},
            }
        ]

        report = analyzer.analyze(results)

        # Should detect chunking issues (uneven sizes)
        assert len(report.chunking_issues) > 0

    def test_pipeline_all_healthy_produces_clean_report(self) -> None:
        """All healthy items should produce a clean report."""
        analyzer = DiagnosisAnalyzer()

        results = [
            {
                "question": f"Explain topic number {i} in detail please",
                "answer": f"Topic {i} is an important concept with many applications.",
                "contexts": [
                    f"Topic {i} covers many aspects of modern technology.",
                    f"Topic {i} is widely used in industry and research.",
                ],
                "metrics": {
                    "context_precision": 0.9,
                    "faithfulness": 0.95,
                },
                "metadata": {},
            }
            for i in range(10)
        ]

        report = analyzer.analyze(results)
        assert report.total_items == 10
        assert report.overall_health == 1.0
        assert len(report.failures) == 0
        assert len(report.recommendations) == 1  # Only the "healthy" message

    def test_blame_attribution_standalone(self) -> None:
        """BlameAttribution should work as a standalone component."""
        blamer = BlameAttribution()

        # Test healthy
        healthy = ComponentScores(
            question="Q",
            retrieval_scores={"context_precision": 0.9},
            generation_scores={"faithfulness": 0.9},
            context_count=3,
            context_lengths=[100, 100, 100],
            answer_length=200,
        )
        result = blamer.analyze(healthy)
        assert result.target == BlameTarget.UNKNOWN

        # Test empty retrieval
        empty = ComponentScores(
            question="Q",
            context_count=0,
        )
        result = blamer.analyze(empty)
        assert result.target == BlameTarget.RETRIEVAL

    def test_chunking_analyzer_standalone(self) -> None:
        """ChunkingQualityAnalyzer should work as a standalone component."""
        analyzer = ChunkingQualityAnalyzer()

        # Normal contexts
        issues = analyzer.analyze(
            "What is Python?",
            ["Python is a language.", "Python is used for AI."],
        )
        assert isinstance(issues, list)

        # Overlapping contexts
        ctx = "The quick brown fox jumps over the lazy dog."
        issues = analyzer.analyze("Tell me about foxes.", [ctx, ctx])
        overlap = [i for i in issues if i.issue_type == "overlapping_chunks"]
        assert len(overlap) > 0

    def test_report_serialization_roundtrip(self) -> None:
        """DiagnosisReport should survive JSON serialization roundtrip."""
        analyzer = DiagnosisAnalyzer()

        results = [
            {
                "question": "What?",
                "answer": "Answer.",
                "contexts": ["Context."],
                "metrics": {"context_precision": 0.9, "faithfulness": 0.9},
                "metadata": {},
            }
        ]

        report = analyzer.analyze(results)
        d = report.to_dict()
        serialized = json.dumps(d)
        deserialized = json.loads(serialized)

        assert deserialized["total_items"] == report.total_items
        assert deserialized["overall_health"] == report.overall_health
        assert len(deserialized["recommendations"]) == len(report.recommendations)


    def test_chunking_receives_validated_contexts(self) -> None:
        """Chunking analyzer should receive only validated string contexts."""

        analyzer = DiagnosisAnalyzer()

        captured: dict[str, object] = {}

        def fake_chunking(
            question: str,
            contexts: list[str],
            metadata: dict[str, float] | None,
        ) -> list:
            captured["question"] = question
            captured["contexts"] = contexts
            captured["metadata"] = metadata
            return []

        analyzer._chunking_analyzer.analyze = fake_chunking  # type: ignore[method-assign]

        results = [
            {
                "question": "What is Python?",
                "answer": "Python is a programming language.",
                "contexts": [
                    "Python is a programming language.",
                    {"content": "invalid"},
                    123,
                    None,
                ],
                "metrics": {},
                "metadata": {},
            }
        ]

        analyzer.analyze(results)

        assert captured["question"] == "What is Python?"
        assert captured["metadata"] == {}
        assert captured["contexts"] == [
            "Python is a programming language."
        ]
        assert len(captured["contexts"]) == 1



class TestDiagnosisReportFileOutput:
    """Test saving diagnosis report to file."""

    def test_save_report_to_json(self, tmp_path: Path) -> None:
        """DiagnosisReport should be saveable to JSON file."""
        analyzer = DiagnosisAnalyzer()

        results = [
            {
                "question": "Explain Python programming in detail",
                "answer": "Python is a popular programming language used for many applications.",
                "contexts": [
                    "Python is a high-level programming language.",
                    "Python is used for web development and data science.",
                ],
                "metrics": {"context_precision": 0.9, "faithfulness": 0.9},
                "metadata": {},
            }
        ]

        report = analyzer.analyze(results)
        output_file = tmp_path / "diagnosis_report.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)

        assert output_file.exists()

        # Read back and verify
        with open(output_file, encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["total_items"] == 1
        assert loaded["overall_health"] == 1.0


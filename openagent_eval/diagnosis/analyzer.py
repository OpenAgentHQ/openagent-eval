"""Diagnosis analyzer — the main orchestrator for component diagnosis.

Runs blame attribution and chunking quality analysis on evaluation results,
producing a DiagnosisReport with actionable recommendations.
"""

from __future__ import annotations

from openagent_eval.diagnosis.blame import BlameAttribution
from openagent_eval.diagnosis.chunking import ChunkingQualityAnalyzer
from openagent_eval.diagnosis.models import (
    BlameResult,
    BlameTarget,
    ChunkingIssue,
    ComponentScores,
    DiagnosisReport,
    FailureInstance,
)

# ---------------------------------------------------------------------------
# Recommendation templates
# ---------------------------------------------------------------------------

_RECOMMENDATIONS: dict[BlameTarget, list[str]] = {
    BlameTarget.RETRIEVAL: [
        "Check if the retriever is using the correct embedding model.",
        "Verify that the vector store contains the relevant documents.",
        "Consider increasing the retrieval k value.",
        "Review chunking strategy to ensure documents are split correctly.",
        "Check for index staleness — rebuild if documents have changed.",
    ],
    BlameTarget.GENERATION: [
        "Review the prompt template for clarity and completeness.",
        "Consider using a more capable LLM model.",
        "Check if the prompt includes enough context from retrieved documents.",
        "Validate that the LLM is not hallucinating by checking faithfulness.",
        "Consider adding explicit instructions to only use provided context.",
    ],
    BlameTarget.CHUNKING: [
        "Review the chunking strategy (fixed-size vs semantic).",
        "Ensure chunk boundaries do not split important information.",
        "Consider using overlapping chunks to preserve context.",
        "Check if metadata is preserved across chunks.",
        "Test different chunk sizes to find the optimal balance.",
    ],
    BlameTarget.DATASET: [
        "Validate the dataset format and required fields.",
        "Check that ground truth answers are accurate.",
        "Review dataset for class imbalance or missing entries.",
    ],
    BlameTarget.UNKNOWN: [
        "Run the evaluation with verbose output for more details.",
        "Check individual metric scores for anomalies.",
        "Review the full evaluation report for patterns.",
    ],
}


class DiagnosisAnalyzer:
    """Orchestrates blame attribution and chunking analysis.

    Usage::

        analyzer = DiagnosisAnalyzer()
        report = analyzer.analyze(evaluation_results)
        print(report.blame_summary)
        print(report.recommendations)
    """

    def __init__(
        self,
        blame_threshold: float = 0.3,
        max_recommendations: int = 5,
    ) -> None:
        """Initialize the diagnosis analyzer.

        Args:
            blame_threshold: Minimum confidence to include a failure in the report.
            max_recommendations: Maximum number of recommendations to generate.
        """
        self._blamer = BlameAttribution()
        self._chunking_analyzer = ChunkingQualityAnalyzer()
        self._blame_threshold = blame_threshold
        self._max_recommendations = max_recommendations

    def analyze(
        self,
        results: list[dict[str, object]],
    ) -> DiagnosisReport:
        """Analyze evaluation results and produce a diagnosis report.

        Args:
            results: List of evaluation result dicts. Each dict should contain
                keys: question, answer, contexts, metrics, metadata.
                This matches the format produced by ``Pipeline._evaluate_item``.

        Returns:
            DiagnosisReport with blame summary, failures, and recommendations.
        """
        all_failures: list[FailureInstance] = []
        all_chunking_issues: list[ChunkingIssue] = []
        blame_counts: dict[str, int] = {}
        failure_counts: dict[str, int] = {}
        healthy_count = 0

        for item in results:
            scores = self._extract_scores(item)
            contexts = self._extract_validated_contexts(item)
            question = scores.question

            # Run blame attribution
            blame_result: BlameResult = self._blamer.analyze(scores)

            # Collect failures above threshold
            for failure in blame_result.failure_modes:
                if failure.confidence >= self._blame_threshold:
                    all_failures.append(failure)
                    mode_key = failure.mode.value
                    failure_counts[mode_key] = failure_counts.get(mode_key, 0) + 1
                    blame_key = failure.blame.value
                    blame_counts[blame_key] = blame_counts.get(blame_key, 0) + 1

            metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                metadata = None

            # Run chunking analysis
            if scores.context_count > 0:
                chunking_issues = self._chunking_analyzer.analyze(
                        question,
                        contexts,
                        metadata,
                )
                all_chunking_issues.extend(chunking_issues)

            # Check if item is healthy
            if blame_result.target == BlameTarget.NONE:
                healthy_count += 1

        # Build recommendations
        recommendations = self._build_recommendations(blame_counts, failure_counts)

        overall_health = (
            1.0
            if not results
            else healthy_count / len(results)
        )

        return DiagnosisReport(
            total_items=len(results),
            blame_summary=blame_counts,
            failure_summary=failure_counts,
            failures=all_failures,
            chunking_issues=all_chunking_issues,
            recommendations=recommendations,
            overall_health=overall_health,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_scores(self, item: dict[str, object]) -> ComponentScores:
        """Extract ComponentScores from an evaluation result dict."""
        question = str(item.get("question", ""))
        metrics = item.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}
        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        # Separate retrieval vs generation metrics
        retrieval_keys = {
            "context_precision",
            "context_recall",
            "recall_at_k",
            "precision_at_k",
            "mrr",
            "ndcg",
            "hit_rate",
        }

        retrieval_scores: dict[str, float] = {}
        generation_scores: dict[str, float] = {}

        for key, value in metrics.items():
            try:
                val = float(value)
            except (TypeError, ValueError):
                continue
            if key in retrieval_keys:
                retrieval_scores[key] = val
            else:
                generation_scores[key] = val

        raw_contexts = item.get("contexts", []) or []

        if not isinstance(raw_contexts, list):
            contexts: list[str] = []
        else:
            contexts = [
                context
                for context in raw_contexts
                if isinstance(context, str)
            ]

        return ComponentScores(
            question=question,
            retrieval_scores=retrieval_scores,
            generation_scores=generation_scores,
            context_count=len(contexts),
            context_lengths=[len(c) for c in contexts],
            answer_length=len(str(item.get("answer", ""))),
            latency_ms=metadata.get("latency_ms"),
        )


    def _extract_validated_contexts(
        self,
        item: dict[str, object],
    ) -> list[str]:
        """Extract validated context strings from an evaluation item."""

        raw_contexts = item.get("contexts", []) or []

        if not isinstance(raw_contexts, list):
            return []

        return [
            context
            for context in raw_contexts
            if isinstance(context, str)
        ]

    def _build_recommendations(
        self,
        blame_counts: dict[str, int],
        failure_counts: dict[str, int],
    ) -> list[str]:
        """Generate actionable recommendations based on blame distribution."""
        if not blame_counts:
            return ["No significant failures detected. System appears healthy."]

        recommendations: list[str] = []

        # Sort blame targets by frequency
        sorted_blame = sorted(blame_counts.items(), key=lambda x: x[1], reverse=True)

        for blame_str, count in sorted_blame:
            try:
                target = BlameTarget(blame_str)
            except ValueError:
                continue

            target_recs = _RECOMMENDATIONS.get(target, [])
            for rec in target_recs:
                if len(recommendations) >= self._max_recommendations:
                    break
                prefixed = f"[{blame_str.upper()}] ({count} failures) {rec}"
                recommendations.append(prefixed)

            if len(recommendations) >= self._max_recommendations:
                break

        return recommendations

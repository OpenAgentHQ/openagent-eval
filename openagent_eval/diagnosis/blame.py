"""Blame attribution for failed RAG evaluations.

Analyzes retrieval scores, generation scores, and context quality to determine
which component (retrieval, generation, or chunking) caused a failure.

Decision rules are derived from D019 (Blame Attribution) and production
research findings (90% of failures are retrieval problems).
"""

from __future__ import annotations

from openagent_eval.diagnosis.models import (
    BlameResult,
    BlameTarget,
    ComponentScores,
    FailureInstance,
    FailureMode,
)

# ---------------------------------------------------------------------------
# Thresholds (tunable)
# ---------------------------------------------------------------------------

# Retrieval thresholds
EMPTY_RETRIEVAL_THRESHOLD = 0  # contexts returned
LOW_CONTEXT_PRECISION = 0.3
LOW_CONTEXT_RECALL = 0.3

# Generation thresholds
LOW_FAITHFULNESS = 0.4
LOW_RELEVANCY = 0.4
ANSWER_TOO_SHORT = 10  # characters

# Chunking thresholds
SINGLE_CONTEXT_THRESHOLD = 1  # if only 1 context, chunking may be the issue
CONTEXT_LENGTH_VARIANCE_RATIO = 5.0  # max/min ratio indicating uneven chunks


class BlameAttribution:
    """Attribute blame for a single evaluation item.

    Usage::

        blamer = BlameAttribution()
        result = blamer.analyze(component_scores)
        print(result.target, result.confidence, result.reason)
    """

    def analyze(self, scores: ComponentScores) -> BlameResult:
        """Analyze component scores and return blame attribution.

        Args:
            scores: Aggregated metric scores for a single evaluation item.

        Returns:
            BlameResult with the blamed component, confidence, and failure details.
        """
        failures: list[FailureInstance] = []
        question = scores.question

        # --- Retrieval analysis ---
        retrieval_failures = self._analyze_retrieval(scores, question)
        failures.extend(retrieval_failures)

        # --- Generation analysis ---
        generation_failures = self._analyze_generation(scores, question)
        failures.extend(generation_failures)

        # --- Chunking analysis ---
        chunking_failures = self._analyze_chunking(scores, question)
        failures.extend(chunking_failures)

        # --- Determine primary blame ---
        return self._determine_blame(scores, failures, question)

    # ------------------------------------------------------------------
    # Private analysis helpers
    # ------------------------------------------------------------------

    def _analyze_retrieval(
        self, scores: ComponentScores, question: str
    ) -> list[FailureInstance]:
        """Check for retrieval-related failures."""
        failures: list[FailureInstance] = []
        ctx_scores = scores.retrieval_scores

        # Empty retrieval
        if scores.context_count == 0:
            failures.append(
                FailureInstance(
                    mode=FailureMode.EMPTY_RETRIEVAL,
                    blame=BlameTarget.RETRIEVAL,
                    confidence=0.95,
                    reason="No contexts were retrieved for this question.",
                    question=question,
                    evidence=ctx_scores,
                )
            )

        # Low context precision
        precision = ctx_scores.get("context_precision", 1.0)
        if precision < LOW_CONTEXT_PRECISION and scores.context_count > 0:
            failures.append(
                FailureInstance(
                    mode=FailureMode.LOW_CONTEXT_RELEVANCE,
                    blame=BlameTarget.RETRIEVAL,
                    confidence=0.8,
                    reason=f"Context precision is low ({precision:.2f}), "
                    f"indicating irrelevant documents were retrieved.",
                    question=question,
                    evidence=ctx_scores,
                )
            )

        # Low context recall
        recall = ctx_scores.get("context_recall", 1.0)
        if recall < LOW_CONTEXT_RECALL and scores.context_count > 0:
            failures.append(
                FailureInstance(
                    mode=FailureMode.MISSING_CONTEXT,
                    blame=BlameTarget.RETRIEVAL,
                    confidence=0.75,
                    reason=f"Context recall is low ({recall:.2f}), "
                    f"indicating relevant documents were missed.",
                    question=question,
                    evidence=ctx_scores,
                )
            )

        return failures

    def _analyze_generation(
        self, scores: ComponentScores, question: str
    ) -> list[FailureInstance]:
        """Check for generation-related failures."""
        failures: list[FailureInstance] = []
        gen_scores = scores.generation_scores

        # Empty or very short answer with non-empty contexts
        if scores.answer_length < ANSWER_TOO_SHORT and scores.context_count > 0:
            failures.append(
                FailureInstance(
                    mode=FailureMode.OFF_TOPIC_ANSWER,
                    blame=BlameTarget.GENERATION,
                    confidence=0.7,
                    reason="Generated answer is empty or very short despite "
                    "having retrieved contexts.",
                    question=question,
                    evidence=gen_scores,
                )
            )

        # Low faithfulness
        faithfulness = gen_scores.get("faithfulness", 1.0)
        if faithfulness < LOW_FAITHFULNESS and scores.answer_length >= ANSWER_TOO_SHORT:
            failures.append(
                FailureInstance(
                    mode=FailureMode.HALLUCINATION,
                    blame=BlameTarget.GENERATION,
                    confidence=0.85,
                    reason=f"Faithfulness is low ({faithfulness:.2f}), "
                    f"suggesting the answer contains unsupported claims.",
                    question=question,
                    evidence=gen_scores,
                )
            )

        # Low relevancy
        relevancy = gen_scores.get("answer_relevancy", 1.0)
        if relevancy < LOW_RELEVANCY and scores.answer_length >= ANSWER_TOO_SHORT:
            failures.append(
                FailureInstance(
                    mode=FailureMode.OFF_TOPIC_ANSWER,
                    blame=BlameTarget.GENERATION,
                    confidence=0.75,
                    reason=f"Answer relevancy is low ({relevancy:.2f}), "
                    f"suggesting the answer does not address the question.",
                    question=question,
                    evidence=gen_scores,
                )
            )

        return failures

    def _analyze_chunking(
        self, scores: ComponentScores, question: str
    ) -> list[FailureInstance]:
        """Check for chunking-related failures."""
        failures: list[FailureInstance] = []

        if scores.context_count == 0:
            return failures

        # Highly uneven context lengths — possible chunking inconsistency
        if len(scores.context_lengths) >= 2:
            lengths = scores.context_lengths
            min_len = min(lengths)
            max_len = max(lengths)
            if min_len > 0 and (max_len / min_len) > CONTEXT_LENGTH_VARIANCE_RATIO:
                failures.append(
                    FailureInstance(
                        mode=FailureMode.CHUNKING_SPLIT_INFO_LOST,
                        blame=BlameTarget.CHUNKING,
                        confidence=0.6,
                        reason=f"Context lengths are highly uneven "
                        f"(min={min_len}, max={max_len}), "
                        f"suggesting inconsistent chunking strategy.",
                        question=question,
                        evidence={
                            "min_length": float(min_len),
                            "max_length": float(max_len),
                            "ratio": float(max_len / min_len),
                        },
                    )
                )

        return failures

    def _determine_blame(
        self,
        scores: ComponentScores,
        failures: list[FailureInstance],
        question: str,
    ) -> BlameResult:
        """Determine the primary blame target from all detected failures."""
        if not failures:
            return BlameResult(
                target=BlameTarget.NONE,
                confidence=1.0,
                reason="No failures detected.",
                failure_modes=[],
            )

        # Count blame targets
        blame_counts: dict[BlameTarget, int] = {}
        blame_confidence: dict[BlameTarget, list[float]] = {}
        for f in failures:
            blame_counts[f.blame] = blame_counts.get(f.blame, 0) + 1
            blame_confidence.setdefault(f.blame, []).append(f.confidence)

        # Weighted scoring: count * average_confidence
        blame_scores: dict[BlameTarget, float] = {}
        for target, count in blame_counts.items():
            avg_conf = sum(blame_confidence[target]) / len(blame_confidence[target])
            blame_scores[target] = count * avg_conf

        # Primary blame = highest weighted score
        primary_target = max(blame_scores, key=lambda t: blame_scores[t])
        primary_confidence = max(blame_confidence[primary_target])

        # Build reason
        primary_failures = [f for f in failures if f.blame == primary_target]
        reasons = [f.reason for f in primary_failures]
        combined_reason = "; ".join(reasons[:3])  # Top 3 reasons

        return BlameResult(
            target=primary_target,
            confidence=primary_confidence,
            reason=combined_reason,
            failure_modes=failures,
        )

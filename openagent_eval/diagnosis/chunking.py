"""Chunking quality analyzer.

Detects issues with how documents are split into chunks, including:
- Information split across chunks (related content in different chunks)
- Overlapping chunks (duplicate content in multiple chunks)
- Inconsistent chunk sizes
- Context gaps (missing information between chunks)
"""

from __future__ import annotations

import re
from openagent_eval.diagnosis.models import ChunkingIssue


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

OVERLAP_SIMILARITY_THRESHOLD = 0.8  # Jaccard similarity for overlap detection
MIN_CHUNK_LENGTH = 50  # minimum expected chunk length in characters
MAX_CHUNK_LENGTH = 5000  # maximum expected chunk length in characters
INCONSISTENCY_RATIO = 4.0  # max/min length ratio


class ChunkingQualityAnalyzer:
    """Analyze chunking quality from retrieved contexts.

    Usage::

        analyzer = ChunkingQualityAnalyzer()
        issues = analyzer.analyze(question, contexts)
        for issue in issues:
            print(issue.issue_type, issue.description)
    """

    def analyze(
        self,
        question: str,
        contexts: list[str],
        metadata: dict[str, float] | None = None,
    ) -> list[ChunkingIssue]:
        """Analyze chunking quality for a set of retrieved contexts.

        Args:
            question: The question that triggered retrieval.
            contexts: List of retrieved context strings.
            metadata: Optional metric scores for additional analysis.

        Returns:
            List of detected chunking issues.
        """
        issues: list[ChunkingIssue] = []

        if not contexts:
            return issues

        issues.extend(self._check_overlap(question, contexts))
        issues.extend(self._check_size_consistency(question, contexts))
        issues.extend(self._check_empty_chunks(question, contexts))
        issues.extend(self._check_content_gaps(question, contexts))

        return issues

    def _check_overlap(
        self, question: str, contexts: list[str]
    ) -> list[ChunkingIssue]:
        """Detect overlapping chunks using Jaccard similarity."""
        issues: list[ChunkingIssue] = []

        for i in range(len(contexts)):
            for j in range(i + 1, len(contexts)):
                similarity = self._jaccard_similarity(contexts[i], contexts[j])
                if similarity > OVERLAP_SIMILARITY_THRESHOLD:
                    issues.append(
                        ChunkingIssue(
                            question=question,
                            issue_type="overlapping_chunks",
                            description=(
                                f"Contexts {i + 1} and {j + 1} have high "
                                f"overlap (similarity={similarity:.2f}), "
                                f"suggesting duplicate chunking."
                            ),
                            affected_contexts=[i, j],
                        )
                    )

        return issues

    def _check_size_consistency(
        self, question: str, contexts: list[str]
    ) -> list[ChunkingIssue]:
        """Detect inconsistent chunk sizes."""
        issues: list[ChunkingIssue] = []
        lengths = [len(c) for c in contexts]

        if len(lengths) < 2:
            return issues

        min_len = min(lengths)
        max_len = max(lengths)

        if min_len > 0 and (max_len / min_len) > INCONSISTENCY_RATIO:
            issues.append(
                ChunkingIssue(
                    question=question,
                    issue_type="inconsistent_chunk_sizes",
                    description=(
                        f"Chunk sizes vary significantly "
                        f"(min={min_len}, max={max_len}, "
                        f"ratio={max_len / min_len:.1f}x). "
                        f"Consider using a consistent chunking strategy."
                    ),
                    affected_contexts=list(range(len(contexts))),
                )
            )

        return issues

    def _check_empty_chunks(
        self, question: str, contexts: list[str]
    ) -> list[ChunkingIssue]:
        """Detect empty or near-empty chunks."""
        issues: list[ChunkingIssue] = []

        for i, ctx in enumerate(contexts):
            stripped = ctx.strip()
            if len(stripped) < MIN_CHUNK_LENGTH:
                issues.append(
                    ChunkingIssue(
                        question=question,
                        issue_type="empty_or_small_chunk",
                        description=(
                            f"Context {i + 1} is very short "
                            f"({len(stripped)} chars), possibly an "
                            f"incomplete or empty chunk."
                        ),
                        affected_contexts=[i],
                    )
                )

        return issues

    def _check_content_gaps(
        self, question: str, contexts: list[str]
    ) -> list[ChunkingIssue]:
        """Detect potential content gaps between chunks.

        Checks if the question keywords are missing from all retrieved contexts,
        indicating a gap in the chunking coverage.
        """
        issues: list[ChunkingIssue] = []

        # Extract meaningful words from the question (4+ chars, lowercase)
        # Skip common short words (what, how, the, etc.)
        stop_words = {
            "what", "how", "why", "when", "where", "which", "who",
            "does", "have", "been", "from", "with", "that", "this",
            "will", "about", "into", "your", "some", "than",
        }
        question_words = set(
            w.lower() for w in re.findall(r"\b\w{4,}\b", question)
        ) - stop_words
        if not question_words:
            return issues

        # Combine all contexts
        all_context_text = " ".join(contexts).lower()

        # Find question words missing from all contexts
        missing_words = [
            w for w in question_words if w not in all_context_text
        ]

        # Only flag if most question words are missing (>60%)
        if len(missing_words) > len(question_words) * 0.6:
            issues.append(
                ChunkingIssue(
                    question=question,
                    issue_type="content_gap",
                    description=(
                        f"Many question keywords are missing from retrieved "
                        f"contexts: {', '.join(sorted(missing_words)[:5])}. "
                        f"This suggests chunking may have split relevant "
                        f"information."
                    ),
                    affected_contexts=list(range(len(contexts))),
                )
            )

        return issues

    @staticmethod
    def _jaccard_similarity(text_a: str, text_b: str) -> float:
        """Compute Jaccard similarity between two text strings.

        Args:
            text_a: First text.
            text_b: Second text.

        Returns:
            Jaccard similarity score (0.0 to 1.0).
        """
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b

        return len(intersection) / len(union)

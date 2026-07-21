"""Chunking quality analyzer.

Detects issues with how documents are split into chunks, including:
- Information split across chunks (related content in different chunks)
- Overlapping chunks (duplicate content in multiple chunks)
- Inconsistent chunk sizes
- Context gaps (missing information between chunks)

Metadata keys (optional):
    chunk_size: Expected chunk size in characters. Used for size deviation checks.
    chunk_overlap: Expected overlap between chunks in characters. Used for overlap analysis.
    chunking_strategy: Strategy name (e.g., "recursive", "fixed", "semantic").
"""

from __future__ import annotations

import re

from openagent_eval.diagnosis.models import ChunkingIssue

# ---------------------------------------------------------------------------
# Thresholds (default values, overridden by metadata when available)
# ---------------------------------------------------------------------------

DEFAULT_OVERLAP_SIMILARITY_THRESHOLD = 0.8  # Jaccard similarity for overlap detection
DEFAULT_MIN_CHUNK_LENGTH = 50  # minimum expected chunk length in characters
DEFAULT_MAX_CHUNK_LENGTH = 5000  # maximum expected chunk length in characters
DEFAULT_INCONSISTENCY_RATIO = 4.0  # max/min length ratio
DEFAULT_MAX_SIZE_DEVIATION = 0.5  # max deviation from expected chunk_size (50%)


class ChunkingQualityAnalyzer:
    """Analyze chunking quality from retrieved contexts.

    Usage::

        analyzer = ChunkingQualityAnalyzer()
        issues = analyzer.analyze(question, contexts)
        for issue in issues:
            print(issue.issue_type, issue.description)

    With metadata for more informed analysis::

        issues = analyzer.analyze(question, contexts, metadata={
            "chunk_size": 512.0,
            "chunk_overlap": 50.0,
        })
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
                Supported keys:
                - ``chunk_size``: Expected chunk size in characters.
                - ``chunk_overlap``: Expected overlap in characters.

        Returns:
            List of detected chunking issues.
        """
        issues: list[ChunkingIssue] = []

        if not contexts:
            return issues

        # Extract metadata values (default to None if not provided)
        expected_chunk_size = (
            int(metadata["chunk_size"]) if metadata and "chunk_size" in metadata else None
        )
        expected_overlap = (
            int(metadata["chunk_overlap"]) if metadata and "chunk_overlap" in metadata else None
        )

        issues.extend(self._check_overlap(question, contexts, expected_overlap))
        issues.extend(self._check_size_consistency(question, contexts, expected_chunk_size))
        issues.extend(self._check_empty_chunks(question, contexts, expected_chunk_size))
        issues.extend(self._check_content_gaps(question, contexts))

        return issues

    def _check_overlap(
        self,
        question: str,
        contexts: list[str],
        expected_overlap: int | None = None,
    ) -> list[ChunkingIssue]:
        """Detect overlapping chunks using Jaccard similarity.

        Args:
            question: The question that triggered retrieval.
            contexts: List of retrieved context strings.
            expected_overlap: Expected overlap in characters from metadata.
                When provided, also checks if actual character overlap is
                significantly higher than expected (indicating redundant chunks).
        """
        issues: list[ChunkingIssue] = []

        for i in range(len(contexts)):
            for j in range(i + 1, len(contexts)):
                similarity = self._jaccard_similarity(contexts[i], contexts[j])
                if similarity > DEFAULT_OVERLAP_SIMILARITY_THRESHOLD:
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

        # If expected_overlap is provided, check for excessive character overlap
        if expected_overlap is not None and expected_overlap > 0:
            for i in range(len(contexts)):
                for j in range(i + 1, len(contexts)):
                    char_overlap = self._char_overlap(contexts[i], contexts[j])
                    # Flag if actual overlap is more than 3x expected
                    if char_overlap > expected_overlap * 3:
                        issues.append(
                            ChunkingIssue(
                                question=question,
                                issue_type="excessive_overlap",
                                description=(
                                    f"Contexts {i + 1} and {j + 1} have "
                                    f"excessive character overlap ({char_overlap} chars vs "
                                    f"expected {expected_overlap} chars), "
                                    f"indicating inefficient chunking."
                                ),
                                affected_contexts=[i, j],
                            )
                        )

        return issues

    def _check_size_consistency(
        self,
        question: str,
        contexts: list[str],
        expected_chunk_size: int | None = None,
    ) -> list[ChunkingIssue]:
        """Detect inconsistent chunk sizes.

        Args:
            question: The question that triggered retrieval.
            contexts: List of retrieved context strings.
            expected_chunk_size: Expected chunk size in characters from metadata.
                When provided, checks if chunks deviate significantly from this size.
        """
        issues: list[ChunkingIssue] = []
        lengths = [len(c) for c in contexts]

        if len(lengths) < 2:
            # Still check single chunk against expected size
            if expected_chunk_size is not None and lengths:
                actual_len = lengths[0]
                deviation = abs(actual_len - expected_chunk_size) / expected_chunk_size
                if deviation > DEFAULT_MAX_SIZE_DEVIATION:
                    issues.append(
                        ChunkingIssue(
                            question=question,
                            issue_type="chunk_size_deviation",
                            description=(
                                f"Chunk size ({actual_len} chars) deviates significantly "
                                f"from expected ({expected_chunk_size} chars, "
                                f"{deviation:.0%} deviation)."
                            ),
                            affected_contexts=[0],
                        )
                    )
            return issues

        min_len = min(lengths)
        max_len = max(lengths)

        # Check for inconsistent chunk sizes
        if min_len > 0 and (max_len / min_len) > DEFAULT_INCONSISTENCY_RATIO:
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

        # If expected_chunk_size is provided, check deviation from expected
        if expected_chunk_size is not None:
            for idx, length in enumerate(lengths):
                deviation = abs(length - expected_chunk_size) / expected_chunk_size
                if deviation > DEFAULT_MAX_SIZE_DEVIATION:
                    issues.append(
                        ChunkingIssue(
                            question=question,
                            issue_type="chunk_size_deviation",
                            description=(
                                f"Context {idx + 1} size ({length} chars) deviates "
                                f"significantly from expected ({expected_chunk_size} chars, "
                                f"{deviation:.0%} deviation)."
                            ),
                            affected_contexts=[idx],
                        )
                    )

        return issues

    def _check_empty_chunks(
        self,
        question: str,
        contexts: list[str],
        expected_chunk_size: int | None = None,
    ) -> list[ChunkingIssue]:
        """Detect empty or near-empty chunks.

        Args:
            question: The question that triggered retrieval.
            contexts: List of retrieved context strings.
            expected_chunk_size: Expected chunk size in characters from metadata.
                When provided, uses 10% of expected size as the threshold
                for detecting empty/small chunks instead of the default.
        """
        issues: list[ChunkingIssue] = []

        # Use expected_chunk_size / 10 as threshold if provided
        min_threshold = (
            expected_chunk_size // 10
            if expected_chunk_size is not None
            else DEFAULT_MIN_CHUNK_LENGTH
        )

        for i, ctx in enumerate(contexts):
            stripped = ctx.strip()
            if len(stripped) < min_threshold:
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
    def _char_overlap(text_a: str, text_b: str) -> int:
        """Compute the length of the longest overlapping suffix/prefix between two texts.

        This measures character-level overlap that might indicate inefficient
        chunking (e.g., the same paragraph appears at the end of one chunk
        and the beginning of the next).

        Args:
            text_a: First text.
            text_b: Second text.

        Returns:
            Number of characters in the longest suffix of text_a that
            matches a prefix of text_b.
        """
        max_overlap = min(len(text_a), len(text_b))
        # Check from longest possible overlap down to 1
        for length in range(max_overlap, 0, -1):
            if text_a.endswith(text_b[:length]):
                return length
            if text_b.endswith(text_a[:length]):
                return length
        return 0

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

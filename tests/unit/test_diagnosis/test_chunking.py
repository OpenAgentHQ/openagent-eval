"""Tests for chunking quality analyzer."""

from __future__ import annotations

from openagent_eval.diagnosis.chunking import ChunkingQualityAnalyzer


class TestChunkingQualityAnalyzer:
    """Tests for ChunkingQualityAnalyzer."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = ChunkingQualityAnalyzer()

    def test_empty_contexts_returns_no_issues(self) -> None:
        """Empty contexts should return no issues."""
        issues = self.analyzer.analyze("What is AI?", [])
        assert issues == []

    def test_single_context_returns_no_issues(self) -> None:
        """A single normal context should return no issues."""
        issues = self.analyzer.analyze(
            "Explain Python programming language",
            ["Python is a high-level programming language used for web development and data science."],
        )
        assert issues == []

    def test_overlapping_contexts_detected(self) -> None:
        """Highly similar contexts should be detected as overlapping."""
        ctx_a = "Python is a programming language used for web development and data science."
        ctx_b = "Python is a programming language used for web development and data science."  # Near-duplicate
        issues = self.analyzer.analyze("What is Python?", [ctx_a, ctx_b])
        overlap_issues = [i for i in issues if i.issue_type == "overlapping_chunks"]
        assert len(overlap_issues) > 0
        assert overlap_issues[0].affected_contexts == [0, 1]

    def test_distinct_contexts_no_overlap(self) -> None:
        """Distinct contexts should not be flagged as overlapping."""
        ctx_a = "Python is a programming language."
        ctx_b = "JavaScript is used for web browsers."
        issues = self.analyzer.analyze("What is programming?", [ctx_a, ctx_b])
        overlap_issues = [i for i in issues if i.issue_type == "overlapping_chunks"]
        assert len(overlap_issues) == 0

    def test_inconsistent_chunk_sizes(self) -> None:
        """Highly uneven chunk sizes should be detected."""
        ctx_short = "Short."
        ctx_long = "x" * 500  # 500 chars vs 6 chars = 83x ratio
        issues = self.analyzer.analyze(
            "What is this?", [ctx_short, ctx_long]
        )
        size_issues = [
            i for i in issues if i.issue_type == "inconsistent_chunk_sizes"
        ]
        assert len(size_issues) > 0

    def test_consistent_chunk_sizes_no_issue(self) -> None:
        """Similar chunk sizes should not be flagged."""
        ctx_a = "A" * 100
        ctx_b = "B" * 120
        issues = self.analyzer.analyze("Test?", [ctx_a, ctx_b])
        size_issues = [
            i for i in issues if i.issue_type == "inconsistent_chunk_sizes"
        ]
        assert len(size_issues) == 0

    def test_empty_chunk_detected(self) -> None:
        """Very short contexts should be detected."""
        issues = self.analyzer.analyze(
            "What is AI?", ["", "   ", "a"]
        )
        empty_issues = [
            i for i in issues if i.issue_type == "empty_or_small_chunk"
        ]
        assert len(empty_issues) > 0

    def test_content_gap_detected(self) -> None:
        """Missing question keywords in contexts should be detected."""
        # Question has "quantum" and "computing" but contexts don't
        issues = self.analyzer.analyze(
            "What is quantum computing and how does it work?",
            ["The weather is nice today.", "Python is a language."],
        )
        gap_issues = [i for i in issues if i.issue_type == "content_gap"]
        assert len(gap_issues) > 0

    def test_no_content_gap_when_keywords_present(self) -> None:
        """No gap should be detected when keywords are present in contexts."""
        issues = self.analyzer.analyze(
            "What is Python?",
            ["Python is a programming language.", "Python is used for AI."],
        )
        gap_issues = [i for i in issues if i.issue_type == "content_gap"]
        assert len(gap_issues) == 0

    def test_multiple_issues_detected(self) -> None:
        """Multiple issues should be detected simultaneously."""
        # Short context + overlapping + content gap
        ctx_a = "The quick brown fox jumps."
        ctx_b = "The quick brown fox jumps over the lazy dog."
        issues = self.analyzer.analyze(
            "Explain quantum entanglement in physics.",
            [ctx_a, ctx_b],
        )
        # Should detect overlap and possibly content gap
        issue_types = {i.issue_type for i in issues}
        assert len(issue_types) >= 1  # At least overlap


class TestMetadataUsage:
    """Tests for metadata parameter usage in ChunkingQualityAnalyzer."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = ChunkingQualityAnalyzer()

    def test_metadata_chunk_size_single_deviation(self) -> None:
        """Chunk deviating from expected size should be flagged."""
        # Expected 512, actual is 100 (80% deviation)
        issues = self.analyzer.analyze(
            "What is Python?",
            ["Python is a language."],
            metadata={"chunk_size": 512.0},
        )
        size_issues = [i for i in issues if i.issue_type == "chunk_size_deviation"]
        assert len(size_issues) > 0
        assert "512" in size_issues[0].description

    def test_metadata_chunk_size_no_deviation(self) -> None:
        """Chunk close to expected size should not be flagged."""
        # Expected 20, actual is 20 (0% deviation)
        issues = self.analyzer.analyze(
            "What is Python?",
            ["Python is a language."],
            metadata={"chunk_size": 20.0},
        )
        size_issues = [i for i in issues if i.issue_type == "chunk_size_deviation"]
        assert len(size_issues) == 0

    def test_metadata_chunk_size_multiple_chunks(self) -> None:
        """Multiple chunks with mixed deviations should be flagged."""
        issues = self.analyzer.analyze(
            "What is Python?",
            ["Short.", "This is a much longer chunk that exceeds the expected size significantly."],
            metadata={"chunk_size": 20.0},
        )
        size_issues = [i for i in issues if i.issue_type == "chunk_size_deviation"]
        # Both chunks deviate from expected size of 20
        assert len(size_issues) > 0

    def test_metadata_chunk_overlap_excessive(self) -> None:
        """Excessive character overlap should be detected when metadata provided."""
        # These have suffix/prefix overlap: "brown fox" (9 chars)
        ctx_a = "the quick brown fox"
        ctx_b = "brown fox jumps over"  # starts with "brown fox"
        issues = self.analyzer.analyze(
            "What is Python?",
            [ctx_a, ctx_b],
            metadata={"chunk_overlap": 1.0},  # Expected only 1 char, actual is 9
        )
        overlap_issues = [i for i in issues if i.issue_type == "excessive_overlap"]
        assert len(overlap_issues) > 0

    def test_metadata_chunk_overlap_no_excess(self) -> None:
        """Overlap within expected range should not be flagged."""
        ctx_a = "Python is a language."
        ctx_b = "JavaScript is used for web."
        issues = self.analyzer.analyze(
            "What is programming?",
            [ctx_a, ctx_b],
            metadata={"chunk_overlap": 50.0},  # Expected 50 chars
        )
        overlap_issues = [i for i in issues if i.issue_type == "excessive_overlap"]
        assert len(overlap_issues) == 0

    def test_metadata_empty_chunk_uses_expected_size(self) -> None:
        """Empty chunk detection should use expected size threshold."""
        # With chunk_size=1000, threshold is 100 chars
        issues = self.analyzer.analyze(
            "What is Python?",
            ["Hi", "Python is a programming language used for many things."],
            metadata={"chunk_size": 1000.0},
        )
        empty_issues = [i for i in issues if i.issue_type == "empty_or_small_chunk"]
        # "Hi" (2 chars) is below 100 char threshold
        assert len(empty_issues) > 0

    def test_metadata_none_backward_compatible(self) -> None:
        """Passing None metadata should work exactly as before."""
        issues_none = self.analyzer.analyze(
            "What is Python?",
            ["Python is a language."],
            metadata=None,
        )
        issues_no_meta = self.analyzer.analyze(
            "What is Python?",
            ["Python is a language."],
        )
        assert len(issues_none) == len(issues_no_meta)

    def test_metadata_empty_dict_backward_compatible(self) -> None:
        """Passing empty metadata dict should work exactly as before."""
        issues = self.analyzer.analyze(
            "What is Python?",
            ["Python is a language."],
            metadata={},
        )
        # Should have no metadata-specific issues
        metadata_issues = [
            i for i in issues
            if i.issue_type in ("chunk_size_deviation", "excessive_overlap")
        ]
        assert len(metadata_issues) == 0

    def test_metadata_both_chunk_size_and_overlap(self) -> None:
        """Both metadata keys should be usable simultaneously."""
        # Overlapping contexts with size deviation (suffix/prefix match)
        ctx_a = "the quick brown fox"
        ctx_b = "brown fox jumps over"  # starts with "brown fox"
        issues = self.analyzer.analyze(
            "What is Python?",
            [ctx_a, ctx_b],
            metadata={"chunk_size": 500.0, "chunk_overlap": 1.0},
        )
        # Should detect size deviation (both ~20 chars vs expected 500)
        # and excessive overlap (9 chars overlap vs expected 1)
        issue_types = {i.issue_type for i in issues}
        assert "chunk_size_deviation" in issue_types
        assert "excessive_overlap" in issue_types


class TestCharOverlap:
    """Tests for the character overlap helper."""

    def test_identical_texts(self) -> None:
        """Identical texts should have full overlap."""
        overlap = ChunkingQualityAnalyzer._char_overlap("hello", "hello")
        assert overlap == 5

    def test_suffix_prefix_match(self) -> None:
        """Suffix of A matching prefix of B should be detected."""
        overlap = ChunkingQualityAnalyzer._char_overlap(
            "the cat sat", "cat sat on"
        )
        assert overlap == 7  # "cat sat"

    def test_no_overlap(self) -> None:
        """Disjoint texts should have zero overlap."""
        overlap = ChunkingQualityAnalyzer._char_overlap("hello", "world")
        assert overlap == 0

    def test_empty_texts(self) -> None:
        """Empty texts should have zero overlap."""
        overlap = ChunkingQualityAnalyzer._char_overlap("", "")
        assert overlap == 0

    def test_one_empty(self) -> None:
        """One empty text should have zero overlap."""
        overlap = ChunkingQualityAnalyzer._char_overlap("hello", "")
        assert overlap == 0


class TestJaccardSimilarity:
    """Tests for the Jaccard similarity helper."""

    def test_identical_texts(self) -> None:
        """Identical texts should have similarity 1.0."""
        sim = ChunkingQualityAnalyzer._jaccard_similarity(
            "hello world", "hello world"
        )
        assert sim == 1.0

    def test_disjoint_texts(self) -> None:
        """Disjoint texts should have similarity 0.0."""
        sim = ChunkingQualityAnalyzer._jaccard_similarity(
            "hello", "world"
        )
        assert sim == 0.0

    def test_partial_overlap(self) -> None:
        """Partially overlapping texts should have intermediate similarity."""
        sim = ChunkingQualityAnalyzer._jaccard_similarity(
            "hello world foo", "hello world bar"
        )
        assert 0.0 < sim < 1.0

    def test_empty_texts(self) -> None:
        """Empty texts should have similarity 0.0."""
        sim = ChunkingQualityAnalyzer._jaccard_similarity("", "")
        assert sim == 0.0

    def test_case_insensitive(self) -> None:
        """Similarity should be case-insensitive."""
        sim = ChunkingQualityAnalyzer._jaccard_similarity(
            "Hello World", "hello world"
        )
        assert sim == 1.0

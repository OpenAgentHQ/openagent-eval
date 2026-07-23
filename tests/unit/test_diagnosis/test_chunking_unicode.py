"""Regression tests for #64: content gap analysis must handle non-ASCII text.

``_check_content_gaps`` extracts question keywords with ``re.findall(r"\\b\\w{4,}\\b")``.
With the previous ``[a-zA-Z]{4,}`` pattern, accented Latin words (French
"différence", German "Größe") were dropped and CJK questions produced zero
keywords — so content gap detection was silently skipped for most of the
world's languages. These tests pin the Unicode-aware behavior.
"""

from __future__ import annotations

from openagent_eval.diagnosis.chunking import ChunkingQualityAnalyzer


class TestContentGapUnicode:
    """Content gap detection across non-ASCII scripts."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = ChunkingQualityAnalyzer()
        # Two unrelated English contexts so any missing keyword drives a gap.
        self.unrelated = [
            "The weather is sunny today and warm.",
            "Cats are small domestic mammals.",
        ]

    def _content_gaps(self, question: str, contexts: list[str]) -> list:
        return [
            i
            for i in self.analyzer.analyze(question, contexts)
            if i.issue_type == "content_gap"
        ]

    def test_accented_german_keyword_is_extracted(self) -> None:
        """The German word 'Größe' must be extracted, not dropped at the umlaut.

        Under the old ``[a-zA-Z]`` regex 'größe' never entered the keyword set,
        so it could never appear as a missing keyword.
        """
        gaps = self._content_gaps(
            "Warum ist die Größe der Chunks wichtig?", self.unrelated
        )
        assert len(gaps) == 1
        assert "größe" in gaps[0].description.lower()

    def test_accented_french_keyword_is_extracted(self) -> None:
        """The French word 'différence' must survive the accented 'é'."""
        gaps = self._content_gaps(
            "Quelle est la différence entre les modèles?", self.unrelated
        )
        assert len(gaps) == 1
        assert "différence" in gaps[0].description.lower()

    def test_cjk_only_question_still_analyzed(self) -> None:
        """A CJK-only question must not short-circuit content gap detection.

        Under the old regex ``re.findall`` returned zero matches, the keyword
        set was empty, and the method returned early with no analysis at all.
        """
        gaps = self._content_gaps("什么是量子计算技术在实践", self.unrelated)
        assert len(gaps) == 1

    def test_no_false_gap_when_accented_keyword_present(self) -> None:
        """No gap should be flagged when the accented keyword is in the contexts."""
        present = [
            "Die Größe der Chunks ist wichtig für die Qualität.",
            "Modelle brauchen gute Chunks.",
        ]
        gaps = self._content_gaps("Warum ist die Größe wichtig?", present)
        assert gaps == []

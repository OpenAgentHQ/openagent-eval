"""Contradiction detector using LLM-as-Judge.

Detects cross-document contradictions by comparing document pairs
using an LLM to determine if they present incompatible information.
"""

from __future__ import annotations

import asyncio
from typing import Any

from openagent_eval.corpus.base import BaseCorpusAnalyzer
from openagent_eval.corpus.models import (
    AuditReport,
    CorpusDocument,
    CorpusIssue,
    IssueSeverity,
    IssueType,
)

# Maximum content length sent to LLM per document (chars)
_MAX_DOC_CHARS = 2000

# Prompt template for contradiction detection
_CONTRADICTION_PROMPT = """You are a document analysis expert. Compare the following two documents and determine if they contain contradictory information about the same topic.

Document A (ID: {doc_a_id}):
{doc_a_content}

Document B (ID: {doc_b_id}):
{doc_b_content}

Answer with ONLY a JSON object in this exact format:
{{
    "contradicts": true/false,
    "confidence": 0.0 to 1.0,
    "topic": "the topic being discussed",
    "explanation": "brief explanation of the contradiction or why they don't contradict"
}}"""


class ContradictionDetector(BaseCorpusAnalyzer):
    """Detects cross-document contradictions using LLM-as-Judge.

    Compares document pairs and uses an LLM to determine if they
    present incompatible information about the same topic.

    Attributes:
        name: Identifier for this analyzer.
        description: Human-readable description.
    """

    name = "contradiction"
    description = "Detects cross-document contradictions using LLM-as-Judge"

    def __init__(
        self,
        llm_provider: Any | None = None,
        model: str | None = None,
        max_pairs: int = 50,
    ) -> None:
        """Initialize the contradiction detector.

        Args:
            llm_provider: LLM provider instance with a generate() method.
            model: Model identifier (for display purposes).
            max_pairs: Maximum document pairs to compare.
        """
        self.llm_provider = llm_provider
        self.model = model
        self.max_pairs = max_pairs

    async def analyze(
        self,
        documents: list[CorpusDocument],
        **kwargs: Any,
    ) -> AuditReport:
        """Analyze documents for contradictions.

        Args:
            documents: List of corpus documents to analyze.
            **kwargs: Additional configuration.

        Returns:
            AuditReport with detected contradictions.

        Raises:
            CorpusAuditError: If analysis fails.
        """
        self.validate_inputs(documents)

        issues: list[CorpusIssue] = []

        # Generate document pairs for comparison
        pairs = self._generate_pairs(documents)

        if self.llm_provider is None:
            # Without LLM, return a report indicating LLM is required
            return AuditReport(
                corpus_path="",
                total_documents=len(documents),
                issues=[],
                health_score=1.0,
                checks_performed=[self.name],
                summary="LLM provider required for contradiction detection. Install and configure an LLM provider.",
                metadata={"requires_llm": True},
            )

        # Compare pairs using LLM
        tasks = [self._compare_pair(doc_a, doc_b) for doc_a, doc_b in pairs[:self.max_pairs]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, CorpusIssue):
                issues.append(result)
            elif isinstance(result, Exception):
                # Log but don't fail on individual pair errors
                continue

        health_score = self._compute_health_score(len(documents), len(issues))

        return AuditReport(
            corpus_path="",
            total_documents=len(documents),
            issues=issues,
            health_score=health_score,
            checks_performed=[self.name],
            summary=self._generate_summary(issues, len(documents)),
            metadata={
                "pairs_compared": min(len(pairs), self.max_pairs),
                "total_possible_pairs": len(pairs),
                "model": self.model,
            },
        )

    def _generate_pairs(
        self, documents: list[CorpusDocument]
    ) -> list[tuple[CorpusDocument, CorpusDocument]]:
        """Generate pairs of documents for comparison.

        Uses a topic-prescreening heuristic: only compare documents
        that share at least one significant word (reduces N^2 to manageable).

        Args:
            documents: List of documents.

        Returns:
            List of document pairs to compare.
        """
        pairs: list[tuple[CorpusDocument, CorpusDocument]] = []

        # Simple heuristic: compare documents that share significant words
        for i, doc_a in enumerate(documents):
            words_a = set(doc_a.content.lower().split())
            for doc_b in documents[i + 1 :]:
                words_b = set(doc_b.content.lower().split())
                # Check for shared significant words (length > 4)
                shared = {
                    w for w in words_a & words_b if len(w) > 4
                }
                if len(shared) >= 3:
                    pairs.append((doc_a, doc_b))

        return pairs

    async def _compare_pair(
        self, doc_a: CorpusDocument, doc_b: CorpusDocument
    ) -> CorpusIssue | None:
        """Compare two documents for contradictions using the LLM.

        Args:
            doc_a: First document.
            doc_b: Second document.

        Returns:
            CorpusIssue if contradiction found, None otherwise.
        """
        if self.llm_provider is None:
            return None

        prompt = _CONTRADICTION_PROMPT.format(
            doc_a_id=doc_a.doc_id,
            doc_a_content=doc_a.content[:_MAX_DOC_CHARS],
            doc_b_id=doc_b.doc_id,
            doc_b_content=doc_b.content[:_MAX_DOC_CHARS],
        )

        try:
            response = await self.llm_provider.generate(prompt)
            result = self._parse_response(response)

            if result and result.get("contradicts") and result.get("confidence", 0) > 0.7:
                severity = (
                    IssueSeverity.HIGH
                    if result.get("confidence", 0) > 0.9
                    else IssueSeverity.MEDIUM
                )
                return CorpusIssue(
                    issue_type=IssueType.CONTRADICTION,
                    severity=severity,
                    title=f"Contradiction on '{result.get('topic', 'shared topic')}'",
                    description=result.get("explanation", "Documents present conflicting information"),
                    document_ids=[doc_a.doc_id, doc_b.doc_id],
                    metadata={
                        "confidence": result.get("confidence", 0),
                        "topic": result.get("topic", ""),
                    },
                )
        except Exception:
            # Don't fail the whole audit for one pair
            pass

        return None

    def _parse_response(self, response: str) -> dict[str, Any] | None:
        """Parse LLM response into structured data.

        Args:
            response: Raw LLM response string.

        Returns:
            Parsed dict or None if parsing fails.
        """
        import json

        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _compute_health_score(self, num_docs: int, num_issues: int) -> float:
        """Compute corpus health score based on contradictions.

        Args:
            num_docs: Number of documents.
            num_issues: Number of contradictions found.

        Returns:
            Health score between 0.0 and 1.0.
        """
        if num_docs <= 1:
            return 1.0

        # Score decreases with more contradictions
        # Use log scale to avoid extreme penalties for large corpora

        max_expected = num_docs * (num_docs - 1) / 2
        ratio = num_issues / max(max_expected * 0.1, 1)  # 10% of max pairs is "bad"
        penalty = min(ratio * 0.5, 0.5)  # Cap penalty at 0.5
        return max(1.0 - penalty, 0.0)

    def _generate_summary(self, issues: list[CorpusIssue], num_docs: int) -> str:
        """Generate a human-readable summary.

        Args:
            issues: Detected issues.
            num_docs: Number of documents analyzed.

        Returns:
            Summary string.
        """
        if not issues:
            return f"No contradictions found across {num_docs} documents."

        high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        medium = sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)

        parts = [f"Found {len(issues)} contradiction(s) across {num_docs} documents."]
        if high:
            parts.append(f"{high} high-severity.")
        if medium:
            parts.append(f"{medium} medium-severity.")

        return " ".join(parts)

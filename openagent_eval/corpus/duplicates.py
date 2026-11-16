"""Duplicate detector using embedding similarity.

Detects divergent duplicates — documents that are nearly identical
but have slight differences (e.g., different versions from
SharePoint vs Confluence).
"""

from __future__ import annotations

from typing import Any

from openagent_eval.corpus.base import BaseCorpusAnalyzer
from openagent_eval.corpus.models import (
    AuditReport,
    CorpusDocument,
    CorpusIssue,
    IssueSeverity,
    IssueType,
)
from openagent_eval.exceptions.corpus import CorpusAuditError


class DuplicateDetector(BaseCorpusAnalyzer):
    """Detects divergent duplicates using embedding similarity.

    Finds documents that are nearly identical but may have subtle
    differences — different versions of the same content.

    Attributes:
        name: Identifier for this analyzer.
        description: Human-readable description.
    """

    name = "duplicate"
    description = "Detects divergent duplicates using embedding similarity"

    def __init__(
        self,
        similarity_threshold: float = 0.92,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        """Initialize the duplicate detector.

        Args:
            similarity_threshold: Cosine similarity threshold (0-1) for duplicates.
            embedding_model: Sentence-transformers model for embeddings.
        """
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self._embedder: Any | None = None

    def _get_embedder(self) -> Any:
        """Lazy-load the sentence-transformer embedder.

        Returns:
            SentenceTransformer instance.

        Raises:
            ImportError: If sentence-transformers is not installed.
        """
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedder = SentenceTransformer(self.embedding_model)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for duplicate detection. "
                    "Install it with: pip install openagent-eval[corpus]"
                )
        return self._embedder

    async def analyze(
        self,
        documents: list[CorpusDocument],
        **kwargs: Any,
    ) -> AuditReport:
        """Analyze documents for duplicates.

        Args:
            documents: List of corpus documents to analyze.
            **kwargs: Additional configuration.

        Returns:
            AuditReport with detected duplicates.

        Raises:
            CorpusAuditError: If analysis fails.
        """
        self.validate_inputs(documents)

        issues: list[CorpusIssue] = []

        try:
            issues = self._find_duplicates(documents)
        except ImportError:
            return AuditReport(
                corpus_path="",
                total_documents=len(documents),
                issues=[],
                health_score=1.0,
                checks_performed=[self.name],
                summary="sentence-transformers is required for duplicate detection. Install with: pip install openagent-eval[corpus]",
                metadata={"requires_sentence_transformers": True},
            )
        except Exception as e:
            raise CorpusAuditError(
                message=f"Duplicate detection failed: {e}",
                analyzer_name=self.name,
                original_error=e,
            ) from e

        health_score = self._compute_health_score(len(documents), len(issues))

        return AuditReport(
            corpus_path="",
            total_documents=len(documents),
            issues=issues,
            health_score=health_score,
            checks_performed=[self.name],
            summary=self._generate_summary(issues, len(documents)),
            metadata={
                "similarity_threshold": self.similarity_threshold,
                "embedding_model": self.embedding_model,
            },
        )

    def _find_duplicates(self, documents: list[CorpusDocument]) -> list[CorpusIssue]:
        """Find duplicate document pairs using embeddings.

        Args:
            documents: List of documents.

        Returns:
            List of CorpusIssue for each duplicate pair.

        Raises:
            ImportError: If sentence-transformers is not installed.
        """
        if len(documents) < 2:
            return []

        embedder = self._get_embedder()

        # Generate embeddings for all documents
        contents = [doc.content[:5000] for doc in documents]  # Truncate long docs
        embeddings = embedder.encode(contents, show_progress_bar=False)

        # Compute pairwise cosine similarities
        import numpy as np

        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        normalized = embeddings / norms

        # Cosine similarity matrix
        similarity_matrix = np.dot(normalized, normalized.T)

        issues: list[CorpusIssue] = []
        seen_pairs: set[tuple[int, int]] = set()

        for i in range(len(documents)):
            for j in range(i + 1, len(documents)):
                if (i, j) in seen_pairs:
                    continue

                similarity = float(similarity_matrix[i, j])

                if similarity >= self.similarity_threshold:
                    seen_pairs.add((i, j))

                    # Determine if truly divergent or exact duplicate
                    is_exact = similarity > 0.99
                    severity = IssueSeverity.LOW if is_exact else IssueSeverity.MEDIUM

                    doc_a = documents[i]
                    doc_b = documents[j]

                    issue_type_title = (
                        "Exact duplicate" if is_exact else "Divergent duplicate"
                    )

                    issues.append(
                        CorpusIssue(
                            issue_type=IssueType.DUPLICATE,
                            severity=severity,
                            title=f"{issue_type_title}: {doc_a.doc_id} & {doc_b.doc_id}",
                            description=(
                                f"Documents '{doc_a.doc_id}' and '{doc_b.doc_id}' have "
                                f"{similarity:.1%} similarity. "
                                f"{'This appears to be an exact copy.' if is_exact else 'These are near-duplicates with potential divergences.'}"
                            ),
                            document_ids=[doc_a.doc_id, doc_b.doc_id],
                            metadata={
                                "similarity": similarity,
                                "is_exact": is_exact,
                            },
                        )
                    )

        return issues

    def _compute_health_score(self, num_docs: int, num_issues: int) -> float:
        """Compute health score based on duplicates.

        Args:
            num_docs: Number of documents.
            num_issues: Number of duplicate pairs found.

        Returns:
            Health score between 0.0 and 1.0.
        """
        if num_docs <= 1:
            return 1.0

        # Each duplicate pair reduces score
        max_pairs = num_docs * (num_docs - 1) / 2
        ratio = num_issues / max(max_pairs * 0.05, 1)  # 5% of max pairs is concerning
        penalty = min(ratio * 0.4, 0.4)  # Cap at 0.4
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
            return f"No duplicates found across {num_docs} documents."

        exact = sum(1 for i in issues if i.metadata.get("is_exact"))
        divergent = len(issues) - exact

        parts = [f"Found {len(issues)} duplicate pair(s) across {num_docs} documents."]
        if exact:
            parts.append(f"{exact} exact duplicate(s).")
        if divergent:
            parts.append(
                f"{divergent} divergent duplicate(s) (potential version conflicts)."
            )

        return " ".join(parts)

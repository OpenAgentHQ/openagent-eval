"""Coverage analyzer for thematic gaps.

Detects missing topics or themes in the knowledge base
by analyzing document clustering and topic distribution.
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


class CoverageAnalyzer(BaseCorpusAnalyzer):
    """Analyzes thematic coverage gaps in the corpus.

    Uses document clustering to identify topic groups and detect
    areas with insufficient coverage.

    Attributes:
        name: Identifier for this analyzer.
        description: Human-readable description.
    """

    name = "coverage"
    description = "Analyzes thematic coverage gaps in the corpus"

    def __init__(
        self,
        min_cluster_size: int = 2,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        """Initialize the coverage analyzer.

        Args:
            min_cluster_size: Minimum documents to form a topic cluster.
            embedding_model: Sentence-transformers model for embeddings.
        """
        self.min_cluster_size = min_cluster_size
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
                    "sentence-transformers is required for coverage analysis. "
                    "Install it with: pip install openagent-eval[corpus]"
                )
        return self._embedder

    async def analyze(
        self,
        documents: list[CorpusDocument],
        **kwargs: Any,
    ) -> AuditReport:
        """Analyze corpus for thematic coverage gaps.

        Args:
            documents: List of corpus documents to analyze.
            **kwargs: Additional configuration.

        Returns:
            AuditReport with coverage analysis.

        Raises:
            CorpusAuditError: If analysis fails.
        """
        self.validate_inputs(documents)

        issues: list[CorpusIssue] = []
        topic_info: dict[str, Any] = {}

        try:
            issues, topic_info = self._analyze_coverage(documents)
        except ImportError:
            return AuditReport(
                corpus_path="",
                total_documents=len(documents),
                issues=[],
                health_score=1.0,
                checks_performed=[self.name],
                summary="sentence-transformers is required for coverage analysis. Install with: pip install openagent-eval[corpus]",
                metadata={"requires_sentence_transformers": True},
            )
        except Exception as e:
            raise CorpusAuditError(
                message=f"Coverage analysis failed: {e}",
                analyzer_name=self.name,
                original_error=e,
            ) from e

        health_score = self._compute_health_score(
            len(documents), len(issues), topic_info
        )

        return AuditReport(
            corpus_path="",
            total_documents=len(documents),
            issues=issues,
            health_score=health_score,
            checks_performed=[self.name],
            summary=self._generate_summary(issues, len(documents), topic_info),
            metadata=topic_info,
        )

    def _analyze_coverage(
        self, documents: list[CorpusDocument]
    ) -> tuple[list[CorpusIssue], dict[str, Any]]:
        """Analyze document coverage using clustering.

        Args:
            documents: List of documents.

        Returns:
            Tuple of (issues list, topic info dict).

        Raises:
            ImportError: If sentence-transformers is not installed.
        """
        if len(documents) < self.min_cluster_size:
            return [], {"num_topics": 0, "clusters": []}

        embedder = self._get_embedder()

        # Generate embeddings
        contents = [doc.content[:5000] for doc in documents]
        embeddings = embedder.encode(contents, show_progress_bar=False)

        # Cluster documents using simple K-means
        import numpy as np
        from sklearn.cluster import KMeans

        # Determine number of clusters (sqrt of document count, min 2)
        n_clusters = max(2, min(int(len(documents) ** 0.5), 20))

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        # Analyze clusters
        issues: list[CorpusIssue] = []
        clusters: list[dict[str, Any]] = []

        for cluster_id in range(n_clusters):
            cluster_mask = labels == cluster_id
            cluster_docs = [
                doc for doc, mask in zip(documents, cluster_mask, strict=False) if mask
            ]
            cluster_size = len(cluster_docs)

            # Find the centroid representative
            cluster_indices = np.where(cluster_mask)[0]
            centroid = kmeans.cluster_centers_[cluster_id]
            distances = np.linalg.norm(embeddings[cluster_indices] - centroid, axis=1)
            representative_idx = cluster_indices[np.argmin(distances)]
            representative_doc = documents[representative_idx]

            # Extract topic from representative document
            topic = self._extract_topic(representative_doc.content)

            cluster_info = {
                "cluster_id": cluster_id,
                "topic": topic,
                "size": cluster_size,
                "document_ids": [d.doc_id for d in cluster_docs],
                "representative_doc_id": representative_doc.doc_id,
            }
            clusters.append(cluster_info)

            # Flag small clusters as potential coverage gaps
            if cluster_size < self.min_cluster_size:
                issues.append(
                    CorpusIssue(
                        issue_type=IssueType.COVERAGE_GAP,
                        severity=IssueSeverity.LOW,
                        title=f"Thin topic coverage: '{topic}'",
                        description=(
                            f"Topic '{topic}' has only {cluster_size} document(s). "
                            f"Consider adding more content to this area."
                        ),
                        document_ids=[d.doc_id for d in cluster_docs],
                        metadata={
                            "cluster_id": cluster_id,
                            "topic": topic,
                            "document_count": cluster_size,
                        },
                    )
                )

        topic_info = {
            "num_topics": n_clusters,
            "clusters": clusters,
            "embedding_model": self.embedding_model,
        }

        return issues, topic_info

    def _extract_topic(self, content: str) -> str:
        """Extract a topic label from document content.

        Uses a simple heuristic: take the first meaningful phrase
        or sentence as the topic.

        Args:
            content: Document text content.

        Returns:
            Topic label string.
        """
        # Take first 100 chars and clean up
        text = content[:100].strip()

        # Try to find a sentence boundary
        for sep in [". ", "! ", "? ", "\n"]:
            idx = text.find(sep)
            if idx > 10:
                text = text[:idx]
                break

        # Truncate if still too long
        if len(text) > 60:
            text = text[:57] + "..."

        return text if text else "Untitled topic"

    def _compute_health_score(
        self,
        num_docs: int,
        num_issues: int,
        topic_info: dict[str, Any],
    ) -> float:
        """Compute health score based on coverage.

        Args:
            num_docs: Number of documents.
            num_issues: Number of coverage gaps.
            topic_info: Topic analysis information.

        Returns:
            Health score between 0.0 and 1.0.
        """
        if num_docs == 0:
            return 1.0

        # Score based on coverage gaps
        num_topics = topic_info.get("num_topics", 0)
        if num_topics == 0:
            return 1.0

        gap_ratio = num_issues / num_topics
        penalty = min(gap_ratio * 0.3, 0.3)  # Cap at 0.3

        return max(1.0 - penalty, 0.0)

    def _generate_summary(
        self,
        issues: list[CorpusIssue],
        num_docs: int,
        topic_info: dict[str, Any],
    ) -> str:
        """Generate a human-readable summary.

        Args:
            issues: Detected issues.
            num_docs: Number of documents analyzed.
            topic_info: Topic analysis information.

        Returns:
            Summary string.
        """
        num_topics = topic_info.get("num_topics", 0)

        if not issues:
            return (
                f"Coverage analysis found {num_topics} topic(s) across "
                f"{num_docs} documents. No significant gaps detected."
            )

        return (
            f"Coverage analysis found {num_topics} topic(s) across "
            f"{num_docs} documents. {len(issues)} thin coverage area(s) detected."
        )

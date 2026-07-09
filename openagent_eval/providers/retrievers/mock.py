"""Mock retriever for dry-run and testing.

This adapter implements the ``Retriever`` interface without a vector store. It
is selected when ``retriever.provider: mock`` is configured, allowing the full
pipeline to run offline. When the caller supplies ``ground_truth_contexts``
(via the pipeline in mock mode), those are returned as the retrieved documents
so retrieval metrics can be exercised meaningfully; otherwise deterministic
placeholder documents are returned.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document


class MockRetriever(Retriever):
    """Offline retriever that returns deterministic documents."""

    name: str = "mock"
    description: str = "Deterministic offline retriever for dry-run and testing"

    def __init__(self, collection_name: str = "mock", **_: Any) -> None:
        """Initialize the mock retriever.

        Args:
            collection_name: Collection name to report (informational).
        """
        self.collection_name = collection_name

    async def retrieve(self, query: str, k: int = 5, **kwargs: Any) -> list[Document]:
        """Return retrieved documents without a vector store.

        Args:
            query: The search query.
            k: Number of documents to return.
            **kwargs: May include ``ground_truth_contexts`` (list[str]) which,
                when present, are returned as the retrieved documents.

        Returns:
            A list of ``Document`` objects.
        """
        self.validate_inputs(query=query, k=k)

        gt_contexts = kwargs.get("ground_truth_contexts")
        if gt_contexts:
            return [
                Document(
                    content=ctx,
                    metadata={"mock": True, "source": "ground_truth_contexts"},
                    score=1.0,
                    id=f"gt-{i}",
                )
                for i, ctx in enumerate(gt_contexts[:k])
            ]

        docs: list[Document] = []
        for i in range(min(k, 3)):
            docs.append(
                Document(
                    content=f"Mock context {i + 1} for query: {query}",
                    metadata={"mock": True},
                    score=max(0.0, 1.0 - i * 0.25),
                    id=f"mock-{i}",
                )
            )
        return docs

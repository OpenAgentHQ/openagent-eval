"""Qdrant retriever adapter for OpenAgent Eval.

Connects to a Qdrant vector store (local ``:memory:``, gRPC/REST URL, or
Qdrant Cloud) and performs similarity search. Documents/queries are embedded
locally with the configured
:class:`~openagent_eval.providers.embedders.base.Embedder`.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.embedders.base import Embedder
from openagent_eval.providers.models import Document


class QdrantRetriever(Retriever):
    """Qdrant-backed dense vector retriever."""

    name: str = "qdrant"
    description: str = "Qdrant vector database retriever"

    def __init__(
        self,
        collection_name: str,
        embedder: Embedder | None = None,
        url: str | None = None,
        api_key: str | None = None,
        prefer_grpc: bool = False,
        distance: str = "Cosine",
        **_: Any,
    ) -> None:
        """Initialize the Qdrant retriever.

        Args:
            collection_name: Qdrant collection to query.
            embedder: Required embedder for query/document vectors.
            url: Qdrant URL (omit for in-memory ``:memory:``).
            api_key: API key for Qdrant Cloud.
            prefer_grpc: Use gRPC transport.
            distance: Distance metric for collection creation (Cosine/Euclid/Dot).
        """
        if embedder is None:
            raise ProviderConnectionError(
                message="QdrantRetriever requires an embedder (set retriever.embedder)",
                provider_name=self.name,
            )
        self._collection = collection_name
        self._embedder = embedder
        self._distance = distance

        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "qdrant-client is required for the qdrant retriever. "
                "Install it with: pip install openagent-eval[qdrant]"
            ) from exc

        try:
            self._client = QdrantClient(
                url=url, api_key=api_key, prefer_grpc=prefer_grpc
            )
        except Exception as exc:
            raise ProviderConnectionError(
                message=f"Failed to connect to Qdrant: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Embed the query and search the Qdrant collection."""
        self.validate_inputs(query=query, k=k)
        try:
            vector = await self._embedder.embed_query(query)
            hits = self._client.search(
                collection_name=self._collection,
                query_vector=vector,
                limit=k,
            )
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"Qdrant search failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        documents: list[Document] = []
        for hit in hits:
            payload = hit.payload or {}
            documents.append(
                Document(
                    content=str(payload.get("content", "")),
                    metadata={k: v for k, v in payload.items() if k != "content"},
                    score=max(0.0, min(1.0, float(hit.score))),
                    id=str(hit.id),
                )
            )
        return documents

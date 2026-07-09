"""Pinecone retriever adapter for OpenAgent Eval.

Queries a Pinecone index and returns the top matches. Documents/queries are
embedded locally with the configured
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


class PineconeRetriever(Retriever):
    """Pinecone-backed dense vector retriever."""

    name: str = "pinecone"
    description: str = "Pinecone managed vector database retriever"

    def __init__(
        self,
        index_name: str,
        embedder: Embedder | None = None,
        api_key: str | None = None,
        environment: str | None = None,
        namespace: str | None = None,
        **_: Any,
    ) -> None:
        """Initialize the Pinecone retriever.

        Args:
            index_name: Pinecone index to query.
            embedder: Required embedder for query/document vectors.
            api_key: Pinecone API key (or ``PINECONE_API_KEY`` env).
            environment: Pinecone environment (legacy indexes).
            namespace: Optional Pinecone namespace.
        """
        if embedder is None:
            raise ProviderConnectionError(
                message="PineconeRetriever requires an embedder (set retriever.embedder)",
                provider_name=self.name,
            )
        self._index_name = index_name
        self._embedder = embedder
        self._namespace = namespace

        try:
            import pinecone
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "pinecone-client is required for the pinecone retriever. "
                "Install it with: pip install openagent-eval[pinecone]"
            ) from exc

        try:
            pc = pinecone.Pinecone(api_key=api_key, environment=environment)
            self._index = pc.Index(index_name)
        except Exception as exc:
            raise ProviderConnectionError(
                message=f"Failed to connect to Pinecone index '{index_name}': {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Embed the query and query the Pinecone index."""
        self.validate_inputs(query=query, k=k)
        try:
            vector = await self._embedder.embed_query(query)
            response = self._index.query(
                vector=vector,
                top_k=k,
                namespace=self._namespace,
                include_metadata=True,
            )
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"Pinecone query failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        documents: list[Document] = []
        for match in response.get("matches", []):
            metadata = match.get("metadata", {}) or {}
            documents.append(
                Document(
                    content=str(metadata.get("content", "")),
                    metadata={k: v for k, v in metadata.items() if k != "content"},
                    score=max(0.0, min(1.0, float(match.get("score", 0.0)))),
                    id=str(match.get("id")),
                )
            )
        return documents

"""Weaviate retriever adapter for OpenAgent Eval.

Performs hybrid/near-text search against a Weaviate collection. Weaviate can
embed the query server-side (when the collection uses a ``text2vec`` module),
so an embedder is optional here; if one is supplied it is used to embed the
query locally instead. Scores come from Weaviate ``certainty`` (already in
``[0, 1]``).
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


class WeaviateRetriever(Retriever):
    """Weaviate retriever (near-text / hybrid search)."""

    name: str = "weaviate"
    description: str = "Weaviate vector database retriever"

    def __init__(
        self,
        collection: str,
        embedder: Embedder | None = None,
        url: str | None = None,
        api_key: str | None = None,
        **_: Any,
    ) -> None:
        """Initialize the Weaviate retriever.

        Args:
            collection: Weaviate collection (class) name.
            embedder: Optional local embedder; if omitted, Weaviate embeds the
                query server-side via its configured vectorizer.
            url: Weaviate REST URL (omit to read ``WEAVIATE_URL`` env).
            api_key: Weaviate API key (omit to read ``WEAVIATE_API_KEY`` env).
        """
        self._collection = collection
        self._embedder = embedder

        try:
            import weaviate
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "weaviate-client is required for the weaviate retriever. "
                "Install it with: pip install openagent-eval[weaviate]"
            ) from exc

        try:
            if url:
                self._client = weaviate.connect_to_local(
                    host=url.replace("http://", "").replace("https://", ""),
                    auth_credentials=weaviate.auth.AuthApiKey(api_key) if api_key else None,
                ) if "localhost" in url else weaviate.connect_to_weaviate_cloud(
                    cluster_url=url, auth_credentials=weaviate.auth.AuthApiKey(api_key)
                )
            else:
                self._client = weaviate.connect_to_local(
                    auth_credentials=weaviate.auth.AuthApiKey(api_key) if api_key else None
                )
        except Exception as exc:
            raise ProviderConnectionError(
                message=f"Failed to connect to Weaviate: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Search the Weaviate collection near the query text."""
        self.validate_inputs(query=query, k=k)
        try:
            collection = self._client.collections.get(self._collection)
            response = collection.query.near_text(query=query, limit=k)
            objects = response.objects
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"Weaviate query failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        documents: list[Document] = []
        for obj in objects:
            props = obj.properties or {}
            documents.append(
                Document(
                    content=str(props.get("content", "")),
                    metadata={k: v for k, v in props.items() if k != "content"},
                    score=max(0.0, min(1.0, float(getattr(obj, "certainty", 0.0) or 0.0))),
                    id=str(obj.uuid),
                )
            )
        return documents

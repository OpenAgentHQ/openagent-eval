"""Elasticsearch retriever adapter for OpenAgent Eval.

Supports both lexical (``multi_match`` on ``content``) and kNN vector search.
Lexical ``_score`` values are unbounded, so they are min-max normalized into
``[0, 1]``. For kNN, the configured
:class:`~openagent_eval.providers.embedders.base.Embedder` supplies the query
vector.
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
from openagent_eval.providers.retrievers._scoring import minmax_normalize


class ElasticsearchRetriever(Retriever):
    """Elasticsearch retriever (lexical or kNN)."""

    name: str = "elasticsearch"
    description: str = "Elasticsearch lexical/kNN retriever"

    def __init__(
        self,
        index: str,
        embedder: Embedder | None = None,
        hosts: str | list[str] | None = None,
        api_key: str | None = None,
        vector_field: str | None = None,
        content_field: str = "content",
        mode: str = "lexical",
        **_: Any,
    ) -> None:
        """Initialize the Elasticsearch retriever.

        Args:
            index: Elasticsearch index name.
            embedder: Required only for ``mode="knn"``.
            hosts: ES host(s) (or ``ELASTICSEARCH_HOSTS`` env).
            api_key: ES API key (or ``ELASTICSEARCH_API_KEY`` env).
            vector_field: Field holding the dense vector (knn mode).
            content_field: Field holding document text.
            mode: ``"lexical"`` (default, BM25) or ``"knn"``.
        """
        self._index = index
        self._embedder = embedder
        self._vector_field = vector_field
        self._content_field = content_field
        self._mode = mode
        if mode == "knn" and embedder is None:
            raise ProviderConnectionError(
                message="ElasticsearchRetriever in knn mode requires an embedder",
                provider_name=self.name,
            )

        try:
            from elasticsearch import Elasticsearch
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "elasticsearch is required for the elasticsearch retriever. "
                "Install it with: pip install openagent-eval[elasticsearch]"
            ) from exc

        try:
            self._client = Elasticsearch(hosts=hosts, api_key=api_key)
        except Exception as exc:
            raise ProviderConnectionError(
                message=f"Failed to connect to Elasticsearch: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Run a lexical or kNN search and normalize scores."""
        self.validate_inputs(query=query, k=k)
        try:
            if self._mode == "knn":
                vector = await self._embedder.embed_query(query)
                body = {
                    "knn": {
                        "field": self._vector_field,
                        "query_vector": vector,
                        "k": k,
                        "num_candidates": max(50, k * 10),
                    },
                    "_source": [self._content_field],
                }
            else:
                body = {
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": [self._content_field],
                        }
                    },
                    "size": k,
                    "_source": [self._content_field],
                }
            resp = self._client.search(index=self._index, **body)
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"Elasticsearch query failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return []

        raw_scores = [float(hit.get("_score", 0.0)) for hit in hits]
        norm = minmax_normalize(raw_scores)

        documents: list[Document] = []
        for hit, score in zip(hits, norm):
            source = hit.get("_source", {})
            documents.append(
                Document(
                    content=str(source.get(self._content_field, "")),
                    metadata=source,
                    score=score,
                    id=hit.get("_id"),
                )
            )
        return documents

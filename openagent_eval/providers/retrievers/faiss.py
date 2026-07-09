"""FAISS retriever adapter for OpenAgent Eval.

Builds (or loads) a local FAISS index from documents embedded with the
configured :class:`~openagent_eval.providers.embedders.base.Embedder` and
performs fast approximate/exact similarity search in process.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.embedders.base import Embedder
from openagent_eval.providers.models import Document


class FAISSRetriever(Retriever):
    """Local FAISS (faiss-cpu) dense vector retriever."""

    name: str = "faiss"
    description: str = "FAISS local vector index retriever"

    def __init__(
        self,
        documents: list[dict[str, Any]] | None = None,
        embedder: Embedder | None = None,
        index_path: str | None = None,
        metric: str = "l2",
        k: int = 5,
        **_: Any,
    ) -> None:
        """Initialize the FAISS retriever.

        Args:
            documents: Documents to index (``{"content", "metadata"?, "id"?}``).
            embedder: Required embedder for query/document vectors.
            index_path: Optional path to a prebuilt ``.index`` file to load
                instead of building from ``documents``.
            metric: ``"l2"`` or ``"ip"`` (inner product / cosine when normalized).
            k: Default number of results.
        """
        if embedder is None:
            raise ProviderConnectionError(
                message="FAISSRetriever requires an embedder (set retriever.embedder)",
                provider_name=self.name,
            )
        self._embedder = embedder
        self._raw_docs = documents or []
        self._index_path = index_path
        self._metric = metric
        self._k = k
        self._index = None
        self._docs: list[Document] = []

    async def _ensure_index(self) -> None:
        """Build or load the FAISS index."""
        if self._index is not None:
            return
        try:
            import faiss
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "faiss-cpu is required for the faiss retriever. "
                "Install it with: pip install openagent-eval[faiss]"
            ) from exc

        try:
            if self._index_path:
                self._index = faiss.read_index(self._index_path)
                self._docs = []  # metadata not stored in the index file
            else:
                texts = [d.get("content", "") for d in self._raw_docs]
                vectors = np.asarray(
                    await self._embedder.embed(texts), dtype="float32"
                )
                dim = vectors.shape[1]
                self._index = (
                    faiss.IndexFlatL2(dim)
                    if self._metric == "l2"
                    else faiss.IndexFlatIP(dim)
                )
                if vectors.shape[0]:
                    self._index.add(vectors)
                self._docs = [
                    Document(
                        content=d.get("content", ""),
                        metadata=d.get("metadata", {}) or {},
                        id=d.get("id"),
                    )
                    for d in self._raw_docs
                ]
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"Failed to build/load FAISS index: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Embed the query and search the FAISS index."""
        self.validate_inputs(query=query, k=k)
        k = k or self._k
        await self._ensure_index()
        if self._index is None or self._index.ntotal == 0:
            return []

        try:
            qvec = np.asarray(
                [await self._embedder.embed_query(query)], dtype="float32"
            )
            scores, indices = self._index.search(qvec, min(k, self._index.ntotal))
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"FAISS search failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        documents: list[Document] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            # FAISS returns distances; normalize to [0,1] (higher = better).
            norm = 1.0 / (1.0 + float(score)) if self._metric == "l2" else float(score)
            doc = self._docs[idx] if idx < len(self._docs) else None
            documents.append(
                Document(
                    content=doc.content if doc else "",
                    metadata=doc.metadata if doc else {},
                    score=max(0.0, min(1.0, norm)),
                    id=doc.id if doc else str(idx),
                )
            )
        return documents

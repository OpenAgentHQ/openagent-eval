"""In-memory vector retriever for OpenAgent Eval.

A dependency-light vector store that embeds documents with a configured
:class:`~openagent_eval.providers.embedders.base.Embedder` and performs cosine
similarity search entirely in process (using NumPy). No external service or
native vector library is required, which makes it ideal for local RAG
evaluation and quick experiments with ``sentence-transformers``.
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


def _load_documents(path: str | None) -> list[dict[str, Any]]:
    """Load documents from a JSON list or JSONL file."""
    if not path:
        return []
    import json

    with open(path, encoding="utf-8") as fh:
        if path.endswith(".jsonl"):
            return [json.loads(line) for line in fh if line.strip()]
        data = json.load(fh)
    return data if isinstance(data, list) else []


class MemoryRetriever(Retriever):
    """Process-local dense vector retriever backed by an embedder.

    Documents are supplied at construction time (``documents``) and embedded
    lazily on the first query. Queries are embedded with the same embedder and
    ranked by cosine similarity.

    Example:
        ```python
        retriever = MemoryRetriever(
            documents=[
                {"content": "Python is a language", "id": "1"},
                {"content": "RAG combines retrieval and generation", "id": "2"},
            ],
            embedder=SentenceTransformerEmbedder(),
        )
        docs = await retriever.retrieve("What is RAG?", k=1)
        ```
    """

    name: str = "memory"
    description: str = "In-memory cosine-similarity vector retriever (NumPy)"

    def __init__(
        self,
        documents: list[dict[str, Any]] | None = None,
        documents_path: str | None = None,
        embedder: Embedder | None = None,
        k: int = 5,
        **_: Any,
    ) -> None:
        """Initialize the in-memory retriever.

        Args:
            documents: List of ``{"content": str, "metadata"?: dict,
                "id"?: str}`` dicts to index.
            documents_path: Optional path to a JSON list or JSONL file of
                documents (used when ``documents`` is not supplied).
            embedder: Required embedder used for both documents and queries.
            k: Default number of results to return.

        Raises:
            ProviderConnectionError: If no embedder is supplied (vector
                retrieval is impossible without one).
        """
        if embedder is None:
            raise ProviderConnectionError(
                message="MemoryRetriever requires an embedder (set retriever.embedder)",
                provider_name=self.name,
            )
        self._embedder = embedder
        self._k = k
        self._raw_docs = documents or _load_documents(documents_path)
        self._indexed = False
        self._matrix: np.ndarray | None = None
        self._docs: list[Document] = []

    async def _ensure_index(self) -> None:
        """Embed and index documents on first use."""
        if self._indexed:
            return
        if not self._raw_docs:
            self._indexed = True
            self._matrix = np.zeros((0, 0), dtype="float32")
            return
        try:
            texts = [d.get("content", "") for d in self._raw_docs]
            vectors = await self._embedder.embed(texts)
            self._matrix = np.asarray(vectors, dtype="float32")
            self._docs = [
                Document(
                    content=d.get("content", ""),
                    metadata=d.get("metadata", {}) or {},
                    id=d.get("id"),
                )
                for d in self._raw_docs
            ]
            self._indexed = True
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"Failed to build in-memory index: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Retrieve the ``k`` most similar documents to ``query``.

        Args:
            query: The search query.
            k: Number of documents to return (defaults to the constructor ``k``).

        Returns:
            Up to ``k`` ``Document`` objects ranked by cosine similarity
            (score in ``[0, 1]``).
        """
        self.validate_inputs(query=query, k=k)
        k = k or self._k
        await self._ensure_index()

        if self._matrix is None or self._matrix.shape[0] == 0:
            return []

        try:
            query_vec = np.asarray(
                await self._embedder.embed_query(query), dtype="float32"
            )
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"Failed to embed query: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        # Cosine similarity (vectors are L2-normalized by the embedder).
        sims = self._matrix @ query_vec
        if np.linalg.norm(query_vec) == 0:
            sims = np.zeros_like(sims)

        top_k = min(k, len(self._docs))
        if top_k == 0:
            return []
        order = np.argsort(-sims)[:top_k]

        results: list[Document] = []
        for idx in order:
            score = float(sims[idx])
            doc = self._docs[idx]
            results.append(
                Document(
                    content=doc.content,
                    metadata=doc.metadata,
                    score=max(0.0, min(1.0, score)),
                    id=doc.id,
                )
            )
        return results

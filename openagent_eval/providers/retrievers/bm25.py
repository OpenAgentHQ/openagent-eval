"""BM25 lexical retriever for OpenAgent Eval.

A classic keyword/lexical baseline using ``rank-bm25``. Unlike dense vector
retrievers it needs no embeddings and often serves as the comparison baseline
in RAG evaluations (does the expensive vector retriever actually beat BM25?).
Scores are min-max normalized into ``[0, 1]``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document
from openagent_eval.providers.retrievers._scoring import minmax_normalize


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


class BM25Retriever(Retriever):
    """In-memory BM25 retriever (``rank-bm25``)."""

    name: str = "bm25"
    description: str = "BM25 lexical retriever (rank-bm25)"

    def __init__(
        self,
        documents: list[dict[str, Any]] | None = None,
        documents_path: str | None = None,
        k: int = 5,
        tokenizer: str = "whitespace",
        **_: Any,
    ) -> None:
        """Initialize the BM25 retriever.

        Args:
            documents: List of ``{"content": str, "metadata"?: dict,
                "id"?: str}`` dicts to index.
            documents_path: Optional path to a JSON list or JSONL file of
                documents (used when ``documents`` is not supplied).
            k: Default number of results to return.
            tokenizer: ``"whitespace"`` (default) or ``"simple"`` lowercasing.
        """
        self._raw_docs = documents or _load_documents(documents_path)
        self._k = k
        self._tokenizer = tokenizer
        self._indexed = False
        self._bm25 = None
        self._docs: list[Document] = []

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text for BM25 indexing/querying."""
        if self._tokenizer == "simple":
            return text.lower().split()
        return text.split()

    async def _ensure_index(self) -> None:
        """Build the BM25 index on first use."""
        if self._indexed:
            return
        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "rank-bm25 is required for the bm25 retriever. "
                "Install it with: pip install openagent-eval[bm25]"
            ) from exc

        try:
            if not self._raw_docs:
                # BM25Okapi([]) raises ZeroDivisionError; an empty corpus is
                # valid (just returns no results) so handle it gracefully.
                self._bm25 = None
                self._docs = []
                self._indexed = True
                return
            corpus = [self._tokenize(d.get("content", "")) for d in self._raw_docs]
            self._bm25 = BM25Okapi(corpus)
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
                message=f"Failed to build BM25 index: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Retrieve the ``k`` highest BM25-scoring documents."""
        self.validate_inputs(query=query, k=k)
        k = k or self._k
        await self._ensure_index()

        if self._bm25 is None or not self._docs:
            return []

        try:
            # get_scores returns a numpy array; convert to a plain list so the
            # shared min-max normalizer (which checks `if not scores`) works.
            raw_scores = self._bm25.get_scores(self._tokenize(query)).tolist()
            norm = minmax_normalize(raw_scores)
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"BM25 scoring failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        top_k = min(k, len(self._docs))
        if top_k == 0:
            return []
        order = np.argsort(-np.asarray(raw_scores))[:top_k]

        return [
            Document(
                content=self._docs[idx].content,
                metadata=self._docs[idx].metadata,
                score=norm[idx],
                id=self._docs[idx].id,
            )
            for idx in order
        ]

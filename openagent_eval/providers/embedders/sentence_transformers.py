"""Sentence-Transformers embedder adapter.

Wraps ``sentence-transformers`` to produce dense vectors. Defaults to the
lightweight, general-purpose ``all-MiniLM-L6-v2`` model (384 dimensions),
which is a good default for local RAG evaluation without API calls.
"""

from __future__ import annotations

import asyncio
from typing import Any

from openagent_eval.providers.embedders.base import Embedder


class SentenceTransformerEmbedder(Embedder):
    """Dense embedder backed by ``sentence-transformers``.

    Example:
        ```python
        embedder = SentenceTransformerEmbedder(model="all-MiniLM-L6-v2")
        vec = await embedder.embed_query("What is RAG?")
        ```
    """

    name: str = "sentence_transformers"
    description: str = "sentence-transformers dense embedding model"

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        device: str | None = None,
        **_: Any,
    ) -> None:
        """Initialize the embedder.

        Args:
            model: Model identifier (default ``all-MiniLM-L6-v2``).
            device: Optional torch device (e.g. ``"cpu"``, ``"cuda"``).
                Defaults to the sentence-transformers default.
        """
        self.model_name = model
        self.device = device

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "sentence-transformers is required for this embedder. "
                "Install it with: pip install openagent-eval[evaluation] "
                "or pip install sentence-transformers"
            ) from exc

        self._model = SentenceTransformer(model, device=device)
        if hasattr(self._model, "get_embedding_dimension"):
            self.dimension = self._model.get_embedding_dimension()
        else:  # pragma: no cover - older sentence-transformers
            self.dimension = self._model.get_sentence_embedding_dimension()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts (runs the sync model in a worker thread)."""
        self.validate_inputs(text=texts[0] if texts else "")
        vectors = await asyncio.to_thread(
            self._model.encode,
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return [vec.tolist() for vec in vectors]

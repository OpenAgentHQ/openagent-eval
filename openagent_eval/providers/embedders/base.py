"""Base embedder interface for OpenAgent Eval.

Every embedder converts text into fixed-dimensional dense vectors. Retrievers
that do not embed server-side (e.g. FAISS, Qdrant, Pinecone, pgvector, the
in-memory vector store) use an :class:`Embedder` to turn queries and documents
into vectors before similarity search.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Embedder(ABC):
    """Abstract base class for text embedders.

    Implementations must expose ``embed`` (batch) and may override
    ``embed_query`` (single string). All vectors are lists of floats of a
    fixed ``dimension``.
    """

    name: str
    description: str
    dimension: int | None = None

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into vectors.

        Args:
            texts: List of input strings.

        Returns:
            List of vectors, one per input text, each of length ``dimension``.
        """
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string.

        Default implementation delegates to :meth:`embed`. Override for
        query-specific prompting (e.g. instruction-tuned models).

        Args:
            text: The query string.

        Returns:
            A single vector of length ``dimension``.
        """
        vectors = await self.embed([text])
        return vectors[0]

    def validate_inputs(self, **kwargs: Any) -> None:
        """Optional input validation hook."""
        text = kwargs.get("text")
        if text is not None and not isinstance(text, str):
            raise ValueError(f"text must be a string, got {type(text).__name__}")

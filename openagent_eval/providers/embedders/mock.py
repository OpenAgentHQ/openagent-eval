"""Deterministic mock embedder for offline tests and dry-runs.

Produces stable, normalized vectors from a hash of the input text so that
identical strings map to identical vectors (enabling cosine similarity checks
in tests) without downloading any model or making network calls.
"""

from __future__ import annotations

import hashlib
import struct
from typing import Any

from openagent_eval.providers.embedders.base import Embedder


class MockEmbedder(Embedder):
    """Hash-based deterministic embedder (no model, no network)."""

    name: str = "mock"
    description: str = "Deterministic hash-based embedder for testing"

    def __init__(self, dimension: int = 32, **_: Any) -> None:
        """Initialize the mock embedder.

        Args:
            dimension: Vector dimensionality (default 32).
        """
        self.dimension = dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return deterministic normalized vectors for each input text."""
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        """Build a normalized vector from a SHA-256 hash of the text."""
        dim = self.dimension
        raw: list[float] = []
        for i in range(dim):
            digest = hashlib.sha256(f"{i}:{text}".encode("utf-8")).digest()
            value = (struct.unpack("!H", digest[:2])[0] / 65535.0) * 2.0 - 1.0
            raw.append(value)
        norm = (sum(v * v for v in raw) ** 0.5) or 1.0
        return [v / norm for v in raw]

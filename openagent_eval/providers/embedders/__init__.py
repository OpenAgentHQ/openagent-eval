"""Embedder adapters for OpenAgent Eval.

This package contains embedder adapters that implement the
:class:`~openagent_eval.providers.embedders.base.Embedder` interface. Each
adapter integrates with a specific embedding backend (sentence-transformers,
etc.). Imports are lazy so optional dependencies are only required when used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openagent_eval.providers.embedders.base import Embedder
    from openagent_eval.providers.embedders.mock import MockEmbedder
    from openagent_eval.providers.embedders.sentence_transformers import (
        SentenceTransformerEmbedder,
    )


def __getattr__(name: str):
    """Lazy import of embedder classes to avoid requiring optional deps."""
    if name == "Embedder":
        from openagent_eval.providers.embedders.base import Embedder
        return Embedder
    if name == "SentenceTransformerEmbedder":
        from openagent_eval.providers.embedders.sentence_transformers import (
            SentenceTransformerEmbedder,
        )
        return SentenceTransformerEmbedder
    if name == "MockEmbedder":
        from openagent_eval.providers.embedders.mock import MockEmbedder
        return MockEmbedder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["Embedder", "SentenceTransformerEmbedder", "MockEmbedder"]

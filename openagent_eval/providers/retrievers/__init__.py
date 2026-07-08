"""Retriever provider adapters.

This package contains retriever provider adapters that implement the Retriever
interface. Each adapter integrates with a specific vector database or search
engine (Chroma, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openagent_eval.providers.retrievers.chroma import ChromaRetriever


def __getattr__(name: str):
    """Lazy import of retriever classes to avoid requiring all optional dependencies."""
    if name == "ChromaRetriever":
        from openagent_eval.providers.retrievers.chroma import ChromaRetriever
        return ChromaRetriever
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ChromaRetriever"]

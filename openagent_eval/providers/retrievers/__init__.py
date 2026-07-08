"""Retriever provider adapters.

This package contains retriever provider adapters that implement the Retriever
interface. Each adapter integrates with a specific vector database or search
engine (Chroma, etc.).
"""

from openagent_eval.providers.retrievers.chroma import ChromaRetriever

__all__ = ["ChromaRetriever"]

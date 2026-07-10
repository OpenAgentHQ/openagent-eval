"""ChromaDB retriever adapter for document retrieval.

This module implements the Retriever interface for ChromaDB, providing
vector-based document retrieval with configurable distance functions.
ChromaDB handles embedding and storage, while this adapter exposes
a clean async interface compatible with the OpenAgent Eval evaluation pipeline.

Example:
    ```python
    from openagent_eval.providers.retrievers.chroma import ChromaRetriever

    retriever = ChromaRetriever(
        collection_name="my_docs",
        persist_directory="./chroma_db",
        distance_fn="cosine",
    )
    results = await retriever.retrieve("machine learning", k=5)
    ```
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document
from openagent_eval.providers.retrievers._scoring import normalize_distance

logger = logging.getLogger(__name__)


class ChromaRetriever(Retriever):
    """ChromaDB-backed document retriever.

    Connects to a ChromaDB collection (persistent or in-memory) and retrieves
    relevant documents for a given query. The collection is initialized or
    connected in the constructor, so callers should create one retriever instance
    per collection.

    Attributes:
        name: Identifier for this retriever type ("chroma").
        description: Human-readable description of the retriever.
        collection_name: Name of the ChromaDB collection.
        distance_fn: Distance function used for similarity ranking.

    Example:
        ```python
        retriever = ChromaRetriever(
            collection_name="knowledge_base",
            persist_directory="./data/chroma",
            distance_fn="l2",
        )
        docs = await retriever.retrieve("What is RAG?", k=3)
        for doc in docs:
            print(f"{doc.score:.3f} - {doc.content[:80]}...")
        ```
    """

    name: str = "chroma"
    description: str = "ChromaDB vector-based document retriever"

    def __init__(
        self,
        collection_name: str,
        persist_directory: str | None = None,
        distance_fn: str = "cosine",
    ) -> None:
        """Initialize the ChromaDB retriever.

        Args:
            collection_name: Name of the ChromaDB collection to query.
            persist_directory: Directory for persistent storage. If None,
                uses an in-memory client.
            distance_fn: Distance function for similarity search.
                Supported values: "l2", "ip", "cosine".

        Raises:
            ProviderConnectionError: If the ChromaDB client or collection
                cannot be initialized.
        """
        self.collection_name = collection_name
        self.distance_fn = distance_fn

        try:
            if persist_directory:
                settings = Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
                self._client = chromadb.PersistentClient(
                    path=persist_directory,
                    settings=settings,
                )
            else:
                self._client = chromadb.Client()

            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": distance_fn},
            )
            logger.info(
                "ChromaDB collection '%s' connected (distance=%s)",
                collection_name,
                distance_fn,
            )
        except Exception as exc:
            raise ProviderConnectionError(
                message=f"Failed to initialize ChromaDB client or collection '{collection_name}'",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Retrieve relevant documents for a given query.

        Args:
            query: The search query string.
            k: Number of documents to retrieve (default: 5).

        Returns:
            List of Document objects ranked by similarity. Each document
            contains content, metadata, a similarity score (distance), and
            an identifier.

        Raises:
            ProviderExecutionError: If the ChromaDB query fails.
        """
        self.validate_inputs(query=query, k=k)

        # ChromaDB raises if n_results exceeds the number of documents in the
        # collection, which is common for small eval fixtures. Clamp it.
        collection_count = self._collection.count()
        safe_k = min(k, collection_count) if collection_count > 0 else k

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=safe_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"ChromaDB query failed for collection '{self.collection_name}'",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        documents: list[Document] = []

        # ChromaDB returns nested lists; unpack the single query result.
        ids_list: list[list[str]] = results.get("ids", [[]])
        docs_list: list[list[str]] = results.get("documents", [[]])
        metas_list: list[list[dict[str, Any]]] = results.get("metadatas", [[]])
        dists_list: list[list[float]] = results.get("distances", [[]])

        if not ids_list or not ids_list[0]:
            return documents

        for doc_id, content, metadata, distance in zip(
            ids_list[0],
            docs_list[0],
            metas_list[0],
            dists_list[0],
            strict=True,
        ):
            # ChromaDB distances are raw; normalise to 0-1 range when possible.
            score = normalize_distance(distance, space=self.distance_fn)
            documents.append(
                Document(
                    content=content,
                    metadata=metadata or {},
                    score=score,
                    id=doc_id,
                )
            )

        logger.debug(
            "Retrieved %d documents from '%s' for query '%s'",
            len(documents),
            self.collection_name,
            query[:50],
        )
        return documents

"""Base retriever interface for document retrieval providers.

This module defines the abstract Retriever interface that all document retrieval
providers must implement. Retriever providers are responsible for finding relevant
documents given a query string.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openagent_eval.providers.base.models import Document


class Retriever(ABC):
    """Abstract base class for all document retrieval providers.

    Every retriever in OpenAgent Eval must implement this interface. The retriever
    receives a query string and returns a list of relevant Document objects.

    Interface Contract:
        - The `retrieve` method must be implemented by all subclasses
        - The `name` attribute must be set to a unique identifier
        - The `description` attribute must provide a human-readable description
        - The method should raise ProviderExecutionError on retrieval failures
        - Input validation is optional but recommended via validate_inputs()

    Example:
        ```python
        class MyRetriever(Retriever):
            name = "my_retriever"
            description = "A custom document retriever"

            async def retrieve(self, query: str, k: int = 5) -> list[Document]:
                # Implementation here
                return documents
        ```
    """

    name: str
    description: str

    @abstractmethod
    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Retrieve relevant documents for a given query.

        Args:
            query: The search query string.
            k: Number of documents to retrieve (default: 5).

        Returns:
            List of Document objects matching the query.

        Raises:
            ProviderExecutionError: If retrieval fails due to provider issues.
            ProviderError: If provider is not configured or unavailable.
        """
        ...

    def validate_inputs(self, **kwargs: object) -> None:
        """Validate retriever inputs before retrieval.

        Override this method to add custom input validation. The default
        implementation does nothing.

        Args:
            **kwargs: Inputs to validate.

        Raises:
            ValueError: If inputs are invalid.
        """
        query = kwargs.get("query")
        if query is not None and not isinstance(query, str):
            raise ValueError(f"Query must be a string, got {type(query).__name__}")

        k = kwargs.get("k")
        if k is not None:
            if not isinstance(k, int):
                raise ValueError(f"k must be an integer, got {type(k).__name__}")
            if k < 1:
                raise ValueError(f"k must be positive, got {k}")

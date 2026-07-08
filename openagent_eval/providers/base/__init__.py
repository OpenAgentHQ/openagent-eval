"""Base interfaces for provider adapters.

This package contains the abstract base classes that all provider adapters
must implement: LLMProvider for LLM integrations and Retriever for
document retrieval integrations.
"""

from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.base.retriever import Retriever

__all__ = ["LLMProvider", "Retriever"]

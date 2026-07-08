"""LLM provider adapters.

This package contains LLM provider adapters that implement the LLMProvider interface.
Each adapter integrates with a specific LLM API (OpenAI, Gemini, Anthropic, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openagent_eval.providers.llm.anthropic import Anthropic
    from openagent_eval.providers.llm.gemini import Gemini
    from openagent_eval.providers.llm.groq import Groq
    from openagent_eval.providers.llm.ollama import Ollama
    from openagent_eval.providers.llm.openai import OpenAIProvider
    from openagent_eval.providers.llm.openrouter import OpenRouter


def __getattr__(name: str):
    """Lazy import of provider classes to avoid requiring all optional dependencies."""
    if name == "Anthropic":
        from openagent_eval.providers.llm.anthropic import Anthropic
        return Anthropic
    elif name == "Gemini":
        from openagent_eval.providers.llm.gemini import Gemini
        return Gemini
    elif name == "Groq":
        from openagent_eval.providers.llm.groq import Groq
        return Groq
    elif name == "Ollama":
        from openagent_eval.providers.llm.ollama import Ollama
        return Ollama
    elif name == "OpenAIProvider":
        from openagent_eval.providers.llm.openai import OpenAIProvider
        return OpenAIProvider
    elif name == "OpenRouter":
        from openagent_eval.providers.llm.openrouter import OpenRouter
        return OpenRouter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Anthropic",
    "Gemini",
    "Groq",
    "Ollama",
    "OpenAIProvider",
    "OpenRouter",
]

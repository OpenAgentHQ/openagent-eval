"""LLM provider adapters.

This package contains LLM provider adapters that implement the LLMProvider interface.
Each adapter integrates with a specific LLM API (OpenAI, Gemini, Anthropic, etc.).
"""

from openagent_eval.providers.llm.anthropic import Anthropic
from openagent_eval.providers.llm.gemini import Gemini
from openagent_eval.providers.llm.groq import Groq
from openagent_eval.providers.llm.ollama import Ollama
from openagent_eval.providers.llm.openai import OpenAIProvider
from openagent_eval.providers.llm.openrouter import OpenRouter

__all__ = [
    "Anthropic",
    "Gemini",
    "Groq",
    "Ollama",
    "OpenAIProvider",
    "OpenRouter",
]

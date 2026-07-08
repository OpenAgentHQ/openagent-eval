"""Tests for LLMProvider and Retriever ABCs, and model validation."""

from __future__ import annotations

import pytest

from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document, LLMResponse, TokenUsage


# ---------------------------------------------------------------------------
# TokenUsage tests
# ---------------------------------------------------------------------------
class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_create_with_valid_values(self):
        """TokenUsage creates with valid token counts."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30

    def test_create_with_zero_tokens(self):
        """TokenUsage accepts zero tokens."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_negative_prompt_tokens_raises(self):
        """TokenUsage rejects negative prompt_tokens."""
        with pytest.raises(ValueError, match="non-negative"):
            TokenUsage(prompt_tokens=-1, completion_tokens=0, total_tokens=0)

    def test_negative_completion_tokens_raises(self):
        """TokenUsage rejects negative completion_tokens."""
        with pytest.raises(ValueError, match="non-negative"):
            TokenUsage(prompt_tokens=0, completion_tokens=-1, total_tokens=0)

    def test_negative_total_tokens_raises(self):
        """TokenUsage rejects negative total_tokens."""
        with pytest.raises(ValueError, match="non-negative"):
            TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=-1)

    def test_frozen_model(self):
        """TokenUsage is immutable."""
        usage = TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3)
        with pytest.raises(Exception):
            usage.prompt_tokens = 10  # type: ignore[misc]


# ---------------------------------------------------------------------------
# LLMResponse tests
# ---------------------------------------------------------------------------
class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_create_with_valid_values(self):
        """LLMResponse creates with all required fields."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        response = LLMResponse(
            content="Hello",
            model="gpt-4o",
            usage=usage,
            provider="openai",
            latency_ms=150.0,
        )
        assert response.content == "Hello"
        assert response.model == "gpt-4o"
        assert response.provider == "openai"
        assert response.latency_ms == 150.0

    def test_empty_content_allowed(self):
        """LLMResponse allows empty content string."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        response = LLMResponse(
            content="",
            model="gpt-4o",
            usage=usage,
            provider="openai",
            latency_ms=0.0,
        )
        assert response.content == ""

    def test_model_whitespace_stripped(self):
        """LLMResponse strips whitespace from model."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        response = LLMResponse(
            content="x",
            model="  gpt-4o  ",
            usage=usage,
            provider="openai",
            latency_ms=0.0,
        )
        assert response.model == "gpt-4o"

    def test_provider_lowercased_and_stripped(self):
        """LLMResponse lowercases and strips provider name."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        response = LLMResponse(
            content="x",
            model="gpt-4o",
            usage=usage,
            provider="  OpenAI  ",
            latency_ms=0.0,
        )
        assert response.provider == "openai"

    def test_empty_model_raises(self):
        """LLMResponse rejects empty model string."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        with pytest.raises(ValueError, match="Model identifier cannot be empty"):
            LLMResponse(
                content="x",
                model="   ",
                usage=usage,
                provider="openai",
                latency_ms=0.0,
            )

    def test_empty_provider_raises(self):
        """LLMResponse rejects empty provider string."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            LLMResponse(
                content="x",
                model="gpt-4o",
                usage=usage,
                provider="   ",
                latency_ms=0.0,
            )

    def test_negative_latency_raises(self):
        """LLMResponse rejects negative latency."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        with pytest.raises(Exception):
            LLMResponse(
                content="x",
                model="gpt-4o",
                usage=usage,
                provider="openai",
                latency_ms=-1.0,
            )

    def test_zero_latency_allowed(self):
        """LLMResponse accepts zero latency."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        response = LLMResponse(
            content="x",
            model="gpt-4o",
            usage=usage,
            provider="openai",
            latency_ms=0.0,
        )
        assert response.latency_ms == 0.0

    def test_frozen_model(self):
        """LLMResponse is immutable."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        response = LLMResponse(
            content="x",
            model="gpt-4o",
            usage=usage,
            provider="openai",
            latency_ms=0.0,
        )
        with pytest.raises(Exception):
            response.content = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Document tests
# ---------------------------------------------------------------------------
class TestDocument:
    """Tests for Document model."""

    def test_create_with_content_only(self):
        """Document creates with content only."""
        doc = Document(content="Hello world")
        assert doc.content == "Hello world"
        assert doc.metadata == {}
        assert doc.score is None
        assert doc.id is None

    def test_create_with_all_fields(self):
        """Document creates with all fields populated."""
        doc = Document(
            content="Machine learning basics",
            metadata={"source": "textbook", "page": 42},
            score=0.95,
            id="doc-001",
        )
        assert doc.content == "Machine learning basics"
        assert doc.metadata == {"source": "textbook", "page": 42}
        assert doc.score == 0.95
        assert doc.id == "doc-001"

    def test_score_boundary_zero(self):
        """Document accepts score of 0.0."""
        doc = Document(content="x", score=0.0)
        assert doc.score == 0.0

    def test_score_boundary_one(self):
        """Document accepts score of 1.0."""
        doc = Document(content="x", score=1.0)
        assert doc.score == 1.0

    def test_score_above_one_raises(self):
        """Document rejects score above 1.0."""
        with pytest.raises(ValueError, match="Score must be between"):
            Document(content="x", score=1.1)

    def test_score_below_zero_raises(self):
        """Document rejects score below 0.0."""
        with pytest.raises(ValueError, match="Score must be between"):
            Document(content="x", score=-0.1)

    def test_none_score_allowed(self):
        """Document allows None score."""
        doc = Document(content="x", score=None)
        assert doc.score is None

    def test_empty_metadata_default(self):
        """Document defaults to empty metadata dict."""
        doc = Document(content="x")
        assert doc.metadata == {}

    def test_frozen_model(self):
        """Document is immutable."""
        doc = Document(content="x")
        with pytest.raises(Exception):
            doc.content = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# LLMProvider ABC tests
# ---------------------------------------------------------------------------
class TestLLMProvider:
    """Tests for LLMProvider abstract base class."""

    def test_cannot_instantiate_directly(self):
        """LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_generate(self):
        """Subclass without generate raises TypeError."""

        class IncompleteProvider(LLMProvider):
            name = "incomplete"
            description = "Missing generate"

            async def get_token_count(self, text: str) -> int:
                return 0

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_get_token_count(self):
        """Subclass without get_token_count raises TypeError."""

        class IncompleteProvider(LLMProvider):
            name = "incomplete"
            description = "Missing get_token_count"

            async def generate(self, prompt: str, **kwargs):
                return "response"

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    def test_subclass_with_all_methods_works(self):
        """Subclass with all abstract methods can be instantiated."""

        class ValidProvider(LLMProvider):
            name = "valid"
            description = "A valid provider"

            async def generate(self, prompt: str, **kwargs):
                return "generated text"

            async def get_token_count(self, text: str) -> int:
                return len(text.split())

        provider = ValidProvider()
        assert provider.name == "valid"
        assert provider.description == "A valid provider"

    def test_validate_inputs_default(self):
        """validate_inputs does nothing by default."""

        class SimpleProvider(LLMProvider):
            name = "simple"
            description = "Simple provider"

            async def generate(self, prompt: str, **kwargs):
                return "ok"

            async def get_token_count(self, text: str) -> int:
                return 0

        provider = SimpleProvider()
        # Should not raise
        provider.validate_inputs(anything="value")


# ---------------------------------------------------------------------------
# Retriever ABC tests
# ---------------------------------------------------------------------------
class TestRetriever:
    """Tests for Retriever abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Retriever cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Retriever()  # type: ignore[abstract]

    def test_subclass_must_implement_retrieve(self):
        """Subclass without retrieve raises TypeError."""

        class IncompleteRetriever(Retriever):
            name = "incomplete"
            description = "Missing retrieve"

        with pytest.raises(TypeError):
            IncompleteRetriever()  # type: ignore[abstract]

    def test_subclass_with_retrieve_works(self):
        """Subclass with retrieve can be instantiated."""

        class ValidRetriever(Retriever):
            name = "valid"
            description = "A valid retriever"

            async def retrieve(self, query: str, k: int = 5):
                return [Document(content=query, score=1.0, id="doc-1")]

        retriever = ValidRetriever()
        assert retriever.name == "valid"
        assert retriever.description == "A valid retriever"

    def test_validate_inputs_query_not_string_raises(self):
        """validate_inputs rejects non-string query."""

        class SimpleRetriever(Retriever):
            name = "simple"
            description = "Simple retriever"

            async def retrieve(self, query: str, k: int = 5):
                return []

        retriever = SimpleRetriever()
        with pytest.raises(ValueError, match="Query must be a string"):
            retriever.validate_inputs(query=123)  # type: ignore[arg-type]

    def test_validate_inputs_k_not_int_raises(self):
        """validate_inputs rejects non-integer k."""

        class SimpleRetriever(Retriever):
            name = "simple"
            description = "Simple retriever"

            async def retrieve(self, query: str, k: int = 5):
                return []

        retriever = SimpleRetriever()
        with pytest.raises(ValueError, match="k must be an integer"):
            retriever.validate_inputs(query="test", k="five")  # type: ignore[arg-type]

    def test_validate_inputs_k_negative_raises(self):
        """validate_inputs rejects negative k."""

        class SimpleRetriever(Retriever):
            name = "simple"
            description = "Simple retriever"

            async def retrieve(self, query: str, k: int = 5):
                return []

        retriever = SimpleRetriever()
        with pytest.raises(ValueError, match="k must be positive"):
            retriever.validate_inputs(query="test", k=0)

    def test_validate_inputs_valid_query_and_k(self):
        """validate_inputs passes with valid query and k."""

        class SimpleRetriever(Retriever):
            name = "simple"
            description = "Simple retriever"

            async def retrieve(self, query: str, k: int = 5):
                return []

        retriever = SimpleRetriever()
        # Should not raise
        retriever.validate_inputs(query="test", k=5)

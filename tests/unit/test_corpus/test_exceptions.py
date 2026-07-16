"""Tests for corpus exceptions."""

from __future__ import annotations


from openagent_eval.exceptions.corpus import (
    CorpusAuditError,
    CorpusError,
    CorpusNotFoundError,
    CorpusValidationError,
)
from openagent_eval.exceptions.base import OpenAgentEvalError


class TestCorpusError:
    """Tests for CorpusError."""

    def test_inherits_from_base(self):
        """Test that CorpusError inherits from OpenAgentEvalError."""
        assert issubclass(CorpusError, OpenAgentEvalError)

    def test_create_with_message(self):
        """Test creating with just a message."""
        error = CorpusError(message="Test error")
        assert str(error) == "Test error"
        assert error.corpus_path is None

    def test_create_with_corpus_path(self):
        """Test creating with corpus path."""
        error = CorpusError(message="Test", corpus_path="/test/corpus")
        assert error.corpus_path == "/test/corpus"
        assert "/test/corpus" in str(error)

    def test_create_with_details(self):
        """Test creating with details dict."""
        error = CorpusError(
            message="Test",
            details={"key": "value"},
        )
        assert error.details["key"] == "value"


class TestCorpusNotFoundError:
    """Tests for CorpusNotFoundError."""

    def test_inherits_from_corpus_error(self):
        """Test inheritance."""
        assert issubclass(CorpusNotFoundError, CorpusError)

    def test_create(self):
        """Test creation."""
        error = CorpusNotFoundError(corpus_path="/missing/path")
        assert "not found" in str(error).lower()
        assert error.corpus_path == "/missing/path"


class TestCorpusValidationError:
    """Tests for CorpusValidationError."""

    def test_inherits_from_corpus_error(self):
        """Test inheritance."""
        assert issubclass(CorpusValidationError, CorpusError)

    def test_create_with_validation_errors(self):
        """Test creation with validation error list."""
        error = CorpusValidationError(
            message="Validation failed",
            validation_errors=["Error 1", "Error 2"],
        )
        assert len(error.validation_errors) == 2
        assert error.validation_errors[0] == "Error 1"


class TestCorpusAuditError:
    """Tests for CorpusAuditError."""

    def test_inherits_from_corpus_error(self):
        """Test inheritance."""
        assert issubclass(CorpusAuditError, CorpusError)

    def test_create_with_analyzer_name(self):
        """Test creation with analyzer name."""
        error = CorpusAuditError(
            message="Audit failed",
            analyzer_name="contradiction",
        )
        assert error.analyzer_name == "contradiction"
        assert "contradiction" in str(error)

    def test_create_with_original_error(self):
        """Test creation with original error."""
        original = ValueError("Original error")
        error = CorpusAuditError(
            message="Failed",
            original_error=original,
        )
        assert error.original_error is original
        assert "Original error" in str(error)

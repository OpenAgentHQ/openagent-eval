"""Base interface for corpus analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openagent_eval.corpus.models import AuditReport, CorpusDocument


class BaseCorpusAnalyzer(ABC):
    """Abstract base class for all corpus analyzers.

    Each analyzer detects a specific type of corpus health issue.
    The ``CorpusAuditor`` orchestrator runs multiple analyzers
    and aggregates their results into a single ``AuditReport``.

    Example:
        ```python
        class MyAnalyzer(BaseCorpusAnalyzer):
            name = "my_analyzer"
            description = "Detects X issues"

            async def analyze(self, documents, **kwargs):
                issues = ...
                return AuditReport(...)
        ```
    """

    name: str
    description: str

    @abstractmethod
    async def analyze(
        self,
        documents: list[CorpusDocument],
        **kwargs: Any,
    ) -> AuditReport:
        """Analyze the corpus and return an audit report.

        Args:
            documents: List of corpus documents to analyze.
            **kwargs: Analyzer-specific configuration.

        Returns:
            AuditReport containing detected issues and health score.

        Raises:
            CorpusAuditError: If analysis fails.
        """
        ...

    def validate_inputs(self, documents: list[CorpusDocument]) -> None:
        """Validate inputs before analysis.

        Override to add custom validation.

        Args:
            documents: Documents to validate.

        Raises:
            ValueError: If documents are invalid.
        """
        if not documents:
            raise ValueError("Cannot analyze an empty corpus")

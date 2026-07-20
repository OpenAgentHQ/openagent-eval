"""Corpus auditor orchestrator.

Runs all configured corpus analyzers and aggregates their results
into a single AuditReport.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from openagent_eval.corpus.base import BaseCorpusAnalyzer
from openagent_eval.corpus.contradiction import ContradictionDetector
from openagent_eval.corpus.coverage import CoverageAnalyzer
from openagent_eval.corpus.duplicates import DuplicateDetector
from openagent_eval.corpus.models import (
    AuditReport,
    CorpusDocument,
    CorpusIssue,
    IssueSeverity,
)
from openagent_eval.corpus.staleness import StalenessDetector
from openagent_eval.exceptions.corpus import (
    CorpusAuditError,
    CorpusNotFoundError,
    CorpusValidationError,
)

# Supported file extensions for document loading
_SUPPORTED_EXTENSIONS = {".txt", ".md", ".rst", ".html", ".json", ".jsonl"}


class CorpusAuditor:
    """Orchestrates corpus health auditing.

    Loads documents from a path, runs configured analyzers, and
    produces a unified AuditReport.

    Example:
        ```python
        auditor = CorpusAuditor(
            llm_provider=openai_provider,
            checks=["contradiction", "staleness"],
        )
        report = await auditor.audit("./knowledge_base/")
        print(report.health_score)
        ```
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        checks: list[str] | None = None,
        staleness_days: int = 365,
        similarity_threshold: float = 0.92,
        embedding_model: str = "all-MiniLM-L6-v2",
        max_documents: int = 1000,
    ) -> None:
        """Initialize the corpus auditor.

        Args:
            llm_provider: LLM provider for contradiction detection.
            checks: List of checks to perform (None = all).
            staleness_days: Days threshold for staleness detection.
            similarity_threshold: Similarity threshold for duplicate detection.
            embedding_model: Embedding model for duplicate/coverage detection.
            max_documents: Maximum documents to load.
        """
        self.llm_provider = llm_provider
        self.checks = checks
        self.staleness_days = staleness_days
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self.max_documents = max_documents

    async def audit(
        self,
        corpus_path: str,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> AuditReport:
        """Run a full corpus audit.

        Args:
            corpus_path: Path to the corpus directory or file.
            progress_callback: Optional callback for reporting audit progress.

        Returns:
            AuditReport with all detected issues.

        Raises:
            CorpusNotFoundError: If corpus path doesn't exist.
            CorpusAuditError: If audit process fails.
        """
        path = Path(corpus_path)

        if not path.exists():
            raise CorpusNotFoundError(corpus_path=corpus_path)

        # Build analyzer list
        analyzers = self._build_analyzers()
        total_steps = len(analyzers) + 1

        if progress_callback:
            progress_callback("Scanning documents...", 0, total_steps)

        # Load documents
        documents = self._load_documents(path)

        if not documents:
            raise CorpusValidationError(
                message=f"No readable documents found at {corpus_path}",
                corpus_path=corpus_path,
            )

        # Run analyzers
        reports: list[AuditReport] = []
        for i, analyzer in enumerate(analyzers):
            if progress_callback:
                progress_callback(f"Running: {analyzer.name}", i + 1, total_steps)
            try:
                report = await analyzer.analyze(documents)
                reports.append(report)
            except CorpusAuditError:
                raise
            except Exception as e:
                raise CorpusAuditError(
                    message=f"Analyzer '{analyzer.name}' failed: {e}",
                    corpus_path=corpus_path,
                    analyzer_name=analyzer.name,
                    original_error=e,
                ) from e

        if progress_callback:
            progress_callback("Audit complete!", total_steps, total_steps)

        # Merge reports
        return self._merge_reports(reports, corpus_path, len(documents))

    def _build_analyzers(self) -> list[BaseCorpusAnalyzer]:
        """Build the list of analyzers based on configuration.

        Returns:
            List of configured analyzer instances.
        """
        all_analyzers: dict[str, BaseCorpusAnalyzer] = {
            "contradiction": ContradictionDetector(
                llm_provider=self.llm_provider,
            ),
            "staleness": StalenessDetector(
                staleness_days=self.staleness_days,
            ),
            "duplicate": DuplicateDetector(
                similarity_threshold=self.similarity_threshold,
                embedding_model=self.embedding_model,
            ),
            "coverage": CoverageAnalyzer(
                embedding_model=self.embedding_model,
            ),
        }

        if self.checks is None:
            return list(all_analyzers.values())

        return [
            all_analyzers[name]
            for name in self.checks
            if name in all_analyzers
        ]

    def _load_documents(self, path: Path) -> list[CorpusDocument]:
        """Load documents from a directory or single file.

        Args:
            path: Path to corpus directory or file.

        Returns:
            List of CorpusDocument instances.
        """
        documents: list[CorpusDocument] = []

        if path.is_file():
            if path.suffix.lower() == ".jsonl":
                documents.extend(self._load_jsonl_documents(path))
            else:
                doc = self._load_single_file(path)
                if doc:
                    documents.append(doc)
        elif path.is_dir():
            files = sorted(path.rglob("*"))
            for file_path in files:
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in _SUPPORTED_EXTENSIONS
                ):
                    if file_path.suffix.lower() == ".jsonl":
                        documents.extend(self._load_jsonl_documents(file_path))
                    else:
                        doc = self._load_single_file(file_path)
                        if doc:
                            documents.append(doc)
                        if len(documents) >= self.max_documents:
                            break

        return documents

    def _load_single_file(self, file_path: Path) -> CorpusDocument | None:
        """Load a single file as a CorpusDocument.

        Args:
            file_path: Path to the file.

        Returns:
            CorpusDocument or None if loading fails.
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                return None

            # Use relative path as doc_id
            doc_id = str(file_path)

            return CorpusDocument(
                doc_id=doc_id,
                content=content,
                metadata={
                    "filename": file_path.name,
                    "extension": file_path.suffix,
                    "size_bytes": file_path.stat().st_size,
                },
            )
        except (OSError, UnicodeDecodeError):
            return None

    def _load_jsonl_documents(self, file_path: Path) -> list[CorpusDocument]:
        """Load a JSONL file as one CorpusDocument per line.

        Args:
            file_path: Path to the JSONL file.

        Returns:
            List of CorpusDocument instances (one per line).
        """
        import json

        documents: list[CorpusDocument] = []
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            return documents

        for line_num, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                json.loads(stripped)  # validate JSON
            except json.JSONDecodeError:
                continue
            doc_id = f"{file_path}:L{line_num}"
            documents.append(
                CorpusDocument(
                    doc_id=doc_id,
                    content=stripped,
                    metadata={
                        "filename": file_path.name,
                        "extension": ".jsonl",
                        "line_number": line_num,
                    },
                )
            )
            if len(documents) >= self.max_documents:
                break

        return documents

    def _merge_reports(
        self,
        reports: list[AuditReport],
        corpus_path: str,
        total_documents: int,
    ) -> AuditReport:
        """Merge multiple analyzer reports into one.

        Args:
            reports: List of individual analyzer reports.
            corpus_path: Original corpus path.
            total_documents: Total number of documents.

        Returns:
            Merged AuditReport.
        """
        all_issues: list[CorpusIssue] = []
        all_checks: list[str] = []
        all_metadata: dict[str, Any] = {}

        for report in reports:
            all_issues.extend(report.issues)
            all_checks.extend(report.checks_performed)
            all_metadata.update(report.metadata)

        # Compute overall health score (average of individual scores)
        if reports:
            avg_score = sum(r.health_score for r in reports) / len(reports)
        else:
            avg_score = 1.0

        # Build summary
        summary = self._build_summary(all_issues, total_documents, len(reports))

        return AuditReport(
            corpus_path=corpus_path,
            total_documents=total_documents,
            issues=all_issues,
            health_score=round(avg_score, 3),
            checks_performed=all_checks,
            summary=summary,
            metadata=all_metadata,
        )

    def _build_summary(
        self,
        issues: list[CorpusIssue],
        num_docs: int,
        num_checks: int,
    ) -> str:
        """Build a high-level summary.

        Args:
            issues: All detected issues.
            num_docs: Number of documents.
            num_checks: Number of checks performed.

        Returns:
            Summary string.
        """
        if not issues:
            return (
                f"Corpus audit complete: {num_docs} documents analyzed "
                f"across {num_checks} checks. No issues found."
            )

        by_severity: dict[IssueSeverity, int] = {}
        for issue in issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1

        parts = [
            f"Corpus audit complete: {num_docs} documents analyzed "
            f"across {num_checks} checks. Found {len(issues)} issue(s)."
        ]

        for severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM, IssueSeverity.LOW]:
            count = by_severity.get(severity, 0)
            if count:
                parts.append(f"  - {severity.value}: {count}")

        return " ".join(parts)

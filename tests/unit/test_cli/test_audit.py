"""Tests for the audit CLI command."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from openagent_eval.cli.context import get_context, reset_context
from openagent_eval.cli.main import app
from openagent_eval.corpus.models import AuditReport, CorpusIssue, IssueSeverity, IssueType
from openagent_eval.exceptions.corpus import (
    CorpusAuditError,
    CorpusNotFoundError,
    CorpusValidationError,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def _reset_cli_context():
    """Reset the global CLI context before and after every test.

    The CLI context (quiet/json/verbose flags) lives in a module-level
    global, so leaving it dirty between tests can make later tests pass
    or fail depending on run order.
    """
    reset_context()
    yield
    reset_context()


def make_issue(
    severity: IssueSeverity = IssueSeverity.MEDIUM,
    issue_type: IssueType = IssueType.DUPLICATE,
    title: str = "Sample issue",
    document_ids: list[str] | None = None,
    metadata: dict | None = None,
    description: str = "A sample issue description.",
) -> CorpusIssue:
    """Build a real CorpusIssue for use in test fixtures."""
    return CorpusIssue(
        issue_type=issue_type,
        severity=severity,
        title=title,
        description=description,
        document_ids=document_ids if document_ids is not None else ["doc1", "doc2"],
        metadata=metadata if metadata is not None else {},
    )


def make_report(
    health_score: float = 0.95,
    summary: str = "Corpus looks healthy.",
    issues: list[CorpusIssue] | None = None,
    checks_performed: list[str] | None = None,
    total_documents: int = 10,
    corpus_path: str = "corpus",
) -> AuditReport:
    """Build a real AuditReport for use in test fixtures.

    Grouping (``issues_by_type``, ``issues_by_severity``, etc.) is a
    computed property on the real model, so we don't need to duplicate
    that logic here — if the model's grouping logic changes, these
    tests will actually notice.
    """
    return AuditReport(
        corpus_path=corpus_path,
        total_documents=total_documents,
        issues=issues if issues is not None else [],
        health_score=health_score,
        checks_performed=checks_performed if checks_performed is not None else ["contradiction", "staleness"],
        summary=summary,
    )


@pytest.fixture
def corpus_dir(tmp_path):
    """A temporary directory standing in for a corpus path."""
    path = tmp_path / "corpus"
    path.mkdir()
    (path / "doc1.md").write_text("Some content.", encoding="utf-8")
    return path


class TestAuditHelp:
    """Tests for --help output of the audit command."""

    def test_audit_help(self):
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "audit" in result.output.lower()

    def test_audit_help_shows_checks_option(self):
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "--checks" in result.output

    def test_audit_help_shows_output_option(self):
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output


class TestAuditArgumentParsing:
    """Tests for command-line argument parsing."""

    def test_audit_missing_corpus_path(self):
        result = runner.invoke(app, ["audit"])
        assert result.exit_code != 0

    def test_audit_nonexistent_path(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        result = runner.invoke(app, ["audit", str(missing)])
        assert result.exit_code == 2
        assert "does not exist" in result.output.lower()

    def test_audit_unknown_check_rejected(self, corpus_dir):
        result = runner.invoke(app, ["audit", str(corpus_dir), "--checks", "bogus"])
        assert result.exit_code == 2
        assert "unknown check" in result.output.lower()

    def test_audit_partial_unknown_check_rejected(self, corpus_dir):
        result = runner.invoke(
            app, ["audit", str(corpus_dir), "--checks", "contradiction,bogus"]
        )
        assert result.exit_code == 2

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_valid_checks_parsed(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report())

        result = runner.invoke(
            app, ["audit", str(corpus_dir), "--checks", "contradiction, staleness"]
        )

        assert result.exit_code == 0
        _, kwargs = mock_auditor_cls.call_args
        assert kwargs["checks"] == ["contradiction", "staleness"]

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_default_options(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report())

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 0
        _, kwargs = mock_auditor_cls.call_args
        assert kwargs["checks"] is None
        assert kwargs["staleness_days"] == 365
        assert kwargs["similarity_threshold"] == pytest.approx(0.92)
        assert kwargs["max_documents"] == 1000

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_custom_options(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report())

        result = runner.invoke(
            app,
            [
                "audit",
                str(corpus_dir),
                "--staleness-days",
                "30",
                "--similarity-threshold",
                "0.5",
                "--max-documents",
                "50",
            ],
        )

        assert result.exit_code == 0
        _, kwargs = mock_auditor_cls.call_args
        assert kwargs["staleness_days"] == 30
        assert kwargs["similarity_threshold"] == pytest.approx(0.5)
        assert kwargs["max_documents"] == 50


class TestAuditIntegration:
    """Tests for integration with the corpus audit module."""

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_calls_auditor_with_corpus_path(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report())

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 0
        mock_auditor.audit.assert_awaited_once_with(str(corpus_dir))

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_corpus_not_found_error(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(
            side_effect=CorpusNotFoundError(corpus_path=str(corpus_dir))
        )

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 2
        assert "error" in result.output.lower()

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_corpus_audit_error(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(
            side_effect=CorpusAuditError(message="audit failed", corpus_path=str(corpus_dir))
        )

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 3
        assert "error" in result.output.lower()

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_empty_corpus_validation_error(self, mock_auditor_cls, corpus_dir):
        """CorpusValidationError (raised by the real auditor when no readable
        documents are found) is NOT one of the exception types the command
        explicitly catches (only CorpusNotFoundError / CorpusAuditError are).
        This pins down current behavior so a future fix is a visible diff
        here rather than a silent regression either way.
        """
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(
            side_effect=CorpusValidationError(
                message="No readable documents found",
                corpus_path=str(corpus_dir),
            )
        )

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code != 0


class TestAuditErrorHandling:
    """Tests for error handling on non-existent or invalid corpus paths."""

    def test_audit_error_message_includes_path(self, tmp_path):
        missing = tmp_path / "missing_corpus"
        result = runner.invoke(app, ["audit", str(missing)])
        assert str(missing) in result.output

    def test_audit_unknown_check_lists_valid_checks(self, corpus_dir):
        result = runner.invoke(app, ["audit", str(corpus_dir), "--checks", "bogus"])
        output_lower = result.output.lower()
        assert "contradiction" in output_lower
        assert "staleness" in output_lower
        assert "duplicate" in output_lower
        assert "coverage" in output_lower


class TestAuditOutputFormatting:
    """Tests for terminal and JSON output formatting."""

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_terminal_output_healthy(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report(health_score=0.9))

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 0
        assert "Healthy" in result.output

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_terminal_output_needs_attention(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report(health_score=0.6))

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 0
        assert "Needs Attention" in result.output

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_terminal_output_unhealthy(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report(health_score=0.2))

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 0
        assert "Unhealthy" in result.output

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_no_issues_found(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report(issues=[]))

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 0
        assert "No issues found" in result.output

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_issues_listed_in_table(self, mock_auditor_cls, corpus_dir):
        issue = make_issue(severity=IssueSeverity.HIGH, title="Duplicate content detected")
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report(issues=[issue]))

        result = runner.invoke(app, ["audit", str(corpus_dir)])

        assert result.exit_code == 0
        assert "Duplicate content detected" in result.output

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_verbose_shows_checks_and_documents(self, mock_auditor_cls, corpus_dir):
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(
            return_value=make_report(
                checks_performed=["contradiction", "duplicate"],
                total_documents=42,
            )
        )

        result = runner.invoke(app, ["audit", str(corpus_dir), "--verbose"])

        assert result.exit_code == 0
        assert "contradiction" in result.output.lower()
        assert "42" in result.output
        # The command sets ctx.verbose = True when --verbose is passed;
        # confirm that actually happens rather than just checking the
        # downstream output it enables.
        assert get_context().verbose is True

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_json_output_structure(self, mock_auditor_cls, corpus_dir):
        issue = make_issue(
            severity=IssueSeverity.LOW,
            issue_type=IssueType.STALENESS,
            title="Stale document",
            document_ids=["docA"],
        )
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(
            return_value=make_report(health_score=0.75, issues=[issue])
        )

        result = runner.invoke(
            app, ["--quiet", "audit", str(corpus_dir), "--output", "json"]
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        payload = json.loads(result.output)
        assert payload["status"] == "success"
        assert payload["health_score"] == pytest.approx(0.75)
        assert payload["issues_count"] == 1
        assert payload["issues"][0]["title"] == "Stale document"
        assert payload["issues"][0]["type"] == "staleness"
        assert "elapsed_seconds" in payload

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_json_output_without_quiet(self, mock_auditor_cls, corpus_dir):
        """Without --quiet, a banner is printed before the JSON payload.
        The JSON itself should still be well-formed once you skip past it.
        """
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit = AsyncMock(return_value=make_report(health_score=0.75))

        result = runner.invoke(app, ["audit", str(corpus_dir), "--output", "json"])

        assert result.exit_code == 0
        json_start = result.output.index("{")
        payload = json.loads(result.output[json_start:])
        assert payload["status"] == "success"
        assert payload["health_score"] == pytest.approx(0.75)
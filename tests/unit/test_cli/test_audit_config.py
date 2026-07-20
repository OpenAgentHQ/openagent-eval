"""Tests for the ``audit`` command reading settings from a config file (#121).

The audit command must accept a ``--config`` pointing at a config file whose
``corpus:`` section supplies the audit settings, while explicit CLI flags keep
precedence over the file's values.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from openagent_eval.cli.main import app
from openagent_eval.corpus.models import AuditReport

runner = CliRunner()


def _write_config(tmp_path: Path, corpus_dir: Path, **corpus_overrides: object) -> Path:
    """Write a minimal config.yaml with a ``corpus:`` section."""
    corpus: dict[str, object] = {
        "path": str(corpus_dir),
        "checks": ["contradiction", "staleness"],
        "staleness_days": 180,
        "similarity_threshold": 0.5,
        "max_documents": 50,
    }
    corpus.update(corpus_overrides)
    config = {
        "dataset": {"path": "data.json"},
        "llm": {"provider": "openai", "model": "gpt-4o"},
        "corpus": corpus,
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")
    return config_path


class _CaptureAuditor:
    """Stand-in for ``CorpusAuditor`` that records constructor kwargs.

    Patching this at the audit-command boundary keeps the heavy embedding /
    LLM machinery from running while still asserting how the command wires
    resolved settings into the auditor.
    """

    captured: dict[str, object] = {}

    def __init__(self, **kwargs: object) -> None:
        type(self).captured = dict(kwargs)

    async def audit(self, corpus_path: str) -> AuditReport:
        type(self).captured["corpus_path"] = corpus_path
        return AuditReport(corpus_path=corpus_path, total_documents=0)


def _patch_auditor(monkeypatch) -> type[_CaptureAuditor]:
    _CaptureAuditor.captured = {}
    monkeypatch.setattr(
        "openagent_eval.cli.commands.audit.CorpusAuditor", _CaptureAuditor
    )
    return _CaptureAuditor


def test_audit_uses_config_file_values_when_flags_absent(tmp_path, monkeypatch):
    """With --config and no tuning flags, config values reach the auditor."""
    corpus_dir = tmp_path / "kb"
    corpus_dir.mkdir()
    auditor = _patch_auditor(monkeypatch)
    config_path = _write_config(tmp_path, corpus_dir)

    result = runner.invoke(app, ["audit", "--config", str(config_path)])

    assert result.exit_code == 0, result.output
    assert auditor.captured["staleness_days"] == 180
    assert auditor.captured["similarity_threshold"] == 0.5
    assert auditor.captured["max_documents"] == 50
    assert auditor.captured["checks"] == ["contradiction", "staleness"]
    assert auditor.captured["corpus_path"] == str(corpus_dir)


def test_audit_flag_overrides_config_value(tmp_path, monkeypatch):
    """Explicit CLI flags win over the config file's corpus values."""
    corpus_dir = tmp_path / "kb"
    corpus_dir.mkdir()
    auditor = _patch_auditor(monkeypatch)
    config_path = _write_config(tmp_path, corpus_dir)

    result = runner.invoke(
        app,
        [
            "audit",
            "--config",
            str(config_path),
            "--staleness-days",
            "30",
            "--max-documents",
            "7",
        ],
    )

    assert result.exit_code == 0, result.output
    # Flags override the file...
    assert auditor.captured["staleness_days"] == 30
    assert auditor.captured["max_documents"] == 7
    # ...but the un-flagged setting still comes from the file.
    assert auditor.captured["similarity_threshold"] == 0.5


def test_audit_positional_path_overrides_config_path(tmp_path, monkeypatch):
    """An explicit positional corpus path wins over corpus.path in the file."""
    config_dir = tmp_path / "from_config"
    config_dir.mkdir()
    cli_dir = tmp_path / "from_cli"
    cli_dir.mkdir()
    auditor = _patch_auditor(monkeypatch)
    config_path = _write_config(tmp_path, config_dir)

    result = runner.invoke(
        app, ["audit", str(cli_dir), "--config", str(config_path)]
    )

    assert result.exit_code == 0, result.output
    assert auditor.captured["corpus_path"] == str(cli_dir)


def test_audit_without_config_uses_builtin_defaults(tmp_path, monkeypatch):
    """Without --config the command keeps its original built-in defaults."""
    corpus_dir = tmp_path / "kb"
    corpus_dir.mkdir()
    auditor = _patch_auditor(monkeypatch)

    result = runner.invoke(app, ["audit", str(corpus_dir)])

    assert result.exit_code == 0, result.output
    assert auditor.captured["staleness_days"] == 365
    assert auditor.captured["similarity_threshold"] == 0.92
    assert auditor.captured["max_documents"] == 1000
    assert auditor.captured["checks"] is None


def test_audit_errors_when_no_path_and_no_config(monkeypatch):
    """No positional path and no config is an error, not a crash."""
    _patch_auditor(monkeypatch)

    result = runner.invoke(app, ["audit"])

    assert result.exit_code == 2
    assert "No corpus path" in result.output


def test_audit_errors_when_config_missing_corpus_section(tmp_path, monkeypatch):
    """A config file without a corpus: section is a clear error."""
    _patch_auditor(monkeypatch)
    config = {
        "dataset": {"path": "data.json"},
        "llm": {"provider": "openai", "model": "gpt-4o"},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")

    result = runner.invoke(app, ["audit", "--config", str(config_path)])

    assert result.exit_code == 2
    assert "corpus:" in result.output

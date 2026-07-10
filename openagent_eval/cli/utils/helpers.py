"""CLI utility functions for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

from openagent_eval.exceptions import ConfigurationError
from openagent_eval.exceptions.cli import CommandError

DEFAULT_OUTPUT_DIR = Path("./reports")


def get_report_generator(format_name: str) -> object:
    """Get report generator by format name.

    Args:
        format_name: Name of the report format.

    Returns:
        Report generator instance.

    Raises:
        CommandError: If format name is unknown.
    """
    from openagent_eval.reports.html import HTMLReport
    from openagent_eval.reports.json_report import JSONReport
    from openagent_eval.reports.markdown import MarkdownReport
    from openagent_eval.reports.terminal import TerminalReport

    generators = {
        "terminal": TerminalReport,
        "markdown": MarkdownReport,
        "html": HTMLReport,
        "json": JSONReport,
    }

    if format_name not in generators:
        raise CommandError(
            message=f"Unknown output format: {format_name}. Choose from: {', '.join(generators.keys())}",
            exit_code=2,
        )

    return generators[format_name]()


def resolve_report_id(
    report_id: str, output_dir: Path, manager: object
) -> dict:
    """Resolve report ID to report data.

    Handles 'latest' keyword and direct file paths.

    Args:
        report_id: Report ID or 'latest'.
        output_dir: Reports directory.
        manager: Report manager instance.

    Returns:
        Report data dictionary.

    Raises:
        CommandError: If report not found.
    """
    import json

    from openagent_eval.reports.manager import ReportManager

    if not isinstance(manager, ReportManager):
        raise CommandError(message="Invalid manager", exit_code=1)

    # A direct file path takes precedence over ID lookup.
    candidate = Path(report_id)
    if candidate.exists() and candidate.is_file():
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise CommandError(
                message=f"Could not read report file: {report_id} ({exc})",
                exit_code=1,
            ) from exc

    if report_id == "latest":
        reports = manager.list_reports(output_dir)
        if not reports:
            raise CommandError(
                message="No reports found", exit_code=1
            )
        report_id = reports[0]["report_id"]

    try:
        return manager.load_report(report_id, output_dir)
    except FileNotFoundError as exc:
        raise CommandError(
            message=f"Report not found: {report_id}", exit_code=1
        ) from exc


def load_config_from_path(config_path: Path) -> object:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Loaded configuration object.

    Raises:
        ConfigurationError: If configuration cannot be loaded.
    """
    from openagent_eval.config.loader import load_config

    try:
        return load_config(config_path)
    except Exception as e:
        raise ConfigurationError(
            message=f"Failed to load configuration: {e}",
            config_path=str(config_path),
        ) from e


def apply_output_override(config: object, output: str | None) -> None:
    """Override output format in config if specified.

    Args:
        config: Configuration object.
        output: Output format to override with.

    Raises:
        ConfigurationError: If output format is invalid.
    """
    if output:
        from openagent_eval.config.models import OutputFormat

        try:
            config.report.output = OutputFormat(output)
        except ValueError as exc:
            raise ConfigurationError(
                message=f"Invalid output format: {output}",
                config_path="",
            ) from exc


def load_dataset_for_run(config: object) -> list:
    """Load dataset items from config.

    Auto-detects the dataset format from the file extension (or the explicit
    ``format`` field in the configuration) and returns a list of item
    dictionaries suitable for the evaluation engine.

    Args:
        config: Configuration object.

    Returns:
        List of dataset items.

    Raises:
        ConfigurationError: If dataset cannot be loaded.
    """
    from openagent_eval.datasets.factory import load_dataset

    try:
        return load_dataset(config.dataset)
    except Exception as e:
        raise ConfigurationError(
            message=f"Failed to load dataset: {e}",
            config_path="",
        ) from e


def execute_evaluation(config: object, dataset_items: list) -> object:
    """Execute the evaluation pipeline.

    Args:
        config: Configuration object.
        dataset_items: List of dataset items to evaluate.

    Returns:
        Evaluation report.

    Raises:
        ConfigurationError: If evaluation fails.
    """
    import asyncio

    from openagent_eval.core.engine import Engine

    try:
        engine = Engine(config)
        return asyncio.run(engine.run(dataset_items))
    except Exception as e:
        raise ConfigurationError(
            message=f"Evaluation failed: {e}",
            config_path="",
        ) from e

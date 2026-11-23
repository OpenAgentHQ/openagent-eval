"""Display a metric across existing local evaluation runs."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from openagent_eval.cli.context import get_context
from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.reports.manager import ReportManager


def history_command(
    metric: Annotated[str, typer.Argument(help="Metric name from the run summary.")],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-d", file_okay=False, help="Reports directory."),
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """Show recorded scores for a metric, oldest first."""
    history = ReportManager().metric_history(metric, output_dir)
    if get_context().json_output:
        typer.echo(
            json.dumps(
                [
                    {
                        "report_id": point.report_id,
                        "created_at": point.created_at.isoformat(),
                        "value": point.value,
                    }
                    for point in history
                ]
            )
        )
        return
    if not history:
        typer.echo(f"No recorded values for {metric} in {output_dir}.")
        return

    table = Table(title=Text(f"Metric history: {metric}"))
    table.add_column("Run")
    table.add_column("Created (UTC)")
    table.add_column("Value", justify="right")
    table.add_column("Change", justify="right")
    previous = None
    for point in history:
        change = "—" if previous is None else f"{point.value - previous:+.6g}"
        table.add_row(
            Text(point.report_id),
            point.created_at.isoformat(),
            f"{point.value:.6g}",
            change,
        )
        previous = point.value
    Console(no_color=get_context().no_color or None).print(table)

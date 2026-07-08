"""Main CLI entry point for OpenAgent Eval."""

from __future__ import annotations

import typer

from openagent_eval.cli.utils.callbacks import version_callback
from openagent_eval.cli.commands.init import init_command
from openagent_eval.cli.commands.run import run_command
from openagent_eval.cli.commands.report import report_command
from openagent_eval.cli.commands.compare import compare_command
from openagent_eval.cli.commands.list_evaluations import list_command
from openagent_eval.cli.commands.doctor import doctor_command

app = typer.Typer(
    name="oaeval",
    help="Open-source CLI framework for evaluating RAG systems and AI Agents.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """OpenAgent Eval - Evaluate RAG systems and AI Agents."""


# Register commands with explicit names
app.command(name="init")(init_command)
app.command(name="run")(run_command)
app.command(name="report")(report_command)
app.command(name="compare")(compare_command)
app.command(name="list")(list_command)
app.command(name="doctor")(doctor_command)

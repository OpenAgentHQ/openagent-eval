"""CLI commands for OpenAgent Eval."""

from openagent_eval.cli.commands.compare import compare_command
from openagent_eval.cli.commands.doctor import doctor_command
from openagent_eval.cli.commands.init import init_command
from openagent_eval.cli.commands.list_evaluations import list_command
from openagent_eval.cli.commands.report import report_command
from openagent_eval.cli.commands.run import run_command

__all__ = [
    "init_command",
    "run_command",
    "report_command",
    "compare_command",
    "list_command",
    "doctor_command",
]

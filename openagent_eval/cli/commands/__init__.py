"""CLI commands for OpenAgent Eval."""

from openagent_eval.cli.commands.audit import audit_command
from openagent_eval.cli.commands.compare import compare_command
from openagent_eval.cli.commands.delete import delete_command
from openagent_eval.cli.commands.diagnose import diagnose_command
from openagent_eval.cli.commands.doctor import doctor_command
from openagent_eval.cli.commands.init import init_command
from openagent_eval.cli.commands.list_evaluations import list_command
from openagent_eval.cli.commands.report import report_command
from openagent_eval.cli.commands.run import run_command
from openagent_eval.cli.commands.synth import synth_command
from openagent_eval.cli.commands.test import test_command
from openagent_eval.cli.commands.validate import validate_command

__all__ = [
    "audit_command",
    "init_command",
    "run_command",
    "report_command",
    "compare_command",
    "list_command",
    "doctor_command",
    "validate_command",
    "delete_command",
    "diagnose_command",
    "synth_command",
    "test_command",
]

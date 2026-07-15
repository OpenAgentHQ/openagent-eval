"""Main CLI entry point for OpenAgent Eval."""

from __future__ import annotations

import sys

import typer
from rich.console import Console

from openagent_eval import __version__
from openagent_eval.cli.banner import create_mini_banner
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
from openagent_eval.cli.commands.audit import audit_command
from openagent_eval.cli.context import CLIContext, set_context
from openagent_eval.cli.utils.callbacks import VERSION_OPTION, version_callback
from openagent_eval.exceptions import OpenAgentEvalError

# Error code mapping for different exception types
_ERROR_CODES: dict[str, int] = {
    "ConfigurationError": 2,
    "DatasetError": 3,
    "ProviderError": 4,
    "MetricError": 5,
    "CorpusError": 6,
}

app = typer.Typer(
    name="oaeval",
    help="Open-source CLI framework for evaluating RAG systems and AI Agents.",
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable color output.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
) -> None:
    """OpenAgent Eval - Evaluate RAG systems and AI Agents."""
    # Set global CLI context
    ctx = CLIContext(
        quiet=quiet,
        json_output=json_output,
        no_color=no_color,
        verbose=verbose,
    )
    set_context(ctx)

    # Show banner when invoked without a subcommand (help display)
    try:
        import click

        ctx = click.get_current_context(silent=True)
        if ctx is not None and ctx.invoked_subcommand is None and not quiet:
            create_mini_banner()
    except Exception:
        pass


def _handle_error(error: OpenAgentEvalError) -> None:
    """Handle OpenAgentEvalError and display friendly message.

    Args:
        error: The exception to handle.
    """
    console = Console(stderr=True)

    # Determine error code
    error_type = type(error).__name__
    exit_code = _ERROR_CODES.get(error_type, 1)

    # Build error display
    console.print(f"\n[red]Error:[/red] {error.message}")

    if error.details:
        for key, value in error.details.items():
            console.print(f"  [dim]{key}:[/dim] {value}")

    raise typer.Exit(code=exit_code) from None


# Register commands with explicit names
app.command(name="init")(init_command)
app.command(name="run")(run_command)
app.command(name="report")(report_command)
app.command(name="compare")(compare_command)
app.command(name="list")(list_command)
app.command(name="doctor")(doctor_command)
app.command(name="validate")(validate_command)
app.command(name="delete")(delete_command)
app.command(name="diagnose")(diagnose_command)
app.command(name="audit")(audit_command)
app.command(name="synth")(synth_command)
app.command(name="test")(test_command)


# Shell completion command
@app.command(name="completion")
def completion_command(
    shell: str = typer.Argument(
        help="Shell to generate completion for (bash, zsh, fish).",
    ),
) -> None:
    """Generate shell completion script.

    Install completion by running the generated script:

        oaeval completion bash >> ~/.bashrc
        oaeval completion zsh >> ~/.zshrc
        oaeval completion fish > ~/.config/fish/completions/oaeval.fish
    """
    console = Console()
    if shell not in ("bash", "zsh", "fish"):
        console.print(f"[red]Error:[/red] Unsupported shell: {shell}")
        console.print("[dim]Supported shells: bash, zsh, fish[/dim]")
        raise typer.Exit(code=1)

    # Generate completion script
    if shell == "bash":
        script = _generate_bash_completion()
    elif shell == "zsh":
        script = _generate_zsh_completion()
    else:
        script = _generate_fish_completion()

    console.print(script)


def _generate_bash_completion() -> str:
    """Generate bash completion script.

    Returns:
        Bash completion script string.
    """
    return """\
# oaeval completion for bash
_oaeval_completion() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="init run report compare list doctor validate delete diagnose audit synth test completion"

    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "--help --version --quiet --json --no-color --verbose" -- ${cur}) )
        return 0
    fi

    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi

    case ${prev} in
        run)
            COMPREPLY=( $(compgen -W "--output --verbose --dry-run --metrics --help" -- ${cur}) )
            ;;
        report)
            COMPREPLY=( $(compgen -W "--output --output-dir --help" -- ${cur}) )
            ;;
        compare)
            COMPREPLY=( $(compgen -W "--metrics --output-dir --help" -- ${cur}) )
            ;;
        list)
            COMPREPLY=( $(compgen -W "--limit --output --output-dir --sort --reverse --search --help" -- ${cur}) )
            ;;
        doctor)
            COMPREPLY=( $(compgen -W "--verbose --check-api --help" -- ${cur}) )
            ;;
        validate)
            COMPREPLY=( $(compgen -W "--help" -- ${cur}) )
            ;;
        delete)
            COMPREPLY=( $(compgen -W "--output-dir --force --help" -- ${cur}) )
            ;;
        audit)
            COMPREPLY=( $(compgen -W "--checks --staleness-days --similarity-threshold --max-documents --output --verbose --help" -- ${cur}) )
            ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh fish" -- ${cur}) )
            ;;
    esac
    return 0
}
complete -F _oaeval_completion oaeval
"""


def _generate_zsh_completion() -> str:
    """Generate zsh completion script.

    Returns:
        zsh completion script string.
    """
    return """\
#compdef oaeval

_oaeval() {
    local commands
    commands=(
        'init:Create a new evaluation configuration'
        'run:Run evaluation pipeline'
        'report:View evaluation reports'
        'compare:Compare two experiments'
        'list:List previous evaluations'
        'doctor:Check environment and dependencies'
        'validate:Validate configuration'
        'delete:Delete evaluation reports'
        'diagnose:Diagnose evaluation failures and attribute blame'
        'audit:Audit corpus health'
        'test:Run evaluation as CI/CD test with threshold gating'
        'completion:Generate shell completion script'
    )

    _arguments -C \\
        '1:command:->command' \\
        '*::arg:->args' \\
        '--help[Show help]' \\
        '--version[Show version]' \\
        '--quiet[Suppress non-essential output]' \\
        '--json[Output machine-readable JSON]' \\
        '--no-color[Disable color output]' \\
        '--verbose[Enable verbose output]'

    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                run)
                    _arguments \\
                        '--output[Output format]:format:(terminal markdown html json)' \\
                        '--verbose[Enable verbose output]' \\
                        '--dry-run[Validate without running]' \\
                        '--metrics[Metrics to run]:metrics:' \\
                        '--help[Show help]'
                    ;;
                report)
                    _arguments \\
                        '--output[Output format]:format:(terminal markdown html json)' \\
                        '--output-dir[Output directory]:dir:' \\
                        '--help[Show help]'
                    ;;
                compare)
                    _arguments \\
                        '--metrics[Metrics to compare]:metrics:' \\
                        '--output-dir[Output directory]:dir:' \\
                        '--help[Show help]'
                    ;;
                list)
                    _arguments \\
                        '--limit[Number of results]:limit:' \\
                        '--output[Filter by format]:format:' \\
                        '--output-dir[Output directory]:dir:' \\
                        '--sort[Sort by]:sort:(date score cost)' \\
                        '--reverse[Reverse sort order]' \\
                        '--search[Search term]:search:' \\
                        '--help[Show help]'
                    ;;
                doctor)
                    _arguments \\
                        '--verbose[Enable verbose output]' \\
                        '--check-api[Test API connectivity]' \\
                        '--help[Show help]'
                    ;;
                validate)
                    _arguments \\
                        '--help[Show help]'
                    ;;
                delete)
                    _arguments \\
                        '--output-dir[Output directory]:dir:' \\
                        '--force[Skip confirmation]' \\
                        '--help[Show help]'
                    ;;
                diagnose)
                    _arguments \\
                        '--output[Output format]:format:(terminal json)' \\
                        '--threshold[Confidence threshold]:threshold:' \\
                        '--max-recs[Max recommendations]:max:' \\
                        '--verbose[Enable verbose output]' \\
                        '--help[Show help]'
                    ;;
                audit)
                    _arguments \\
                        '--checks[Checks to perform]:checks:' \\
                        '--staleness-days[Staleness threshold]:days:' \\
                        '--similarity-threshold[Similarity threshold]:threshold:' \\
                        '--max-documents[Max documents]:max:' \\
                        '--output[Output format]:format:(json)' \\
                        '--verbose[Enable verbose output]' \\
                        '--help[Show help]'
                    ;;
                test)
                    _arguments \\
                        '--threshold[Threshold gate]:threshold:' \\
                        '--fail-on-error[Fail on error]' \\
                        '--no-fail-on-error[Do not fail on error]' \\
                        '--timeout[Timeout in seconds]:timeout:' \\
                        '--verbose[Enable verbose output]' \\
                        '--json[Output JSON]' \\
                        '--help[Show help]'
                    ;;
                completion)
                    _arguments \\
                        '1:shell:(bash zsh fish)'
                    ;;
            esac
            ;;
    esac
}

_oaeval "$@"
"""


def _generate_fish_completion() -> str:
    """Generate fish completion script.

    Returns:
        fish completion script string.
    """
    return """\
# oaeval completion for fish

# Helper function
function __oaeval_no_subcommand
    set -l cmd (commandline -opc)
    test (count $cmd) -eq 1
end

function __oaeval_using_command
    set -l cmd (commandline -opc)
    test (count $cmd) -gt 1; and test "$cmd[2]" = "$argv[1]"
end

# Global flags
complete -c oaeval -l help -s h -d 'Show help'
complete -c oaeval -l version -s V -d 'Show version'
complete -c oaeval -l quiet -s q -d 'Suppress non-essential output'
complete -c oaeval -l json -d 'Output machine-readable JSON'
complete -c oaeval -l no-color -d 'Disable color output'
complete -c oaeval -l verbose -s v -d 'Enable verbose output'

# Subcommands
complete -c oaeval -n __oaeval_no_subcommand -a init -d 'Create a new evaluation configuration'
complete -c oaeval -n __oaeval_no_subcommand -a run -d 'Run evaluation pipeline'
complete -c oaeval -n __oaeval_no_subcommand -a report -d 'View evaluation reports'
complete -c oaeval -n __oaeval_no_subcommand -a compare -d 'Compare two experiments'
complete -c oaeval -n __oaeval_no_subcommand -a list -d 'List previous evaluations'
complete -c oaeval -n __oaeval_no_subcommand -a doctor -d 'Check environment and dependencies'
complete -c oaeval -n __oaeval_no_subcommand -a validate -d 'Validate configuration'
complete -c oaeval -n __oaeval_no_subcommand -a delete -d 'Delete evaluation reports'
complete -c oaeval -n __oaeval_no_subcommand -a diagnose -d 'Diagnose evaluation failures and attribute blame'
complete -c oaeval -n __oaeval_no_subcommand -a audit -d 'Audit corpus health'
complete -c oaeval -n __oaeval_no_subcommand -a test -d 'Run evaluation as CI/CD test with threshold gating'
complete -c oaeval -n __oaeval_no_subcommand -a completion -d 'Generate shell completion script'

# run command options
complete -c oaeval -n __oaeval_using_command -a run -l output -s o -d 'Output format' -r
complete -c oaeval -n __oaeval_using_command -a run -l verbose -s v -d 'Enable verbose output'
complete -c oaeval -n __oaeval_using_command -a run -l dry-run -d 'Validate without running'
complete -c oaeval -n __oaeval_using_command -a run -l metrics -s m -d 'Metrics to run' -r

# report command options
complete -c oaeval -n __oaeval_using_command -a report -l output -s o -d 'Output format' -r
complete -c oaeval -n __oaeval_using_command -a report -l output-dir -s d -d 'Output directory' -r

# compare command options
complete -c oaeval -n __oaeval_using_command -a compare -l metrics -s m -d 'Metrics to compare' -r
complete -c oaeval -n __oaeval_using_command -a compare -l output-dir -s d -d 'Output directory' -r

# list command options
complete -c oaeval -n __oaeval_using_command -a list -l limit -s l -d 'Number of results' -r
complete -c oaeval -n __oaeval_using_command -a list -l output -s o -d 'Filter by format' -r
complete -c oaeval -n __oaeval_using_command -a list -l output-dir -s d -d 'Output directory' -r
complete -c oaeval -n __oaeval_using_command -a list -l sort -s s -d 'Sort by' -r
complete -c oaeval -n __oaeval_using_command -a list -l reverse -s r -d 'Reverse sort order'
complete -c oaeval -n __oaeval_using_command -a list -l search -d 'Search term' -r

# doctor command options
complete -c oaeval -n __oaeval_using_command -a doctor -l verbose -s v -d 'Enable verbose output'
complete -c oaeval -n __oaeval_using_command -a doctor -l check-api -d 'Test API connectivity'

# delete command options
complete -c oaeval -n __oaeval_using_command -a delete -l output-dir -s d -d 'Output directory' -r
complete -c oaeval -n __oaeval_using_command -a delete -l force -s f -d 'Skip confirmation'

# diagnose command options
complete -c oaeval -n __oaeval_using_command -a diagnose -l output -s o -d 'Output format' -r
complete -c oaeval -n __oaeval_using_command -a diagnose -l threshold -s t -d 'Confidence threshold' -r
complete -c oaeval -n __oaeval_using_command -a diagnose -l max-recs -d 'Max recommendations' -r
complete -c oaeval -n __oaeval_using_command -a diagnose -l verbose -s v -d 'Enable verbose output'

# audit command options
complete -c oaeval -n __oaeval_using_command -a audit -l checks -s c -d 'Checks to perform' -r
complete -c oaeval -n __oaeval_using_command -a audit -l staleness-days -d 'Staleness threshold' -r
complete -c oaeval -n __oaeval_using_command -a audit -l similarity-threshold -d 'Similarity threshold' -r
complete -c oaeval -n __oaeval_using_command -a audit -l max-documents -d 'Max documents' -r
complete -c oaeval -n __oaeval_using_command -a audit -l output -s o -d 'Output format' -r
complete -c oaeval -n __oaeval_using_command -a audit -l verbose -s v -d 'Enable verbose output'

# test command options
complete -c oaeval -n __oaeval_using_command -a test -l threshold -s t -d 'Threshold gate' -r
complete -c oaeval -n __oaeval_using_command -a test -l fail-on-error -d 'Fail on error'
complete -c oaeval -n __oaeval_using_command -a test -l no-fail-on-error -d 'Do not fail on error'
complete -c oaeval -n __oaeval_using_command -a test -l timeout -d 'Timeout in seconds' -r
complete -c oaeval -n __oaeval_using_command -a test -l verbose -s v -d 'Enable verbose output'
complete -c oaeval -n __oaeval_using_command -a test -l json -d 'Output JSON'

# completion command options
complete -c oaeval -n __oaeval_using_command -a completion -a 'bash zsh fish' -d 'Shell'
"""


# Override the default exception handler
def _cli_exception_handler(exc_type: type, exc_value: BaseException, exc_tb: object) -> None:
    """Custom exception handler for CLI.

    Args:
        exc_type: Exception type.
        exc_value: Exception instance.
        exc_tb: Traceback object.
    """
    if isinstance(exc_value, OpenAgentEvalError):
        _handle_error(exc_value)
    else:
        # For unexpected errors, show a user-friendly message
        console = Console(stderr=True)
        console.print(f"\n[red]Unexpected error:[/red] {exc_value}")
        console.print("[dim]This is a bug. Please report it at:")
        console.print("  https://github.com/OpenAgentHQ/openagent-eval/issues[/dim]")
        raise typer.Exit(code=1) from None


# Install custom exception handler
sys.excepthook = _cli_exception_handler


def _version_aware_cli() -> None:
    """CLI entry point that also responds to ``--version`` in subcommand position.

    Typer requires callback options (e.g. ``--version``) to appear *before*
    the subcommand token.  This wrapper scans ``sys.argv`` so that
    ``oaeval run --version`` prints the version and exits.
    """
    for token in sys.argv[1:]:
        if token in ("--version", "-V"):
            typer.echo(f"OpenAgent Eval v{__version__}")
            raise SystemExit(0)
    app()

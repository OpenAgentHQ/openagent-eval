"""Test command for OpenAgent Eval CI/CD integration."""

from __future__ import annotations

import time

import typer
from rich.console import Console
from rich.table import Table

from openagent_eval import __version__
from openagent_eval.cicd.models import CICDConfig, EvaluationGate, ThresholdConfig
from openagent_eval.cicd.plugin import OAEvalPlugin
from openagent_eval.cicd.thresholds import ThresholdEvaluator
from openagent_eval.exceptions import ConfigurationError

console = Console()


def test_command(
    config_path: str = typer.Argument(
        ...,
        help="Path to evaluation configuration file.",
    ),
    threshold: list[str] = typer.Option(
        [],
        "--threshold",
        "-t",
        help=(
            "Threshold gate in format: metric:operator:value. "
            "Operators: gt, gte, lt, lte, eq, neq. "
            "Example: -t faithfulness:gte:0.8"
        ),
    ),
    fail_on_error: bool = typer.Option(
        True,
        "--fail-on-error/--no-fail-on-error",
        help="Fail test on evaluation errors.",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Timeout in seconds for evaluation.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON.",
    ),
) -> None:
    """Run evaluation as a CI/CD test with threshold gating.

    This command runs the evaluation pipeline and checks results against
    configured thresholds. It exits with code 0 if all thresholds pass,
    or code 1 if any required threshold fails.

    \b
    Examples:
        oaeval test config.yaml -t faithfulness:gte:0.8
        oaeval test config.yaml -t faithfulness:gte:0.8 -t answer_relevancy:gte:0.7
        oaeval test config.yaml --timeout 600 --json
    """
    from openagent_eval.cli.utils.discovery import get_config_path

    console.print(f"[bold blue]OpenAgent Eval[/bold blue] v{__version__}")
    console.print(f"[dim]CI/CD Test Mode[/dim]\n")

    # Resolve config path
    try:
        resolved_path = get_config_path(config_path)
    except SystemExit as exc:
        raise typer.Exit(code=2) from exc

    path = resolved_path
    console.print(f"[dim]Configuration: {path}[/dim]")

    if threshold:
        console.print(f"[dim]Thresholds: {', '.join(threshold)}[/dim]")

    console.print()

    # Build CICD config
    cicd_config = CICDConfig(
        config_path=str(path),
        fail_on_error=fail_on_error,
        timeout=timeout,
    )

    # Parse thresholds
    for threshold_str in threshold:
        parts = threshold_str.split(":")
        if len(parts) != 3:
            console.print(
                f"[red]Error:[/red] Invalid threshold format: {threshold_str}"
            )
            console.print("[dim]Expected: metric:operator:value[/dim]")
            console.print(
                "[dim]Example: faithfulness:gte:0.8[/dim]"
            )
            raise typer.Exit(code=2)

        metric_name, operator_str, value_str = parts

        try:
            value = float(value_str)
        except ValueError:
            console.print(
                f"[red]Error:[/red] Invalid threshold value: {value_str}"
            )
            raise typer.Exit(code=2)

        # Validate operator
        valid_operators = ["gt", "gte", "lt", "lte", "eq", "neq"]
        if operator_str not in valid_operators:
            console.print(
                f"[red]Error:[/red] Invalid operator: {operator_str}"
            )
            console.print(f"[dim]Valid operators: {', '.join(valid_operators)}[/dim]")
            raise typer.Exit(code=2)

        cicd_config.gates.append(
            EvaluationGate(
                name=f"gate_{metric_name}",
                thresholds=[
                    ThresholdConfig(
                        metric=metric_name,
                        operator=operator_str,  # type: ignore[arg-type]
                        value=value,
                    )
                ],
            )
        )

    # Run evaluation
    start_time = time.time()

    try:
        console.print("[bold]Running evaluation...[/bold]")
        result = OAEvalPlugin.run_evaluation(
            config_path=str(path),
            timeout=timeout,
        )
        duration = time.time() - start_time

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=2) from e
    except ConfigurationError as e:
        console.print(f"[red]Configuration Error:[/red] {e.message}")
        raise typer.Exit(code=2) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if fail_on_error:
            raise typer.Exit(code=1) from e
        raise typer.Exit(code=0) from e

    # Evaluate thresholds if any gates configured
    if cicd_config.gates:
        evaluator = ThresholdEvaluator(cicd_config)
        metrics = result.summary.get("metrics_summary", {})
        eval_result = evaluator.evaluate_all_gates(metrics)
        result = eval_result
        result.summary["duration_seconds"] = duration

    # Display results
    if json_output:
        _output_json(result, duration)
    else:
        _display_results(result, duration, verbose)

    # Exit with appropriate code
    if result.passed:
        raise typer.Exit(code=0)
    else:
        raise typer.Exit(code=1)


def _display_results(
    result: "EvaluationResult",
    duration: float,
    verbose: bool,
) -> None:
    """Display evaluation results in a formatted table."""

    # Summary table
    table = Table(title="Evaluation Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    if "error" in result.summary:
        table.add_row("Status", "[red]ERROR[/red]")
        table.add_row("Error", result.summary["error"])
    else:
        table.add_row("Status", "[green]PASSED[/green]" if result.passed else "[red]FAILED[/red]")
        table.add_row("Total Gates", str(result.summary.get("total_gates", 0)))
        table.add_row("Passed Gates", str(result.summary.get("passed_gates", 0)))
        table.add_row("Failed Gates", str(result.summary.get("failed_gates", 0)))
        table.add_row("Duration", f"{duration:.2f}s")

    console.print(table)

    # Gate details
    if result.gate_results:
        console.print()
        gate_table = Table(title="Gate Results", show_header=True)
        gate_table.add_column("Gate", style="cyan")
        gate_table.add_column("Status", style="bold")
        gate_table.add_column("Thresholds", style="dim")

        for gate in result.gate_results:
            status = "[green]PASS[/green]" if gate.passed else "[red]FAIL[/red]"
            thresholds_str = "\n".join(
                [tr.message for tr in gate.threshold_results]
            )
            gate_table.add_row(gate.gate_name, status, thresholds_str)

        console.print(gate_table)

    # Verbose output
    if verbose and result.gate_results:
        console.print()
        console.print("[bold]Detailed Threshold Results:[/bold]")
        for gate in result.gate_results:
            console.print(f"\n[dim]Gate: {gate.gate_name}[/dim]")
            for tr in gate.threshold_results:
                status = "[green]✓[/green]" if tr.passed else "[red]✗[/red]"
                console.print(f"  {status} {tr.message}")


def _output_json(result: "EvaluationResult", duration: float) -> None:
    """Output results as JSON."""
    import json


    output = {
        "status": "passed" if result.passed else "failed",
        "duration_seconds": round(duration, 2),
        "summary": result.summary,
        "gates": [
            {
                "name": gate.gate_name,
                "passed": gate.passed,
                "behavior": gate.behavior.value,
                "thresholds": [
                    {
                        "metric": tr.metric,
                        "operator": tr.operator.value,
                        "threshold": tr.threshold_value,
                        "actual": tr.actual_value,
                        "passed": tr.passed,
                        "message": tr.message,
                    }
                    for tr in gate.threshold_results
                ],
                "failure_reasons": gate.failure_reasons,
            }
            for gate in result.gate_results
        ],
    }

    console.print(json.dumps(output, indent=2))

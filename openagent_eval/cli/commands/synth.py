"""Synth command for OpenAgent Eval.

Generates synthetic test cases from a document corpus or inline text.
Produces standard Q&A pairs and adversarial test cases for RAG evaluation.

Usage::

    oaeval synth --corpus ./knowledge_base/ --count 100
    oaeval synth --corpus ./knowledge_base/ --count 50 --adversarial
    oaeval synth --corpus ./knowledge_base/ --adversarial --types unanswerable,misleading
    oaeval synth --text "Your document text" --count 10
    oaeval synth --corpus ./docs/ --output synthetic_dataset.json
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from openagent_eval.cli.context import get_context
from openagent_eval.config.models import LLMConfig
from openagent_eval.exceptions.synthesis import SynthesisError
from openagent_eval.providers.factory import get_llm_provider
from openagent_eval.synthesis import SyntheticDataGenerator, TestCaseType

if TYPE_CHECKING:
    from openagent_eval.providers.base.llm import LLMProvider
    from openagent_eval.synthesis.models import SyntheticDataset

console = Console()

# Supported adversarial type names
_ADVERSARIAL_TYPES = [t.value for t in TestCaseType if t != TestCaseType.STANDARD]


def synth_command(
    corpus: str | None = typer.Option(
        None,
        "--corpus",
        "-c",
        help="Path to corpus directory or file.",
    ),
    text: str | None = typer.Option(
        None,
        "--text",
        "-t",
        help="Inline text to generate from (alternative to --corpus).",
    ),
    count: int = typer.Option(
        10,
        "--count",
        "-n",
        help="Number of standard test cases to generate.",
        min=1,
    ),
    adversarial: bool = typer.Option(
        False,
        "--adversarial",
        "-a",
        help="Also generate adversarial test cases.",
    ),
    adversarial_count: int = typer.Option(
        1,
        "--adversarial-count",
        help="Number of adversarial cases per type per chunk.",
        min=1,
    ),
    adversarial_types: str | None = typer.Option(
        None,
        "--types",
        help="Comma-separated adversarial types to generate (default: all). "
        f"Options: {', '.join(_ADVERSARIAL_TYPES)}",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (JSON). Defaults to stdout summary.",
    ),
    llm_provider: str = typer.Option(
        "openai",
        "--llm-provider",
        help="LLM provider to use for generation.",
    ),
    llm_model: str = typer.Option(
        "gpt-4o-mini",
        "--llm-model",
        help="LLM model to use for generation.",
    ),
    chunk_size: int = typer.Option(
        2000,
        "--chunk-size",
        help="Maximum chunk size in characters.",
        min=100,
    ),
    chunk_overlap: int = typer.Option(
        200,
        "--chunk-overlap",
        help="Overlap between consecutive chunks.",
        min=0,
    ),
    max_concurrent: int = typer.Option(
        5,
        "--max-concurrent",
        help="Maximum concurrent LLM calls.",
        min=1,
    ),
    output_format: str = typer.Option(
        "huggingface",
        "--format",
        "-f",
        help="Output dataset format (huggingface, json, jsonl).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed generation progress.",
    ),
) -> None:
    """Generate synthetic test cases from a corpus or text.

    Creates Q&A test cases and adversarial scenarios for RAG evaluation.
    Requires an LLM provider for question generation.

    Examples:

        # Generate 100 test cases from a knowledge base
        oaeval synth --corpus ./knowledge_base/ --count 100

        # Generate with adversarial test cases
        oaeval synth --corpus ./knowledge_base/ --count 50 --adversarial

        # Generate only unanswerable and misleading questions
        oaeval synth --corpus ./docs/ --adversarial --types unanswerable,misleading

        # Generate from inline text
        oaeval synth --text "Your document content here..." --count 10

        # Save to file
        oaeval synth --corpus ./docs/ --count 20 --output dataset.json
    """
    ctx = get_context()

    # Validate inputs
    if not corpus and not text:
        console.print("[red]Error:[/red] Must provide either --corpus or --text.")
        raise typer.Exit(code=2)

    if corpus and text:
        console.print("[red]Error:[/red] Cannot use both --corpus and --text.")
        raise typer.Exit(code=2)

    # Parse adversarial types
    selected_types: list[TestCaseType] | None = None
    if adversarial_types:
        try:
            selected_types = [
                TestCaseType(t.strip()) for t in adversarial_types.split(",")
            ]
        except ValueError as e:
            console.print(f"[red]Error:[/red] Invalid adversarial type: {e}")
            console.print(f"[dim]Valid types: {', '.join(_ADVERSARIAL_TYPES)}[/dim]")
            raise typer.Exit(code=2) from e

    # Create LLM provider
    try:
        provider = _create_provider(llm_provider, llm_model)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to create LLM provider: {e}")
        raise typer.Exit(code=2) from e

    # Create generator
    generator = SyntheticDataGenerator(
        llm_provider=provider,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_concurrent=max_concurrent,
    )

    # Run generation
    try:
        dataset = asyncio.run(
            _run_generation(
                generator=generator,
                corpus=corpus,
                text=text,
                count=count,
                adversarial=adversarial,
                adversarial_count=adversarial_count,
                selected_types=selected_types,
            )
        )
    except SynthesisError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.details:
            for key, value in e.details.items():
                console.print(f"  [dim]{key}:[/dim] {value}")
        raise typer.Exit(code=1) from e

    # Output results
    if output:
        _save_output(dataset, output, output_format)
    elif ctx.json_output:
        console.print(json.dumps(dataset.to_dict(), indent=2))
    else:
        _display_summary(dataset, verbose)


async def _run_generation(
    generator: SyntheticDataGenerator,
    corpus: str | None,
    text: str | None,
    count: int,
    adversarial: bool,
    adversarial_count: int,
    selected_types: list[TestCaseType] | None,
) -> SyntheticDataset:
    """Run the generation process.

    Args:
        generator: The synthetic data generator.
        corpus: Corpus path (or None).
        text: Inline text (or None).
        count: Number of standard test cases.
        adversarial: Whether to generate adversarial cases.
        adversarial_count: Adversarial cases per type per chunk.
        selected_types: Selected adversarial types (None = all).

    Returns:
        SyntheticDataset with generated test cases.
    """
    if corpus:
        return await generator.generate(
            corpus_path=corpus,
            count=count,
            adversarial=adversarial,
            adversarial_count_per_chunk=adversarial_count,
            adversarial_types=selected_types,
        )
    else:
        return await generator.generate_from_text(
            text=text or "",
            count=count,
            adversarial=adversarial,
            adversarial_count_per_type=adversarial_count,
            adversarial_types=selected_types,
        )


def _create_provider(provider_name: str, model: str) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider_name: Name of the provider (e.g., openai, gemini).
        model: Model identifier.

    Returns:
        LLMProvider instance.

    Raises:
        ProviderNotFoundError: If the provider name is unknown.
        ImportError: If the provider SDK is not installed.
    """
    config = LLMConfig(
        provider=provider_name,
        model=model,
        api_key=None,
        temperature=0.0,
        max_tokens=None,
    )
    return get_llm_provider(config)


def _save_output(
    dataset: SyntheticDataset,
    output_path: str,
    format_type: str,
) -> None:
    """Save the dataset to a file.

    Args:
        dataset: The synthetic dataset.
        output_path: Output file path.
        format_type: Output format (json, jsonl, huggingface).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "jsonl":
        with open(path, "w", encoding="utf-8") as f:
            for tc in dataset.test_cases:
                f.write(json.dumps(tc.to_dict()) + "\n")
    elif format_type == "huggingface":
        # HuggingFace format is just JSON with a specific structure
        hf_data = {
            "data": dataset.to_list(),
            "metadata": dataset.metadata,
            "type_counts": dataset.type_counts,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(hf_data, f, indent=2)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dataset.to_dict(), f, indent=2)

    console.print(
        f"[green]Saved {dataset.total_count} test cases to {path}[/green]"
    )


def _display_summary(dataset: SyntheticDataset, verbose: bool) -> None:
    """Display a summary of the generated dataset.

    Args:
        dataset: The synthetic dataset.
        verbose: Whether to show detailed information.
    """
    # Header
    console.print(
        Panel(
            f"[bold blue]Synthetic Dataset Generated[/bold blue]\n"
            f"Total test cases: {dataset.total_count}",
            title="Synthesis Complete",
            border_style="blue",
        )
    )

    # Type breakdown
    if dataset.type_counts:
        table = Table(title="Test Case Breakdown", show_lines=True)
        table.add_column("Type", style="bold")
        table.add_column("Count", justify="right")

        for test_type, count in sorted(
            dataset.type_counts.items(), key=lambda x: x[1], reverse=True
        ):
            table.add_row(test_type, str(count))

        console.print(table)

    # Show examples in verbose mode
    if verbose and dataset.test_cases:
        console.print("\n[bold]Sample Test Cases:[/bold]\n")
        for i, tc in enumerate(dataset.test_cases[:5], 1):
            console.print(
                f"  {i}. [cyan]Type:[/cyan] {tc.test_type.value}\n"
                f"     [cyan]Q:[/cyan] {tc.question[:100]}{'...' if len(tc.question) > 100 else ''}\n"
                f"     [cyan]A:[/cyan] {tc.ground_truth[:100] if tc.ground_truth else '(unanswerable)'}{'...' if tc.ground_truth and len(tc.ground_truth) > 100 else ''}\n"
            )

        if len(dataset.test_cases) > 5:
            console.print(
                f"  [dim]... and {len(dataset.test_cases) - 5} more test cases[/dim]\n"
            )

    # Metadata
    if dataset.metadata:
        console.print("[bold]Metadata:[/bold]")
        for key, value in dataset.metadata.items():
            console.print(f"  [dim]{key}:[/dim] {value}")

"""Init command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from openagent_eval.cli.context import get_context
from openagent_eval.cli.utils.constants import DEFAULT_CONFIG_CONTENT
from openagent_eval.exceptions import ConfigurationError

console = Console()

# Provider options
LLM_PROVIDERS = [
    ("openai", "OpenAI (GPT-4, GPT-4o, etc.)"),
    ("anthropic", "Anthropic (Claude)"),
    ("gemini", "Google Gemini"),
    ("groq", "Groq (fast inference)"),
    ("openrouter", "OpenRouter (multi-provider)"),
]

RETRIEVER_PROVIDERS = [
    ("chroma", "ChromaDB (local, default)"),
    ("qdrant", "Qdrant"),
    ("pinecone", "Pinecone (cloud)"),
    ("weaviate", "Weaviate"),
    ("faiss", "FAISS (local)"),
    ("memory", "In-memory (testing)"),
]

# Model options per provider
MODEL_OPTIONS = {
    "openai": [
        ("gpt-4o", "GPT-4o (recommended)"),
        ("gpt-4o-mini", "GPT-4o Mini (faster, cheaper)"),
        ("gpt-4-turbo", "GPT-4 Turbo"),
        ("gpt-3.5-turbo", "GPT-3.5 Turbo (legacy)"),
    ],
    "anthropic": [
        ("claude-sonnet-4-20250514", "Claude Sonnet (recommended)"),
        ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku (fast)"),
        ("claude-3-opus-20240229", "Claude 3 Opus (powerful)"),
    ],
    "gemini": [
        ("gemini-1.5-pro", "Gemini 1.5 Pro (recommended)"),
        ("gemini-1.5-flash", "Gemini 1.5 Flash (fast)"),
        ("gemini-2.0-flash", "Gemini 2.0 Flash (latest)"),
    ],
    "groq": [
        ("llama-3.1-70b-versatile", "Llama 3.1 70B (recommended)"),
        ("llama-3.1-8b-instant", "Llama 3.1 8B (fast)"),
        ("mixtral-8x7b-32768", "Mixtral 8x7B"),
    ],
    "openrouter": [
        ("openai/gpt-4o", "GPT-4o via OpenRouter"),
        ("anthropic/claude-sonnet-4-20250514", "Claude Sonnet via OpenRouter"),
        ("meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B via OpenRouter"),
    ],
}

METRIC_PRESETS = {
    "quick": {
        "retrieval": ["context_precision", "context_recall"],
        "generation": ["faithfulness"],
        "performance": ["latency"],
        "cost": ["token_count"],
    },
    "standard": {
        "retrieval": ["context_precision", "context_recall", "mrr"],
        "generation": ["faithfulness", "answer_relevancy"],
        "performance": ["latency"],
        "cost": ["token_count"],
    },
    "comprehensive": {
        "retrieval": ["context_precision", "context_recall", "mrr", "ndcg", "hit_rate"],
        "generation": ["faithfulness", "answer_relevancy", "hallucination", "semantic_similarity"],
        "performance": ["latency"],
        "cost": ["token_count"],
    },
}


def init_command(
    config_path: str = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to create configuration file.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration file.",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Use interactive wizard or defaults.",
    ),
) -> None:
    """Create a new evaluation configuration file interactively or using defaults.

    Args:
        config_path (str): The file path where the configuration YAML should be created.
            Defaults to 'config.yaml'.
        force (bool): Overwrite the configuration file if it already exists.
            Defaults to False.
        interactive (bool): Run an interactive wizard to configure the settings.
            Defaults to True.

    Returns:
        None. Writes the YAML configuration file to the disk.
        Raises ConfigurationError if the configuration file cannot be created/written.
        Raises typer.Exit if creation is aborted or completed.

    Example:
        $ oaeval init --config my_config.yaml --no-interactive
    """
    ctx = get_context()
    path = Path(config_path)

    if path.exists() and not force and not Confirm.ask(
        f"Configuration file '{config_path}' already exists. Overwrite?"
    ):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit()

    if interactive and not ctx.quiet:
        config_content = _interactive_wizard()
    else:
        config_content = DEFAULT_CONFIG_CONTENT

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(config_content, encoding="utf-8")
        console.print(f"\n[green]OK[/green] Configuration created: {config_path}")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("  1. Review the configuration file")
        console.print("  2. Run [bold]oaeval validate[/bold] to check it")
        console.print("  3. Run [bold]oaeval run[/bold] to start evaluation")
    except OSError as e:
        raise ConfigurationError(
            message=f"Failed to create configuration: {e}",
            config_path=config_path,
        ) from e


def _interactive_wizard() -> str:
    """Run interactive configuration wizard.

    Returns:
        Generated YAML configuration string.
    """
    console.print("[bold blue]OpenAgent Eval[/bold blue] - Configuration Wizard\n")
    console.print("Let's set up your evaluation configuration.\n")

    # 1. Dataset path
    console.print("[bold]1. Dataset Configuration[/bold]")
    dataset_path = Prompt.ask(
        "  Path to dataset file",
        default="data/questions.json",
    )

    # 2. LLM Provider
    console.print("\n[bold]2. LLM Provider[/bold]")
    for i, (_, desc) in enumerate(LLM_PROVIDERS, 1):
        console.print(f"  {i}. {desc}")
    provider_idx = Prompt.ask(
        "  Select provider",
        default="1",
        choices=[str(i) for i in range(1, len(LLM_PROVIDERS) + 1)],
    )
    provider_name = LLM_PROVIDERS[int(provider_idx) - 1][0]

    # 3. Model
    console.print(f"\n[bold]3. Model ({provider_name})[/bold]")
    models = MODEL_OPTIONS.get(provider_name, [("custom", "Custom model")])
    for i, (_, desc) in enumerate(models, 1):
        console.print(f"  {i}. {desc}")
    model_idx = Prompt.ask(
        "  Select model",
        default="1",
        choices=[str(i) for i in range(1, len(models) + 1)],
    )
    model_name = models[int(model_idx) - 1][0]

    # 4. Retriever
    console.print("\n[bold]4. Retriever[/bold]")
    for i, (_, desc) in enumerate(RETRIEVER_PROVIDERS, 1):
        console.print(f"  {i}. {desc}")
    retriever_idx = Prompt.ask(
        "  Select retriever",
        default="1",
        choices=[str(i) for i in range(1, len(RETRIEVER_PROVIDERS) + 1)],
    )
    retriever_name = RETRIEVER_PROVIDERS[int(retriever_idx) - 1][0]

    # 5. Metrics
    console.print("\n[bold]5. Metrics[/bold]")
    console.print("  1. Quick (3 metrics) - Fast, basic evaluation")
    console.print("  2. Standard (5 metrics) - Balanced (recommended)")
    console.print("  3. Comprehensive (9 metrics) - Thorough, slower")
    metrics_idx = Prompt.ask(
      "  Select metric preset",
        default="2",
        choices=["1", "2", "3"],
    )
    metrics_preset = ["quick", "standard", "comprehensive"][int(metrics_idx) - 1]
    metrics = METRIC_PRESETS[metrics_preset]

    # 6. Output format
    console.print("\n[bold]6. Output Format[/bold]")
    console.print("  1. terminal - Rich terminal output")
    console.print("  2. markdown - Markdown file")
    console.print("  3. html - HTML report")
    console.print("  4. json - JSON data")
    output_idx = Prompt.ask(
        "  Select output format",
        default="1",
        choices=["1", "2", "3", "4"],
    )
    output_format = ["terminal", "markdown", "html", "json"][int(output_idx) - 1]

    # Build configuration
    config = _build_config(
        dataset_path=dataset_path,
        llm_provider=provider_name,
        model=model_name,
        retriever_provider=retriever_name,
        metrics=metrics,
        output_format=output_format,
    )

    console.print("\n[dim]Configuration generated successfully![/dim]")
    return config


def _build_config(
    dataset_path: str,
    llm_provider: str,
    model: str,
    retriever_provider: str,
    metrics: dict,
    output_format: str,
) -> str:
    """Build YAML configuration string.

    Args:
        dataset_path: Path to dataset file.
        llm_provider: LLM provider name.
        model: Model identifier.
        retriever_provider: Retriever provider name.
        metrics: Metrics configuration dict.
        output_format: Output format.

    Returns:
        YAML configuration string.
    """
    config = f"""\
# OpenAgent Eval Configuration
# Generated by: oaeval init --interactive
#
# For a fully offline dry-run (no API keys / vector store required), set:
#   llm.provider: mock
#   retriever.provider: mock

dataset:
  path: {dataset_path}

llm:
  provider: {llm_provider}
  model: {model}
  temperature: 0.0

retriever:
  provider: {retriever_provider}
  settings:
    collection_name: my_collection

metrics:
  retrieval:
{chr(10).join(f'    - {m}' for m in metrics['retrieval'])}
  generation:
{chr(10).join(f'    - {m}' for m in metrics['generation'])}
  performance:
{chr(10).join(f'    - {m}' for m in metrics['performance'])}
  cost:
{chr(10).join(f'    - {m}' for m in metrics['cost'])}

report:
  output: {output_format}
  output_dir: ./reports
"""
    return config

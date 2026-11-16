# CLI Reference

OpenAgent Eval ships a [Typer](https://typer.tiangolo.com)-based command line interface named `oaeval`.

## Global options

| Option | Description |
| --- | --- |
| `--version`, `-V` | Show the installed version and exit |
| `--help` | Show help for any command |
| `--quiet`, `-q` | Suppress non-essential output |
| `--json` | Output machine-readable JSON |
| `--no-color` | Disable color output |
| `--verbose`, `-v` | Enable verbose output |

```bash
oaeval --version
oaeval --help
oaeval --quiet run config.yaml
oaeval --json run config.yaml
```

## `oaeval init`

Create a `config.yaml` with default settings in the current directory.

```bash
oaeval init
oaeval init --config eval.yaml --force
oaeval init --interactive
```

| Option | Description |
| --- | --- |
| `--config`, `-c` | Path to create (default `config.yaml`) |
| `--force`, `-f` | Overwrite an existing file without prompting |
| `--interactive/--no-interactive` | Use interactive wizard or defaults (default: `--interactive`) |

The interactive wizard guides you through:
1. Dataset path selection
2. LLM provider selection (OpenAI, Anthropic, Gemini, Groq, OpenRouter)
3. Model selection based on provider
4. Retriever selection (Chroma, Qdrant, Pinecone, Weaviate, FAISS, Memory)
5. Metric preset (Quick, Standard, Comprehensive)
6. Output format selection

## `oaeval validate`

Validate configuration without running evaluation.

```bash
oaeval validate config.yaml
oaeval validate
```

| Argument | Description |
| --- | --- |
| `config_path` | Path to configuration file (optional, auto-discovered if not provided) |

The validate command checks:
- YAML syntax validity
- Configuration schema compliance
- API key availability
- Dataset file existence
- Output directory accessibility
- Provider configuration
- Metric configuration

## `oaeval run`

Run an evaluation pipeline using a configuration file.

```bash
oaeval run config.yaml
oaeval run config.yaml --output html --verbose
oaeval run config.yaml --dry-run
oaeval run config.yaml --metrics faithfulness,answer_relevancy,latency
```

| Argument | Description |
| --- | --- |
| `config_path` | Path to the configuration file (optional, auto-discovered if not provided) |

| Option | Description |
| --- | --- |
| `--output`, `-o` | Override output format: `terminal`, `markdown`, `html`, `json` |
| `--verbose`, `-v` | Enable verbose output |
| `--dry-run` | Validate config and show evaluation plan without running |
| `--metrics`, `-m` | Comma-separated list of metrics to run (overrides config) |

## `oaeval report`

View a stored evaluation report.

```bash
oaeval report latest
oaeval report exp-001 --output html
oaeval report latest --json
```

| Argument | Description |
| --- | --- |
| `report_id` | Report ID, or `latest` for the most recent run |

| Option | Description |
| --- | --- |
| `--output`, `-o` | Output format (default `terminal`) |
| `--output-dir`, `-d` | Reports directory (default `./reports`) |

## `oaeval compare`

Compare two experiments side by side.

```bash
oaeval compare exp-001 exp-002
oaeval compare exp-001 exp-002 --metrics faithfulness answer_relevancy
```

| Argument | Description |
| --- | --- |
| `experiment_a` | First experiment ID or path |
| `experiment_b` | Second experiment ID or path |

| Option | Description |
| --- | --- |
| `--metrics`, `-m` | Specific metrics to compare (default: all) |
| `--output-dir`, `-d` | Reports directory (default `./reports`) |

## `oaeval list`

List previous evaluation runs.

```bash
oaeval list --limit 20
oaeval list --sort score --limit 5
oaeval list --search "data/questions" --sort date
```

| Option | Description |
| --- | --- |
| `--limit`, `-l` | Number of evaluations to show (default `10`) |
| `--output`, `-o` | Filter by output format |
| `--output-dir`, `-d` | Reports directory (default `./reports`) |
| `--sort`, `-s` | Sort by: `date`, `score`, or `cost` (default `date`) |
| `--reverse`, `-r` | Reverse sort order |
| `--search` | Search reports by config path or ID |

## `oaeval delete`

Delete evaluation reports.

```bash
oaeval delete exp-001
oaeval delete all --force
```

| Argument | Description |
| --- | --- |
| `report_id` | Report ID to delete, or `all` to delete all reports |

| Option | Description |
| --- | --- |
| `--output-dir`, `-d` | Reports directory (default `./reports`) |
| `--force`, `-f` | Skip confirmation prompt |

## `oaeval doctor`

Check the environment, installed dependencies, and API key availability.

```bash
oaeval doctor --verbose
oaeval doctor --check-api
```

| Option | Description |
| --- | --- |
| `--verbose`, `-v` | Show detailed information |
| `--check-api` | Test API connectivity (requires API keys) |

The doctor command checks:
- Python version compatibility
- Required dependencies
- API key availability
- API connectivity (with `--check-api`)
- Configuration file presence

Use this when something looks wrong after [installation](installation.md).

## `oaeval completion`

Generate shell completion script.

```bash
oaeval completion bash
oaeval completion zsh
oaeval completion fish
```

| Argument | Description |
| --- | --- |
| `shell` | Shell to generate completion for: `bash`, `zsh`, or `fish` |

### Installing completion

```bash
# Bash
oaeval completion bash >> ~/.bashrc

# Zsh
oaeval completion zsh >> ~/.zshrc

# Fish
oaeval completion fish > ~/.config/fish/completions/oaeval.fish
```

## Exit Codes

The CLI returns the following exit codes so scripts and CI/CD pipelines can check command results.

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | General or runtime error |
| `2` | Invalid CLI usage or configuration error |
| `3` | Dataset error |
| `4` | Provider error |
| `5` | Metric error |
| `6` | Corpus error |

## Config auto-discovery

OpenAgent Eval automatically finds your configuration file:

1. Explicit path via command argument
2. `OAEVAL_CONFIG` environment variable
3. `config.yaml` or `config.yml` in current directory
4. `oaeval.yaml` or `oaeval.yml` in current directory
5. Parent directories up to filesystem root

## Next steps

- Embed evaluations in tests via the [API Reference](api.md).
- See real commands in [Examples](examples.md).

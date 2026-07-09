# CLI Reference

OpenAgent Eval ships a Typer-based command line interface named `oaeval`.

## Global options

| Option | Description |
| --- | --- |
| `--version`, `-V` | Show the installed version and exit |
| `--help` | Show help for any command |

```bash
oaeval --version
oaeval --help
```

## `oaeval init`

Create a `config.yaml` file with default settings in the current directory.

```bash
oaeval init
```

## `oaeval run`

Run an evaluation pipeline using a configuration file.

```bash
oaeval run config.yaml
```

| Option | Description |
| --- | --- |
| `--output`, `-o` | Override output format: `terminal`, `markdown`, `html`, `json` |
| `--verbose`, `-v` | Enable verbose output |

```bash
oaeval run config.yaml --output html --verbose
```

## `oaeval report`

View a stored evaluation report.

```bash
oaeval report latest
oaeval report exp-001
```

| Argument | Description |
| --- | --- |
| `id` | Evaluation ID, or `latest` for the most recent run |

## `oaeval compare`

Compare two experiments side by side.

```bash
oaeval compare exp-001 exp-002
```

| Argument | Description |
| --- | --- |
| `a` | First evaluation ID |
| `b` | Second evaluation ID |

## `oaeval list`

List all previously stored evaluations.

```bash
oaeval list
```

## `oaeval doctor`

Check the environment, installed versions, and dependency compatibility.

```bash
oaeval doctor
```

Use this when something looks wrong after [installation](installation.md).

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Configuration or runtime error |
| `2` | Invalid CLI usage |

## Shell completion

`oaeval` is built on Typer and supports shell completion. Enable it for your shell:

```bash
# bash
eval "$(_OAeval_COMPLETE=bash_source oaeval)"

# zsh
eval "$(_OAeval_COMPLETE=zsh_source oaeval)"

# fish
_oaeval_completion fish | source
```

## Next steps

- Embed evaluations in tests via the [API Reference](api.md).
- See real commands in [Examples](examples.md).

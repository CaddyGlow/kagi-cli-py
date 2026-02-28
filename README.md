# kagi-cli-py

Python CLI and client for Kagi services.

PyPI package name: `kagi-cli`

## Features

- `proofread`: improve text quality
- `summarize`: summarize URLs
- `ask`: query Kagi Assistant
- `search`: run Kagi search queries

## Requirements

- Python 3.12+
- A valid `KAGI_SESSION` value from your Kagi session link

## Install

```bash
uv sync
```

## Install and run from PyPI

```bash
# Run without installing globally
uvx --from kagi-cli kagi --help
pipx run --spec kagi-cli kagi --help

# Install globally with pipx
pipx install kagi-cli
kagi --help
```

## Authentication

Set `KAGI_SESSION` from your Kagi session link before using the CLI:

```bash
export KAGI_SESSION="your_session_value_from_link"
```

## CLI usage

```bash
# Show help
uv run kagi --help

# Show version (git tag when available)
uv run kagi --version

# Proofread text
uv run kagi proofread "Ths is a tset."

# Summarize a URL
uv run kagi summarize "https://example.com"

# Ask assistant
uv run kagi ask "What is 2+2?"

# Search
uv run kagi search "python async"
```

## Output formats

Commands support:

- `--format console` (default)
- `--format json`
- `--format md`
- `--format csv`

## Run tests

```bash
uv run pytest -q
```

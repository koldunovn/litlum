# CLAUDE.md

## Project Overview

LitLum is a scientific publication monitoring tool that tracks new papers from journals (via CrossRef API) and arXiv, analyzes their relevance using a local Ollama LLM, and generates reports with a static web interface.

## Architecture

- `litlum/config/` — YAML-based configuration with default + user override layering
- `litlum/feeds/parser.py` — CrossRef and arXiv API feed parsers
- `litlum/llm/analyzer.py` — Ollama LLM integration for relevance scoring and summarization
- `litlum/db/database.py` — SQLite persistence layer
- `litlum/reports/generator.py` — Report generation and display
- `litlum/ui/cli.py` — Rich-based CLI interface (entry point)
- `litlum/web/` — Static site generator and web server

## Running Tests

```bash
/Users/nkolduno/micromamba/envs/litlum/bin/python -m unittest discover tests/ -v
```

pytest is not installed in the environment. Use `unittest` directly.

## Key Commands

```bash
litlum fetch          # Fetch new publications from configured feeds
litlum analyze        # Analyze unprocessed publications with LLM
litlum report --generate  # Generate daily report
litlum run            # Full pipeline: fetch -> analyze -> report -> web
```

## Configuration

- Default config: `litlum/config/default-config.yaml`
- User config: `~/.config/litlum/config.yaml` (overrides defaults)
- Environment variables: `LITLUM_REPORTS_DIR`, `LITLUM_WEB_DIR`

## LLM Prompts

The relevance and summary prompts are in `default-config.yaml` under the `ollama:` key. Interests are defined as descriptive phrases and interpolated into prompts via `{interests}` placeholder. The `config.py:get_ollama_config()` method handles the formatting, joining interests as a bulleted list.

## Dependencies

Python 3.10+, PyYAML, requests, feedparser, python-dateutil, rich, ollama, setuptools.

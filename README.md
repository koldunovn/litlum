# Publication Reader

A scientific publication monitoring and analysis application that tracks RSS feeds from scientific journals, analyzes them using Ollama LLM, and generates relevance reports.

## Features

- **RSS Feed Monitoring**: Track multiple scientific journal feeds
- **LLM Integration**: Use Ollama to analyze publication relevance and generate summaries
- **SQLite Database**: Store publications, analysis results, and daily reports
- **Rich CLI Interface**: User-friendly terminal interface with formatted output
- **Scheduled Execution**: Can be run via cron job for automated monitoring
- **Customizable**: Configure RSS feeds, LLM prompts, and more via configuration file

## Installation

### Prerequisites

- Python 3.8+
- Micromamba (for environment management)
- Ollama (for LLM integration)

### Setup with Micromamba

1. Create a new environment:

```bash
micromamba create -n publication_reader python=3.10
```

2. Install the package and dependencies:

```bash
# Activate the environment (or use micromamba run -n publication_reader)
micromamba run -n publication_reader pip install -e .
```

### Ollama Setup

Make sure Ollama is installed and running on your system. By default, the application will try to connect to Ollama at `http://localhost:11434`.

To install Ollama, follow the instructions at: https://ollama.com/download

Pull the LLM model specified in your config (default is llama3.2):

```bash
ollama pull llama3.2
```

## Usage

The application provides a command-line interface with several commands:

### Basic Commands

```bash
# Fetch new publications from configured RSS feeds
micromamba run -n publication_reader python -m publication_reader fetch

# Analyze unprocessed publications
micromamba run -n publication_reader python -m publication_reader analyze

# Generate and display a report for today
micromamba run -n publication_reader python -m publication_reader report --generate

# Run the full pipeline (fetch, analyze, report)
micromamba run -n publication_reader python -m publication_reader run
```

### Additional Commands

```bash
# List available reports
micromamba run -n publication_reader python -m publication_reader list --reports

# List recent publications with minimum relevance score
micromamba run -n publication_reader python -m publication_reader list --publications --days 7 --min-relevance 5

# Show details for a specific publication
micromamba run -n publication_reader python -m publication_reader show <publication_id>

# Reanalyze publications from a specific date
micromamba run -n publication_reader python -m publication_reader analyze --date 2025-05-30 --reanalyze

# Reset the database (useful for debugging)
micromamba run -n publication_reader python -m publication_reader reset

# Reset without confirmation prompt
micromamba run -n publication_reader python -m publication_reader reset --force
```

## Configuration

The default configuration file is created at `~/.config/publication_reader/config.yaml` when you first run the application. You can edit this file to:

- Add or modify RSS feeds
- Configure the Ollama model and prompts
- Change database and reports paths

Example configuration:

```yaml
feeds:
  - name: Nature
    url: https://www.nature.com/nature.rss
    type: rss
  - name: Science
    url: https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science
    type: rss
  - name: PNAS
    url: https://www.pnas.org/action/showFeed?type=etoc&feed=rss
    type: rss
database:
  path: ~/.local/share/publication_reader/publications.db
ollama:
  model: llama3
  host: http://localhost:11434
  relevance_prompt: >
    Analyze this scientific publication and determine if it's relevant based on the following interests:
    artificial intelligence, machine learning, computational biology.
    Rate relevance from 0-10 and explain why.
  summary_prompt: >
    Create a concise summary of this scientific publication highlighting key findings and methodology.
reports:
  path: ~/.local/share/publication_reader/reports
```

## Setting Up a Cron Job

To run the application automatically, you can set up a cron job:

1. Create a script to run the application (e.g., `~/scripts/run_publication_reader.sh`):

```bash
#!/bin/bash
export PATH="/path/to/micromamba/bin:$PATH"
micromamba run -n publication_reader python -m publication_reader run
```

2. Make the script executable:

```bash
chmod +x ~/scripts/run_publication_reader.sh
```

3. Add a cron job (edit with `crontab -e`):

```
# Run daily at 8 AM
0 8 * * * ~/scripts/run_publication_reader.sh
```

## Future Development

This application is designed with future extensibility in mind:

- Web interface development
- More sophisticated relevance analysis
- Additional publication sources
- Email notifications
- Custom user interests configuration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

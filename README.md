# Litlum

A scientific publication monitoring and analysis application that tracks RSS feeds from scientific journals, analyzes them using Ollama LLM, and generates relevance reports.

## Features

- **RSS Feed Monitoring**: Track multiple scientific journal feeds
- **LLM Integration**: Use Ollama to analyze publication relevance and generate summaries
- **SQLite Database**: Store publications, analysis results, and daily reports
- **Rich CLI Interface**: User-friendly terminal interface with formatted output
- **Static Web Interface**: Browse reports and publications through a clean, modern web UI
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
micromamba create -n litlum python=3.10
```

2. Install the package and dependencies:

```bash
# Activate the environment (or use micromamba run -n litlum)
micromamba run -n litlum pip install -e .
```

### Ollama Setup

Make sure Ollama is installed and running on your system. By default, the application will try to connect to Ollama at `http://localhost:11434`.

To install Ollama, follow the instructions at: https://ollama.com/download

Pull the LLM model specified in your config (default is llama3.2):

```bash
ollama pull llama3.2
```

## Usage

First, activate the micromamba environment:

```bash
# Activate the litlum environment
micromamba activate litlum

# Or run a single command:
# micromamba run -n litlum <command>
```

The application provides a command-line interface with several commands:

### Basic Commands

```bash
# Fetch new publications from configured RSS feeds
python -m litlum fetch

# Analyze unprocessed publications
python -m publication_reader analyze

# Generate and display a report for today
python -m publication_reader report --generate

# Run the full pipeline (fetch, analyze, report)
python -m publication_reader run

# Run the full pipeline (fetch, analyze, report) and serve the web interface
python -m litlum run --serve
```

### Additional Commands

```bash
# List available reports
python -m litlum list --reports

# List recent publications with minimum relevance score
python -m litlum list --publications --days 7 --min-relevance 5

# Show details for a specific publication
python -m litlum show <publication_id>

# Reanalyze publications from a specific date
python -m publication_reader analyze --date 2025-05-30 --reanalyze

# Reset the database (useful for debugging)
python -m publication_reader reset

# Reset without confirmation prompt
python -m publication_reader reset --force
```

### Advanced Usage

This section demonstrates more complex workflows and advanced options for working with the LitLum application.

#### Viewing Individual Publications

To view detailed information about a specific publication, including its abstract, relevance score, and LLM-generated summary:

```bash
# Show publication with ID 5
python -m litlum show 5
```


#### Filtering Publications by Date and Relevance

Filter publications by date range and minimum relevance score:

```bash
# List publications from the last 14 days with relevance score of at least 6
python -m litlum list --publications --days 14 --min-relevance 6

```

#### Reanalyzing Publications

Reanalyze publications if you've changed your interests or LLM configuration:

```bash
# Reanalyze all publications
python -m litlum analyze --reanalyze

# Reanalyze publications from a specific date
python -m publication_reader analyze --date 2025-05-30 --reanalyze

```

#### Working with Reports

Generate and view reports:

```bash
# Generate a report for today
python -m publication_reader report --generate

# Generate a report for a specific date
python -m litlum report --generate --date 2025-05-30

# View a report for a specific date
python -m litlum report --date 2025-05-30
```

> Note: The minimum relevance for reports is configured in the `config.yaml` file under the `reports` section. To customize this, update your configuration file.

#### Debugging

The application includes debug output in the analyzer to show LLM prompts and responses. This output is always enabled when running the analyze command.

For troubleshooting database issues, you can reset the database:

```bash
# Reset the database (will prompt for confirmation)
python -m publication_reader reset

# Force reset without confirmation
python -m publication_reader reset --force
```

## Configuration

The default configuration file is created at `~/.config/litlum/config.yaml` when you first run the application. You can edit this file to:

- Add or modify RSS feeds
- Configure the Ollama model and prompts
- Change database and reports paths

Example configuration:

```yaml
crossref:
  days_range: 10
database:
  path: ~/.local/share/litlum/publications.db
feeds:
- issn: 2169-9291
  name: JGR Oceans
  type: crossref
- issn: 1812-0792
  name: Ocean Science
  type: crossref

interests:
- Arctic ocean
- climate modelling
- high resolution modelling
- sea ice
- Southern Ocean
- climate change
ollama:
  host: http://localhost:11434
  model: llama3.2
  relevance_prompt: 'Analyze this scientific publication and determine if it''s relevant
    based on the following interests: {interests}. Rate relevance from 0-10 and explain
    why. Keep your explanation brief (1-2 sentences).'
  summary_prompt: 'Create a very concise summary (1-2 sentences) of this scientific
    publication highlighting key findings and briefly explain its relevance to the
    following interests: {interests}.'
reports:
  min_relevance: 5
  path: ~/.local/share/litlum/reports

```

## Setting Up a Cron Job

To run the application automatically, you can set up a cron job:

1. Create a script to run the application (e.g., `~/scripts/run_litlum.sh`):

```bash
#!/bin/bash
export PATH="/path/to/micromamba/bin:$PATH"

# Activate the environment and run the command
micromamba activate litlum
python -m litlum run
```

2. Make the script executable:

```bash
chmod +x ~/scripts/run_litlum.sh
```

3. Add a cron job (edit with `crontab -e`):

```
# Run daily at 8 AM
0 8 * * * ~/scripts/run_litlum.sh
```

## Web Interface

The LitLum application now includes a static web interface that makes it easy to browse reports and publications:

### Features

- **Index Page**: Lists all available reports by date
- **Report Pages**: Displays publications above the relevance threshold
- **Interactive Tables**: Each publication includes:
  - Title and journal information
  - Relevance score
  - Link to the original paper (via DOI/URL)
  - Expandable sections for AI assessment and abstract
- **Responsive Design**: Works on desktop and mobile devices

### Using the Web Interface

```bash
# Generate the static website
python -m publication_reader web

# Generate and serve the website locally
python -m litlum web --serve
```

The web interface will be generated in the configured web path (default: `~/.local/share/litlum/web`).

## Future Development

This application is designed with future extensibility in mind:

- More sophisticated relevance analysis
- Additional publication sources
- Email notifications
- Custom user interests configuration
- Enhanced web interface with search and filtering

## License

This project is licensed under the MIT License - see the LICENSE file for details.

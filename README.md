# LitLum

A scientific publication monitoring and analysis application that tracks new publications from scientific journals, analyzes them using Ollama LLM, and generates relevance reports.

## Features

- **Journal Monitoring using CrossRef**: Track multiple scientific journal feeds
- **LLM Integration**: Use Ollama to analyze publication relevance and generate summaries
- **SQLite Database**: Store publications, analysis results, and daily reports
- **Rich CLI Interface**: User-friendly terminal interface with formatted output
- **Static Web Interface**: Browse reports and publications through a clean, modern web UI
- **Customizable**: Configure journals, LLM prompts, and more via YAML configuration
- **Docker Support**: Easy deployment using Docker containers
- **Configuration Management**: Default configuration with user overrides

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


# Or, if you prefer to use the environment just for a single command:
micromamba run -n publication_reader <command>
```

The application provides a command-line interface with several commands. You can run the application in multiple ways:

1. **Recommended**: Using the `litlum` command (after installation with `pip install -e .`):
   ```bash
   # First activate the environment
   micromamba activate litlum
   
   # Then use the litlum command
   litlum --help  # Show help and available commands
   ```
   > **Note**: The `litlum` command is only available when the environment is activated.

2. Using Python's `-m` flag (works without activating the environment):
   ```bash
   python -m litlum --help
   ```

3. Using Micromamba (works without activating the environment):
   ```bash
   micromamba run -n litlum litlum --help
   ```

### Basic Commands

```bash
# Fetch new publications from configured RSS feeds
litlum fetch

# Analyze unprocessed publications
litlum analyze

# Generate and display a report for today
litlum report --generate

# Run the full pipeline (fetch, analyze, report)
litlum run

# Run the full pipeline (fetch, analyze, report) and serve the web interface
litlum run --serve
```

### Additional Commands

```bash
# List available reports
litlum list --reports

# List recent publications with minimum relevance score
litlum list --publications --days 7 --min-relevance 5

# Show details for a specific publication
litlum show <publication_id>

# Reanalyze publications from a specific date
litlum analyze --date 2025-05-30 --reanalyze

# Reset the database (useful for debugging)
litlum reset

# Reset without confirmation prompt
micromamba run -n litlum python -m litlum reset --force
```

### Advanced Usage

This section demonstrates more complex workflows and advanced options for working with the LitLum application.

#### Viewing Individual Publications

To view detailed information about a specific publication, including its abstract, relevance score, and LLM-generated summary:

```bash
# Show publication with ID 5
litlum show 5
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

LitLum uses a layered configuration system that loads settings in the following order (each layer overrides the previous one):

1. **Default Configuration** - Built-in default settings from `litlum/config/default-config.yaml`
2. **User Configuration** - Custom settings from `~/.config/litlum/config.yaml` (if exists)
3. **Environment Variables** - Specific path overrides (see below)

### Viewing Current Configuration

When you run any LitLum command, it will show which configuration files are being loaded:

```
[INFO] Loading default configuration from: /path/to/package/litlum/config/default-config.yaml
[INFO] Successfully loaded default configuration
[INFO] Loading user configuration from: /home/username/.config/litlum/config.yaml
[INFO] Successfully loaded user configuration
```

If no user configuration is found, you'll see:

```
[INFO] Loading default configuration from: /path/to/package/litlum/config/default-config.yaml
[INFO] Successfully loaded default configuration
[INFO] No user configuration found at /home/username/.config/litlum/config.yaml. Using default configuration.
```

You can also check the configuration files directly:
1. Default configuration: `litlum/config/default-config.yaml` in the package directory
2. User configuration: `~/.config/litlum/config.yaml` (if it exists)

### Default Configuration

The default configuration includes sensible defaults for all settings. You can find the complete default configuration in the package's `litlum/config/default-config.yaml`.

### User Configuration

To customize settings, create a `config.yaml` file in `~/.config/litlum/`. This file will be merged with the default configuration, with your settings taking precedence.

Example user configuration (`~/.config/litlum/config.yaml`):

```yaml
# Override database location
database:
  path: "/custom/path/publications.db"

# Customize your interests
interests:
  - "Arctic ocean"
  - "climate modelling"
  - "machine learning"
  - "ocean eddies"

# Configure Ollama LLM settings
ollama:
  model: "llama3.2"  # or "gemma3:27b" for better results
  host: "http://localhost:11434"

# Add or modify journal feeds
feeds:
  - name: "Nature Climate Change"
    type: "crossref"
    issn: "1758-6798"
    active: true
  - name: "Science"
    type: "crossref"
    issn: "1095-9203"
    active: true

# Reports configuration
reports:
  min_relevance: 5.0  # Minimum relevance score (0-10) for including publications in reports

# Web interface settings
web:
  title: "My Custom LitLum"
```

### Environment Variables

The following environment variables can be used to override specific paths:

- `LITLUM_REPORTS_DIR`: Override the directory for storing reports
- `LITLUM_WEB_DIR`: Override the web output directory

Note: Database path can only be configured through the config file, not via environment variables.

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

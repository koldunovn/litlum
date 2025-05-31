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

First, activate the micromamba environment:

```bash
# Activate the publication_reader environment
micromamba activate publication_reader

# Or, if you prefer to use the environment just for a single command:
# micromamba run -n publication_reader <command>
```

The application provides a command-line interface with several commands:

### Basic Commands

```bash
# Fetch new publications from configured RSS feeds
python -m publication_reader fetch

# Analyze unprocessed publications
python -m publication_reader analyze

# Generate and display a report for today
python -m publication_reader report --generate

# Run the full pipeline (fetch, analyze, report)
python -m publication_reader run
```

### Additional Commands

```bash
# List available reports
python -m publication_reader list --reports

# List recent publications with minimum relevance score
python -m publication_reader list --publications --days 7 --min-relevance 5

# Show details for a specific publication
python -m publication_reader show <publication_id>

# Reanalyze publications from a specific date
python -m publication_reader analyze --date 2025-05-30 --reanalyze

# Reset the database (useful for debugging)
python -m publication_reader reset

# Reset without confirmation prompt
python -m publication_reader reset --force
```

### Advanced Usage

This section demonstrates more complex workflows and advanced options for working with the publication reader.

#### Viewing Individual Publications

To view detailed information about a specific publication, including its abstract, relevance score, and LLM-generated summary:

```bash
# Show publication with ID 5
python -m publication_reader show 5
```

Example output:

```
╭──────────────────────────────────────────────────────────────────────────────╮
│                                                                              │
│   Seasonal and Interannual Variability of the Aragonite Saturation Horizon   │
│                in the California Current System of Baja California           │
│                                                                              │
│  ID: 5 | Date: 2025-05-28 | Journal: JGR Oceans | Relevance: 4/10           │
│  URL: https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024JC021884      │
│                                                                              │
│  Abstract:                                                                   │
│  This study investigated the factors influencing the seasonal and            │
│  interannual variability of the aragonite saturation horizon (ASH) in the    │
│  California Current System off Baja California. We used hydrographic data    │
│  collected from 2004 to 2022 to construct regression models between ASH      │
│  depth and variables such as dissolved inorganic carbon, sea surface         │
│  temperature, salinity, dissolved oxygen, and atmospheric CO2                │
│  concentrations. We found that sea surface temperature and atmospheric CO2   │
│  explain most of the ASH variability on seasonal and interannual scales.     │
│  Our results show a shoaling ASH trend of ‐1.14±0.49 m yr‐1, confirming     │
│  that ocean acidification is affecting the region.                           │
│                                                                              │
│  LLM Analysis:                                                               │
│  Relevance Score: 4/10                                                       │
│  Explanation: This study focuses on ocean acidification in the California    │
│  Current System rather than the Arctic or Southern Ocean. While it does      │
│  relate to climate change impacts on marine environments, it doesn't         │
│  specifically address the interests of Arctic ocean, sea ice, or climate     │
│  modeling in polar regions.                                                  │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### Filtering Publications by Date and Relevance

Filter publications by date range and minimum relevance score:

```bash
# List publications from the last 14 days with relevance score of at least 6
python -m publication_reader list --publications --days 14 --min-relevance 6

# List publications from a specific date range
python -m publication_reader list --publications --from-date 2025-05-01 --to-date 2025-05-31 --min-relevance 5
```

#### Reanalyzing Publications

Reanalyze publications if you've changed your interests or LLM configuration:

```bash
# Reanalyze all publications
python -m publication_reader analyze --reanalyze

# Reanalyze publications from a specific date
python -m publication_reader analyze --date 2025-05-30 --reanalyze

# To reanalyze specific publications, you'll need to reset and selectively fetch
# For example, to reanalyze only certain journals, you would modify your config.yaml
# temporarily to include only those feeds, then run:
python -m publication_reader reset --force
python -m publication_reader fetch
python -m publication_reader analyze
```

#### Working with Reports

Generate and view reports:

```bash
# Generate a report for today
python -m publication_reader report --generate

# Generate a report for a specific date
python -m publication_reader report --generate --date 2025-05-30

# View a report for a specific date
python -m publication_reader report --date 2025-05-30
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

The default configuration file is created at `~/.config/publication_reader/config.yaml` when you first run the application. You can edit this file to:

- Add or modify RSS feeds
- Configure the Ollama model and prompts
- Change database and reports paths

Example configuration:

```yaml
feeds:
  - name: JGR Oceans
    url: https://agupubs.onlinelibrary.wiley.com/action/showFeed?jc=21699291&type=etoc&feed=rss
    type: rss
  - name: Ocean Science
    url: https://os.copernicus.org/rss.xml
    type: rss
  - name: Earth's Future
    url: https://agupubs.onlinelibrary.wiley.com/action/showFeed?jc=23284277&type=etoc&feed=rss
    type: rss

# Separate interests section for better organization and flexibility
interests:
  - Arctic ocean
  - climate modelling
  - high resolution modelling
  - sea ice
  - Southern Ocean
  - climate change

database:
  path: ~/.local/share/publication_reader/publications.db

ollama:
  model: llama3.2  # Using a specific model version
  host: http://localhost:11434
  relevance_prompt: >
    Analyze this scientific publication and determine if it's relevant based on the following interests: {interests}.
    Rate relevance from 0-10 and explain why. Keep your explanation brief (1-2 sentences).
  summary_prompt: >
    Create a concise summary of this scientific publication highlighting key findings and methodology.
    Keep the summary to 1-2 sentences. Include relevance to these interests: {interests}.

reports:
  path: ~/.local/share/publication_reader/reports
  min_relevance: 6  # Only include publications with relevance score ≥ 6
```

## Setting Up a Cron Job

To run the application automatically, you can set up a cron job:

1. Create a script to run the application (e.g., `~/scripts/run_publication_reader.sh`):

```bash
#!/bin/bash
export PATH="/path/to/micromamba/bin:$PATH"

# Activate the environment and run the command
micromamba activate publication_reader
python -m publication_reader run
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

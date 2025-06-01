# Running LitLum with Docker

This document explains how to run the LitLum application using Docker Compose, including building the image, running containers, and managing persistent data.

## Prerequisites

- Docker and Docker Compose installed on your system
- At least 2GB of free disk space for the Docker image and data
- Ollama running on your host machine (for LLM integration)

## Quick Start with Docker Compose

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/yourusername/litlum.git
   cd litlum
   ```

2. **Set up directories**:
   ```bash
   # Create directories for persistent storage
   mkdir -p data/web data/reports config
   
   # Set proper permissions
   chmod -R 777 data config
   ```

3. **Start the services**:
   ```bash
   # Build and start the container
   docker compose up --build
   ```
   
   This will:
   - Build the LitLum Docker image
   - Start the container with proper volume mounts
   - Run the LitLum workflow (fetch, analyze, generate reports)
   - Start a web server on port 8000

4. **Access the web interface**:
   - Open your browser and go to: http://localhost:8000

## Managing the Application

### Viewing Logs
```bash
# Follow the logs in real-time
docker compose logs -f

# View the last 100 lines of logs
docker compose logs --tail=100
```

### Running Commands
You can run any LitLum command in the container:

```bash
# Show help
docker compose exec litlum litlum --help

# Fetch new publications
docker compose exec litlum litlum fetch

# Generate reports
docker compose exec litlum litlum report generate

# Start the web server
docker compose exec litlum litlum web --serve
```

### Stopping the Application
```bash
# Stop the container
docker compose down

# Stop and remove volumes (deletes all data)
docker compose down -v
```

## Configuration

### Customizing Configuration
1. Edit the configuration file at `config/config.yaml`
2. Restart the container for changes to take effect

### Environment Variables
You can customize the following environment variables in `docker-compose.yml`:

- `OLLAMA_HOST`: Host and port for Ollama (default: `host.docker.internal:11434`)
- `LITLUM_CONFIG_DIR`: Directory for configuration files (default: `/config`)
- `LITLUM_DATA_DIR`: Directory for data storage (default: `/data`)
- `LITLUM_WEB_DIR`: Directory for web interface files (default: `/data/web`)
- `LITLUM_REPORTS_DIR`: Directory for report files (default: `/data/reports`)

## Data Persistence
All data is stored in the following directories on your host machine:

- `./data/web`: Generated web interface files
- `./data/reports`: Generated report files
- `./config`: Configuration files

## Troubleshooting

### Web Interface Not Loading
If the web interface is not accessible:

1. Check the logs for errors:
   ```bash
   docker compose logs
   ```

2. Ensure the web files were generated:
   ```bash
   ls -la data/web/
   ```

3. If needed, manually generate the web interface:
   ```bash
   docker compose exec litlum litlum web generate
   ```

### Rebuilding the Container
If you make changes to the code or configuration:

```bash
# Rebuild and restart
docker compose up --build -d
```

## Updating
To update to the latest version:

```bash
# Pull the latest changes
git pull

# Rebuild and restart
docker compose up --build -d
```
  -e OLLAMA_HOST=host.docker.internal:11434 \
  -p 8000:8000 \
  litlum --help
```

## Configuration

The application will create a default configuration file at `/config/config.yaml` if it doesn't exist. You can edit this file to customize the application settings.

### Environment Variables

You can override the following environment variables:

- `LITLUM_CONFIG_DIR`: Directory containing the config file (default: `/config`)
- `LITLUM_DATA_DIR`: Base directory for data storage (default: `/data`)
- `OLLAMA_HOST`: Ollama server URL (default: `http://host.docker.internal:11434`)

## Persistent Storage

The Docker container uses the following volume mounts for persistent storage:

- `/config`: Contains the application configuration (`config.yaml`)
- `/data`: Contains the database, reports, and web content
  - `/data/reports`: Generated report files
  - `/data/web`: Static website files
  - `/data/litlum.db`: SQLite database file

## Common Commands

### Update feeds and generate reports
```bash
docker-compose exec litlum litlum update
```

### View reports in the terminal
```bash
docker-compose exec litlum litlum show-reports
```

### Access the web interface
If you have the web interface enabled, it will be available at http://localhost:8000

### View logs
```bash
docker-compose logs -f
```

## Development

### Rebuild the container after changes
```bash
docker-compose build --no-cache
```

### Run tests
```bash
docker-compose exec litlum pytest
```

## Troubleshooting

### Ollama Connection Issues
If you're having trouble connecting to Ollama, try:
1. Make sure Ollama is running on your host machine
2. Use `host.docker.internal` as the hostname to connect to services on the host (works on Mac/Windows)
3. On Linux, you might need to use `--network=host` instead of port mapping

### Permission Issues
If you encounter permission issues with the mounted volumes, try:
```bash
sudo chown -R $USER:$USER ~/litlum
```

### View Container Shell
To get a shell inside the running container:
```bash
docker-compose exec litlum /bin/bash
```

## Production Deployment

For production deployments, consider:
1. Using a proper database like PostgreSQL instead of SQLite
2. Setting up proper backups for the database
3. Configuring HTTPS for the web interface
4. Setting up log rotation
5. Using environment variables for sensitive configuration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository.

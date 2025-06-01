#!/bin/sh
set -e

# Debug: Print environment variables
echo "=== Environment Variables ==="
printenv | sort
echo "==========================="

# Create necessary directories with correct permissions
mkdir -p /data/reports /data/web
chmod -R 777 /data  # Using 777 for now to avoid permission issues

# Ensure config directory exists and has correct permissions
mkdir -p "$LITLUM_CONFIG_DIR"
chmod -R 777 "$LITLUM_CONFIG_DIR"  # Using 777 for now to avoid permission issues

# Create a default config if it doesn't exist
if [ ! -f "$LITLUM_CONFIG_DIR/config.yaml" ]; then
    echo "Creating default config in $LITLUM_CONFIG_DIR/config.yaml"
    mkdir -p "$LITLUM_CONFIG_DIR"
    
    # Create a minimal config that will be merged with the default config
    cat > "$LITLUM_CONFIG_DIR/config.yaml" << 'EOL'
# User configuration for LitLum
# This file overrides the default configuration

# Database path (relative to LITLUM_DATA_DIR or absolute path)
database:
  path: "litlum.db"

# Storage paths (relative to LITLUM_DATA_DIR or absolute paths)
storage:
  reports: "reports"
  web: "web"

# Ollama configuration
ollama:
  host: "${OLLAMA_HOST:-http://host.docker.internal:11434}"
  model: "llama3.2"
  temperature: 0.7
  system_prompt: "You are a helpful research assistant that analyzes scientific publications."
  relevance_prompt: |
    Analyze this scientific publication and determine if it's relevant based on the following interests: {interests}.
    Rate relevance from 0-10 and explain why. Keep your explanation brief (1-2 sentences).
  summary_prompt: |
    Create a very concise summary (1-2 sentences) of this scientific publication 
    highlighting key findings and its relevance to: {interests}.

# Interests for filtering publications
interests:
  - "ocean modeling"
  - "climate change"
  - "ocean circulation"
  - "marine ecosystems"
  - "climate modeling"
  - "ocean eddies"
  - "sea ice"
  - "Southern Ocean"
  - "Arctic"
  - "machine learning in climate science"

# Feed configuration
feeds:
  - name: "JGR Oceans"
    type: "crossref"
    issn: "2169-9291"
    active: true
  - name: "Nature Climate Change"
    type: "crossref"
    issn: "1758-6798"
    active: true
  - name: "Science"
    type: "crossref"
    issn: "1095-9203"
    active: true

# Application settings
min_relevance: 5  # 0-10 scale
update_interval: 3600  # in seconds
log_level: "INFO"
EOL
    
    chmod 644 "$LITLUM_CONFIG_DIR/config.yaml"
    
    echo "Default configuration created at $LITLUM_CONFIG_DIR/config.yaml"
else
    echo "Using existing configuration from $LITLUM_CONFIG_DIR/config.yaml"
fi

# Create necessary directories if they don't exist
for dir in "/data/reports" "/data/web"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chmod 755 "$dir"
    fi
done

# Set proper permissions on the data directory
chmod -R 755 /data

# Print configuration summary
echo "=== Configuration Summary ==="
echo "Config directory: $LITLUM_CONFIG_DIR"
echo "Data directory: $LITLUM_DATA_DIR"
echo "Ollama host: ${OLLAMA_HOST:-http://host.docker.internal:11434}"

# Add the current directory to PYTHONPATH
export PYTHONPATH="/app:${PYTHONPATH}"

# Execute the command directly without gosu
if [ "$1" = "litlum" ] || [ "$1" = "/usr/local/bin/litlum" ]; then
    shift
    exec litlum "$@"
else
    exec "$@"
fi

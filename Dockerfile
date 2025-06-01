# Use Python 3.11-slim as the base image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --user -r requirements.txt

# Copy the application code
COPY . .

# Install the package in development mode
RUN pip install --user -e .

# Final stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/root/.local/bin:$PATH" \
    LITLUM_CONFIG_DIR=/config \
    LITLUM_DATA_DIR=/data \
    OLLAMA_HOST=host.docker.internal:11434

# Install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /config /data && \
    chmod -R 755 /config /data

# Set the working directory
WORKDIR /app

# Copy the installed package from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Install the package in development mode in the final image
WORKDIR /app
RUN pip install -e .

# Copy the entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set up volume mount points
VOLUME ["/config", "/data"]

# Set the entrypoint and default command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["litlum"]

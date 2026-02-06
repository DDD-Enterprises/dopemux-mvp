# LiteLLM Proxy Server for Dopemux
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install LiteLLM with all optional dependencies
RUN pip install --no-cache-dir \
    litellm[proxy]==1.75.0 \
    prisma \
    pyyaml

# Copy configuration and entrypoint from docker/mcp-servers/litellm/
COPY docker/mcp-servers/litellm/litellm.config.yaml /app/config.yaml
COPY docker/mcp-servers/litellm/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 4000

# NOTE: Healthcheck defined in docker-compose.yml to use correct auth token

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

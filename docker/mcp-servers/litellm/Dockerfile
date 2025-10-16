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

# Generate Prisma binaries
RUN prisma generate --schema=/usr/local/lib/python3.11/site-packages/litellm/proxy/schema.prisma

# Copy configuration
COPY litellm.config.yaml /app/config.yaml

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

# Start LiteLLM proxy server
CMD ["litellm", "--config", "/app/config.yaml", "--port", "4000", "--host", "0.0.0.0"]

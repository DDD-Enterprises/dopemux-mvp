FROM python:3.11-slim

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from centralized manifest
RUN pip install --no-cache-dir .[services]

# Copy application code (relative to root)
COPY docker/mcp-servers-source/exa/exa_server.py .

# Environment variables
ENV MCP_SERVER_PORT=3011
ENV EXA_API_KEY=""
ENV PORT=3011

EXPOSE 3011

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3011/health || exit 1

ENTRYPOINT ["python", "exa_server.py"]

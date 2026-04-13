# Dope-Context MCP Server Dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install dependencies from centralized manifest
RUN uv pip install --system --no-cache .[services] mcp-proxy

# Copy the entire dope-context service (relative to root)
COPY services/dope-context/ .

# Try to install the MCP package if it exists
RUN if [ -d "/app/src/mcp" ]; then cd /app/src/mcp && uv pip install --system --no-cache -e . || true; fi

# Set environment variables
ENV MCP_SERVER_PORT=3010
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Health check - verify MCP server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:3010/health || exit 0

# Labels
LABEL mcp.role="search"
LABEL mcp.priority="high"
LABEL mcp.description="Semantic code and document search with AST-aware indexing"

# Run the canonical FastMCP server
CMD ["python", "-m", "src.mcp.server"]

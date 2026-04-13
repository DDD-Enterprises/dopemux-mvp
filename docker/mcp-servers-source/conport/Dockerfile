# ConPort MCP Server Dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    git \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from centralized manifest
RUN uv uv pip install --system --no-cache --system --no-cache .[services]

# Copy shared monitoring module (relative to root build context)
RUN mkdir -p /app/shared/monitoring
COPY docker/mcp-servers-source/conport/shared_monitoring.py /app/shared/monitoring/base.py
COPY docker/mcp-servers-source/conport/shared_monitoring_init.py /app/shared/monitoring/__init__.py

# Copy the enhanced server with PostgreSQL + Redis persistence (relative to root)
COPY docker/mcp-servers-source/conport/server.py .
COPY docker/mcp-servers-source/conport/enhanced_server.py .
COPY docker/mcp-servers-source/conport/instance_detector.py .
COPY docker/mcp-servers-source/conport/integration_bridge_client.py .
COPY docker/mcp-servers-source/conport/conport_mcp_stdio.py .
COPY docker/mcp-servers-source/conport/schema.sql .
COPY docker/mcp-servers-source/conport/info_server.py .
COPY docker/mcp-servers-source/conport/start_with_info.sh .

# Expose ports (MCP server + info server)
EXPOSE 3004 4004

# Health check - test the enhanced HTTP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1

# Run both MCP server and info server
CMD ["bash", "start_with_info.sh"]

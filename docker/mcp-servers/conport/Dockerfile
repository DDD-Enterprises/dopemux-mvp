# ConPort MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies for enhanced server with database persistence
RUN pip install uv aiohttp asyncpg redis mcp prometheus-client fastapi uvicorn

# Copy shared monitoring module
RUN mkdir -p /app/shared/monitoring
COPY shared_monitoring.py /app/shared/monitoring/base.py
COPY shared_monitoring_init.py /app/shared/monitoring/__init__.py

# Copy the enhanced server with PostgreSQL + Redis persistence
COPY enhanced_server.py .
COPY instance_detector.py .
COPY integration_bridge_client.py .
COPY conport_mcp_stdio.py .
COPY schema.sql .
COPY info_server.py .
COPY start_with_info.sh .

# Expose ports (MCP server + info server)
EXPOSE 3004 4004

# Health check - test the enhanced HTTP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1

# Run both MCP server and info server
CMD ["bash", "start_with_info.sh"]

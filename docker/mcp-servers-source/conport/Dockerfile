# ConPort MCP Server Dockerfile
FROM python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:ecd4de2f060c64bea0ff8ecb182ddf46ba3fcccdc8a60cfdbaf20d1a047d7437 /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .
COPY src src
COPY tools tools

# Install system dependencies from immutable Debian snapshots.
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' \
      'Types: deb' \
      'URIs: https://snapshot.debian.org/archive/debian/20260722T022634Z/' \
      'Suites: trixie trixie-updates' \
      'Components: main' \
      'Check-Valid-Until: no' \
      '' \
      'Types: deb' \
      'URIs: https://snapshot.debian.org/archive/debian-security/20260722T034327Z/' \
      'Suites: trixie-security' \
      'Components: main' \
      'Check-Valid-Until: no' \
      > /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y \
    bash \
    git \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from centralized manifest
RUN uv sync --frozen --no-dev --extra services
ENV PATH="/app/.venv/bin:${PATH}"

# Copy shared monitoring module (relative to root build context)
RUN mkdir -p /app/shared/monitoring
COPY docker/mcp-servers-source/conport/shared_monitoring.py /app/shared/monitoring/base.py
COPY docker/mcp-servers-source/conport/shared_monitoring_init.py /app/shared/monitoring/__init__.py

# Copy the enhanced server with PostgreSQL + Redis persistence (relative to root)
COPY docker/mcp-servers-source/conport/server.py .
COPY docker/mcp-servers-source/conport/enhanced_server.py .
COPY docker/mcp-servers-source/conport/unified_queries.py .
COPY docker/mcp-servers-source/conport/instance_detector.py .
COPY docker/mcp-servers-source/conport/integration_bridge_client.py .
COPY docker/mcp-servers-source/conport/conport_mcp_stdio.py .
COPY docker/mcp-servers-source/conport/schema.sql .
COPY docker/mcp-servers-source/conport/migrations /app/migrations
COPY docker/mcp-servers-source/conport/info_server.py .
COPY docker/mcp-servers-source/conport/start_with_info.sh .

# Expose ports (MCP server + info server)
EXPOSE 3004 4004

# Health check - test the enhanced HTTP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1

# Run both MCP server and info server
CMD ["bash", "start_with_info.sh"]

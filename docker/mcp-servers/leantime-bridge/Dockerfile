FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=3015 \
    LEAN_TIME_RATE_LIMIT_SECONDS=1.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY leantime_bridge /app/leantime_bridge
COPY mcp_stdio.py /app/mcp_stdio.py

RUN mkdir -p /app/data /app/logs && \
    useradd --create-home --shell /bin/bash mcp && \
    chown -R mcp:mcp /app
USER mcp

EXPOSE 3015

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS "http://localhost:${MCP_SERVER_PORT}/health" || exit 1

CMD ["python", "/app/leantime_bridge/http_server.py"]

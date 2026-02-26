FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=3012 \
    DISPLAY=:0

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    scrot \
    wmctrl \
    xdotool \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY server.py /app/server.py
COPY integration_bridge_connector.py /app/integration_bridge_connector.py

RUN useradd --create-home --shell /bin/bash mcp && chown -R mcp:mcp /app
USER mcp

EXPOSE 3012

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS "http://localhost:${MCP_SERVER_PORT}/health" || exit 1

CMD ["python", "/app/server.py"]

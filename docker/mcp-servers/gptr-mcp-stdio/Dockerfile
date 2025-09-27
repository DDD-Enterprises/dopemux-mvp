# GPT Researcher MCP (STDIO) helper container
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create scripts directory and copy the stdio MCP server
RUN mkdir -p /app/scripts/gpt-researcher
COPY scripts/gpt-researcher/mcp_server.py /app/scripts/gpt-researcher/mcp_server.py

# Install minimal dependencies for MCP + GPT Researcher
# Note: gpt-researcher installs its own deps (requests/bs4/etc.)
RUN pip install --no-cache-dir mcp && \
    (pip install --no-cache-dir gpt-researcher || pip install --no-cache-dir gpt_researcher)

# Keep container running for docker exec stdio
CMD ["tail", "-f", "/dev/null"]

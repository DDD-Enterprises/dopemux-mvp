# PAL Stdio MCP Server for Docker MCP Toolkit
# Runs server.py directly on stdio (no HTTP wrapper)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Copy PAL source (same as HTTP variant, without unused wrapper)
COPY docker/mcp-servers/pal/pal-mcp-server/ .

# Install dependencies using uv
RUN rm -rf .venv && uv venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

# Run the PAL MCP server directly on stdio
CMD ["/app/.venv/bin/python", "server.py"]

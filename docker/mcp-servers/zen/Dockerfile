# Zen MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Copy zen-mcp-server source code
COPY zen-mcp-server/ .
COPY zen_http_wrapper.py .

# Install dependencies using uv
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

# Expose port
EXPOSE 3003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3003/health || exit 1

# Run the HTTP wrapper with activated environment
CMD ["bash", "-c", "source .venv/bin/activate && python zen_http_wrapper.py"]
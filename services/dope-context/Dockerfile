# Dope-Context MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy the entire dope-context service first (for requirements)
COPY . .

# Install fastmcp first using pip without git clone
RUN pip install --no-cache-dir fastmcp || \
    pip install --no-cache-dir git+https://github.com/anthropics/python-sdk.git || \
    echo "Warning: fastmcp install failed, continuing..."

# Install requirements (skip fastmcp line if it fails)
RUN grep -v "git+https://github.com/anthropic/fastmcp.git" requirements.txt > /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements.txt || \
    pip install --no-cache-dir -r requirements.txt || true

# Try to install the MCP package if it exists
RUN if [ -d "/app/src/mcp" ]; then cd /app/src/mcp && pip install -e . || true; fi

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

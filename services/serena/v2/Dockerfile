FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for LSP and Tree-sitter
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Tree-sitter grammars
RUN pip install --no-cache-dir tree-sitter>=0.25.2 \
    tree-sitter-python==0.23.0 \
    tree-sitter-javascript==0.23.0 \
    tree-sitter-typescript==0.23.0

# Copy application code
COPY . .

# Expose MCP port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3001/health')" || exit 1

# Run MCP server
CMD ["python", "mcp_server.py"]

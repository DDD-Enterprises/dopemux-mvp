# Leantime MCP Bridge Service
# Python-based bridge connecting Leantime JSON-RPC API to MCP protocol
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Set up environment
ENV PYTHONPATH=/app
ENV MCP_SERVER_PORT=3015
ENV LEANTIME_API_URL=http://leantime:80
ENV LEANTIME_API_TOKEN=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${MCP_SERVER_PORT}/health || exit 1

# Expose MCP server port
EXPOSE 3015

# Labels for Docker metadata
LABEL mcp.role="workflow"
LABEL mcp.priority="high"
LABEL mcp.description="Leantime project management bridge"
LABEL mcp.integration="leantime"

# Run the MCP bridge server
CMD ["python", "-m", "leantime_bridge.server"]
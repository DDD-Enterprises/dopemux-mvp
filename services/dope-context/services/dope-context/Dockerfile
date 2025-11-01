# Dope-Context MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire dope-context service
COPY . .

# Set environment variables
ENV MCP_SERVER_PORT=3010
ENV PYTHONUNBUFFERED=1

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Health check - verify MCP server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3010/health', timeout=5)" || exit 1

# Labels
LABEL mcp.role="search"
LABEL mcp.priority="high"
LABEL mcp.description="Semantic code and document search with AST-aware indexing"

# Run the MCP server
CMD ["python", "-m", "src.mcp.server"]
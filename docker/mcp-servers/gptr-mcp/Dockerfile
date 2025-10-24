# GPT Researcher MCP Server Dockerfile
# Enables autonomous research capabilities via MCP protocol with HTTP transport
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Clone GPT Researcher MCP server to /app/gptr-mcp
RUN git clone https://github.com/assafelovic/gptr-mcp.git /app/gptr-mcp

# Install Python dependencies from the cloned repo
RUN pip install --no-cache-dir -r /app/gptr-mcp/requirements.txt && \
    pip install --no-cache-dir aiohttp requests

# Fix langchain compatibility issues - downgrade to versions compatible with gpt-researcher
# gpt-researcher 0.14.4 requires older langchain API structure
# Use langchain-community 0.0.20 which is compatible with langsmith 0.0.87
RUN pip install --no-cache-dir --force-reinstall \
    'langchain==0.0.354' \
    'langchain-community==0.0.20' \
    'langchain-core==0.1.23' \
    'langsmith==0.0.87' \
    'numpy<2'

# Create logs and data directories
RUN mkdir -p /app/logs /app/data

# Copy our HTTP wrapper script and env template
COPY gptr_http_wrapper.py /app/gptr_http_wrapper.py
COPY .env.template /app/.env

# Expose MCP server port (wrapper listens on 3009, upstream on 3015)
EXPOSE 3009

# Set environment variables
ENV MCP_SERVER_PORT=3009
ENV GPTR_UPSTREAM_PORT=3015
ENV PYTHONUNBUFFERED=1

# Health check for HTTP /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:3009/health || exit 1

# Labels
LABEL mcp.role="research"
LABEL mcp.priority="high"
LABEL mcp.transport="http-proxy"
LABEL mcp.description="GPT Researcher with HTTP transport via proxy wrapper"

# Run the HTTP wrapper (spawns server.py internally and proxies HTTP)
CMD ["python", "/app/gptr_http_wrapper.py"]

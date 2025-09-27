# GPT Researcher MCP Server Dockerfile
# Enables autonomous research capabilities via MCP protocol
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Clone GPT Researcher MCP server
RUN git clone https://github.com/assafelovic/gptr-mcp.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir aiohttp requests

# Create logs directory
RUN mkdir -p /app/logs

# Copy environment template
COPY .env.template .env

# Copy HTTP wrapper and expose port
COPY gptr_http_wrapper.py /app/gptr_http_wrapper.py

# Expose MCP server port
EXPOSE 3009

# Health check (wrapper proxies to underlying server when available)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:3009/health || exit 1

# Run the HTTP wrapper (spawns upstream server on 3015)
CMD ["python", "/app/gptr_http_wrapper.py"]

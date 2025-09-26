# ConPort MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and aiohttp for direct HTTP server
RUN pip install uv aiohttp

# Copy the direct server (bypasses mcp-proxy complexity)
COPY direct_server.py .

# Expose port
EXPOSE 3004

# Health check - test the direct HTTP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1

# Run the direct HTTP server
CMD ["python", "direct_server.py"]
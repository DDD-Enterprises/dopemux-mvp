FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Exa MCP server
COPY exa_server.py .

# Make script executable
RUN chmod +x exa_server.py

EXPOSE 3008

# Add health check for HTTP endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3008/health || exit 1

# Run FastMCP directly in HTTP mode (no mcp-proxy needed)
CMD ["python", "exa_server.py"]
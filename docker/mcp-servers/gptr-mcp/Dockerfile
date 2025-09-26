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
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy environment template
COPY .env.template .env

# Expose MCP server port
EXPOSE 3009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3009/health', timeout=5)" || exit 1

# Run the MCP server
CMD ["python", "server.py", "--port", "3009"]
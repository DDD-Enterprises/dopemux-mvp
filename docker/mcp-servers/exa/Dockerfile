FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install uv for uvx
RUN pip install --no-cache-dir uv

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Exa MCP server and wrapper
COPY exa_server.py .
COPY wrapper.py .

# Make scripts executable
RUN chmod +x exa_server.py wrapper.py

EXPOSE 3008

# Add health check for SSE endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3008/sse || exit 1

# Set environment to use stdio mode
ENV MCP_RUN_MODE=stdio

CMD ["python", "wrapper.py"]
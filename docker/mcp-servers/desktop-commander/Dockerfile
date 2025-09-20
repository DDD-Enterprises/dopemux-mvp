# Desktop Commander MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including desktop tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    x11-apps \
    xdotool \
    wmctrl \
    scrot \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Install Desktop Commander MCP (if available as package)
# RUN uv tool install desktop-commander-mcp

# For now, create a simple desktop automation server
COPY server.py .
COPY requirements.txt .

# Install requirements
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

# Expose port
EXPOSE 3012

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the server
CMD [".venv/bin/python", "server.py"]
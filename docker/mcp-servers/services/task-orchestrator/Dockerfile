FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Java for Kotlin backend
RUN apt-get update && apt-get install -y --no-install-recommends \
   gcc \
   openjdk-17-jdk \
   && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose MCP port
EXPOSE 3014

# Health check for MCP SSE endpoint
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3014/sse')" || exit 1

# Run the Python MCP wrapper persistently
CMD ["python", "server.py"]

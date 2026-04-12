# MCP Integration Bridge Service
# Python-based central coordination layer for task management systems
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs and data directories
RUN mkdir -p /app/logs /app/data

# Set up environment
ENV PYTHONPATH=/app
ENV MCP_INTEGRATION_PORT=3016
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${MCP_INTEGRATION_PORT}/health || exit 1

# Expose integration service port
EXPOSE 3016

# Labels for Docker metadata
LABEL mcp.role="integration"
LABEL mcp.priority="critical"
LABEL mcp.description="Central task management coordination layer"
LABEL mcp.integrates="task-master-ai,task-orchestrator,leantime-bridge"

# Run the integration bridge service
CMD ["python", "main.py"]
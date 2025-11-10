# Task Orchestrator Dockerfile
# Phase 2: Production Deployment - Enhanced Python Implementation

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check - check both MCP and HTTP API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3014/health || curl -f http://localhost:8000/health || exit 1

# Expose ports for MCP and HTTP API
EXPOSE 3014 8000

# Default command - run the enhanced orchestrator
CMD ["python", "enhanced_orchestrator.py"]
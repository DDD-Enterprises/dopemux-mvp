# ConPort MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies for enhanced server with database persistence
RUN pip install uv aiohttp asyncpg redis

# Copy the enhanced server with PostgreSQL + Redis persistence
COPY enhanced_server.py .
COPY schema.sql .

# Expose port
EXPOSE 3004

# Health check - test the enhanced HTTP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1

# Run the enhanced HTTP server with real persistence
CMD ["python", "enhanced_server.py"]
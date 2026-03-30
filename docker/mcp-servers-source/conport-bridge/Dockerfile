FROM python:3.11-slim

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

# Install dependencies from centralized manifest
RUN pip install --no-cache-dir .[services]

# Copy application (relative to root build context)
COPY docker/mcp-servers-source/conport-bridge/*.py ./

# Environment variables with defaults
ENV CONPORT_DB_PATH=/workspace/context_portal/context.db
ENV REDIS_URL=redis://dopemux-redis-events:6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import redis; r=redis.from_url('${REDIS_URL}'); r.ping()"

# Run
CMD ["python", "-u", "main.py"]

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for app detection
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir redis

# Copy application code
COPY . .

# Create workspace config directory
RUN mkdir -p /app/config && chown -R 1000:1000 /app
RUN useradd -m -u 1000 workspace && chown -R workspace:workspace /app

# Switch to non-root user
USER workspace

# No exposed ports (background monitoring)

# Health check for background service
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import psutil; exit(0 if any('main.py' in [p.name() for p in psutil.process_iter()]) else 1)"

# Run workspace watcher
CMD ["python", "main.py"]
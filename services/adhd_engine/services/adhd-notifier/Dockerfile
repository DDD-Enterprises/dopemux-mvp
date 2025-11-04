FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for notifications
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir redis

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 notifier && chown -R notifier:notifier /app
USER notifier

# No exposed ports (notification service)

# Health check for background service
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import psutil; exit(0 if any('main.py' in [p.name() for p in psutil.process_iter()]) else 1)"

# Run ADHD notifier
CMD ["python", "main.py"]
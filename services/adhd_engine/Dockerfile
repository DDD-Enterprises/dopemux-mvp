FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (gcc for builds, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 adhd && chown -R adhd:adhd /app
USER adhd

# Expose API port (8095 for ADHD Engine)
EXPOSE 8095

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8095/health || exit 1

# Set Python path and run main.py directly
ENV PYTHONPATH=/app
ENV API_PORT=8095
CMD ["python", "main.py"]

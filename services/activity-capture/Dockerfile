FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 activity && chown -R activity:activity /app
USER activity

# Expose API port
EXPOSE 8096

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8096/health || exit 1

# Set Python path and run
ENV PYTHONPATH=/app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8096", "--log-level", "info"]
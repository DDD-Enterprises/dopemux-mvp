FROM python:3.11-slim

# Set workdir to root app for structure
WORKDIR /app

# Install system dependencies (gcc for builds, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY services/adhd_engine/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/adhd_engine ./services/adhd_engine
COPY shared ./services/shared
# Make sure services is a proper package
RUN touch services/__init__.py

# Create non-root user for security
RUN useradd -m -u 1000 adhd && chown -R adhd:adhd /app
USER adhd

# Expose API port (8095 for ADHD Engine)
EXPOSE 8095

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8095/health || exit 1

# Set paths: engine dir for execution, root for shared resolution
ENV PYTHONPATH=/app/services/adhd_engine:/app:/app/services
WORKDIR /app/services/adhd_engine
ENV API_PORT=8095
CMD ["python", "main.py"]

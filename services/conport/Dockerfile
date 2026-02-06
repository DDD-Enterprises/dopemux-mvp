# ConPort Service - Standardized Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Python environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy root library build inputs
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY src /app/src
RUN pip install --no-cache-dir /app

# Copy shared library (Legacy support)
COPY services/shared /app/services/shared

# Copy conport service code
COPY services/conport /app/services/conport
WORKDIR /app/services/conport

# Install dependencies (including local shared lib)
RUN pip install --no-cache-dir .

# Compile gate: catch syntax errors at build time
RUN python -m compileall -q .

# Import proof: fail build if runtime deps missing
RUN python -c "import fastapi, uvicorn, asyncpg, pydantic; print('✅ conport deps verified')"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose HTTP port
EXPOSE 3004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1

# Run the ConPort HTTP server
CMD ["python", "app.py"]
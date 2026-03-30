# Dopemux GPT Researcher - ADHD-Optimized Research Service
# Multi-stage build for Python backend with enhanced features

# === Base Stage ===
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create application user for security
RUN useradd --create-home --shell /bin/bash dopemux

# Set working directory
WORKDIR /app

# === Dependencies Stage ===
FROM base as dependencies

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .[services]

# Install gpt-researcher (will be configurable for different versions)
RUN pip install --no-cache-dir gpt-researcher

# === Application Stage ===
FROM dependencies as application

# Copy research_api source code (renamed from backend to avoid package collision)
COPY services/dopemux-gpt-researcher/research_api/ ./research_api/
COPY --chown=dopemux:dopemux services/dopemux-gpt-researcher/ .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/cache && \
    chown -R dopemux:dopemux /app

# Switch to application user
USER dopemux

# Set Python path for imports
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run FastAPI server (no more package collision!)
CMD ["python", "-m", "uvicorn", "research_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
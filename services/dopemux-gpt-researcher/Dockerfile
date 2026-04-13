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

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install gpt-researcher (will be configurable for different versions)
RUN pip install --no-cache-dir gpt-researcher

# === Application Stage ===
FROM dependencies as application

# Copy backend source code
COPY backend/ ./backend/
COPY --chown=dopemux:dopemux . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/cache && \
    chown -R dopemux:dopemux /app

# Switch to application user
USER dopemux

# Set Python path for imports
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run FastAPI server
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
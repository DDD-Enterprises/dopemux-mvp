# Legacy compatibility image for the historical `dopemux-backend` tag.
# Repo runtime truth currently routes this image to the canonical
# task-orchestrator FastAPI surface.
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/__init__.py

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies from centralized manifest
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy canonical task-orchestrator runtime inputs from the repo root context.
COPY services/task-orchestrator/app /app/app
COPY services/task-orchestrator/intelligence /app/intelligence
COPY services/task-orchestrator/task_orchestrator /app/task_orchestrator
COPY services/task-orchestrator/mcp_stdio.py /app/mcp_stdio.py
COPY services/task-orchestrator/task_decomposition_endpoint.py /app/task_decomposition_endpoint.py
COPY services/task-orchestrator/pal_client.py /app/pal_client.py
COPY services/shared /app/services/shared
COPY src/dopemux /app/dopemux

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    COORDINATION_API_PORT=8000 \
    PORT=8000 \
    WORKSPACE_ID=/workspace

# Create non-root user for security
RUN useradd -m -u 1000 dopemux && \
    chown -R dopemux:dopemux /app
USER dopemux

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Canonical task-orchestrator HTTP port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

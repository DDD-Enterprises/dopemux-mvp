FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/__init__.py

# Install Python dependencies from centralized manifest
RUN pip install --no-cache-dir .[services]

# Copy application code and dopemux package (relative to root build context)
COPY services/task-orchestrator/app /app/app
COPY services/task-orchestrator/intelligence /app/intelligence
COPY services/task-orchestrator/task_orchestrator /app/task_orchestrator
COPY services/task-orchestrator/mcp_stdio.py /app/mcp_stdio.py
COPY services/task-orchestrator/task_decomposition_endpoint.py /app/task_decomposition_endpoint.py
COPY services/task-orchestrator/pal_client.py /app/pal_client.py
COPY services/shared /app/services/shared
COPY src/dopemux /app/dopemux

# Set up environment
ENV PYTHONPATH=/app \
  PYTHONUNBUFFERED=1 \
  COORDINATION_API_PORT=8000 \
  PORT=8000 \
  WORKSPACE_ID=/workspace

# Expose service port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

<<<<<<< HEAD
# Run the canonical task orchestrator runtime
=======
# Run the canonical HTTP runtime surface.
>>>>>>> f03e263bd (fix(task-orchestrator): restore canonical workflow route surface)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

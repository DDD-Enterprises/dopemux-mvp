FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/task-orchestrator/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and dopemux package
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

# Run the task orchestrator service
CMD ["uvicorn", "task_orchestrator.app:app", "--host", "0.0.0.0", "--port", "8000"]

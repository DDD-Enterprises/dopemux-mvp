FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set up environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose service port
EXPOSE 3014

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:3014/health || exit 1

# Run the task orchestrator service
CMD ["python", "-m", "task_orchestrator.app"]

# Dockerfile for ADHD Dashboard
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/adhd-dashboard/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files and shared runtime dependencies
COPY services/adhd-dashboard /app
COPY services/shared /app/services/shared
COPY src/dopemux /app/src/dopemux

# Run service
ENV PYTHONPATH=/app:/app/src
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8097"]

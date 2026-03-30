FROM python:3.11-slim

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*
# Install Python dependencies from centralized manifest
RUN pip install --no-cache-dir .[services]

COPY services/webhook_receiver /app/services/webhook_receiver

COPY scripts/webhook_migrate.py /app/scripts/webhook_migrate.py
EXPOSE 8790
CMD ["python", "/app/services/webhook_receiver/server.py"]

FROM python:3.11-slim

WORKDIR /app

# Install minimal dependencies
RUN pip install --no-cache-dir redis aiohttp

# Copy application code
COPY . .

# No exposed port (EventBus consumer only)

# Run as background service
CMD ["python", "start_service.py", "default"]

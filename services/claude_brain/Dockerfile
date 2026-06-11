# Claude Brain Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY README.md .
COPY src src
COPY tools tools

# Install Python dependencies from centralized manifest
RUN pip install --no-cache-dir "wheel>=0.46.2" && pip install --no-cache-dir .[services]

# Copy application code (relative to root build context)
COPY services/claude_brain/ .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "main.py"]

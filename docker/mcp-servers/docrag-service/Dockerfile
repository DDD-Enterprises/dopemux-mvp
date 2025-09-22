FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy source code and requirements
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install Python dependencies
RUN pip install -e .

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash docrag
RUN chown -R docrag:docrag /app
USER docrag

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3009/health || exit 1

# Expose port
EXPOSE 3009

# Default command
CMD ["python", "-m", "docrag.main"]
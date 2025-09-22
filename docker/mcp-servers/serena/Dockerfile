FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install uv for fast package management
RUN pip install uv

# Copy wrapper script
COPY wrapper.py /app/wrapper.py

EXPOSE 3006

CMD ["python", "/app/wrapper.py"]
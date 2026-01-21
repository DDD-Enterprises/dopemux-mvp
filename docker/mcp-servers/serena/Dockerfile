FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (including serena from git)
# Pinning to main branch for now, ideally should be a tag
RUN pip install "git+https://github.com/oraios/serena.git" mcp-proxy

# Copy wrapper script
COPY wrapper.py /app/wrapper.py

EXPOSE 3006

CMD ["python", "/app/wrapper.py"]
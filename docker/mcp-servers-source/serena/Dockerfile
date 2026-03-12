FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (including serena from git)
# Pinning to main branch for now, ideally should be a tag
RUN pip install "git+https://github.com/oraios/serena.git" mcp-proxy fastapi uvicorn

# Copy wrapper script and info server
COPY wrapper.py /app/wrapper.py
COPY info_server.py /app/info_server.py
COPY start_with_info.sh /app/start_with_info.sh

# Expose ports (MCP server + info server)
EXPOSE 3006 4006

CMD ["bash", "/app/start_with_info.sh"]
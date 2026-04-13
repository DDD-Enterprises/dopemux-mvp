FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from centralized manifest
# We also include serena from git as before
RUN uv pip install --system --no-cache .[services] mcp-proxy && \
    uv pip install --system --no-cache "git+https://github.com/oraios/serena.git@f561204840eb4a96c6956d5cd98712f8ed52d0cb"

# Copy wrapper script and info server (relative to root)
COPY docker/mcp-servers-source/serena/wrapper.py /app/wrapper.py
COPY docker/mcp-servers-source/serena/info_server.py /app/info_server.py
COPY docker/mcp-servers-source/serena/start_with_info.sh /app/start_with_info.sh

# Expose ports (MCP server + info server)
EXPOSE 3006 4006

CMD ["bash", "/app/start_with_info.sh"]
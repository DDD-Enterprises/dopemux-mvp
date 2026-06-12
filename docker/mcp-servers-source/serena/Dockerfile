FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests and package sources required by setuptools metadata
# (pyproject [tool.setuptools] packages spans conport/core/dopemux + tools.*)
COPY pyproject.toml ./
COPY src/ src/
COPY tools/ tools/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from centralized manifest
# We also include serena from git as before
RUN uv pip install --system --no-cache .[services] && \
    uv pip install --system --no-cache "git+https://github.com/oraios/serena.git@f561204840eb4a96c6956d5cd98712f8ed52d0cb"

# mcp-proxy CLI is invoked by wrapper.py to bridge serena stdio -> SSE on :3006;
# it is not part of the [services] extra, so install it explicitly
RUN uv pip install --system --no-cache mcp-proxy

# Copy wrapper script and info server (relative to root)
COPY docker/mcp-servers-source/serena/wrapper.py /app/wrapper.py
COPY docker/mcp-servers-source/serena/info_server.py /app/info_server.py
COPY docker/mcp-servers-source/serena/start_with_info.sh /app/start_with_info.sh

# Expose ports (MCP server + info server)
EXPOSE 3006 4006

CMD ["bash", "/app/start_with_info.sh"]
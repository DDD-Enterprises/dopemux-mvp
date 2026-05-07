# GPT Researcher MCP Server Dockerfile
# Enables autonomous research capabilities via MCP protocol with HTTP transport
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first for better caching
COPY pyproject.toml .
COPY src/dopemux/__init__.py src/dopemux/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install dependencies from centralized manifest
RUN uv pip install --system --no-cache .[services]

# Clone GPT Researcher MCP server to /app/gptr-mcp at a pinned ref for reproducibility.
# Override at build time with --build-arg GPTR_MCP_REF=<branch|tag|sha>.
ARG GPTR_MCP_REF=63884773685b1f12c7f0d9e283b3d71a5b9b5fda
RUN git clone https://github.com/assafelovic/gptr-mcp.git /app/gptr-mcp \
    && cd /app/gptr-mcp && git checkout "${GPTR_MCP_REF}"

# Modify server.py to use MCP_SERVER_PORT environment variable
RUN sed -i 's/port=8000/port=int(os.getenv("MCP_SERVER_PORT", "8000"))/g' /app/gptr-mcp/server.py

# Install Python dependencies from the cloned repo
RUN uv pip install --system --no-cache -r /app/gptr-mcp/requirements.txt

# Force-pin gpt-researcher to an explicit version so rebuilds don't drift backward
# when upstream gptr-mcp's requirements.txt changes. Override at build time with
# --build-arg GPT_RESEARCHER_VERSION=<version>.
ARG GPT_RESEARCHER_VERSION=0.14.8
RUN uv pip install --system --no-cache "gpt-researcher==${GPT_RESEARCHER_VERSION}"

# Create logs and data directories
RUN mkdir -p /app/logs /app/data

# Copy wrapper and environment files (relative to root)
COPY docker/mcp-servers-source/gptr-mcp/wrapper.py /app/wrapper.py

# Expose MCP server ports
EXPOSE 3009 3013

# Set environment variables
ENV MCP_SERVER_PORT=3009
ENV GPTR_UPSTREAM_PORT=3013
ENV PYTHONUNBUFFERED=1

# Health check - MCP servers don't expose HTTP endpoints, just verify python process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD pgrep -f "python.*server.py" > /dev/null || exit 1

# Labels
LABEL mcp.role="research"
LABEL mcp.priority="high"
LABEL mcp.transport="mcp"
LABEL mcp.description="GPT Researcher MCP server with direct MCP protocol"

# Run the MCP server directly (server.py is the actual MCP server using FastMCP)
CMD ["python", "/app/gptr-mcp/server.py"]

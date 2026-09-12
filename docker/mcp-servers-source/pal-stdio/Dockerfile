# PAL Stdio MCP Server for Docker MCP Toolkit
# Runs server.py directly on stdio (no HTTP wrapper)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Copy PAL source (same as HTTP variant, without unused wrapper)
COPY docker/mcp-servers-source/pal/pal-mcp-server/ .

# Install dependencies using uv
RUN rm -rf .venv && uv venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

# Prove at BUILD time that this image can actually serve MCP.
#
# The failure this catches is invisible at runtime: on mcp 2.x the low-level
# Server API no longer exposes list_tools, so server.py raises AttributeError
# during startup while the HTTP wrapper's /health still reports the process as
# running. Importing the module here exercises the @server.list_tools()
# registration that broke, needs no API keys, and fails the build instead of
# shipping an image whose server cannot start.
RUN /app/.venv/bin/python -c \
      "import importlib, sys; \
       import importlib.metadata as md; \
       v = md.version('mcp'); \
       sys.exit('FATAL: resolved mcp ' + v + '; server.py requires mcp<2') if int(v.split('.')[0]) >= 2 else None; \
       from mcp.server import Server; \
       sys.exit('FATAL: mcp ' + v + ' has no Server.list_tools') if not hasattr(Server, 'list_tools') else None; \
       importlib.import_module('server'); \
       print('build guard OK: mcp ' + v + ', server.py imports and registers handlers')"

# Run the PAL MCP server directly on stdio
CMD ["/app/.venv/bin/python", "server.py"]

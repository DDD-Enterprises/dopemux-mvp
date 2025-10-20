#!/usr/bin/env python3
"""
HTTP wrapper for GPT Researcher MCP Server
- Spawns upstream server.py in stdio mode
- Exposes port 3009 with:
  - /health: simple health check (always returns healthy if wrapper is running)
  - Note: Upstream runs in stdio mode, not HTTP, so we just verify wrapper is working
"""

import asyncio
import os
import signal
import sys
import logging
from aiohttp import web, ClientSession
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPSTREAM_PORT = int(os.getenv("GPTR_UPSTREAM_PORT", "3015"))
WRAPPER_PORT = int(os.getenv("MCP_SERVER_PORT", "3009"))
GPTR_MCP_DIR = "/app/gptr-mcp"

process = None

async def start_upstream():
    """Start the upstream GPT Researcher MCP server in stdio mode"""
    global process
    if process is not None and process.poll() is None:
        logger.info("Upstream server already running")
        return

    # Run server.py from the gptr-mcp directory
    # The upstream server runs in stdio mode (not HTTP)
    cmd = [sys.executable, "server.py"]
    logger.info(f"Starting upstream server: {' '.join(cmd)} in {GPTR_MCP_DIR}")

    process = subprocess.Popen(
        cmd,
        cwd=GPTR_MCP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"}
    )
    logger.info(f"Upstream server started with PID {process.pid}")

async def stop_upstream():
    global process
    if process and process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
            process.wait()

async def health_handler(_request: web.Request):
    """
    Health check endpoint
    Since upstream runs in stdio mode (not HTTP), we just check if the process is alive
    """
    global process

    status = {
        "status": "healthy",
        "wrapper_port": WRAPPER_PORT,
        "upstream_mode": "stdio",
        "upstream_running": False
    }

    if process is not None:
        poll_result = process.poll()
        if poll_result is None:
            # Process is still running
            status["upstream_running"] = True
            status["upstream_pid"] = process.pid
            return web.json_response(status, status=200)
        else:
            # Process has exited
            status["status"] = "degraded"
            status["upstream_exit_code"] = poll_result
            return web.json_response(status, status=503)
    else:
        # Process was never started
        status["status"] = "starting"
        return web.json_response(status, status=503)

async def info_handler(_request: web.Request):
    """
    Info endpoint explaining the server mode
    """
    return web.json_response({
        "server": "GPT Researcher MCP",
        "mode": "stdio",
        "note": "This server runs in STDIO mode for Claude Desktop compatibility",
        "wrapper_port": WRAPPER_PORT,
        "health_endpoint": "/health",
        "mcp_access": "Use via Claude Desktop stdio transport or docker exec for stdio access"
    }, status=200)

async def on_startup(app: web.Application):
    await start_upstream()

async def on_shutdown(app: web.Application):
    await stop_upstream()

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Health check endpoint for Docker
    app.router.add_get("/health", health_handler)

    # Info endpoint
    app.router.add_get("/", info_handler)
    app.router.add_get("/info", info_handler)

    logger.info(f"Starting HTTP wrapper on port {WRAPPER_PORT}")
    logger.info(f"Upstream GPT Researcher MCP will run in STDIO mode")
    logger.info(f"Health check available at http://0.0.0.0:{WRAPPER_PORT}/health")

    web.run_app(app, host="0.0.0.0", port=WRAPPER_PORT)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass


#!/usr/bin/env python3
"""
Serena MCP Server with /info endpoint support
Wraps mcp-proxy with parallel HTTP server for service discovery
"""

import os
import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get port from environment
PORT = int(os.getenv('MCP_SERVER_PORT', 3006))
INFO_PORT = PORT + 1000  # Parallel HTTP server on 4006

app = FastAPI(title="Serena Info Server")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "serena-v2", "port": PORT}

@app.get("/info")
async def service_info():
    """Service discovery endpoint - auto-config support (ADR-208)"""
    return {
        "name": "serena-v2",
        "version": "1.0.0",
        "mcp": {
            "protocol": "sse",
            "connection": {
                "type": "sse",
                "url": f"http://localhost:{PORT}/sse"
            },
            "env": {
                "WORKSPACE_ID": "${WORKSPACE_ID:-}"
            }
        },
        "health": "/health",
        "description": "ADHD-Optimized Code Navigation & Project Memory",
        "metadata": {
            "role": "workflow",
            "priority": "high",
            "adhd_optimized": True,
            "lsp_server": True,
            "mcp_proxy_wrapped": True,
            "info_port": INFO_PORT,
            "mcp_port": PORT
        }
    }

if __name__ == "__main__":
    logger.info(f"Starting Serena info server on port {INFO_PORT}")
    logger.info(f"MCP server accessible at port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=INFO_PORT)

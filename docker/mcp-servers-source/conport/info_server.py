#!/usr/bin/env python3
"""
ConPort MCP Server with /info endpoint support
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

# Get port from environment. This info server itself never binds the MCP/SSE
# port -- PORT here only derives INFO_PORT. The client-facing MCP endpoint is
# a *sibling* process (server.py sse) whose real port start_with_info.sh
# passes separately, since MCP_SERVER_PORT is overridden to the REST port
# (3004) for this process's own env.
PORT = int(os.getenv('MCP_SERVER_PORT', 3004))
INFO_PORT = PORT + 1000  # Parallel HTTP server on 4004
ADVERTISED_MCP_PORT = int(os.getenv('CONPORT_ADVERTISED_MCP_PORT', PORT + 1))

app = FastAPI(title="ConPort Info Server")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "conport", "port": PORT}

@app.get("/info")
async def service_info():
    """Service discovery endpoint - auto-config support (ADR-208)"""
    return {
        "name": "conport",
        "version": "1.0.0",
        "mcp": {
            "protocol": "sse",
            "connection": {
                "type": "sse",
                "url": f"http://localhost:{ADVERTISED_MCP_PORT}/sse"
            },
            "env": {
                "WORKSPACE_ID": "${WORKSPACE_ID:-}",
                "GEMINI_API_KEY": "${GEMINI_API_KEY:-}",
                "VOYAGEAI_API_KEY": "${VOYAGEAI_API_KEY:-}",
                "OPENAI_API_KEY": "${OPENAI_API_KEY:-}"
            }
        },
        "health": "/health",
        "description": "Knowledge graph and context management",
        "metadata": {
            "role": "workflow",
            "priority": "high",
            "mcp_proxy_wrapped": True,
            "info_port": INFO_PORT,
            "mcp_port": ADVERTISED_MCP_PORT
        }
    }

if __name__ == "__main__":
    logger.info(f"Starting ConPort info server on port {INFO_PORT}")
    logger.info(f"MCP server accessible at port {ADVERTISED_MCP_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=INFO_PORT)

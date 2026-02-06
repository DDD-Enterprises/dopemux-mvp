#!/usr/bin/env python3
"""
GPT-Researcher MCP Server with HTTP Health Check Wrapper
Wraps the gptr-mcp stdio server from assafelovic/gptr-mcp
Provides HTTP endpoints for Docker health checks while maintaining stdio compatibility
"""

import os
import asyncio
import sys
import logging
import signal
import json
from typing import Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GptrMcpWrapper:
    def __init__(self):
        self.app = FastAPI(title="GPT Researcher MCP Wrapper")
        self.process: Optional[asyncio.subprocess.Process] = None
        self.port = int(os.getenv('MCP_SERVER_PORT', 3009))
        self.upstream_port = int(os.getenv('GPTR_UPSTREAM_PORT', 3013))  # Different port for upstream
        self.shutdown_event = asyncio.Event()

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for Docker"""
            if self.process and self.process.returncode is None:
                return JSONResponse({
                    "status": "healthy",
                    "wrapper_port": self.port,
                    "upstream_mode": "stdio",
                    "upstream_running": True,
                    "upstream_pid": self.process.pid if self.process else None,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return JSONResponse({
                    "status": "unhealthy",
                    "error": "Upstream process not running",
                    "timestamp": datetime.now().isoformat()
                }, status_code=503)

        @self.app.get("/")
        async def root():
            """Root endpoint redirects to info"""
            return JSONResponse({
                "message": "GPT Researcher MCP Wrapper",
                "endpoints": ["/health", "/info"],
                "timestamp": datetime.now().isoformat()
            })

        @self.app.get("/info")
        async def service_info():
            """Service discovery endpoint - auto-config support (ADR-208)"""
            return JSONResponse({
                "name": "gpt-researcher",
                "version": "1.0.0",
                "mcp": {
                    "protocol": "sse",
                    "connection": {
                        "type": "sse",
                        "url": f"http://localhost:{self.port}/sse"
                    },
                    "env": {
                        "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
                        "TAVILY_API_KEY": "${TAVILY_API_KEY:-}",
                        "EXA_API_KEY": "${EXA_API_KEY:-}",
                        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY:-}",
                        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY:-}"
                    }
                },
                "health": "/health",
                "description": "Deep research with comprehensive analysis using Docker container",
                "metadata": {
                    "role": "research",
                    "priority": "medium",
                    "wrapper": True,
                    "upstream_mode": "stdio",
                    "upstream_running": self.process is not None and self.process.returncode is None,
                    "upstream_pid": self.process.pid if self.process else None
                }
            })

    async def start_upstream_server(self):
        """Start the upstream GPT Researcher MCP server in stdio mode"""
        logger.info("🔬 Starting upstream GPT Researcher MCP server (stdio mode)")

        # Command to run the upstream server in stdio mode
        cmd = [
            'python', '/app/gptr-mcp/server.py'
        ]

        logger.info(f"Running upstream command: {' '.join(cmd)}")

        try:
            # Create async subprocess for upstream server
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'MCP_SERVER_PORT': str(self.upstream_port)},
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

            logger.info(f"Upstream GPT Researcher MCP server started with PID {self.process.pid}")

            # Monitor process output
            async def read_output(stream, prefix):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    logger.info(f"[GPTR {prefix}] {line.decode().strip()}")

            # Create tasks for stdout and stderr monitoring
            asyncio.create_task(read_output(self.process.stdout, "OUT"))
            asyncio.create_task(read_output(self.process.stderr, "ERR"))

        except Exception as e:
            logger.error(f"Failed to start upstream GPT Researcher MCP server: {e}")
            raise

    async def start_http_server(self):
        """Start the HTTP wrapper server"""
        logger.info(f"🌐 Starting HTTP wrapper server on port {self.port}")

        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        await server.serve()

    async def start(self):
        """Start both the upstream server and HTTP wrapper"""
        logger.info("🚀 Starting GPT Researcher MCP Wrapper")

        try:
            # Start upstream server first
            await self.start_upstream_server()

            # Wait a moment for upstream server to initialize
            await asyncio.sleep(2)

            # Start HTTP server
            await self.start_http_server()

        except Exception as e:
            logger.error(f"Failed to start wrapper: {e}")
            raise

    async def shutdown(self):
        """Shutdown both servers gracefully"""
        logger.info("Shutting down GPT Researcher MCP Wrapper...")

        if self.process:
            try:
                # Send SIGTERM to process group
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()

                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Upstream server didn't stop gracefully, killing...")
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
            except Exception as e:
                logger.error(f"Error during upstream shutdown: {e}")

    def handle_signal(self, sig):
        """Handle shutdown signals"""
        logger.info(f"Received signal {sig}, initiating shutdown...")
        self.shutdown_event.set()


async def main():
    wrapper = GptrMcpWrapper()

    # Set up signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: server.handle_signal(s))

    try:
        await wrapper.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await wrapper.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

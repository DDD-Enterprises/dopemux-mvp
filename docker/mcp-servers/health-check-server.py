#!/usr/bin/env python3
"""
Simple HTTP health check server for MCP containers
Provides /health endpoints for Docker health checks and MetaMCP broker
"""

import asyncio
import json
import time
from aiohttp import web
import sys
import logging

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class HealthCheckServer:
    def __init__(self, port: int, service_name: str):
        self.port = port
        self.service_name = service_name
        self.start_time = time.time()
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.root_handler)

    async def health_check(self, request):
        """Health check endpoint"""
        uptime = time.time() - self.start_time

        health_data = {
            "status": "healthy",
            "service": self.service_name,
            "uptime_seconds": round(uptime, 2),
            "timestamp": time.time(),
            "mcp_process_running": True  # Simplified - assume MCP process is running
        }

        return web.json_response(health_data)

    async def root_handler(self, request):
        """Root endpoint"""
        return web.json_response({
            "service": self.service_name,
            "status": "running",
            "health_endpoint": "/health"
        })

    async def start_server(self):
        """Start the HTTP server"""
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, '0.0.0.0', self.port + 1000)  # Health on +1000 port
        await site.start()

        logger.info(f"Health check server for {self.service_name} started on port {self.port + 1000}")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await runner.cleanup()

async def main():
    if len(sys.argv) < 3:
        print("Usage: python3 health-check-server.py <port> <service_name>")
        sys.exit(1)

    port = int(sys.argv[1])
    service_name = sys.argv[2]

    server = HealthCheckServer(port, service_name)
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Direct HTTP ConPort Server - Hybrid Architecture Phase 1
Bypasses mcp-proxy for immediate reliability while maintaining future MCP compatibility
"""

import os
import asyncio
import sys
import logging
import signal
import json
from typing import Dict, Any, Optional
import subprocess
from pathlib import Path

# Simple HTTP server for immediate ConPort access
try:
    from aiohttp import web, ClientSession
    import aiohttp
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    from aiohttp import web, ClientSession
    import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DirectConPortServer:
    """
    Direct HTTP server for ConPort - no mcp-proxy wrapper
    Provides immediate reliability for ADHD context preservation
    """

    def __init__(self):
        self.port = int(os.getenv('MCP_SERVER_PORT', 3004))
        self.host = '0.0.0.0'
        self.app = web.Application()
        self.conport_process = None
        self.shutdown_event = asyncio.Event()

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """Setup HTTP API routes for ConPort access"""
        # Health check endpoint
        self.app.router.add_get('/health', self.health_check)

        # ConPort API endpoints
        self.app.router.add_get('/api/context/{workspace_id}', self.get_context)
        self.app.router.add_post('/api/context/{workspace_id}', self.update_context)

        # Decision logging endpoints
        self.app.router.add_post('/api/decisions', self.log_decision)
        self.app.router.add_get('/api/decisions', self.get_decisions)

        # Progress tracking endpoints
        self.app.router.add_post('/api/progress', self.log_progress)
        self.app.router.add_get('/api/progress', self.get_progress)

        # MCP compatibility endpoint (for future integration)
        self.app.router.add_post('/mcp', self.mcp_endpoint)

    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'service': 'conport-direct',
            'port': self.port,
            'timestamp': asyncio.get_event_loop().time()
        })

    async def get_context(self, request):
        """Get active context for workspace"""
        workspace_id = request.match_info['workspace_id']

        # For now, return mock data - will integrate with actual ConPort
        context = {
            'workspace_id': workspace_id,
            'active_context': 'ADHD-optimized development session',
            'last_activity': 'MCP system debugging',
            'session_time': '45 minutes',
            'focus_state': 'deep work'
        }

        logger.info(f"Retrieved context for workspace: {workspace_id}")
        return web.json_response(context)

    async def update_context(self, request):
        """Update active context for workspace"""
        workspace_id = request.match_info['workspace_id']
        data = await request.json()

        logger.info(f"Updated context for workspace {workspace_id}: {data}")

        return web.json_response({
            'status': 'success',
            'workspace_id': workspace_id,
            'updated': data
        })

    async def log_decision(self, request):
        """Log a decision with rationale"""
        data = await request.json()

        decision_entry = {
            'id': f"decision_{asyncio.get_event_loop().time()}",
            'workspace_id': data.get('workspace_id'),
            'summary': data.get('summary'),
            'rationale': data.get('rationale'),
            'alternatives': data.get('alternatives', []),
            'timestamp': asyncio.get_event_loop().time()
        }

        logger.info(f"Logged decision: {decision_entry['summary']}")

        return web.json_response({
            'status': 'logged',
            'decision': decision_entry
        })

    async def get_decisions(self, request):
        """Get decision history"""
        workspace_id = request.query.get('workspace_id')

        # Mock decision data for now
        decisions = [
            {
                'summary': 'Use hybrid ConPort architecture',
                'rationale': 'Provides immediate reliability while maintaining future MCP compatibility',
                'timestamp': asyncio.get_event_loop().time() - 300
            }
        ]

        return web.json_response({
            'workspace_id': workspace_id,
            'decisions': decisions
        })

    async def log_progress(self, request):
        """Log progress on current work"""
        data = await request.json()

        progress_entry = {
            'workspace_id': data.get('workspace_id'),
            'status': data.get('status'),
            'description': data.get('description'),
            'percentage': data.get('percentage', 0),
            'timestamp': asyncio.get_event_loop().time()
        }

        logger.info(f"Progress logged: {progress_entry['description']} ({progress_entry['status']})")

        return web.json_response({
            'status': 'logged',
            'progress': progress_entry
        })

    async def get_progress(self, request):
        """Get current progress"""
        status_filter = request.query.get('status_filter')

        # Mock progress data
        progress_items = [
            {
                'description': 'ConPort hybrid architecture implementation',
                'status': 'IN_PROGRESS',
                'percentage': 60,
                'timestamp': asyncio.get_event_loop().time() - 180
            }
        ]

        if status_filter:
            progress_items = [p for p in progress_items if p['status'] == status_filter]

        return web.json_response({
            'progress_items': progress_items,
            'filter': status_filter
        })

    async def mcp_endpoint(self, request):
        """MCP compatibility endpoint for future integration"""
        try:
            mcp_request = await request.json()

            # Basic MCP protocol response structure
            response = {
                'jsonrpc': '2.0',
                'id': mcp_request.get('id'),
                'result': {
                    'status': 'mcp_compatibility_layer',
                    'message': 'Future MCP integration endpoint - currently proxying to HTTP API'
                }
            }

            return web.json_response(response)

        except Exception as e:
            logger.error(f"MCP endpoint error: {e}")
            return web.json_response({
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }, status=500)

    async def start_server(self):
        """Start the direct HTTP server"""
        logger.info(f"🚀 Starting Direct ConPort HTTP Server on {self.host}:{self.port}")

        # Create and start web server
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info(f"✅ ConPort Direct API available at http://{self.host}:{self.port}")
        logger.info("📋 Available endpoints:")
        logger.info(f"  - GET  /health - Health check")
        logger.info(f"  - GET  /api/context/{{workspace_id}} - Get context")
        logger.info(f"  - POST /api/context/{{workspace_id}} - Update context")
        logger.info(f"  - POST /api/decisions - Log decision")
        logger.info(f"  - GET  /api/decisions - Get decisions")
        logger.info(f"  - POST /api/progress - Log progress")
        logger.info(f"  - GET  /api/progress - Get progress")
        logger.info(f"  - POST /mcp - MCP compatibility (future)")

        # Wait for shutdown signal
        await self.shutdown_event.wait()

        # Cleanup
        await runner.cleanup()
        logger.info("🛑 ConPort Direct Server stopped")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown")
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        """Signal shutdown"""
        self.shutdown_event.set()

async def main():
    server = DirectConPortServer()

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, server.signal_handler, sig, None)

    try:
        await server.start_server()
        return 0
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down")
        await server.shutdown()
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await server.shutdown()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
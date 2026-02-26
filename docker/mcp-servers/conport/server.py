#!/usr/bin/env python3
"""
ConPort MCP Server wrapper for Dopemux
Converts stdio-based ConPort to HTTP server
"""

import asyncio
import subprocess
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConPortMCPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.conport_process = None
        super().__init__(*args, **kwargs)

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Forward to ConPort stdio process
            if not hasattr(self.server, 'conport_process') or self.server.conport_process.poll() is not None:
                self.server.start_conport_process()

            # Send request to ConPort
            self.server.conport_process.stdin.write(post_data + b'\n')
            self.server.conport_process.stdin.flush()

            # Read response
            response = self.server.conport_process.stdout.readline()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response)

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

class ConPortMCPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conport_process = None
        self.start_conport_process()

    def start_conport_process(self):
        try:
            # Start ConPort MCP in stdio mode
            self.conport_process = subprocess.Popen(
                ['uvx', '--from', 'context-portal-mcp', 'conport-mcp', '--mode', 'stdio'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False
            )
            logger.info("ConPort MCP process started")
        except Exception as e:
            logger.error(f"Failed to start ConPort process: {e}")

if __name__ == "__main__":
    port = int(os.getenv('MCP_SERVER_PORT', 3004))
    server = ConPortMCPServer(('0.0.0.0', port), ConPortMCPHandler)

    logger.info(f"🧠 ConPort MCP Server starting on port {port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down ConPort MCP Server")
        if server.conport_process:
            server.conport_process.terminate()
        server.shutdown()
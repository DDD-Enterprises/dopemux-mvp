#!/usr/bin/env python3
"""
MorphLLM Fast Apply MCP Server wrapper for Dopemux
Converts stdio-based MorphLLM to HTTP server
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

class MorphLLMMCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Forward to MorphLLM stdio process
            if not hasattr(self.server, 'morphllm_process') or self.server.morphllm_process.poll() is not None:
                self.server.start_morphllm_process()

            # Send request to MorphLLM
            self.server.morphllm_process.stdin.write(post_data + b'\n')
            self.server.morphllm_process.stdin.flush()

            # Read response
            response = self.server.morphllm_process.stdout.readline()

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

class MorphLLMMCPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.morphllm_process = None
        self.start_morphllm_process()

    def start_morphllm_process(self):
        try:
            # Start MorphLLM Fast Apply MCP in stdio mode
            self.morphllm_process = subprocess.Popen(
                ['uvx', 'morphllm-fast-apply'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False
            )
            logger.info("MorphLLM Fast Apply MCP process started")
        except Exception as e:
            logger.error(f"Failed to start MorphLLM process: {e}")

if __name__ == "__main__":
    port = int(os.getenv('MCP_SERVER_PORT', 3011))
    server = MorphLLMMCPServer(('0.0.0.0', port), MorphLLMMCPHandler)

    logger.info(f"🔧 MorphLLM Fast Apply MCP Server starting on port {port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down MorphLLM Fast Apply MCP Server")
        if server.morphllm_process:
            server.morphllm_process.terminate()
        server.shutdown()
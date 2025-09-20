#!/usr/bin/env python3
"""
Task Master AI MCP Server wrapper for Dopemux
Converts stdio-based Task Master AI to HTTP server
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

class TaskMasterMCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Forward to Task Master AI stdio process
            if not hasattr(self.server, 'task_master_process') or self.server.task_master_process.poll() is not None:
                self.server.start_task_master_process()

            # Send request to Task Master AI
            self.server.task_master_process.stdin.write(post_data + b'\n')
            self.server.task_master_process.stdin.flush()

            # Read response
            response = self.server.task_master_process.stdout.readline()

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

class TaskMasterMCPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_master_process = None
        self.start_task_master_process()

    def start_task_master_process(self):
        try:
            # Start Task Master AI MCP in stdio mode
            self.task_master_process = subprocess.Popen(
                ['uvx', '--from', 'task-master-ai', 'task_master_mcp', '--mode', 'stdio'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False
            )
            logger.info("Task Master AI MCP process started")
        except Exception as e:
            logger.error(f"Failed to start Task Master AI process: {e}")

if __name__ == "__main__":
    port = int(os.getenv('MCP_SERVER_PORT', 3005))
    server = TaskMasterMCPServer(('0.0.0.0', port), TaskMasterMCPHandler)

    logger.info(f"📋 Task Master AI MCP Server starting on port {port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Task Master AI MCP Server")
        if server.task_master_process:
            server.task_master_process.terminate()
        server.shutdown()
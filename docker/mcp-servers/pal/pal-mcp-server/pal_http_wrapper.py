#!/usr/bin/env python3
"""
HTTP wrapper for Zen MCP Server
Runs the MCP server as a subprocess and provides HTTP health endpoint
"""

import subprocess
import threading
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import signal
import sys
import os

class ZenServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Check if MCP process is still running
            if hasattr(self.server, 'mcp_process') and self.server.mcp_process.poll() is None:
                status = {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "mcp_process_running": True,
                    "mcp_pid": self.server.mcp_process.pid
                }
            else:
                status = {
                    "status": "unhealthy",
                    "timestamp": time.time(),
                    "mcp_process_running": False
                }

            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def log_message(self, format, *args):
        # Suppress default HTTP request logging
        pass

def start_zen_server():
    """Start the Zen MCP server as a subprocess"""
    cmd = [sys.executable, "server.py"]
    print(f"Starting Zen MCP server with command: {' '.join(cmd)}", flush=True)

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,   # Text mode for JSON-RPC (line-based)
        bufsize=1,   # Line-buffered for JSON-RPC
        universal_newlines=True
    )

    # Start threads to handle output
    def handle_output(stream, prefix):
        try:
            for line in iter(stream.readline, ''):
                if line.strip():  # Only print non-empty lines
                    print(f"[ZEN {prefix}] {line.strip()}")
        except Exception as e:
            print(f"[ZEN {prefix}] Error reading output: {e}")
        finally:
            stream.close()

    threading.Thread(target=handle_output, args=(process.stdout, "OUT"), daemon=True).start()
    threading.Thread(target=handle_output, args=(process.stderr, "ERR"), daemon=True).start()

    return process

def main():
    port = int(os.environ.get('MCP_SERVER_PORT', 3003))
    
    print(f"🧠 Zen HTTP Wrapper starting...", flush=True)
    print(f"📍 Port: {port}", flush=True)

    # Start Zen MCP server
    mcp_process = start_zen_server()

    # Create HTTP server
    server = HTTPServer(('0.0.0.0', port), ZenServerHandler)
    print(f"HTTP server started on 0.0.0.0:{port}", flush=True)
    server.mcp_process = mcp_process

    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        if mcp_process.poll() is None:
            mcp_process.terminate()
            try:
                mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mcp_process.kill()
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print(f"🧠 Zen MCP Server wrapper running on port {port}", flush=True)
    print(f"💡 Health endpoint: http://0.0.0.0:{port}/health", flush=True)

    try:
        print("Starting HTTP server serve_forever...", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        signal_handler(signal.SIGTERM, None)

if __name__ == "__main__":
    main()
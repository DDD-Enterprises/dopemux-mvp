#!/usr/bin/env python3
"""
HTTP wrapper for Zen MCP Server with SSE support.
Runs the MCP server as a subprocess and provides HTTP health and SSE endpoints.
"""

import subprocess
import threading
import time
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import signal
import sys
import os
import queue
import uuid

# Global queue registry for SSE clients.
sse_queues = {}

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
        elif self.path == '/sse':
            client_id = str(uuid.uuid4())
            client_queue = queue.Queue()
            sse_queues[client_id] = client_queue

            try:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.send_header('X-MCP-SSE-Endpoint', f'/message?client_id={client_id}')
                self.end_headers()

                endpoint_msg = f"event: endpoint\ndata: /message?client_id={client_id}\n\n"
                self.wfile.write(endpoint_msg.encode())
                self.wfile.flush()

                print(f"New SSE client connected: {client_id}")

                while True:
                    try:
                        message = client_queue.get(timeout=30)
                        if message is None:
                            break
                        sse_msg = f"event: message\ndata: {message}\n\n"
                        self.wfile.write(sse_msg.encode())
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
            except Exception as exc:
                print(f"SSE client {client_id} disconnected: {exc}")
            finally:
                sse_queues.pop(client_id, None)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_POST(self):
        if self.path == '/message' or self.path.startswith('/message?'):
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            if hasattr(self.server, 'mcp_process') and self.server.mcp_process.poll() is None:
                try:
                    self.server.mcp_process.stdin.write(post_data + "\n")
                    self.server.mcp_process.stdin.flush()
                    self.send_response(202)
                    self.end_headers()
                    self.wfile.write(b'OK')
                except Exception as exc:
                    print(f"Error writing to MCP stdin: {exc}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(str(exc).encode())
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'MCP process not running')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP request logging
        pass

def start_zen_server():
    """Start the Zen MCP server as a subprocess"""
    cmd = ["/app/.venv/bin/python", "server.py"]
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

    def handle_stdout(stream):
        try:
            for line in iter(stream.readline, ''):
                line = line.strip()
                if line:
                    for client_queue in list(sse_queues.values()):
                        client_queue.put(line)
        except Exception as exc:
            print(f"[ZEN OUT] Error reading stdout: {exc}")
        finally:
            stream.close()

    def handle_stderr(stream):
        try:
            for line in iter(stream.readline, ''):
                if line.strip():
                    print(f"[ZEN ERR] {line.strip()}")
        except Exception as exc:
            print(f"[ZEN ERR] Error reading stderr: {exc}")
        finally:
            stream.close()

    threading.Thread(target=handle_stdout, args=(process.stdout,), daemon=True).start()
    threading.Thread(target=handle_stderr, args=(process.stderr,), daemon=True).start()

    return process

def main():
    port = int(os.environ.get('MCP_SERVER_PORT', 3003))
    
    print(f"🧠 Zen HTTP Wrapper with SSE starting...", flush=True)
    print(f"📍 Port: {port}", flush=True)

    # Start Zen MCP server
    mcp_process = start_zen_server()

    # Create HTTP server
    server = ThreadingHTTPServer(('0.0.0.0', port), ZenServerHandler)
    print(f"HTTP server started on 0.0.0.0:{port}", flush=True)
    server.mcp_process = mcp_process

    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        for client_queue in list(sse_queues.values()):
            client_queue.put(None)
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
    print(f"📡 SSE endpoint: http://0.0.0.0:{port}/sse", flush=True)

    try:
        print("Starting HTTP server serve_forever...", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        signal_handler(signal.SIGTERM, None)

if __name__ == "__main__":
    main()

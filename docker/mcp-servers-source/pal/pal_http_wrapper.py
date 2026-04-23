#!/usr/bin/env python3
"""
HTTP wrapper for the PAL MCP server with SSE support.
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
from urllib.parse import parse_qs, urlparse

SSE_QUEUE_MAXSIZE = 256

# Single-session registry for the PAL stdio subprocess.
sse_queues = {}
sse_lock = threading.Lock()
shutdown_requested = threading.Event()

class PalServerHandler(BaseHTTPRequestHandler):
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
            session_id = str(uuid.uuid4())
            client_queue = queue.Queue(maxsize=SSE_QUEUE_MAXSIZE)
            with sse_lock:
                if sse_queues:
                    self.send_response(409)
                    self.end_headers()
                    self.wfile.write(b'PAL SSE wrapper supports only one active session')
                    return
                sse_queues[session_id] = client_queue

            try:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.send_header('X-MCP-SSE-Endpoint', f'/messages/?session_id={session_id}')
                self.end_headers()

                endpoint_msg = f"event: endpoint\ndata: /messages/?session_id={session_id}\n\n"
                self.wfile.write(endpoint_msg.encode())
                self.wfile.flush()

                print(f"New PAL SSE session connected: {session_id}")

                while not shutdown_requested.is_set():
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
                print(f"PAL SSE session {session_id} disconnected: {exc}")
            finally:
                with sse_lock:
                    sse_queues.pop(session_id, None)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/messages/':
            self.send_response(404)
            self.end_headers()
            return

        session_id = parse_qs(parsed.query).get('session_id', [None])[0]
        if not session_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'session_id query parameter is required')
            return

        with sse_lock:
            active = session_id in sse_queues

        if not active:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Unknown or inactive session_id')
            return

        content_length_header = self.headers.get('Content-Length')
        if content_length_header is None:
            self.send_response(411)
            self.end_headers()
            self.wfile.write(b'Content-Length header is required')
            return

        try:
            content_length = int(content_length_header)
        except ValueError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid Content-Length header')
            return

        if content_length < 0:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid Content-Length header')
            return

        post_data = self.rfile.read(content_length).decode('utf-8')

        if hasattr(self.server, 'mcp_process') and self.server.mcp_process.poll() is None:
            try:
                self.server.mcp_process.stdin.write(post_data + "\n")
                self.server.mcp_process.stdin.flush()
                self.send_response(202)
                self.end_headers()
                self.wfile.write(b'OK')
            except Exception as exc:
                print(f"Error writing to PAL MCP stdin: {exc}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(exc).encode())
        else:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'MCP process not running')

    def log_message(self, format, *args):
        # Suppress default HTTP request logging
        pass

def start_pal_server():
    """Start the PAL MCP server as a subprocess."""
    cmd = ["/app/.venv/bin/python", "server.py"]
    print(f"Starting PAL MCP server with command: {' '.join(cmd)}", flush=True)

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
                    with sse_lock:
                        clients = list(sse_queues.items())
                    for session_id, client_queue in clients:
                        try:
                            client_queue.put_nowait(line)
                        except queue.Full:
                            print(
                                f"PAL SSE session {session_id} is too slow; closing session",
                                flush=True,
                            )
                            with sse_lock:
                                stale_queue = sse_queues.pop(session_id, None)
                            if stale_queue is not None:
                                try:
                                    stale_queue.put_nowait(None)
                                except queue.Full:
                                    pass
        except Exception as exc:
            print(f"[PAL OUT] Error reading stdout: {exc}")
        finally:
            stream.close()

    def handle_stderr(stream):
        try:
            for line in iter(stream.readline, ''):
                if line.strip():
                    print(f"[PAL ERR] {line.strip()}")
        except Exception as exc:
            print(f"[PAL ERR] Error reading stderr: {exc}")
        finally:
            stream.close()

    threading.Thread(target=handle_stdout, args=(process.stdout,), daemon=True).start()
    threading.Thread(target=handle_stderr, args=(process.stderr,), daemon=True).start()

    return process

def main():
    port = int(os.environ.get('MCP_SERVER_PORT', 3003))
    
    print("PAL HTTP Wrapper with SSE starting...", flush=True)
    print(f"📍 Port: {port}", flush=True)

    # Start PAL MCP server
    mcp_process = start_pal_server()

    # Create HTTP server
    server = ThreadingHTTPServer(('0.0.0.0', port), PalServerHandler)
    print(f"HTTP server started on 0.0.0.0:{port}", flush=True)
    server.mcp_process = mcp_process

    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        shutdown_requested.set()
        with sse_lock:
            active_queues = list(sse_queues.values())
            sse_queues.clear()
        for client_queue in active_queues:
            try:
                client_queue.put_nowait(None)
            except queue.Full:
                pass
        if mcp_process.poll() is None:
            mcp_process.terminate()
            try:
                mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mcp_process.kill()
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print(f"PAL MCP server wrapper running on port {port}", flush=True)
    print(f"💡 Health endpoint: http://0.0.0.0:{port}/health", flush=True)
    print(f"📡 SSE endpoint: http://0.0.0.0:{port}/sse", flush=True)
    print(f"📨 Message endpoint: http://0.0.0.0:{port}/messages/?session_id=<id>", flush=True)

    try:
        print("Starting HTTP server serve_forever...", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    finally:
        if not shutdown_requested.is_set():
            signal_handler(signal.SIGTERM, None)
        sys.exit(0)

if __name__ == "__main__":
    main()

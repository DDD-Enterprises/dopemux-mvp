#!/usr/bin/env python3

import subprocess
import http.server
import socketserver
import threading
import signal
import sys
import json
import os

port = int(os.environ.get('MCP_SERVER_PORT', 3006))

print('🔧 Starting Serena MCP Server...')

# Start serena MCP server as subprocess
serena_process = subprocess.Popen(
    ['uvx', '--from', 'git+https://github.com/oraios/serena', 'serena', 'start-mcp-server'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default request logging
        pass

    def do_GET(self):
        if self.path == '/health':
            status = {
                'status': 'healthy' if serena_process.poll() is None else 'unhealthy',
                'serena_running': serena_process.poll() is None,
                'pid': serena_process.pid if serena_process.poll() is None else None
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

def output_reader(pipe, prefix):
    try:
        for line in iter(pipe.readline, ''):
            if line.strip():
                print(f'[SERENA {prefix}] {line.strip()}')
    except:
        pass

# Start output readers
threading.Thread(target=output_reader, args=(serena_process.stdout, 'OUT'), daemon=True).start()
threading.Thread(target=output_reader, args=(serena_process.stderr, 'ERR'), daemon=True).start()

def signal_handler(signum, frame):
    print('🔧 Shutting down Serena MCP Server...')
    serena_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start HTTP server
with socketserver.TCPServer(('0.0.0.0', port), HealthHandler) as httpd:
    print(f'🔧 Serena MCP Server wrapper running on port {port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
#!/usr/bin/env python3
"""
HTTP wrapper for GPT Researcher MCP Server
- Spawns upstream server.py on port 3015
- Exposes port 3009 and:
  - /health: returns status based on upstream
  - Proxies other routes to upstream (best-effort)
"""

import asyncio
import os
import signal
import sys
from aiohttp import web, ClientSession
import subprocess

UPSTREAM_PORT = int(os.getenv("GPTR_UPSTREAM_PORT", "3015"))
WRAPPER_PORT = int(os.getenv("MCP_SERVER_PORT", "3009"))

process = None

async def start_upstream():
    global process
    if process is not None and process.poll() is None:
        return
    cmd = [sys.executable, "server.py", "--port", str(UPSTREAM_PORT)]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

async def stop_upstream():
    global process
    if process and process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
            process.wait()

async def health_handler(_request: web.Request):
    async with ClientSession() as session:
        try:
            async with session.get(f"http://127.0.0.1:{UPSTREAM_PORT}/health", timeout=3) as resp:
                text = await resp.text()
                return web.Response(status=resp.status, text=text, content_type="application/json")
        except Exception:
            return web.json_response({"status": "unhealthy"}, status=503)

async def proxy_handler(request: web.Request):
    method = request.method
    path_qs = request.rel_url
    url = f"http://127.0.0.1:{UPSTREAM_PORT}{path_qs}"

    headers = dict(request.headers)
    body = await request.read()

    async with ClientSession() as session:
        try:
            async with session.request(method, url, data=body, headers=headers) as resp:
                data = await resp.read()
                return web.Response(status=resp.status, body=data, headers=resp.headers)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=502)

async def on_startup(app: web.Application):
    await start_upstream()

async def on_shutdown(app: web.Application):
    await stop_upstream()

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Dedicated health route
    app.router.add_get("/health", health_handler)

    # Proxy all other routes
    app.router.add_route("GET", "/{tail:.*}", proxy_handler)
    app.router.add_route("POST", "/{tail:.*}", proxy_handler)
    app.router.add_route("OPTIONS", "/{tail:.*}", proxy_handler)

    web.run_app(app, host="0.0.0.0", port=WRAPPER_PORT)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass


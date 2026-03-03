#!/usr/bin/env python3
"""
Simple ConPort metrics server
Just exports /metrics endpoint for Prometheus
"""
import os
import sys
sys.path.insert(0, '/app/shared')

from aiohttp import web
from monitoring.base import DopemuxMonitoring
from prometheus_client import generate_latest

# Initialize monitoring
monitoring = DopemuxMonitoring(
    service_name="conport",
    workspace_id=os.getenv("WORKSPACE_ID", "default"),
    instance_id=os.getenv("INSTANCE_ID", "0"),
    version=os.getenv("SERVICE_VERSION", "1.0.0")
)

async def metrics_handler(request):
    """Prometheus metrics endpoint"""
    metrics_output = generate_latest(monitoring.registry)
    return web.Response(
        body=metrics_output,
        content_type='text/plain'
    )

async def health_handler(request):
    """Health check"""
    return web.json_response({
        "status": "healthy",
        "service": "conport-metrics",
        "version": "1.0.0"
    })

# Create web app
app = web.Application()
app.router.add_get('/metrics', metrics_handler)
app.router.add_get('/health', health_handler)

if __name__ == '__main__':
    port = int(os.getenv('MCP_SERVER_PORT', 3004))
    print(f"🚀 Starting ConPort metrics server on port {port}")
    print(f"📊 Metrics available at http://localhost:{port}/metrics")
    web.run_app(app, host='0.0.0.0', port=port)

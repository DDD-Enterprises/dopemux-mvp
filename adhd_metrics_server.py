"""
Standalone metrics endpoint for ADHD Engine
Runs on port 9095 to serve /metrics
"""
import os
import sys
sys.path.insert(0, '/app/shared')

from monitoring.base import DopemuxMonitoring
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from aiohttp import web
import asyncio

# Initialize monitoring
monitoring = DopemuxMonitoring(
    service_name="adhd-engine",
    workspace_id=os.getenv("WORKSPACE_ID", "default"),
    instance_id=os.getenv("INSTANCE_ID", "5"),
    version=os.getenv("SERVICE_VERSION", "1.0.0")
)

async def metrics_handler(request):
    """Prometheus metrics endpoint"""
    metrics_output = generate_latest(monitoring.registry)
    return web.Response(
        body=metrics_output,
        content_type='text/plain; charset=utf-8'
    )

async def health_handler(request):
    """Health check"""
    return web.json_response({"status": "healthy", "service": "adhd-engine-metrics"})

# Create web app
app = web.Application()
app.router.add_get('/metrics', metrics_handler)
app.router.add_get('/health', health_handler)

if __name__ == '__main__':
    print("🚀 Starting ADHD Engine metrics server on port 9095")
    print("📊 Metrics available at http://localhost:9095/metrics")
    web.run_app(app, host='0.0.0.0', port=9095)

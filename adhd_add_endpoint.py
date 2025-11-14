"""
Add /metrics-v2 endpoint to existing ADHD Engine
Run this to patch the running service
"""
import sys
sys.path.insert(0, '/app')

from fastapi import FastAPI, Response
from monitoring_patch import get_metrics_v2, monitoring
import uvicorn

# Get the existing app
from main import app

# Add new endpoint
@app.get("/metrics-v2")
async def metrics_v2():
    """Prometheus metrics endpoint - New monitoring system"""
    from prometheus_client import CONTENT_TYPE_LATEST
    return Response(
        content=get_metrics_v2(),
        media_type=CONTENT_TYPE_LATEST
    )

# Record that monitoring is active
monitoring.set_health(True)

print("✅ /metrics-v2 endpoint added to ADHD Engine")
print("📊 Access metrics at http://localhost:8095/metrics-v2")

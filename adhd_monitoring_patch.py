"""
Monitoring patch for ADHD Engine
Adds /metrics-v2 endpoint with DopemuxMonitoring without breaking existing code
"""
import os
import sys
sys.path.insert(0, '/app/shared')

from monitoring.base import DopemuxMonitoring
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Initialize monitoring
monitoring = DopemuxMonitoring(
    service_name="adhd-engine",
    workspace_id=os.getenv("WORKSPACE_ID", "default"),
    instance_id=os.getenv("INSTANCE_ID", "0"),
    version=os.getenv("SERVICE_VERSION", "1.0.0")
)

def get_metrics_v2():
    """Get metrics in Prometheus format"""
    return generate_latest(monitoring.registry).decode('utf-8')

print("✅ Monitoring patch loaded successfully")

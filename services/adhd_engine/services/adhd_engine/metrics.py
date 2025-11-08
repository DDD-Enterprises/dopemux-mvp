"""
Minimal metrics module for ADHD Engine.

Provides Prometheus-compatible metrics for monitoring ADHD accommodation services.
This is a simplified implementation to allow the service to start.
"""

# Try to import prometheus_client, but don't fail if it's not available
try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for when prometheus is not available
    class DummyMetric:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def info(self, *args, **kwargs):
            pass

    Counter = Histogram = Gauge = Info = DummyMetric

import time

# Request metrics
REQUEST_COUNT = Counter('adhd_requests_total', 'Total number of requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('adhd_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])

# ADHD state metrics
ENERGY_LEVEL = Gauge('adhd_energy_level', 'Current energy level', ['user_id'])
ATTENTION_STATE = Gauge('adhd_attention_state', 'Current attention state', ['user_id'])
COGNITIVE_LOAD = Gauge('adhd_cognitive_load', 'Current cognitive load', ['user_id'])

# Accommodation metrics
BREAK_RECOMMENDATIONS = Counter('adhd_break_recommendations_total', 'Total break recommendations')
ACCOMMODATION_STATS = Counter('adhd_accommodation_actions_total', 'Total accommodation actions', ['action_type'])

# User metrics
ACTIVE_USERS = Gauge('adhd_active_users', 'Number of active users')
MONITORING_CYCLES = Counter('adhd_monitoring_cycles_total', 'Total monitoring cycles completed')

# Service info (only if prometheus is available)
if PROMETHEUS_AVAILABLE:
    SERVICE_INFO = Info('adhd_service', 'ADHD Engine service information')
    SERVICE_INFO.info({'version': '1.0.0', 'service': 'adhd-engine'})
else:
    SERVICE_INFO = None


def record_request(method: str, endpoint: str, duration: float = None):
    """Record a request."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    if duration is not None:
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def update_energy_level(user_id: str, level: float):
    """Update energy level metric."""
    ENERGY_LEVEL.labels(user_id=user_id).set(level)


def update_attention_state(user_id: str, state: float):
    """Update attention state metric."""
    ATTENTION_STATE.labels(user_id=user_id).set(state)


def update_cognitive_load(user_id: str, load: float):
    """Update cognitive load metric."""
    COGNITIVE_LOAD.labels(user_id=user_id).set(load)


def record_break_recommendation():
    """Record a break recommendation."""
    BREAK_RECOMMENDATIONS.inc()


def record_accommodation_action(action_type: str):
    """Record an accommodation action."""
    ACCOMMODATION_STATS.labels(action_type=action_type).inc()


def update_active_users(count: int):
    """Update active users count."""
    ACTIVE_USERS.set(count)


def record_monitoring_cycle():
    """Record a monitoring cycle completion."""
    MONITORING_CYCLES.inc()


def get_metrics():
    """Get current metrics snapshot."""
    return {
        'requests_total': REQUEST_COUNT._value,
        'active_users': ACTIVE_USERS._value,
        'monitoring_cycles': MONITORING_CYCLES._value,
        'break_recommendations': BREAK_RECOMMENDATIONS._value,
    }
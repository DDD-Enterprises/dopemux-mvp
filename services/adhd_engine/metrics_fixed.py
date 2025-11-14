"""
Metrics module for ADHD Engine - Fixed version
Provides Prometheus-compatible metrics for monitoring ADHD accommodation services.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST

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

# Service info
SERVICE_INFO = Info('adhd_service', 'ADHD Engine service information')
SERVICE_INFO.info({
    'version': '1.0.0',
    'service': 'adhd-accommodation-engine'
})


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
    """Get current metrics in Prometheus format."""
    return generate_latest().decode('utf-8')

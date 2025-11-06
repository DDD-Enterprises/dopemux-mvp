"""
Prometheus metrics for ADHD Engine monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from typing import Dict, Any

# Request metrics
REQUEST_COUNT = Counter(
    'adhd_engine_requests_total',
    'Total number of requests to ADHD Engine',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'adhd_engine_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

# ADHD-specific metrics
ENERGY_LEVEL = Gauge(
    'adhd_engine_energy_level',
    'Current energy level (0-1 scale)',
    ['user_id']
)

ATTENTION_STATE = Gauge(
    'adhd_engine_attention_state',
    'Current attention state (0-1 scale)',
    ['user_id']
)

COGNITIVE_LOAD = Gauge(
    'adhd_engine_cognitive_load',
    'Current cognitive load (0-1 scale)',
    ['user_id']
)

BREAK_RECOMMENDATIONS = Counter(
    'adhd_engine_break_recommendations_total',
    'Total break recommendations issued',
    ['reason']
)

ACCOMMODATION_STATS = Counter(
    'adhd_engine_accommodation_actions_total',
    'Total accommodation actions taken',
    ['action_type']
)

# System metrics
ACTIVE_USERS = Gauge(
    'adhd_engine_active_users',
    'Number of active users being monitored'
)

MONITORING_CYCLES = Counter(
    'adhd_engine_monitoring_cycles_total',
    'Total monitoring cycles completed'
)

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record a request metric"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

def update_energy_level(user_id: str, level: float):
    """Update energy level metric"""
    ENERGY_LEVEL.labels(user_id=user_id).set(level)

def update_attention_state(user_id: str, state: float):
    """Update attention state metric"""
    ATTENTION_STATE.labels(user_id=user_id).set(state)

def update_cognitive_load(user_id: str, load: float):
    """Update cognitive load metric"""
    COGNITIVE_LOAD.labels(user_id=user_id).set(load)

def record_break_recommendation(reason: str):
    """Record break recommendation"""
    BREAK_RECOMMENDATIONS.labels(reason=reason).inc()

def record_accommodation_action(action_type: str):
    """Record accommodation action"""
    ACCOMMODATION_STATS.labels(action_type=action_type).inc()

def update_active_users(count: int):
    """Update active users count"""
    ACTIVE_USERS.set(count)

def record_monitoring_cycle():
    """Record completed monitoring cycle"""
    MONITORING_CYCLES.inc()

def get_metrics():
    """Get all metrics in Prometheus format"""
    return generate_latest()
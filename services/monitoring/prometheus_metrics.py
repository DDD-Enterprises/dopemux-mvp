"""
Prometheus Metrics for Dopemux Production Monitoring

Tracks ADHD-critical metrics across all services.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client import CollectorRegistry, generate_latest

# Create custom registry
registry = CollectorRegistry()

# =====================================================================
# Request Metrics
# =====================================================================

http_requests_total = Counter(
    'dopemux_http_requests_total',
    'Total HTTP requests',
    ['service', 'endpoint', 'method', 'status'],
    registry=registry
)

http_request_duration = Histogram(
    'dopemux_http_request_duration_seconds',
    'HTTP request latency',
    ['service', 'endpoint'],
    buckets=[.001, .005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0],
    registry=registry
)

# =====================================================================
# ADHD Performance Metrics (CRITICAL)
# =====================================================================

adhd_search_latency = Histogram(
    'dopemux_adhd_search_latency_seconds',
    'Search latency for ADHD-optimized queries',
    ['search_type'],  # 'semantic', 'unified', 'code', 'docs'
    buckets=[.01, .05, .1, .2, .5, 1.0],  # Target: <200ms = 0.2s
    registry=registry
)

adhd_complexity_calculations = Counter(
    'dopemux_adhd_complexity_calculations_total',
    'Total complexity calculations performed',
    ['feature'],  # 'f-new-3', 'ast', 'lsp', 'unified'
    registry=registry
)

adhd_break_suggestions = Counter(
    'dopemux_adhd_break_suggestions_total',
    'Total break suggestions generated',
    ['priority'],  # 'low', 'medium', 'high', 'critical'
    registry=registry
)

adhd_task_completions = Counter(
    'dopemux_adhd_task_completions_total',
    'Tasks completed vs abandoned',
    ['outcome'],  # 'completed', 'abandoned', 'switched'
    registry=registry
)

adhd_cognitive_state = Gauge(
    'dopemux_adhd_cognitive_state',
    'Current cognitive state metrics',
    ['user_id', 'metric'],  # metric: 'energy', 'attention', 'cognitive_load'
    registry=registry
)

# =====================================================================
# Feature-Specific Metrics
# =====================================================================

fnew6_session_intelligence_calls = Counter(
    'dopemux_fnew6_session_intelligence_total',
    'F-NEW-6 session intelligence queries',
    ['user_id'],
    registry=registry
)

fnew8_break_adherence = Counter(
    'dopemux_fnew8_break_adherence_total',
    'Break suggestions followed vs ignored',
    ['action'],  # 'followed', 'ignored', 'snoozed'
    registry=registry
)

# =====================================================================
# Database Metrics
# =====================================================================

db_query_duration = Histogram(
    'dopemux_db_query_duration_seconds',
    'Database query latency',
    ['operation', 'table'],
    buckets=[.001, .005, .01, .025, .05, .1, .25, .5],
    registry=registry
)

db_connections = Gauge(
    'dopemux_db_connections',
    'Active database connections',
    ['pool'],  # 'conport', 'task-orchestrator', 'serena'
    registry=registry
)

# =====================================================================
# Cache Metrics
# =====================================================================

cache_operations = Counter(
    'dopemux_cache_operations_total',
    'Cache hit/miss operations',
    ['cache_type', 'operation'],  # operation: 'hit', 'miss', 'set', 'invalidate'
    registry=registry
)

cache_latency = Histogram(
    'dopemux_cache_latency_seconds',
    'Cache operation latency',
    ['cache_type', 'operation'],
    buckets=[.0001, .0005, .001, .005, .01, .05],
    registry=registry
)

# =====================================================================
# Event Bus Metrics
# =====================================================================

eventbus_events_published = Counter(
    'dopemux_eventbus_events_published_total',
    'Events published to stream',
    ['event_type', 'source'],
    registry=registry
)

eventbus_events_consumed = Counter(
    'dopemux_eventbus_events_consumed_total',
    'Events consumed from stream',
    ['event_type', 'consumer'],
    registry=registry
)

eventbus_consumer_lag = Gauge(
    'dopemux_eventbus_consumer_lag',
    'Consumer group lag in messages',
    ['consumer_group'],
    registry=registry
)

# =====================================================================
# MCP Metrics
# =====================================================================

mcp_tool_calls = Counter(
    'dopemux_mcp_tool_calls_total',
    'MCP tool invocations',
    ['server', 'tool'],
    registry=registry
)

mcp_tool_duration = Histogram(
    'dopemux_mcp_tool_duration_seconds',
    'MCP tool execution time',
    ['server', 'tool'],
    buckets=[.01, .05, .1, .25, .5, 1.0, 2.5, 5.0],
    registry=registry
)

mcp_tool_errors = Counter(
    'dopemux_mcp_tool_errors_total',
    'MCP tool errors',
    ['server', 'tool', 'error_type'],
    registry=registry
)

# =====================================================================
# Helper Functions
# =====================================================================

def get_metrics():
    """Get current metrics in Prometheus format."""
    return generate_latest(registry).decode('utf-8')


def track_adhd_latency(search_type: str, duration_seconds: float):
    """Track ADHD-critical search latency."""
    adhd_search_latency.labels(search_type=search_type).observe(duration_seconds)


def track_break_suggestion(priority: str):
    """Track break suggestion generated."""
    adhd_break_suggestions.labels(priority=priority).inc()


def track_task_completion(outcome: str):
    """Track task completion outcome."""
    adhd_task_completions.labels(outcome=outcome).inc()


def update_cognitive_state(user_id: str, energy: float, attention: float, cognitive_load: float):
    """Update cognitive state gauges."""
    adhd_cognitive_state.labels(user_id=user_id, metric='energy').set(energy)
    adhd_cognitive_state.labels(user_id=user_id, metric='attention').set(attention)
    adhd_cognitive_state.labels(user_id=user_id, metric='cognitive_load').set(cognitive_load)

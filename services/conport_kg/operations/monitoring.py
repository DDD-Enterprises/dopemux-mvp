#!/usr/bin/env python3
"""
ConPort-KG Operational Monitoring & Observability
Production monitoring, metrics collection, and alerting system.

This module provides:
- Prometheus metrics collection
- Structured logging with correlation IDs
- Performance monitoring and profiling
- Health checks and service discovery
- Alerting thresholds and notifications
- Distributed tracing support
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import asynccontextmanager
import functools

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback mock implementations
    class MockMetric:
        def inc(self, value=1): pass
        def observe(self, value): pass
        def set(self, value): pass
        def labels(self, **kwargs): return self

    def Counter(*args, **kwargs): return MockMetric()
    def Histogram(*args, **kwargs): return MockMetric()
    def Gauge(*args, **kwargs): return MockMetric()
    def generate_latest(*args, **kwargs): return b""

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus Registry
registry = CollectorRegistry()

# Core Metrics
REQUEST_COUNT = Counter(
    'conport_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'conport_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=registry
)

ACTIVE_CONNECTIONS = Gauge(
    'conport_active_connections',
    'Number of active connections',
    registry=registry
)

DATABASE_CONNECTIONS = Gauge(
    'conport_db_connections_active',
    'Number of active database connections',
    registry=registry
)

CACHE_HITS = Counter(
    'conport_cache_hits_total',
    'Total number of cache hits',
    ['cache_type'],
    registry=registry
)

CACHE_MISSES = Counter(
    'conport_cache_misses_total',
    'Total number of cache misses',
    ['cache_type'],
    registry=registry
)

ERROR_COUNT = Counter(
    'conport_errors_total',
    'Total number of errors',
    ['error_type', 'severity'],
    registry=registry
)

# Business Metrics
DECISION_QUERIES = Counter(
    'conport_decision_queries_total',
    'Total number of decision queries',
    ['query_type', 'result_count'],
    registry=registry
)

USER_SESSIONS = Gauge(
    'conport_active_user_sessions',
    'Number of active user sessions',
    registry=registry
)

WORKSPACE_OPERATIONS = Counter(
    'conport_workspace_operations_total',
    'Total workspace operations',
    ['operation_type', 'workspace_id'],
    registry=registry
)

# System Metrics
MEMORY_USAGE = Gauge(
    'conport_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

CPU_USAGE = Gauge(
    'conport_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

DISK_USAGE = Gauge(
    'conport_disk_usage_bytes',
    'Disk usage in bytes',
    ['mount_point'],
    registry=registry
)

@dataclass
class RequestContext:
    """Request context for correlation and monitoring"""
    request_id: str
    user_id: Optional[int] = None
    workspace_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    method: str = ""
    endpoint: str = ""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @property
    def duration(self) -> float:
        """Calculate request duration"""
        return time.time() - self.start_time

class MonitoringService:
    """Central monitoring service"""

    def __init__(self):
        self.request_contexts: Dict[str, RequestContext] = {}
        self.system_metrics_enabled = True
        self.collection_interval = 30  # seconds

    def start_request(self, request_id: str, **kwargs) -> RequestContext:
        """Start monitoring a request"""
        context = RequestContext(request_id=request_id, **kwargs)
        self.request_contexts[request_id] = context
        ACTIVE_CONNECTIONS.inc()
        return context

    def end_request(self, request_id: str, status_code: int = 200):
        """End monitoring a request"""
        context = self.request_contexts.pop(request_id, None)
        if context:
            ACTIVE_CONNECTIONS.dec()

            # Record metrics
            REQUEST_COUNT.labels(
                method=context.method,
                endpoint=context.endpoint,
                status_code=status_code
            ).inc()

            REQUEST_LATENCY.labels(
                method=context.method,
                endpoint=context.endpoint
            ).observe(context.duration)

            # Log slow requests
            if context.duration > 5.0:  # 5 seconds
                logger.warning(
                    f"Slow request: {context.method} {context.endpoint} "
                    f"took {context.duration:.2f}s",
                    extra={"request_context": context}
                )

    def record_error(self, error_type: str, severity: str, context: Optional[RequestContext] = None):
        """Record an error"""
        ERROR_COUNT.labels(error_type=error_type, severity=severity).inc()

        if context:
            logger.error(
                f"Error in request {context.request_id}: {error_type}",
                extra={"request_context": context, "error_type": error_type, "severity": severity}
            )

    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        CACHE_HITS.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        CACHE_MISSES.labels(cache_type=cache_type).inc()

    def record_decision_query(self, query_type: str, result_count: int):
        """Record decision query metrics"""
        DECISION_QUERIES.labels(query_type=query_type, result_count=str(result_count)).inc()

    def update_user_sessions(self, count: int):
        """Update active user sessions count"""
        USER_SESSIONS.set(count)

    def update_database_connections(self, count: int):
        """Update database connections count"""
        DATABASE_CONNECTIONS.set(count)

    async def collect_system_metrics(self):
        """Collect system-level metrics"""
        if not self.system_metrics_enabled:
            return

        try:
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)

            # Disk usage
            disk = psutil.disk_usage('/')
            DISK_USAGE.labels(mount_point='/').set(disk.used)

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    def get_prometheus_metrics(self) -> bytes:
        """Get Prometheus metrics output"""
        return generate_latest(registry)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get human-readable metrics summary"""
        return {
            "active_connections": ACTIVE_CONNECTIONS._value,
            "total_requests": sum(c._value for c in REQUEST_COUNT._metrics.values()),
            "error_rate": self._calculate_error_rate(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "avg_response_time": self._calculate_avg_response_time(),
            "system": {
                "memory_usage": MEMORY_USAGE._value,
                "cpu_usage": CPU_USAGE._value,
                "disk_usage": DISK_USAGE._metrics[('/',)]._value
            }
        }

    def _calculate_error_rate(self) -> float:
        """Calculate error rate from metrics"""
        total_requests = sum(c._value for c in REQUEST_COUNT._metrics.values())
        total_errors = sum(c._value for c in ERROR_COUNT._metrics.values())

        if total_requests == 0:
            return 0.0

        return (total_errors / total_requests) * 100

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_hits = sum(c._value for c in CACHE_HITS._metrics.values())
        total_misses = sum(c._value for c in CACHE_MISSES._metrics.values())
        total_requests = total_hits + total_misses

        if total_requests == 0:
            return 0.0

        return (total_hits / total_requests) * 100

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        # This is a simplified calculation - in practice you'd need to aggregate histogram data
        return REQUEST_LATENCY._sum / REQUEST_LATENCY._count if REQUEST_LATENCY._count > 0 else 0.0

def monitor_request(method: str = "", endpoint: str = "") -> callable:
    """Decorator to monitor FastAPI requests"""
    def decorator(func: callable) -> callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request context
            request = None
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'url'):
                    request = arg
                    break

            if request:
                request_id = getattr(request.state, 'request_id', str(time.time()))
                context = monitoring_service.start_request(
                    request_id=request_id,
                    method=request.method,
                    endpoint=str(request.url.path),
                    ip_address=getattr(request.client, 'host', None) if hasattr(request, 'client') else None,
                    user_agent=request.headers.get('user-agent')
                )

                # Store context in request state
                request.state.monitoring_context = context

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                if request and hasattr(request.state, 'monitoring_context'):
                    monitoring_service.record_error(
                        error_type=type(e).__name__,
                        severity="high",
                        context=request.state.monitoring_context
                    )
                raise
            finally:
                if request and hasattr(request.state, 'monitoring_context'):
                    status_code = getattr(request.state, 'status_code', 500)
                    monitoring_service.end_request(request_id, status_code)

        return wrapper
    return decorator

@asynccontextmanager
async def monitor_operation(operation_name: str, **context):
    """Context manager for monitoring operations"""
    start_time = time.time()
    logger.info(f"Starting operation: {operation_name}", extra=context)

    try:
        yield
        duration = time.time() - start_time
        logger.info(
            f"Completed operation: {operation_name} in {duration:.2f}s",
            extra={**context, "duration": duration, "success": True}
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Failed operation: {operation_name} in {duration:.2f}s - {e}",
            extra={**context, "duration": duration, "success": False, "error": str(e)},
            exc_info=True
        )
        raise

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    condition: str  # e.g., "> 90", "< 10"
    threshold: float
    severity: str
    description: str
    cooldown: int = 300  # seconds

class AlertManager:
    """Alert management system"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.last_alerts: Dict[str, float] = {}

    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules.append(rule)

    async def check_alerts(self):
        """Check all alert rules and trigger if needed"""
        metrics = monitoring_service.get_metrics_summary()

        for rule in self.rules:
            # Check cooldown
            last_alert = self.last_alerts.get(rule.name, 0)
            if time.time() - last_alert < rule.cooldown:
                continue

            # Evaluate condition
            if self._evaluate_condition(metrics, rule):
                await self._trigger_alert(rule)
                self.last_alerts[rule.name] = time.time()

    def _evaluate_condition(self, metrics: Dict[str, Any], rule: AlertRule) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation (could be more sophisticated)
            if rule.condition.startswith(">"):
                threshold = float(rule.condition[1:])
                value = self._get_metric_value(metrics, rule.metric)
                return value > threshold
            elif rule.condition.startswith("<"):
                threshold = float(rule.condition[1:])
                value = self._get_metric_value(metrics, rule.metric)
                return value < threshold
            return False
        except Exception as e:
            logger.error(f"Failed to evaluate alert condition: {e}")
            return False

    def _get_metric_value(self, metrics: Dict[str, Any], path: str) -> float:
        """Extract metric value from nested dict"""
        keys = path.split('.')
        value = metrics
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, 0)
            else:
                return 0
        return float(value) if isinstance(value, (int, float)) else 0

    async def _trigger_alert(self, rule: AlertRule):
        """Trigger an alert"""
        logger.warning(
            f"ALERT: {rule.name} - {rule.description}",
            extra={
                "alert_name": rule.name,
                "severity": rule.severity,
                "description": rule.description,
                "rule": rule.__dict__
            }
        )

        # Here you would integrate with external alerting systems
        # (PagerDuty, Slack, email, etc.)

# Global instances
monitoring_service = MonitoringService()
alert_manager = AlertManager()

# Default alert rules
default_alerts = [
    AlertRule(
        name="high_error_rate",
        metric="error_rate",
        condition="> 5",
        threshold=5.0,
        severity="high",
        description="Error rate exceeded 5%",
        cooldown=300
    ),
    AlertRule(
        name="high_memory_usage",
        metric="system.memory_usage",
        condition="> 8000000000",  # 8GB
        threshold=8000000000,
        severity="medium",
        description="Memory usage exceeded 8GB",
        cooldown=600
    ),
    AlertRule(
        name="slow_response_time",
        metric="avg_response_time",
        condition="> 5.0",
        threshold=5.0,
        severity="medium",
        description="Average response time exceeded 5 seconds",
        cooldown=300
    )
]

for alert in default_alerts:
    alert_manager.add_rule(alert)

__all__ = [
    "RequestContext",
    "MonitoringService",
    "monitor_request",
    "monitor_operation",
    "AlertRule",
    "AlertManager",
    "monitoring_service",
    "alert_manager",
    "registry"
]
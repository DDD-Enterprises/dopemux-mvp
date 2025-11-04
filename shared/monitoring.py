"""
Comprehensive Monitoring System for ADHD Services

Provides structured logging, metrics collection, health monitoring,
and observability across all ADHD services.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import sys

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Structured JSON logging formatter."""

    def format(self, record: logging.LogRecord) -> str:
        # Add structured fields
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, 'service', 'unknown'),
            "request_id": getattr(record, 'request_id', None),
            "user_id": getattr(record, 'user_id', None),
            "operation": getattr(record, 'operation', None),
            "duration_ms": getattr(record, 'duration_ms', None),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                             'pathname', 'filename', 'module', 'exc_info',
                             'exc_text', 'stack_info', 'lineno', 'funcName',
                             'created', 'msecs', 'relativeCreated', 'thread',
                             'threadName', 'processName', 'process', 'message']:
                    log_entry[key] = value

        return json.dumps(log_entry, default=str)


class MonitoringSystem:
    """
    Comprehensive monitoring system for ADHD services.

    Provides metrics collection, health monitoring, structured logging,
    and performance tracking across all services.
    """

    def __init__(self):
        self.redis_pool = None
        self.service_name = "unknown"
        self.metrics: Dict[str, Any] = {}
        self.health_checks: Dict[str, Any] = {}
        self.start_time = time.time()

    async def initialize(self, service_name: str = "unknown"):
        """Initialize monitoring system."""
        self.service_name = service_name

        # Initialize Redis pool for metrics storage
        from .redis_pool import get_redis_pool
        self.redis_pool = await get_redis_pool()

        # Setup structured logging
        self._setup_logging()

        # Initialize metrics
        self.metrics = {
            "service_name": service_name,
            "start_time": self.start_time,
            "uptime_seconds": 0,
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "response_time_avg": 0,
            "response_times": [],
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "active_connections": 0,
            "error_rate": 0,
        }

        logger.info("Monitoring system initialized", extra={
            "service": service_name,
            "operation": "monitoring_init"
        })

    def _setup_logging(self):
        """Setup structured logging."""
        # Remove existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(handler)

        # Set log level
        log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())
        root_logger.setLevel(log_level)

    async def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Record API request metrics.

        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user identifier
            error: Optional error message
        """
        self.metrics["requests_total"] += 1

        if 200 <= status_code < 400:
            self.metrics["requests_success"] += 1
        else:
            self.metrics["requests_error"] += 1

        self.metrics["response_times"].append(response_time_ms)

        # Keep only last 1000 response times for memory efficiency
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

        # Update averages
        self.metrics["response_time_avg"] = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
        self.metrics["error_rate"] = self.metrics["requests_error"] / max(self.metrics["requests_total"], 1)

        # Log structured request
        log_level = logging.ERROR if error else logging.INFO
        logger.log(log_level, f"API Request: {method} {endpoint}", extra={
            "service": self.service_name,
            "operation": "api_request",
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "user_id": user_id,
            "error": error,
        })

    async def record_operation(
        self,
        operation: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record operation metrics.

        Args:
            operation: Operation name
            duration_ms: Operation duration
            success: Whether operation succeeded
            metadata: Additional operation metadata
        """
        # Initialize operation metrics if needed
        if operation not in self.metrics:
            self.metrics[operation] = {
                "count": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_duration_ms": 0,
                "durations": []
            }

        op_metrics = self.metrics[operation]
        op_metrics["count"] += 1

        if success:
            op_metrics["success_count"] += 1
        else:
            op_metrics["error_count"] += 1

        if duration_ms is not None:
            op_metrics["durations"].append(duration_ms)
            # Keep only last 100 durations
            if len(op_metrics["durations"]) > 100:
                op_metrics["durations"] = op_metrics["durations"][-100:]
            op_metrics["avg_duration_ms"] = sum(op_metrics["durations"]) / len(op_metrics["durations"])

        # Log operation
        logger.info(f"Operation: {operation}", extra={
            "service": self.service_name,
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata or {},
        })

    async def update_health_check(self, component: str, status: str, details: Optional[Dict[str, Any]] = None):
        """
        Update health check status for a component.

        Args:
            component: Component name (e.g., "redis", "database")
            status: Health status ("healthy", "unhealthy", "degraded")
            details: Additional health details
        """
        self.health_checks[component] = {
            "status": status,
            "timestamp": time.time(),
            "details": details or {}
        }

        logger.info(f"Health check: {component} = {status}", extra={
            "service": self.service_name,
            "operation": "health_check",
            "component": component,
            "status": status,
            "details": details or {},
        })

    async def collect_system_metrics(self):
        """Collect system resource metrics."""
        try:
            import psutil

            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics["memory_usage_mb"] = memory.used / 1024 / 1024
            self.metrics["memory_percent"] = memory.percent

            # CPU usage
            self.metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=1)

            # Uptime
            self.metrics["uptime_seconds"] = time.time() - self.start_time

        except ImportError:
            # psutil not available
            pass

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        await self.collect_system_metrics()

        # Determine overall health
        unhealthy_components = [
            comp for comp, status in self.health_checks.items()
            if status["status"] != "healthy"
        ]

        overall_status = "healthy"
        if unhealthy_components:
            overall_status = "degraded" if len(unhealthy_components) < len(self.health_checks) else "unhealthy"

        return {
            "service": self.service_name,
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": self.metrics["uptime_seconds"],
            "components": self.health_checks,
            "system": {
                "memory_usage_mb": round(self.metrics.get("memory_usage_mb", 0), 1),
                "cpu_usage_percent": round(self.metrics.get("cpu_usage_percent", 0), 1),
            }
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics."""
        await self.collect_system_metrics()

        # Calculate percentiles
        response_times = self.metrics.get("response_times", [])
        if response_times:
            response_times.sort()
            p50 = response_times[len(response_times) // 2]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0

        return {
            "service": self.service_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": self.metrics["uptime_seconds"],
            "requests": {
                "total": self.metrics["requests_total"],
                "success": self.metrics["requests_success"],
                "error": self.metrics["requests_error"],
                "success_rate": round(self.metrics["requests_success"] / max(self.metrics["requests_total"], 1), 3),
                "error_rate": round(self.metrics["error_rate"], 3),
            },
            "performance": {
                "response_time_avg_ms": round(self.metrics["response_time_avg"], 1),
                "response_time_p50_ms": round(p50, 1),
                "response_time_p95_ms": round(p95, 1),
                "response_time_p99_ms": round(p99, 1),
            },
            "system": {
                "memory_usage_mb": round(self.metrics.get("memory_usage_mb", 0), 1),
                "cpu_usage_percent": round(self.metrics.get("cpu_usage_percent", 0), 1),
            },
            "operations": {
                op: {
                    "count": data["count"],
                    "success_rate": round(data["success_count"] / max(data["count"], 1), 3),
                    "avg_duration_ms": round(data.get("avg_duration_ms", 0), 1)
                }
                for op, data in self.metrics.items()
                if isinstance(data, dict) and "count" in data
            }
        }

    async def save_metrics_to_redis(self):
        """Save metrics to Redis for persistence."""
        if not self.redis_pool:
            return

        try:
            metrics_key = f"metrics:{self.service_name}"
            health_key = f"health:{self.service_name}"

            async with self.redis_pool.get_client() as client:
                # Save metrics with 5-minute TTL
                await client.setex(metrics_key, 300, json.dumps(await self.get_metrics()))

                # Save health with 1-minute TTL
                await client.setex(health_key, 60, json.dumps(await self.get_health_status()))

        except Exception as e:
            logger.error(f"Failed to save metrics to Redis: {e}")


# Global monitoring instance
_monitoring: Optional[MonitoringSystem] = None

async def get_monitoring(service_name: str = "unknown") -> MonitoringSystem:
    """Get global monitoring instance."""
    global _monitoring
    if _monitoring is None:
        _monitoring = MonitoringSystem()
        await _monitoring.initialize(service_name)
    return _monitoring

async def monitor_request(method: str, endpoint: str, status_code: int, response_time_ms: float, **kwargs):
    """Convenience function for request monitoring."""
    monitoring = await get_monitoring()
    await monitoring.record_request(method, endpoint, status_code, response_time_ms, **kwargs)

async def monitor_operation(operation: str, **kwargs):
    """Convenience function for operation monitoring."""
    monitoring = await get_monitoring()
    await monitoring.record_operation(operation, **kwargs)

async def health_check():
    """Convenience function for health status."""
    monitoring = await get_monitoring()
    return await monitoring.get_health_status()

async def service_metrics():
    """Convenience function for service metrics."""
    monitoring = await get_monitoring()
    return await monitoring.get_metrics()


# FastAPI middleware for automatic request monitoring
class MonitoringMiddleware:
    """FastAPI middleware for automatic request monitoring."""

    def __init__(self, app, service_name: str = "unknown"):
        self.app = app
        self.service_name = service_name
        self.monitoring = None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Initialize monitoring if needed
        if not self.monitoring:
            self.monitoring = await get_monitoring(self.service_name)

        # Monitor request
        start_time = time.time()

        # Create response wrapper to capture status code
        response_started = False
        status_code = 500

        async def send_wrapper(message):
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            if response_started:
                response_time = (time.time() - start_time) * 1000
                method = scope["method"]
                path = scope["path"]

                await self.monitoring.record_request(
                    method=method,
                    endpoint=path,
                    status_code=status_code,
                    response_time_ms=response_time
                )
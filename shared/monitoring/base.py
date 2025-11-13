"""
Unified Monitoring Base for Dopemux Services

Provides consistent, multi-workspace aware monitoring across all services.
Integrates with Prometheus for metrics collection and visualization.

Features:
- Multi-workspace support (workspace_id labels)
- Multi-instance support (instance_id labels)
- Consistent metric naming conventions
- Automatic service health tracking
- FastAPI/Starlette middleware integration
- Low overhead (< 100ms)

Usage:
    from shared.monitoring import DopemuxMonitoring
    from prometheus_client import make_asgi_app
    
    monitoring = DopemuxMonitoring(
        service_name="adhd-engine",
        workspace_id=os.getenv("WORKSPACE_ID"),
        instance_id=os.getenv("INSTANCE_ID")
    )
    
    # Mount metrics endpoint
    app.mount("/metrics", make_asgi_app(registry=monitoring.registry))
    
    # Track requests
    monitoring.record_request(
        endpoint="/api/endpoint",
        method="GET",
        status=200,
        duration=0.123
    )
"""

import os
import time
from typing import Optional, Dict, Any
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    CollectorRegistry, generate_latest
)


class DopemuxMonitoring:
    """
    Unified monitoring for Dopemux services.
    
    Implements label-based multi-tenancy following Prometheus best practices.
    All metrics include workspace_id and instance_id for filtering and aggregation.
    """
    
    def __init__(
        self,
        service_name: str,
        workspace_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        registry: Optional[CollectorRegistry] = None,
        version: Optional[str] = None
    ):
        """
        Initialize monitoring for a service.
        
        Args:
            service_name: Name of the service (e.g., "adhd-engine", "conport")
            workspace_id: Workspace identifier (from env or explicit)
            instance_id: Instance identifier (from env or explicit)
            registry: Optional Prometheus registry (creates new if None)
            version: Service version (from env if None)
        """
        self.service_name = service_name
        self.workspace_id = workspace_id or os.getenv("WORKSPACE_ID", "default")
        self.instance_id = instance_id or os.getenv("INSTANCE_ID", "0")
        self.version = version or os.getenv("SERVICE_VERSION", "unknown")
        
        # Create or use provided registry
        self.registry = registry if registry is not None else CollectorRegistry()
        
        # Core labels applied to ALL metrics
        self.core_labels = {
            "service": self.service_name,
            "workspace_id": self.workspace_id,
            "instance_id": self.instance_id
        }
        
        # Label keys for metric definitions
        self.label_keys = list(self.core_labels.keys())
        
        # Initialize all metrics
        self._init_common_metrics()
        
        # Track initialization time
        self.start_time = time.time()
    
    def _init_common_metrics(self):
        """Initialize metrics common to all services."""
        
        # Service metadata
        self.info = Info(
            'dopemux_service',
            'Service metadata and labels',
            registry=self.registry
        )
        self.info.info({
            **self.core_labels,
            'version': self.version
        })
        
        # === Request Metrics ===
        
        self.requests_total = Counter(
            'dopemux_requests_total',
            'Total requests processed by the service',
            ['endpoint', 'method', 'status'] + self.label_keys,
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'dopemux_request_duration_seconds',
            'Request processing time in seconds',
            ['endpoint', 'method'] + self.label_keys,
            # Buckets optimized for typical API response times
            buckets=[.001, .005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0],
            registry=self.registry
        )
        
        self.requests_in_progress = Gauge(
            'dopemux_requests_in_progress',
            'Number of requests currently being processed',
            self.label_keys,
            registry=self.registry
        )
        
        # === Health Metrics ===
        
        self.health_status = Gauge(
            'dopemux_health_status',
            'Service health status (1=healthy, 0=unhealthy)',
            self.label_keys,
            registry=self.registry
        )
        
        # Set initial health to healthy
        self.health_status.labels(**self.core_labels).set(1)
        
        self.uptime_seconds = Gauge(
            'dopemux_uptime_seconds',
            'Service uptime in seconds',
            self.label_keys,
            registry=self.registry
        )
        
        # === Error Metrics ===
        
        self.errors_total = Counter(
            'dopemux_errors_total',
            'Total errors encountered by the service',
            ['error_type', 'endpoint'] + self.label_keys,
            registry=self.registry
        )
        
        # === Resource Metrics ===
        
        self.active_connections = Gauge(
            'dopemux_active_connections',
            'Number of active connections/sessions',
            self.label_keys,
            registry=self.registry
        )
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        duration: float
    ):
        """
        Record request metrics with automatic labeling.
        
        Args:
            endpoint: API endpoint path (e.g., "/api/v1/energy-level")
            method: HTTP method (e.g., "GET", "POST")
            status: HTTP status code (e.g., 200, 404, 500)
            duration: Request duration in seconds
        
        Example:
            start = time.time()
            # ... process request
            monitoring.record_request(
                endpoint="/api/v1/energy-level",
                method="GET",
                status=200,
                duration=time.time() - start
            )
        """
        # Increment request counter
        self.requests_total.labels(
            endpoint=endpoint,
            method=method,
            status=str(status),
            **self.core_labels
        ).inc()
        
        # Record duration
        self.request_duration.labels(
            endpoint=endpoint,
            method=method,
            **self.core_labels
        ).observe(duration)
    
    def record_error(
        self,
        error_type: str,
        endpoint: Optional[str] = None
    ):
        """
        Record an error occurrence.
        
        Args:
            error_type: Type of error (e.g., "validation_error", "timeout", "database_error")
            endpoint: Optional endpoint where error occurred
        
        Example:
            try:
                result = process()
            except ValueError as e:
                monitoring.record_error("validation_error", "/api/endpoint")
                raise
        """
        self.errors_total.labels(
            error_type=error_type,
            endpoint=endpoint or "unknown",
            **self.core_labels
        ).inc()
    
    def set_health(self, healthy: bool):
        """
        Update service health status.
        
        Args:
            healthy: True if service is healthy, False otherwise
        
        Example:
            # Check dependencies and update health
            db_healthy = await check_database()
            redis_healthy = await check_redis()
            monitoring.set_health(db_healthy and redis_healthy)
        """
        self.health_status.labels(**self.core_labels).set(1 if healthy else 0)
    
    def update_uptime(self):
        """Update uptime metric with current value."""
        uptime = time.time() - self.start_time
        self.uptime_seconds.labels(**self.core_labels).set(uptime)
    
    def set_active_connections(self, count: int):
        """
        Update active connection count.
        
        Args:
            count: Number of active connections
        
        Example:
            monitoring.set_active_connections(len(active_websockets))
        """
        self.active_connections.labels(**self.core_labels).set(count)
    
    def increment_in_progress(self):
        """Increment in-progress request count (use in middleware)."""
        self.requests_in_progress.labels(**self.core_labels).inc()
    
    def decrement_in_progress(self):
        """Decrement in-progress request count (use in middleware)."""
        self.requests_in_progress.labels(**self.core_labels).dec()
    
    def get_metrics(self) -> str:
        """
        Get current metrics in Prometheus text format.
        
        Returns:
            Metrics as string in Prometheus exposition format
        
        Example:
            # For debugging or manual export
            metrics_text = monitoring.get_metrics()
            print(metrics_text)
        """
        return generate_latest(self.registry).decode('utf-8')
    
    def create_middleware(self):
        """
        Create ASGI middleware for automatic request tracking.
        
        Returns:
            Middleware function for FastAPI/Starlette
        
        Usage:
            app = FastAPI()
            app.middleware("http")(monitoring.create_middleware())
        """
        async def monitoring_middleware(request, call_next):
            """Middleware to automatically track all HTTP requests."""
            # Track in-progress requests
            self.increment_in_progress()
            
            # Record start time
            start_time = time.time()
            
            # Get endpoint path
            endpoint = request.url.path
            method = request.method
            
            try:
                # Process request
                response = await call_next(request)
                status = response.status_code
                
                # Record metrics
                duration = time.time() - start_time
                self.record_request(endpoint, method, status, duration)
                
                return response
                
            except Exception as e:
                # Record error
                duration = time.time() - start_time
                self.record_request(endpoint, method, 500, duration)
                self.record_error(type(e).__name__, endpoint)
                raise
                
            finally:
                # Always decrement in-progress
                self.decrement_in_progress()
        
        return monitoring_middleware


# Convenience function for quick setup
def create_monitoring(
    service_name: str,
    **kwargs
) -> DopemuxMonitoring:
    """
    Convenience function to create monitoring instance.
    
    Args:
        service_name: Name of the service
        **kwargs: Additional arguments passed to DopemuxMonitoring
    
    Returns:
        Configured DopemuxMonitoring instance
    
    Example:
        monitoring = create_monitoring("adhd-engine")
    """
    return DopemuxMonitoring(service_name=service_name, **kwargs)

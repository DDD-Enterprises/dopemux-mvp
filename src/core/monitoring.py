"""
Metrics collection for Dopemux operations.

Provides monitoring and metrics collection capabilities for
ADHD optimization and integration tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class MetricRecord:
    """Individual metric record."""

    service: str
    method: str
    status: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and tracks metrics for Dopemux operations."""

    def __init__(self):
        self.records: list[MetricRecord] = []

    def record_api_call(
        self,
        service: str,
        method: str,
        status: str,
        duration: Optional[float] = None,
        **metadata,
    ) -> None:
        """Record an API call metric."""
        record = MetricRecord(
            service=service,
            method=method,
            status=status,
            duration=duration,
            metadata=metadata,
        )
        self.records.append(record)

    def get_metrics(
        self, service: Optional[str] = None, last_n: Optional[int] = None
    ) -> list[MetricRecord]:
        """Get collected metrics with optional filtering."""
        filtered = self.records

        if service:
            filtered = [r for r in filtered if r.service == service]

        if last_n:
            filtered = filtered[-last_n:]

        return filtered

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.records.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of collected metrics."""
        if not self.records:
            return {"total_calls": 0}

        total_calls = len(self.records)
        success_calls = len([r for r in self.records if r.status == "success"])
        error_calls = total_calls - success_calls

        services = {}
        for record in self.records:
            if record.service not in services:
                services[record.service] = {"total": 0, "success": 0, "error": 0}
            services[record.service]["total"] += 1
            if record.status == "success":
                services[record.service]["success"] += 1
            else:
                services[record.service]["error"] += 1

        return {
            "total_calls": total_calls,
            "success_calls": success_calls,
            "error_calls": error_calls,
            "success_rate": success_calls / total_calls if total_calls > 0 else 0,
            "services": services,
        }

    def record_sync_error(self, operation: str, error: str) -> None:
        """Record a sync failure using the standard metric schema."""
        self.record_api_call(
            service="sync",
            method=operation,
            status="error",
            error=error,
        )

    def record_sync_operation(self, result: Any) -> None:
        """Record a sync operation summary."""
        status = "success" if getattr(result, "success", False) else "error"
        self.record_api_call(
            service="sync",
            method="operation",
            status=status,
            duration=getattr(result, "sync_duration", None),
            synced_tasks=getattr(result, "synced_tasks", 0),
            created_tasks=getattr(result, "created_tasks", 0),
            updated_tasks=getattr(result, "updated_tasks", 0),
            conflicts=getattr(result, "conflicts", 0),
        )

    def record_adhd_optimization(
        self,
        optimization_type: str,
        status: str = "success",
        duration: Optional[float] = None,
        **metadata,
    ) -> None:
        """Record an ADHD optimization event."""
        self.record_api_call(
            service="adhd",
            method=optimization_type,
            status=status,
            duration=duration,
            **metadata,
        )

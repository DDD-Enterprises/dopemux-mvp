"""
Metrics collection for Dopemux operations.

Provides monitoring and metrics collection capabilities for
ADHD optimization and integration tracking.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


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

    def record_api_call(self, service: str, method: str, status: str,
                       duration: Optional[float] = None, **metadata) -> None:
        """Record an API call metric."""
        record = MetricRecord(
            service=service,
            method=method,
            status=status,
            duration=duration,
            metadata=metadata
        )
        self.records.append(record)

    def get_metrics(self, service: Optional[str] = None,
                   last_n: Optional[int] = None) -> list[MetricRecord]:
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
        success_calls = len([r for r in self.records if r.status == 'success'])
        error_calls = total_calls - success_calls

        services = {}
        for record in self.records:
            if record.service not in services:
                services[record.service] = {"total": 0, "success": 0, "error": 0}
            services[record.service]["total"] += 1
            if record.status == 'success':
                services[record.service]["success"] += 1
            else:
                services[record.service]["error"] += 1

        return {
            "total_calls": total_calls,
            "success_calls": success_calls,
            "error_calls": error_calls,
            "success_rate": success_calls / total_calls if total_calls > 0 else 0,
            "services": services
        }
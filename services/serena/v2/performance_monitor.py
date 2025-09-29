"""
Serena v2 Performance Monitor

Real-time performance tracking and ADHD-optimized degradation for navigation operations.
Ensures <200ms response targets with intelligent fallbacks and user guidance.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, NamedTuple, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PerformanceLevel(str, Enum):
    """Performance level categories for ADHD users."""
    EXCELLENT = "excellent"    # < 100ms
    GOOD = "good"             # 100-200ms
    ACCEPTABLE = "acceptable"  # 200-500ms
    SLOW = "slow"             # 500-1000ms
    DEGRADED = "degraded"     # > 1000ms


@dataclass
class PerformanceTarget:
    """Performance target configuration."""
    target_ms: float = 200.0
    warning_ms: float = 150.0
    critical_ms: float = 500.0
    failure_ms: float = 1000.0


class OperationMetrics(NamedTuple):
    """Metrics for a single operation."""
    operation: str
    duration_ms: float
    success: bool
    cache_hit: bool
    timestamp: datetime
    context: Dict[str, Any] = {}


@dataclass
class PerformanceAlert:
    """Performance alert for ADHD users."""
    level: str  # "warning", "critical", "degraded"
    message: str
    operation: str
    duration_ms: float
    suggestion: str
    timestamp: datetime
    adhd_guidance: str


class PerformanceMonitor:
    """
    Real-time performance monitoring with ADHD-optimized alerts and degradation.

    Features:
    - Sub-200ms navigation target tracking
    - Intelligent performance degradation
    - ADHD-friendly alert messaging
    - Real-time metrics collection
    - Adaptive caching strategies
    - Context-aware performance tuning
    """

    def __init__(
        self,
        target: PerformanceTarget = None,
        history_size: int = 1000,
        alert_threshold: int = 3  # Alerts after 3 consecutive violations
    ):
        self.target = target or PerformanceTarget()
        self.history_size = history_size
        self.alert_threshold = alert_threshold

        # Metrics storage
        self.operation_history: deque = deque(maxlen=history_size)
        self.recent_violations: defaultdict = defaultdict(int)
        self.performance_stats: Dict[str, Dict] = defaultdict(dict)

        # Real-time tracking
        self.active_operations: Dict[str, float] = {}  # operation_id -> start_time
        self.current_performance_level = PerformanceLevel.EXCELLENT

        # Alert callbacks for UI integration
        self.alert_callbacks: List[Callable] = []
        self.degradation_callbacks: List[Callable] = []

        # ADHD-specific configuration
        self.adhd_optimizations = {
            "gentle_alerts": True,
            "progressive_degradation": True,
            "context_preservation": True,
            "adaptive_caching": True
        }

        # Performance counters
        self.counters = {
            "total_operations": 0,
            "target_violations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "degradation_activations": 0,
            "user_alerts_sent": 0
        }

    # Core Performance Tracking

    def start_operation(self, operation_name: str, context: Dict[str, Any] = None) -> str:
        """Start tracking a navigation operation."""
        operation_id = f"{operation_name}_{time.time()}"
        self.active_operations[operation_id] = time.time()

        logger.debug(f"⏱️ Started tracking: {operation_name}")
        return operation_id

    def end_operation(
        self,
        operation_id: str,
        success: bool = True,
        cache_hit: bool = False,
        context: Dict[str, Any] = None
    ) -> OperationMetrics:
        """End operation tracking and analyze performance."""
        if operation_id not in self.active_operations:
            logger.warning(f"Unknown operation ID: {operation_id}")
            return None

        start_time = self.active_operations.pop(operation_id)
        duration_ms = (time.time() - start_time) * 1000

        # Extract operation name
        operation_name = operation_id.split('_')[0]

        # Create metrics record
        metrics = OperationMetrics(
            operation=operation_name,
            duration_ms=duration_ms,
            success=success,
            cache_hit=cache_hit,
            timestamp=datetime.now(timezone.utc),
            context=context or {}
        )

        # Add to history
        self.operation_history.append(metrics)

        # Update counters
        self.counters["total_operations"] += 1
        if cache_hit:
            self.counters["cache_hits"] += 1
        else:
            self.counters["cache_misses"] += 1

        # Analyze performance
        self._analyze_performance(metrics)

        # Update operation statistics
        self._update_operation_stats(metrics)

        logger.debug(
            f"⏱️ {operation_name} completed: {duration_ms:.1f}ms "
            f"({'HIT' if cache_hit else 'MISS'}) "
            f"({'✅' if success else '❌'})"
        )

        return metrics

    def _analyze_performance(self, metrics: OperationMetrics) -> None:
        """Analyze performance and trigger alerts if needed."""
        duration_ms = metrics.duration_ms
        operation = metrics.operation

        # Check performance targets
        if duration_ms > self.target.failure_ms:
            self._handle_performance_violation(metrics, "critical")
        elif duration_ms > self.target.critical_ms:
            self._handle_performance_violation(metrics, "degraded")
        elif duration_ms > self.target.target_ms:
            self._handle_performance_violation(metrics, "warning")
        else:
            # Reset violation counter for this operation
            self.recent_violations[operation] = 0

    def _handle_performance_violation(self, metrics: OperationMetrics, level: str) -> None:
        """Handle performance target violations with ADHD-friendly responses."""
        operation = metrics.operation
        duration_ms = metrics.duration_ms

        # Track violations
        self.recent_violations[operation] += 1
        self.counters["target_violations"] += 1

        # Generate alert if threshold reached
        if self.recent_violations[operation] >= self.alert_threshold:
            alert = self._create_performance_alert(metrics, level)
            self._send_alert(alert)

            # Reset counter after alerting
            self.recent_violations[operation] = 0

        # Update current performance level
        self._update_performance_level(duration_ms)

        # Trigger degradation if needed
        if level in ["critical", "degraded"]:
            self._trigger_performance_degradation(metrics, level)

    def _create_performance_alert(self, metrics: OperationMetrics, level: str) -> PerformanceAlert:
        """Create ADHD-friendly performance alert."""
        operation = metrics.operation
        duration_ms = metrics.duration_ms

        # Generate appropriate messaging
        if level == "warning":
            message = f"Navigation slower than usual: {operation} took {duration_ms:.0f}ms"
            suggestion = "Consider closing unused files or restarting the workspace"
            adhd_guidance = "💡 This is still usable - no need to stop working"

        elif level == "degraded":
            message = f"Navigation performance degraded: {operation} took {duration_ms:.0f}ms"
            suggestion = "Focus mode activated to improve responsiveness"
            adhd_guidance = "🎯 I've reduced background operations to help you focus"

        else:  # critical
            message = f"Navigation very slow: {operation} took {duration_ms:.0f}ms"
            suggestion = "Consider taking a break or restarting the development environment"
            adhd_guidance = "☕ High cognitive load detected - a short break might help"

        return PerformanceAlert(
            level=level,
            message=message,
            operation=operation,
            duration_ms=duration_ms,
            suggestion=suggestion,
            timestamp=datetime.now(timezone.utc),
            adhd_guidance=adhd_guidance
        )

    def _send_alert(self, alert: PerformanceAlert) -> None:
        """Send alert to registered callbacks."""
        self.counters["user_alerts_sent"] += 1

        for callback in self.alert_callbacks:
            try:
                asyncio.create_task(callback(alert))
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        logger.info(
            f"🚨 Performance Alert [{alert.level}]: {alert.message} - {alert.adhd_guidance}"
        )

    def _update_performance_level(self, duration_ms: float) -> None:
        """Update current performance level based on recent operations."""
        # Determine performance level
        if duration_ms < 100:
            new_level = PerformanceLevel.EXCELLENT
        elif duration_ms < 200:
            new_level = PerformanceLevel.GOOD
        elif duration_ms < 500:
            new_level = PerformanceLevel.ACCEPTABLE
        elif duration_ms < 1000:
            new_level = PerformanceLevel.SLOW
        else:
            new_level = PerformanceLevel.DEGRADED

        # Update if changed
        if new_level != self.current_performance_level:
            old_level = self.current_performance_level
            self.current_performance_level = new_level

            logger.info(f"📊 Performance level: {old_level.value} → {new_level.value}")

    def _trigger_performance_degradation(self, metrics: OperationMetrics, level: str) -> None:
        """Trigger performance degradation strategies."""
        self.counters["degradation_activations"] += 1

        degradation_strategies = {
            "degraded": [
                "Reduce concurrent operations",
                "Increase cache TTL",
                "Limit result sets",
                "Enable focus mode filtering"
            ],
            "critical": [
                "Disable non-essential operations",
                "Force cache-only responses",
                "Minimize UI updates",
                "Suggest user break"
            ]
        }

        strategies = degradation_strategies.get(level, [])

        for callback in self.degradation_callbacks:
            try:
                asyncio.create_task(callback(level, strategies, metrics))
            except Exception as e:
                logger.error(f"Degradation callback failed: {e}")

        logger.warning(f"🔄 Performance degradation activated: {level} - {strategies}")

    def _update_operation_stats(self, metrics: OperationMetrics) -> None:
        """Update rolling statistics for operation types."""
        operation = metrics.operation

        if operation not in self.performance_stats:
            self.performance_stats[operation] = {
                "count": 0,
                "total_duration": 0.0,
                "average_duration": 0.0,
                "success_rate": 0.0,
                "cache_hit_rate": 0.0,
                "target_violations": 0,
                "last_update": datetime.now(timezone.utc)
            }

        stats = self.performance_stats[operation]
        stats["count"] += 1
        stats["total_duration"] += metrics.duration_ms

        # Update rolling averages (simple moving average)
        stats["average_duration"] = stats["total_duration"] / stats["count"]

        # Update rates
        successes = sum(1 for m in self.operation_history if m.operation == operation and m.success)
        cache_hits = sum(1 for m in self.operation_history if m.operation == operation and m.cache_hit)
        total_ops = sum(1 for m in self.operation_history if m.operation == operation)

        if total_ops > 0:
            stats["success_rate"] = successes / total_ops
            stats["cache_hit_rate"] = cache_hits / total_ops

        # Count target violations
        if metrics.duration_ms > self.target.target_ms:
            stats["target_violations"] += 1

        stats["last_update"] = datetime.now(timezone.utc)

    # Performance Analysis and Reporting

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        try:
            # Calculate overall metrics
            recent_operations = list(self.operation_history)[-100:]  # Last 100 operations

            if not recent_operations:
                return {
                    "status": "No operations recorded",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            total_duration = sum(op.duration_ms for op in recent_operations)
            avg_duration = total_duration / len(recent_operations)
            success_rate = sum(1 for op in recent_operations if op.success) / len(recent_operations)
            cache_hit_rate = sum(1 for op in recent_operations if op.cache_hit) / len(recent_operations)

            # Performance level distribution
            level_counts = defaultdict(int)
            for op in recent_operations:
                if op.duration_ms < 100:
                    level_counts["excellent"] += 1
                elif op.duration_ms < 200:
                    level_counts["good"] += 1
                elif op.duration_ms < 500:
                    level_counts["acceptable"] += 1
                else:
                    level_counts["slow"] += 1

            # Target compliance
            target_compliant = sum(1 for op in recent_operations if op.duration_ms <= self.target.target_ms)
            compliance_rate = target_compliant / len(recent_operations)

            return {
                "overview": {
                    "current_performance_level": self.current_performance_level.value,
                    "average_duration_ms": round(avg_duration, 1),
                    "target_compliance_rate": f"{compliance_rate:.1%}",
                    "success_rate": f"{success_rate:.1%}",
                    "cache_hit_rate": f"{cache_hit_rate:.1%}"
                },
                "performance_distribution": {
                    f"{level} (<{threshold}ms)": f"{count} ({count/len(recent_operations):.1%})"
                    for level, count, threshold in [
                        ("excellent", level_counts["excellent"], 100),
                        ("good", level_counts["good"], 200),
                        ("acceptable", level_counts["acceptable"], 500),
                        ("slow", level_counts["slow"], "500+")
                    ]
                },
                "operation_stats": {
                    op: {
                        "average_ms": round(stats["average_duration"], 1),
                        "count": stats["count"],
                        "success_rate": f"{stats['success_rate']:.1%}",
                        "cache_hit_rate": f"{stats['cache_hit_rate']:.1%}",
                        "violations": stats["target_violations"]
                    }
                    for op, stats in self.performance_stats.items()
                },
                "targets": {
                    "target_ms": self.target.target_ms,
                    "warning_ms": self.target.warning_ms,
                    "critical_ms": self.target.critical_ms
                },
                "counters": self.counters,
                "adhd_insights": self._generate_adhd_insights(recent_operations),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}

    def _generate_adhd_insights(self, recent_operations: List[OperationMetrics]) -> List[str]:
        """Generate ADHD-friendly performance insights."""
        insights = []

        if not recent_operations:
            return ["No recent activity to analyze"]

        avg_duration = sum(op.duration_ms for op in recent_operations) / len(recent_operations)

        # Performance insights
        if avg_duration < 100:
            insights.append("🚀 Excellent responsiveness - system is running smoothly")
        elif avg_duration < 200:
            insights.append("✅ Good performance - navigation feels snappy")
        elif avg_duration < 500:
            insights.append("👍 Acceptable performance - may feel slightly slower during complex operations")
        else:
            insights.append("⚠️ Slower performance detected - consider enabling focus mode or taking a break")

        # Cache insights
        cache_hit_rate = sum(1 for op in recent_operations if op.cache_hit) / len(recent_operations)
        if cache_hit_rate > 0.7:
            insights.append(f"💾 Great cache utilization ({cache_hit_rate:.1%}) - repeat navigation is fast")
        elif cache_hit_rate < 0.3:
            insights.append("🔄 Low cache hits - exploring new areas or cache may need warming")

        # Pattern insights
        operation_counts = defaultdict(int)
        for op in recent_operations:
            operation_counts[op.operation] += 1

        most_common = max(operation_counts.items(), key=lambda x: x[1], default=("none", 0))
        if most_common[1] > len(recent_operations) * 0.4:
            insights.append(f"🎯 Primary activity: {most_common[0]} - good focused workflow")

        return insights

    # Configuration and Management

    def add_alert_callback(self, callback: Callable) -> None:
        """Add callback for performance alerts."""
        self.alert_callbacks.append(callback)

    def add_degradation_callback(self, callback: Callable) -> None:
        """Add callback for performance degradation."""
        self.degradation_callbacks.append(callback)

    def adjust_targets(self, new_target: PerformanceTarget) -> None:
        """Adjust performance targets dynamically."""
        old_target = self.target
        self.target = new_target

        logger.info(f"🎯 Performance targets updated: {old_target.target_ms}ms → {new_target.target_ms}ms")

    async def reset_statistics(self) -> None:
        """Reset all performance statistics."""
        self.operation_history.clear()
        self.recent_violations.clear()
        self.performance_stats.clear()
        self.active_operations.clear()
        self.counters = {key: 0 for key in self.counters}

        logger.info("📊 Performance statistics reset")

    # Context Decorators for Easy Integration

    def track_performance(self, operation_name: str):
        """Decorator to automatically track function performance."""
        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                async def async_wrapper(*args, **kwargs):
                    operation_id = self.start_operation(operation_name)
                    try:
                        result = await func(*args, **kwargs)
                        self.end_operation(operation_id, success=True)
                        return result
                    except Exception as e:
                        self.end_operation(operation_id, success=False)
                        raise e
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    operation_id = self.start_operation(operation_name)
                    try:
                        result = func(*args, **kwargs)
                        self.end_operation(operation_id, success=True)
                        return result
                    except Exception as e:
                        self.end_operation(operation_id, success=False)
                        raise e
                return sync_wrapper
        return decorator

    # Health and Monitoring

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for performance monitor."""
        try:
            recent_ops = list(self.operation_history)[-10:]

            if recent_ops:
                avg_recent = sum(op.duration_ms for op in recent_ops) / len(recent_ops)
                health_status = "🚀 Excellent" if avg_recent < 200 else "⚠️ Degraded"
            else:
                health_status = "📊 No Data"

            return {
                "status": health_status,
                "performance_level": self.current_performance_level.value,
                "active_operations": len(self.active_operations),
                "total_operations_tracked": self.counters["total_operations"],
                "target_violations": self.counters["target_violations"],
                "alerts_sent": self.counters["user_alerts_sent"],
                "degradation_activations": self.counters["degradation_activations"],
                "callbacks_registered": {
                    "alert_callbacks": len(self.alert_callbacks),
                    "degradation_callbacks": len(self.degradation_callbacks)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Performance monitor health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}
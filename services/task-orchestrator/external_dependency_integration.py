"""
External Dependency Integration Engine for Task Orchestrator
API/Service Dependency Tracking with ADHD-Optimized Monitoring

Handles third-party system dependencies, API availability monitoring,
and external service coordination with minimal cognitive overhead.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiohttp

logger = logging.getLogger(__name__)


class DependencyType(str, Enum):
    """Types of external dependencies."""
    API_SERVICE = "api_service"           # REST/GraphQL APIs
    DATABASE = "database"                 # External databases
    MICROSERVICE = "microservice"         # Internal microservices
    THIRD_PARTY = "third_party"          # External services (GitHub, etc.)
    INFRASTRUCTURE = "infrastructure"     # Cloud services, CDNs
    INTEGRATION = "integration"           # Webhook/event systems


class DependencyStatus(str, Enum):
    """Status of external dependencies."""
    HEALTHY = "healthy"                   # Fully operational
    DEGRADED = "degraded"                # Partial functionality
    UNSTABLE = "unstable"                # Intermittent issues
    DOWN = "down"                        # Not accessible
    UNKNOWN = "unknown"                  # Status unclear


@dataclass
class ExternalDependency:
    """External dependency definition with monitoring metadata."""
    dependency_id: str
    name: str
    dependency_type: DependencyType
    endpoint_url: str
    health_check_url: Optional[str]
    authentication_required: bool
    timeout_seconds: float
    retry_attempts: int

    # Status tracking
    current_status: DependencyStatus
    last_check: Optional[datetime]
    last_healthy: Optional[datetime]
    downtime_duration: float              # Total minutes down

    # Impact assessment
    critical_for_tasks: List[str]         # Tasks that can't proceed without this
    affects_cognitive_load: bool          # Does failure increase mental overhead?
    adhd_impact_level: float              # 0.0-1.0 impact on ADHD users
    fallback_available: bool              # Is there a workaround?

    # Monitoring configuration
    check_interval: timedelta
    alert_threshold: int                  # Failed checks before alerting
    escalation_timeout: timedelta         # When to escalate to urgent


@dataclass
class DependencyMonitoringResult:
    """Result of dependency monitoring check."""
    dependency_id: str
    check_timestamp: datetime
    status: DependencyStatus
    response_time: Optional[float]        # Response time in seconds
    error_message: Optional[str]
    resolution_suggestions: List[str]
    adhd_friendly_alternatives: List[str]


class ExternalDependencyIntegrationEngine:
    """
    Intelligent external dependency tracking with ADHD considerations.

    Features:
    - Real-time dependency health monitoring
    - ADHD-friendly failure notifications
    - Automatic fallback suggestion generation
    - Cognitive load impact assessment
    - Smart alerting to minimize interruptions
    """

    def __init__(self, conport_client=None, context7_client=None):
        self.conport = conport_client
        self.context7 = context7_client

        # Dependency registry
        self.dependencies: Dict[str, ExternalDependency] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

        # Status tracking
        self.dependency_status: Dict[str, DependencyMonitoringResult] = {}
        self.failure_history: Dict[str, List[DependencyMonitoringResult]] = {}

        # ADHD optimizations
        self.alert_batching_window = timedelta(minutes=15)  # Batch alerts
        self.max_alerts_per_hour = 3                        # Prevent overwhelm
        self.alert_queue: List[Dict] = []
        self.last_alert_batch: Optional[datetime] = None

        # Circuit breaker pattern for failed dependencies
        self.circuit_breakers: Dict[str, Dict] = {}

        # Statistics
        self.monitoring_stats = {
            "dependencies_tracked": 0,
            "health_checks_performed": 0,
            "failures_detected": 0,
            "fallbacks_activated": 0,
            "adhd_optimizations_applied": 0,
            "cognitive_load_reduced": 0
        }

    async def initialize(self) -> None:
        """Initialize the external dependency engine."""
        try:
            await self._load_dependency_registry()
            await self._start_monitoring_loops()
            await self._initialize_circuit_breakers()
            logger.info("External dependency integration engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize dependency engine: {e}")

    async def register_dependency(self, dependency: ExternalDependency) -> bool:
        """Register a new external dependency for monitoring."""
        try:
            self.dependencies[dependency.dependency_id] = dependency

            # Start monitoring for this dependency
            monitor_task = asyncio.create_task(
                self._monitor_dependency(dependency)
            )
            self.monitoring_tasks[dependency.dependency_id] = monitor_task

            # Initialize circuit breaker
            self.circuit_breakers[dependency.dependency_id] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure": None,
                "next_attempt": None
            }

            self.monitoring_stats["dependencies_tracked"] += 1
            logger.info(f"Registered dependency: {dependency.name}")

            return True

        except Exception as e:
            logger.error(f"Failed to register dependency {dependency.name}: {e}")
            return False

    async def check_dependency_health(self, dependency_id: str) -> Optional[DependencyMonitoringResult]:
        """Perform immediate health check on specific dependency."""
        try:
            dependency = self.dependencies.get(dependency_id)
            if not dependency:
                return None

            check_url = dependency.health_check_url or dependency.endpoint_url

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(
                total=dependency.timeout_seconds
            )) as session:
                start_time = datetime.now()

                try:
                    async with session.get(check_url) as response:
                        response_time = (datetime.now() - start_time).total_seconds()

                        if response.status == 200:
                            status = DependencyStatus.HEALTHY
                            error_message = None
                        elif 200 <= response.status < 300:
                            status = DependencyStatus.HEALTHY
                            error_message = None
                        elif response.status >= 500:
                            status = DependencyStatus.DOWN
                            error_message = f"Server error: {response.status}"
                        else:
                            status = DependencyStatus.DEGRADED
                            error_message = f"HTTP {response.status}"

                except asyncio.TimeoutError:
                    status = DependencyStatus.DOWN
                    response_time = dependency.timeout_seconds
                    error_message = "Request timeout"
                except aiohttp.ClientError as e:
                    status = DependencyStatus.DOWN
                    response_time = None
                    error_message = str(e)

            # Generate resolution suggestions
            suggestions = await self._generate_resolution_suggestions(dependency, status, error_message)

            # Generate ADHD-friendly alternatives
            adhd_alternatives = await self._generate_adhd_alternatives(dependency, status)

            result = DependencyMonitoringResult(
                dependency_id=dependency_id,
                check_timestamp=datetime.now(),
                status=status,
                response_time=response_time,
                error_message=error_message,
                resolution_suggestions=suggestions,
                adhd_friendly_alternatives=adhd_alternatives
            )

            # Update status tracking
            self.dependency_status[dependency_id] = result
            dependency.current_status = status
            dependency.last_check = result.check_timestamp

            if status == DependencyStatus.HEALTHY:
                dependency.last_healthy = result.check_timestamp

            self.monitoring_stats["health_checks_performed"] += 1

            return result

        except Exception as e:
            logger.error(f"Health check failed for {dependency_id}: {e}")
            return None

    async def get_critical_dependencies_status(self) -> Dict[str, Any]:
        """Get status of all critical dependencies affecting current tasks."""
        try:
            critical_deps = []

            for dep_id, dependency in self.dependencies.items():
                if dependency.critical_for_tasks:
                    status_result = self.dependency_status.get(dep_id)

                    critical_deps.append({
                        "dependency_id": dep_id,
                        "name": dependency.name,
                        "type": dependency.dependency_type.value,
                        "status": dependency.current_status.value,
                        "last_check": dependency.last_check.isoformat() if dependency.last_check else None,
                        "critical_tasks": dependency.critical_for_tasks,
                        "adhd_impact": dependency.adhd_impact_level,
                        "fallback_available": dependency.fallback_available,
                        "response_time": status_result.response_time if status_result else None
                    })

            return {
                "critical_dependencies": critical_deps,
                "overall_health": self._calculate_overall_health(),
                "monitoring_stats": self.monitoring_stats,
                "next_batch_alert": self.last_alert_batch + self.alert_batching_window if self.last_alert_batch else None
            }

        except Exception as e:
            logger.error(f"Failed to get critical dependencies status: {e}")
            return {"error": str(e)}

    async def suggest_dependency_alternatives(self, dependency_id: str) -> List[str]:
        """Suggest alternatives when dependency fails."""
        try:
            dependency = self.dependencies.get(dependency_id)
            if not dependency:
                return []

            alternatives = []

            # Generate type-specific alternatives
            if dependency.dependency_type == DependencyType.API_SERVICE:
                alternatives.extend([
                    "Switch to cached/offline mode if available",
                    "Use mock data for development continuation",
                    "Implement graceful degradation",
                    "Consider alternative API providers"
                ])

            elif dependency.dependency_type == DependencyType.DATABASE:
                alternatives.extend([
                    "Use local SQLite fallback",
                    "Enable read-only mode",
                    "Use cached query results",
                    "Switch to backup database instance"
                ])

            elif dependency.dependency_type == DependencyType.MICROSERVICE:
                alternatives.extend([
                    "Route through service mesh fallback",
                    "Use circuit breaker pattern",
                    "Enable local service mode",
                    "Defer non-critical operations"
                ])

            # Add ADHD-specific alternatives
            if dependency.affects_cognitive_load:
                alternatives.extend([
                    "Create visual status dashboard for dependency tracking",
                    "Set up gentle notifications instead of alerts",
                    "Prepare context preservation for when service returns"
                ])

            return alternatives

        except Exception as e:
            logger.error(f"Failed to suggest alternatives for {dependency_id}: {e}")
            return []

    # Private implementation methods

    async def _load_dependency_registry(self) -> None:
        """Load dependency definitions from configuration."""
        # Load common dependencies for dopemux-mvp
        common_deps = [
            ExternalDependency(
                dependency_id="leantime_api",
                name="LeanTime API",
                dependency_type=DependencyType.API_SERVICE,
                endpoint_url="http://localhost:8080",
                health_check_url="http://localhost:8080/api/projects",
                authentication_required=True,
                timeout_seconds=10.0,
                retry_attempts=3,
                current_status=DependencyStatus.UNKNOWN,
                last_check=None,
                last_healthy=None,
                downtime_duration=0.0,
                critical_for_tasks=["pm_sync", "task_status_updates"],
                affects_cognitive_load=True,
                adhd_impact_level=0.8,
                fallback_available=False,
                check_interval=timedelta(minutes=5),
                alert_threshold=3,
                escalation_timeout=timedelta(minutes=30)
            ),
            ExternalDependency(
                dependency_id="redis_cache",
                name="Redis Cache",
                dependency_type=DependencyType.DATABASE,
                endpoint_url="redis://localhost:6379",
                health_check_url=None,
                authentication_required=False,
                timeout_seconds=5.0,
                retry_attempts=2,
                current_status=DependencyStatus.UNKNOWN,
                last_check=None,
                last_healthy=None,
                downtime_duration=0.0,
                critical_for_tasks=["session_management", "cache_operations"],
                affects_cognitive_load=False,
                adhd_impact_level=0.3,
                fallback_available=True,
                check_interval=timedelta(minutes=2),
                alert_threshold=2,
                escalation_timeout=timedelta(minutes=10)
            )
        ]

        for dep in common_deps:
            await self.register_dependency(dep)

    async def _start_monitoring_loops(self) -> None:
        """Start background monitoring for all dependencies."""
        # Start alert batching loop
        asyncio.create_task(self._alert_batching_loop())

    async def _initialize_circuit_breakers(self) -> None:
        """Initialize circuit breakers for all dependencies."""
        for dep_id in self.dependencies:
            self.circuit_breakers[dep_id] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure": None,
                "next_attempt": None
            }

    async def _monitor_dependency(self, dependency: ExternalDependency) -> None:
        """Continuous monitoring loop for a specific dependency."""
        while True:
            try:
                result = await self.check_dependency_health(dependency.dependency_id)

                if result and result.status != DependencyStatus.HEALTHY:
                    await self._handle_dependency_failure(dependency, result)

                await asyncio.sleep(dependency.check_interval.total_seconds())

            except Exception as e:
                logger.error(f"Monitoring error for {dependency.name}: {e}")
                await asyncio.sleep(60)  # Back off on errors

    async def _handle_dependency_failure(
        self, dependency: ExternalDependency, result: DependencyMonitoringResult
    ) -> None:
        """Handle dependency failure with ADHD considerations."""

        # Update circuit breaker
        circuit = self.circuit_breakers[dependency.dependency_id]
        circuit["failure_count"] += 1
        circuit["last_failure"] = datetime.now()

        # Check if we should open circuit breaker
        if circuit["failure_count"] >= dependency.alert_threshold:
            circuit["state"] = "open"
            circuit["next_attempt"] = datetime.now() + dependency.escalation_timeout

        # Queue alert with ADHD considerations
        alert = {
            "dependency_id": dependency.dependency_id,
            "name": dependency.name,
            "status": result.status.value,
            "error": result.error_message,
            "critical_tasks": dependency.critical_for_tasks,
            "adhd_impact": dependency.adhd_impact_level,
            "alternatives": result.adhd_friendly_alternatives,
            "timestamp": datetime.now(),
            "urgency": "high" if dependency.adhd_impact_level > 0.7 else "medium"
        }

        self.alert_queue.append(alert)
        self.monitoring_stats["failures_detected"] += 1

    async def _generate_resolution_suggestions(
        self, dependency: ExternalDependency, status: DependencyStatus, error: Optional[str]
    ) -> List[str]:
        """Generate resolution suggestions based on failure type."""
        suggestions = []

        if status == DependencyStatus.DOWN:
            suggestions.extend([
                f"Verify {dependency.name} service is running",
                "Check network connectivity",
                "Verify authentication credentials",
                "Review service logs for errors"
            ])

        elif status == DependencyStatus.DEGRADED:
            suggestions.extend([
                f"Monitor {dependency.name} performance",
                "Consider reducing request frequency",
                "Enable graceful degradation mode",
                "Prepare fallback mechanisms"
            ])

        return suggestions

    async def _generate_adhd_alternatives(
        self, dependency: ExternalDependency, status: DependencyStatus
    ) -> List[str]:
        """Generate ADHD-friendly alternatives during failures."""
        alternatives = []

        if dependency.affects_cognitive_load:
            alternatives.extend([
                "Switch to offline/local development mode",
                "Use visual status indicators instead of constant checking",
                "Set up batch notification when service recovers",
                "Create distraction-free workaround workflow"
            ])

        if dependency.adhd_impact_level > 0.6:
            alternatives.extend([
                "Pause dependent tasks to avoid frustration",
                "Focus on independent tasks during outage",
                "Use this time for planning/documentation",
                "Take a break if this was your primary focus"
            ])

        return alternatives

    def _calculate_overall_health(self) -> Dict[str, Any]:
        """Calculate overall dependency health metrics."""
        if not self.dependencies:
            return {"health_score": 1.0, "status": "no_dependencies"}

        healthy_count = sum(1 for dep in self.dependencies.values()
                          if dep.current_status == DependencyStatus.HEALTHY)
        total_count = len(self.dependencies)

        health_score = healthy_count / total_count

        if health_score >= 0.9:
            overall_status = "excellent"
        elif health_score >= 0.7:
            overall_status = "good"
        elif health_score >= 0.5:
            overall_status = "degraded"
        else:
            overall_status = "poor"

        return {
            "health_score": health_score,
            "overall_status": overall_status,
            "healthy_dependencies": healthy_count,
            "total_dependencies": total_count,
            "critical_failures": len([dep for dep in self.dependencies.values()
                                    if dep.current_status == DependencyStatus.DOWN
                                    and dep.critical_for_tasks])
        }

    async def _alert_batching_loop(self) -> None:
        """Batch alerts to reduce ADHD cognitive interruption."""
        while True:
            try:
                if self.alert_queue and (
                    not self.last_alert_batch or
                    datetime.now() - self.last_alert_batch >= self.alert_batching_window
                ):
                    await self._send_batched_alerts()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Alert batching loop error: {e}")
                await asyncio.sleep(300)  # Back off on errors

    async def _send_batched_alerts(self) -> None:
        """Send batched alerts in ADHD-friendly format."""
        if not self.alert_queue:
            return

        # Group alerts by urgency
        urgent_alerts = [a for a in self.alert_queue if a["urgency"] == "high"]
        normal_alerts = [a for a in self.alert_queue if a["urgency"] != "high"]

        # Send urgent alerts immediately
        if urgent_alerts:
            await self._send_urgent_dependency_alerts(urgent_alerts)

        # Batch normal alerts
        if normal_alerts:
            await self._send_normal_dependency_alerts(normal_alerts)

        # Clear queue and update timestamp
        self.alert_queue.clear()
        self.last_alert_batch = datetime.now()

    async def _send_urgent_dependency_alerts(self, alerts: List[Dict]) -> None:
        """Send urgent dependency alerts."""
        for alert in alerts:
            logger.warning(f"🚨 URGENT: {alert['name']} is {alert['status']}")

            if alert.get("alternatives"):
                logger.info(f"💡 ADHD Alternatives: {', '.join(alert['alternatives'][:2])}")

    async def _send_normal_dependency_alerts(self, alerts: List[Dict]) -> None:
        """Send batched normal dependency alerts."""
        if len(alerts) == 1:
            alert = alerts[0]
            logger.info(f"⚠️ Dependency Update: {alert['name']} is {alert['status']}")
        else:
            logger.info(f"⚠️ Dependency Status: {len(alerts)} services need attention")
            for alert in alerts:
                logger.info(f"  • {alert['name']}: {alert['status']}")

        self.monitoring_stats["adhd_optimizations_applied"] += 1
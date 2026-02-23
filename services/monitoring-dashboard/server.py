#!/usr/bin/env python3
"""
Unified Monitoring Dashboard for Dopemux 30+ Services

Aggregates health metrics from all services with ADHD-optimized progressive disclosure.
Provides real-time visibility into system health with gentle, non-overwhelming notifications.

Architecture:
- FastAPI service (Port 8098)
- Collects health from ADHD Engine (8095), ConPort (5455), MCP servers, Task Orchestrator
- ConPort integration for historical trends and decision logging
- Progressive disclosure: overview → details → deep diagnostics
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

async def _run_subprocess_async(cmd: List[str], timeout: float = 10) -> subprocess.CompletedProcess:
    """
    Run a subprocess asynchronously and return a CompletedProcess-like object.

    Prevents blocking the event loop during external command execution.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=proc.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else ""
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
            # Create a CompletedProcess for timeout
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr="Subprocess timed out"
            )
    except Exception as e:
        logger.error(f"Error running async subprocess {cmd}: {e}")
        # Return a failed process instead of crashing
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="",
            stderr=str(e)
        )

# Import the global error handling framework
from ..error_handling import (
    GlobalErrorHandler,
    with_error_handling,
    create_dopemux_error,
    ErrorType,
    ErrorSeverity,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState
)

# Add src to path for dopemux imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ADHD-optimized health levels
class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

# Service health model
class ServiceHealth(BaseModel):
    name: str
    status: HealthLevel
    message: str
    last_check: datetime
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    adhd_optimized: bool = False  # Whether service supports ADHD metrics

# Dashboard response model
class DashboardResponse(BaseModel):
    overall_health: HealthLevel
    total_services: int
    healthy_services: int
    warning_services: int
    critical_services: int
    last_update: datetime
    services: List[ServiceHealth]
    summary: Dict[str, Any]

@dataclass
class RecoveryAction:
    """Automated recovery action with outcome."""
    service_id: str
    action_type: str  # 'restart_container', 'clear_cache', 'reset_connections'
    timestamp: datetime
    reason: str
    success: Optional[bool] = None
    details: Optional[Dict[str, Any]] = None


class RecoveryManager:
    """
    Automated recovery system for self-healing service operations.

    Handles common failure scenarios with minimal human intervention.
    """

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.recovery_strategies = {
            "container_down": self._recover_container_down,
            "circuit_breaker_open": self._recover_circuit_breaker,
            "connection_refused": self._recover_connection_refused,
            "timeout": self._recover_timeout,
            "high_memory": self._recover_high_memory
        }

        # Recovery limits to prevent runaway operations
        self.max_recovery_attempts = 3
        self.recovery_cooldown_minutes = 5
        self.attempts_history = {}  # service_id -> list of recent attempts

    async def attempt_recovery(self, service_id: str, failure_type: str, service_config: Dict[str, Any]) -> Optional[RecoveryAction]:
        """
        Attempt automated recovery for a failed service.

        Returns RecoveryAction if recovery was attempted, None if no recovery available.
        """
        if not self.dashboard.recovery_enabled:
            return None

        # Check recovery attempt limits
        if not self._can_attempt_recovery(service_id):
            logger.warning(f"Recovery rate limited for {service_id}")
            return None

        # Find appropriate recovery strategy
        strategy = self.recovery_strategies.get(failure_type)
        if not strategy:
            logger.debug(f"No recovery strategy for failure type: {failure_type}")
            return None

        # Attempt recovery
        recovery_action = RecoveryAction(
            service_id=service_id,
            action_type=strategy.__name__.replace('_recover_', ''),
            timestamp=datetime.now(timezone.utc),
            reason=f"Automatic recovery for {failure_type}",
            success=False
        )

        try:
            success = await strategy(service_id, service_config)
            recovery_action.success = success
            recovery_action.details = {"strategy": strategy.__name__}

            if success:
                logger.info(f"✅ Recovery successful for {service_id}: {recovery_action.action_type}")
                recovery_action.details["message"] = "Recovery completed successfully"
            else:
                logger.warning(f"❌ Recovery failed for {service_id}: {recovery_action.action_type}")
                recovery_action.details["message"] = "Recovery attempt failed"

        except Exception as e:
            logger.error(f"Recovery error for {service_id}: {e}")
            recovery_action.success = False
            recovery_action.details = {"error": str(e), "strategy": strategy.__name__}

        # Record the attempt
        self._record_recovery_attempt(service_id, recovery_action)
        self.dashboard.recovery_history.append(recovery_action)

        return recovery_action

    def _can_attempt_recovery(self, service_id: str) -> bool:
        """Check if recovery can be attempted based on rate limits."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=self.recovery_cooldown_minutes)

        if service_id not in self.attempts_history:
            self.attempts_history[service_id] = []

        # Filter recent attempts
        recent_attempts = [a for a in self.attempts_history[service_id] if a.timestamp > cutoff]

        # Limit to max attempts per cooldown period
        return len(recent_attempts) < self.max_recovery_attempts

    def _record_recovery_attempt(self, service_id: str, action: RecoveryAction):
        """Record recovery attempt for rate limiting."""
        if service_id not in self.attempts_history:
            self.attempts_history[service_id] = []
        self.attempts_history[service_id].append(action)

        # Clean old attempts (keep last 10)
        if len(self.attempts_history[service_id]) > 10:
            self.attempts_history[service_id] = self.attempts_history[service_id][-10:]

    async def _recover_container_down(self, service_id: str, service_config: Dict[str, Any]) -> bool:
        """Attempt to restart a down container."""
        if service_config.get('discovery') != 'docker':
            return False

        try:
            # Use docker-compose to restart the service
            result = await _run_subprocess_async(
                ['docker-compose', '-f', 'docker-compose.staging.yml', 'restart', service_id],
                timeout=30
            )

            if result.returncode == 0:
                # Wait a moment for container to start
                await asyncio.sleep(5)
                return True

            logger.warning(f"Container restart failed: {result.stderr}")
            return False

        except Exception as e:
            logger.error(f"Container restart error: {e}")
            return False

    async def _recover_circuit_breaker(self, service_id: str, service_config: Dict[str, Any]) -> bool:
        """Wait for circuit breaker to recover naturally."""
        # Circuit breakers recover automatically, just wait for half-open state
        await asyncio.sleep(60)  # Wait 1 minute for natural recovery
        return True  # Circuit breaker will handle the rest

    async def _recover_connection_refused(self, service_id: str, service_config: Dict[str, Any]) -> bool:
        """Try container restart for connection issues."""
        return await self._recover_container_down(service_id, service_config)

    async def _recover_timeout(self, service_id: str, service_config: Dict[str, Any]) -> bool:
        """For timeout issues, try clearing any cached connections or restarting."""
        # For now, just attempt container restart
        return await self._recover_container_down(service_id, service_config)

    async def _recover_high_memory(self, service_id: str, service_config: Dict[str, Any]) -> bool:
        """Restart container to clear memory issues."""
        return await self._recover_container_down(service_id, service_config)

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery system statistics."""
        total_attempts = sum(len(attempts) for attempts in self.attempts_history.values())
        successful_attempts = sum(
            len([a for a in attempts if a.success])
            for attempts in self.attempts_history.values()
        )

        return {
            "total_recovery_attempts": total_attempts,
            "successful_recoveries": successful_attempts,
            "success_rate": successful_attempts / max(1, total_attempts),
            "services_with_attempts": len(self.attempts_history),
            "recent_attempts": [
                {
                    "service": action.service_id,
                    "action": action.action_type,
                    "success": action.success,
                    "timestamp": action.timestamp.isoformat()
                }
                for action in list(self.dashboard.recovery_history)[-5:]  # Last 5
            ]
        }


class MonitoringDashboard:
    """
    Unified monitoring dashboard with ADHD-optimized progressive disclosure.
    """

    def __init__(self):
        # Initialize with empty services - will be populated by discover_services()
        self.services = {}
        self.discovery_cache = {}
        self.discovery_cache_ttl = 300  # 5 minutes

        self.session = None
        self.last_update = None
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds cache

        # Initialize circuit breakers for resilience
        self.circuit_breakers = self._init_circuit_breakers()

        # Performance monitoring
        self.performance_history = {}  # service_id -> deque of response times
        self.performance_window_size = 20  # Keep last 20 measurements
        self.performance_thresholds = {
            "slow_response_ms": 1000,  # Flag responses > 1s as slow
            "degradation_threshold": 1.5,  # 50% degradation triggers warning
            "bottleneck_threshold": 2000  # > 2s considered bottleneck
        }

        # Automated recovery system
        self.recovery_manager = RecoveryManager(self)
        self.recovery_enabled = True
        self.recovery_history = deque(maxlen=50)  # Track last 50 recovery actions

        # ADHD-optimized alert system
        self.alert_system = ADHDAlertSystem(self)
        self.alert_history = []
        self.alert_thresholds = {
            "warning_threshold": 2,  # Alert if 2+ services warning
            "critical_threshold": 1,  # Alert if 1+ services critical
            "progressive_urgency": True,  # Enable progressive alerts
            "break_integration": True  # Integrate with ADHD Engine breaks
        }

    def _init_circuit_breakers(self) -> Dict[str, CircuitBreaker]:
        """
        Initialize circuit breakers for each service to prevent cascading failures.

        ADHD-optimized: Different thresholds for different service types.
        """
        circuit_breakers = {}

        for service_id, service_config in self.services.items():
            # Configure circuit breaker based on service type and importance
            service_type = service_config.get("type", "web_api")

            # ADHD-optimized thresholds: more forgiving for less critical services
            if service_type == "mcp_server":
                # MCP servers can fail without breaking core functionality
                config = CircuitBreakerConfig(
                    name=f"{service_id}_circuit",
                    failure_threshold=3,  # Allow 3 failures before opening
                    recovery_timeout=120,  # 2 minutes before trying again
                    success_threshold=2,  # Need 2 successes to close
                    timeout=service_config["timeout"]
                )
            elif service_type == "database_api":
                # Database failures are more critical
                config = CircuitBreakerConfig(
                    name=f"{service_id}_circuit",
                    failure_threshold=2,  # Fail fast for DB issues
                    recovery_timeout=60,  # 1 minute recovery
                    success_threshold=3,  # Need more confirmations for DB
                    timeout=service_config["timeout"]
                )
            else:
                # Default for web APIs and apps
                config = CircuitBreakerConfig(
                    name=f"{service_id}_circuit",
                    failure_threshold=5,  # More forgiving for web services
                    recovery_timeout=90,  # 1.5 minutes recovery
                    success_threshold=2,  # Quick recovery
                    timeout=service_config["timeout"]
                )

            circuit_breakers[service_id] = CircuitBreaker(config)
            logger.info(f"Initialized circuit breaker for {service_id}: {config.failure_threshold} failures, {config.recovery_timeout}s recovery")

        return circuit_breakers

    async def discover_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Auto-discover running services from Docker containers and static config.

        ADHD-optimized: Combines static known services with dynamic discovery
        to ensure comprehensive coverage without overwhelming complexity.
        """
        discovered_services = {}

        # Start with static known services (core Dopemux services)
        static_services = self._get_static_services()
        discovered_services.update(static_services)

        # Auto-discover Docker containers
        try:
            docker_services = await self._discover_docker_services()
            discovered_services.update(docker_services)
            logger.info(f"Auto-discovered {len(docker_services)} Docker services")
        except Exception as e:
            logger.warning(f"Could not auto-discover Docker services: {e}")

        # Log discovery summary
        total_services = len(discovered_services)
        mcp_services = sum(1 for s in discovered_services.values() if s.get('type') == 'mcp_server')
        logger.info(f"Service discovery complete: {total_services} total services ({mcp_services} MCP servers)")

        return discovered_services

    def _get_static_services(self) -> Dict[str, Dict[str, Any]]:
        """Get statically configured core services."""
        return {
            "adhd_engine": {
                "name": "ADHD Engine",
                "type": "web_api",
                "url": "http://localhost:8095/health",
                "timeout": 5.0,
                "adhd_optimized": True,
                "discovery": "static"
            },
            "adhd_dashboard": {
                "name": "ADHD Dashboard",
                "type": "web_api",
                "url": "http://localhost:8097/health",
                "timeout": 5.0,
                "adhd_optimized": True,
                "discovery": "static"
            },
            "conport": {
                "name": "ConPort Knowledge Graph",
                "type": "database_api",
                "url": "http://localhost:5455/health",
                "timeout": 10.0,
                "adhd_optimized": False,
                "fallback_check": "process_check",
                "discovery": "static"
            },
            "task_orchestrator": {
                "name": "Task Orchestrator (Leantime)",
                "type": "web_app",
                "url": "http://localhost:8080/health",
                "timeout": 5.0,
                "adhd_optimized": True,
                "auth_required": True,
                "fallback_check": "docker_check",
                "discovery": "static"
            },
            "monitoring_dashboard": {
                "name": "Monitoring Dashboard",
                "type": "web_api",
                "url": "http://localhost:8098/health",
                "timeout": 3.0,
                "adhd_optimized": True,
                "discovery": "static"
            }
        }

    async def _discover_docker_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover services from running Docker containers.

        Uses docker ps to find containers and infers service types from names/ports.
        """
        discovered = {}

        try:
            # Get running containers in JSON format
            result = await _run_subprocess_async(
                ['docker', 'ps', '--format', 'json'],
                timeout=10
            )

            if result.returncode != 0:
                logger.warning(f"Docker ps failed: {result.stderr}")
                return discovered

            containers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            logger.debug(f"Found {len(containers)} running containers")

            for container in containers:
                service_config = self._analyze_container(container)
                if service_config:
                    service_id = service_config['id']
                    discovered[service_id] = service_config
                    logger.debug(f"Discovered service: {service_id} ({service_config['name']})")

        except Exception as e:
            logger.warning(f"Docker discovery error: {e}")

        return discovered

    def _analyze_container(self, container: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a Docker container and create service configuration if it's a Dopemux service.

        Returns service config dict or None if not a Dopemux service.
        """
        name = container.get('Names', '').strip('/')
        image = container.get('Image', '')
        ports = container.get('Ports', '')

        # Skip non-Dopemux containers
        if not any(keyword in name.lower() for keyword in ['dopemux', 'mcp-', 'staging-', 'adhd', 'conport', 'serena', 'zen', 'dope-context', 'gpt-researcher', 'desktop-commander', 'exa', 'leantime']):
            return None

        # Determine service type and health check config
        service_config = {
            'id': name.replace('staging-', '').replace('mcp-', ''),
            'discovery': 'docker'
        }

        # MCP Servers
        if 'mcp-' in name or 'zen' in name or 'serena' in name or 'dope-context' in name or 'gpt-researcher' in name or 'desktop-commander' in name or 'exa' in name:
            service_config.update({
                'name': self._format_service_name(name),
                'type': 'mcp_server',
                'timeout': 3.0,
                'adhd_optimized': True,
                'fallback_check': 'mcp_ping'
            })

            # Extract health check port from container ports
            health_port = self._extract_health_port(ports, name)
            if health_port:
                service_config['url'] = f"http://localhost:{health_port}/health"

        # Web APIs
        elif 'adhd' in name and 'engine' in name:
            service_config.update({
                'name': 'ADHD Engine (Docker)',
                'type': 'web_api',
                'timeout': 5.0,
                'adhd_optimized': True
            })
            health_port = self._extract_health_port(ports, 'adhd-engine')
            if health_port:
                service_config['url'] = f"http://localhost:{health_port}/health"

        # Database services
        elif 'postgres' in name or 'conport' in name:
            service_config.update({
                'name': 'ConPort PostgreSQL',
                'type': 'database_api',
                'timeout': 10.0,
                'adhd_optimized': False,
                'fallback_check': 'process_check'
            })
            health_port = self._extract_health_port(ports, 'conport')
            if health_port:
                service_config['url'] = f"http://localhost:{health_port}/health"

        # Web applications
        elif 'leantime' in name:
            service_config.update({
                'name': 'Leantime (Docker)',
                'type': 'web_app',
                'timeout': 5.0,
                'adhd_optimized': True,
                'auth_required': True,
                'fallback_check': 'docker_check'
            })
            health_port = self._extract_health_port(ports, 'leantime')
            if health_port:
                service_config['url'] = f"http://localhost:{health_port}/health"

        # Only return if we have a health check URL
        if 'url' in service_config:
            return service_config

        return None

    def _format_service_name(self, container_name: str) -> str:
        """Format container name into human-readable service name."""
        name = container_name.replace('staging-', '').replace('mcp-', '')

        # Special cases
        name_map = {
            'zen': 'Zen MCP Server',
            'serena': 'Serena MCP Server',
            'dope-context': 'Dope-Context MCP Server',
            'gpt-researcher': 'GPT Researcher MCP',
            'desktop-commander': 'Desktop Commander MCP',
            'exa': 'Exa MCP Server'
        }

        return name_map.get(name, f"{name.replace('-', ' ').title()} MCP")

    def _extract_health_port(self, ports_str: str, service_name: str) -> Optional[int]:
        """Extract health check port from Docker ports string."""
        if not ports_str:
            return None

        # Parse port mappings like "0.0.0.0:3012->3001/tcp"
        import re
        port_matches = re.findall(r'0\.0\.0\.0:(\d+)->(\d+)/tcp', ports_str)

        if not port_matches:
            return None

        # For MCP servers, look for specific port patterns
        for external, internal in port_matches:
            external_port = int(external)

            # MCP server port patterns
            if service_name in ['zen', 'mcp-zen'] and internal == '3001':
                return external_port
            elif service_name in ['serena', 'mcp-serena'] and internal == '3006':
                return external_port
            elif service_name in ['dope-context', 'mcp-dope-context'] and internal == '3014':
                return external_port
            elif service_name in ['gpt-researcher', 'mcp-gptr-mcp'] and internal == '3009':
                return external_port
            elif service_name in ['desktop-commander', 'mcp-desktop-commander'] and internal == '3012':
                return external_port
            elif service_name in ['exa', 'mcp-exa'] and internal == '3008':
                return external_port

            # ADHD Engine
            elif 'adhd-engine' in service_name and internal == '8001':
                return external_port

            # ConPort
            elif 'conport' in service_name and internal == '3004':
                return external_port

            # Leantime
            elif 'leantime' in service_name and internal == '80':
                return external_port

        # Return first available port as fallback
        if port_matches:
            return int(port_matches[0][0])

        return None

    async def _attempt_service_recovery(self, service_id: str, health_result: ServiceHealth, service_config: Dict[str, Any]):
        """Attempt automated recovery for a failed service."""
        if not self.recovery_enabled:
            return

        # Determine failure type from health result
        failure_type = self._classify_failure(health_result)

        # Attempt recovery
        recovery_action = await self.recovery_manager.attempt_recovery(service_id, failure_type, service_config)

        if recovery_action:
            logger.info(f"Recovery attempted for {service_id}: {recovery_action.action_type} - {'Success' if recovery_action.success else 'Failed'}")

            # Add recovery information to service details
            if not health_result.details:
                health_result.details = {}
            health_result.details["recovery_attempted"] = True
            health_result.details["recovery_action"] = recovery_action.action_type
            health_result.details["recovery_success"] = recovery_action.success

    def _classify_failure(self, health_result: ServiceHealth) -> str:
        """Classify the type of failure for recovery selection."""
        message = health_result.message.lower()

        if "circuit breaker" in message and "open" in message:
            return "circuit_breaker_open"
        elif "connection refused" in message:
            return "connection_refused"
        elif "timeout" in message or "taking longer" in message:
            return "timeout"
        elif "service down" in message or "not responding" in message:
            return "container_down"
        elif "memory" in message or "resources" in message:
            return "high_memory"
        else:
            return "container_down"  # Default fallback

    async def get_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current service registry with discovery refresh if needed.

        ADHD-optimized: Caches discovery results to avoid overwhelming users
        with constant discovery operations.
        """
        now = datetime.now(timezone.utc)

        # Check if discovery cache is still valid
        if self.discovery_cache and self.discovery_cache.get('timestamp'):
            cache_age = (now - self.discovery_cache['timestamp']).total_seconds()
            if cache_age < self.discovery_cache_ttl:
                return self.discovery_cache['services']

        # Cache expired or missing - refresh discovery
        logger.info("Refreshing service discovery...")
        try:
            discovered_services = await self.discover_services()
            self.discovery_cache = {
                'services': discovered_services,
                'timestamp': now
            }
            self.services = discovered_services

            # Re-initialize circuit breakers for new services
            self.circuit_breakers = self._init_circuit_breakers()

            logger.info(f"Service discovery refreshed: {len(discovered_services)} services")
            return discovered_services

        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            # Return cached services if available, otherwise empty dict
            return self.discovery_cache.get('services', {}) if self.discovery_cache else {}

    async def init_session(self):
        """Initialize aiohttp session for HTTP requests."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def check_service_health(self, service_id: str, service_config: Dict[str, Any]) -> ServiceHealth:
        """
        Check health of a single service with ADHD-optimized error handling and fallback checks.
        """
        name = service_config["name"]
        url = service_config["url"]
        timeout = service_config["timeout"]
        adhd_optimized = service_config["adhd_optimized"]
        service_type = service_config.get("type", "web_api")

        start_time = datetime.now(timezone.utc)

        # Primary health check via HTTP with circuit breaker protection
        primary_result = await self._check_http_health(service_id, service_config, start_time)

        # If primary check failed and fallback is available, try fallback
        if primary_result["status"] in [HealthLevel.CRITICAL, HealthLevel.UNKNOWN]:
            fallback_check = service_config.get("fallback_check")
            if fallback_check:
                logger.debug(f"Primary health check failed for {name}, trying fallback: {fallback_check}")
                fallback_result = await self._check_fallback_health(service_config, start_time)
                if fallback_result["status"] == HealthLevel.HEALTHY:
                    # Fallback succeeded, use that result
                    primary_result = fallback_result
                    primary_result["message"] += " (via fallback check)"

        return ServiceHealth(
            name=name,
            status=primary_result["status"],
            message=primary_result["message"],
            last_check=start_time,
            response_time=primary_result.get("response_time"),
            details=primary_result.get("details", {}),
            adhd_optimized=adhd_optimized
        )

    async def _check_http_health(self, service_id: str, service_config: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Check health via HTTP endpoint with circuit breaker protection."""
        name = service_config["name"]
        url = service_config["url"]
        timeout = service_config["timeout"]
        auth_required = service_config.get("auth_required", False)

        circuit_breaker = self.circuit_breakers.get(service_id)
        if not circuit_breaker:
            # Fallback to direct HTTP call without circuit breaker
            logger.warning(f"No circuit breaker found for {service_id}, using direct HTTP call")
            return await self._check_http_health_direct(service_config, start_time)

        # Check circuit breaker state
        if circuit_breaker.state == CircuitBreakerState.OPEN:
            logger.warning(f"Circuit breaker for {service_id} is OPEN - skipping health check")
            return {
                "status": HealthLevel.CRITICAL,
                "message": f"Service unavailable (circuit breaker open)",
                "response_time": None,
                "details": {
                    "circuit_breaker": "open",
                    "consecutive_failures": circuit_breaker.stats.consecutive_failures,
                    "last_failure": circuit_breaker.stats.last_failure_time.isoformat() if circuit_breaker.stats.last_failure_time else None
                }
            }
        elif circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"Circuit breaker for {service_id} is HALF_OPEN - testing recovery")

        try:
            # Use circuit breaker to protect the HTTP call
            result = await circuit_breaker.call(self._make_http_request, service_config, start_time)

            # Circuit breaker succeeded - return the result
            return result

        except Exception as e:
            # Circuit breaker failed - this will update failure stats automatically
            logger.warning(f"Circuit breaker call failed for {service_id}: {e}")

            # Check if circuit breaker opened due to this failure
            if circuit_breaker.state == CircuitBreakerState.OPEN:
                logger.error(f"Circuit breaker for {service_id} opened after consecutive failures")

            return {
                "status": HealthLevel.CRITICAL,
                "message": f"Service health check failed: {str(e)}",
                "response_time": None,
                "details": {
                    "error": str(e),
                    "circuit_breaker_state": circuit_breaker.state.value,
                    "consecutive_failures": circuit_breaker.stats.consecutive_failures
                }
            }

    async def _make_http_request(self, service_config: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Make the actual HTTP request (called by circuit breaker)."""
        url = service_config["url"]
        timeout = service_config["timeout"]
        auth_required = service_config.get("auth_required", False)

        if not self.session:
            await self.init_session()

        try:
            async with self.session.get(url, timeout=timeout) as response:
                    response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                    if response.status == 200:
                        try:
                            data = await response.json()
                            return {
                                "status": HealthLevel.HEALTHY,
                                "message": data.get("message", "Service is healthy"),
                                "response_time": response_time,
                                "details": data
                            }
                        except Exception:
                            # Non-JSON response but 200 status
                            return {
                                "status": HealthLevel.HEALTHY,
                                "message": "Service responding",
                                "response_time": response_time,
                                "details": {"response": "non-json"}
                            }
                    elif response.status == 302 and auth_required:
                        # Redirect to login is expected for auth-required services
                        return {
                            "status": HealthLevel.HEALTHY,
                            "message": "Service responding (auth required)",
                            "response_time": response_time,
                            "details": {"redirect": "login_required", "status_code": 302}
                        }
                    else:
                        return {
                            "status": HealthLevel.CRITICAL,
                            "message": f"HTTP {response.status}",
                            "response_time": None,
                            "details": {"status_code": response.status}
                        }

        except asyncio.TimeoutError:
            return {
                "status": HealthLevel.WARNING,
                "message": "Timeout - service may be slow",
                "response_time": timeout,
                "details": {"error": "timeout"}
            }

        except aiohttp.ClientConnectorError:
            return {
                "status": HealthLevel.CRITICAL,
                "message": "Connection refused - service down",
                "response_time": None,
                "details": {"error": "connection_refused"}
            }

        except Exception as e:
            return {
                "status": HealthLevel.WARNING,
                "message": f"Check failed: {str(e)[:50]}",
                "response_time": None,
                "details": {"error": str(e)}
            }

    async def _check_http_health_direct(self, service_config: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Direct HTTP health check without circuit breaker protection (fallback method)."""
        url = service_config["url"]
        timeout = service_config["timeout"]
        auth_required = service_config.get("auth_required", False)

        try:
            if not self.session:
                await self.init_session()

            async with self.session.get(url, timeout=timeout) as response:
                response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                if response.status == 200:
                    try:
                        data = await response.json()
                        return {
                            "status": HealthLevel.HEALTHY,
                            "message": data.get("message", "Service is healthy"),
                            "response_time": response_time,
                            "details": data
                        }
                    except:
                        # Non-JSON response but 200 status
                        return {
                            "status": HealthLevel.HEALTHY,
                            "message": "Service responding",
                            "response_time": response_time,
                            "details": {"response": "non-json"}
                        }
                elif response.status == 302 and auth_required:
                    # Redirect to login is expected for auth-required services
                    return {
                        "status": HealthLevel.HEALTHY,
                        "message": "Service responding (auth required)",
                        "response_time": response_time,
                        "details": {"redirect": "login_required", "status_code": 302}
                    }
                else:
                    return {
                        "status": HealthLevel.CRITICAL,
                        "message": f"HTTP {response.status}",
                        "response_time": None,
                        "details": {"status_code": response.status}
                    }

        except asyncio.TimeoutError:
            return {
                "status": HealthLevel.WARNING,
                "message": "Timeout - service may be slow",
                "response_time": timeout,
                "details": {"error": "timeout"}
            }

        except aiohttp.ClientConnectorError:
            return {
                "status": HealthLevel.CRITICAL,
                "message": "Connection refused - service down",
                "response_time": None,
                "details": {"error": "connection_refused"}
            }

        except Exception as e:
            return {
                "status": HealthLevel.WARNING,
                "message": f"Check failed: {str(e)[:50]}",
                "response_time": None,
                "details": {"error": str(e)}
            }

    async def _check_fallback_health(self, service_config: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Check health using fallback methods when HTTP fails."""
        fallback_check = service_config.get("fallback_check")
        name = service_config["name"]

        if fallback_check == "process_check":
            # Check if PostgreSQL process is running (for ConPort)
            try:
                result = await _run_subprocess_async(
                    ["pg_isready", "-h", "localhost", "-p", "5432"],
                    timeout=5
                )
                if result.returncode == 0:
                    return {
                        "status": HealthLevel.HEALTHY,
                        "message": "PostgreSQL database responding",
                        "response_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
                        "details": {"check_type": "pg_isready"}
                    }
                else:
                    return {
                        "status": HealthLevel.CRITICAL,
                        "message": "PostgreSQL database not responding",
                        "response_time": None,
                        "details": {"check_type": "pg_isready", "error": result.stderr}
                    }
            except Exception as e:
                return {
                    "status": HealthLevel.WARNING,
                    "message": f"Process check failed: {str(e)[:30]}",
                    "response_time": None,
                    "details": {"check_type": "process_check", "error": str(e)}
                }

        elif fallback_check == "docker_check":
            # Check if Docker container is running (for Leantime)
            try:
                result = await _run_subprocess_async(
                    ["docker", "ps", "--filter", "name=leantime", "--format", "{{.Status}}"],
                    timeout=5
                )
                if result.returncode == 0 and "Up" in result.stdout:
                    return {
                        "status": HealthLevel.HEALTHY,
                        "message": "Docker container running",
                        "response_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
                        "details": {"check_type": "docker_ps", "container": "leantime"}
                    }
                else:
                    return {
                        "status": HealthLevel.CRITICAL,
                        "message": "Docker container not running",
                        "response_time": None,
                        "details": {"check_type": "docker_ps", "output": result.stdout.strip()}
                    }
            except Exception as e:
                return {
                    "status": HealthLevel.WARNING,
                    "message": f"Docker check failed: {str(e)[:30]}",
                    "response_time": None,
                    "details": {"check_type": "docker_check", "error": str(e)}
                }

        elif fallback_check == "mcp_ping":
            # Basic MCP connectivity check (simplified)
            try:
                # Try to connect to MCP server port
                import socket
                url_parts = service_config["url"].replace("http://", "").split(":")
                host = url_parts[0]
                port = int(url_parts[1].split("/")[0]) if "/" in url_parts[1] else int(url_parts[1])

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    return {
                        "status": HealthLevel.HEALTHY,
                        "message": "MCP server port responding",
                        "response_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
                        "details": {"check_type": "socket_connect", "port": port}
                    }
                else:
                    return {
                        "status": HealthLevel.CRITICAL,
                        "message": "MCP server port not responding",
                        "response_time": None,
                        "details": {"check_type": "socket_connect", "port": port, "error": "connection_failed"}
                    }
            except Exception as e:
                return {
                    "status": HealthLevel.WARNING,
                    "message": f"MCP ping failed: {str(e)[:30]}",
                    "response_time": None,
                    "details": {"check_type": "mcp_ping", "error": str(e)}
                }

        # No fallback available or fallback failed
        return {
            "status": HealthLevel.UNKNOWN,
            "message": "No health check available",
            "response_time": None,
            "details": {"check_type": "none"}
        }

    def _track_performance(self, service_id: str, response_time: float):
        """Track performance metrics for the service."""
        if service_id not in self.performance_history:
            self.performance_history[service_id] = deque(maxlen=self.performance_window_size)

        self.performance_history[service_id].append(response_time)

        # Log if this is a slow response
        if response_time > self.performance_thresholds["slow_response_ms"] / 1000:
            logger.warning(f"Slow response from {service_id}: {response_time:.2f}s")

    def _analyze_performance_trends(self, service_id: str) -> Dict[str, Any]:
        """Analyze performance trends and detect bottlenecks."""
        if service_id not in self.performance_history or len(self.performance_history[service_id]) < 5:
            return {
                "status": "insufficient_data",
                "message": "Need more response times for trend analysis",
                "bottleneck": False,
                "degradation": False,
                "recommendation": None
            }

        times = list(self.performance_history[service_id])
        avg_response = sum(times) / len(times)
        min_response = min(times)
        max_response = max(times)

        # Check for degradation (standard deviation > 50% of mean)
        if len(times) > 1:
            std_dev = stdev(times)
            degradation_ratio = std_dev / avg_response if avg_response > 0 else 0
            has_degradation = degradation_ratio > self.performance_thresholds["degradation_threshold"]
        else:
            has_degradation = False

        # Check for bottleneck (avg > threshold)
        is_bottleneck = avg_response > self.performance_thresholds["bottleneck_threshold"] / 1000

        # Generate recommendation
        recommendation = None
        if is_bottleneck:
            recommendation = f"Service {service_id} is a performance bottleneck. Average response: {avg_response:.2f}s. Consider optimization or scaling."
        elif has_degradation:
            recommendation = f"Service {service_id} shows performance degradation. Std dev: {std_dev:.2f}s. Monitor for emerging issues."
        elif avg_response > self.performance_thresholds["slow_response_ms"] / 1000:
            recommendation = f"Service {service_id} has slow responses. Average: {avg_response:.2f}s. Consider performance tuning."

        return {
            "status": "analyzed",
            "avg_response_time": avg_response,
            "min_response_time": min_response,
            "max_response_time": max_response,
            "bottleneck": is_bottleneck,
            "degradation": has_degradation,
            "recommendation": recommendation,
            "trend_data": {
                "count": len(times),
                "avg_ms": avg_response * 1000,
                "std_dev_ms": std_dev * 1000 if 'std_dev' in locals() else None
            }
        }

    async def get_dashboard_data(self) -> DashboardResponse:
        """
        Get comprehensive dashboard data with progressive disclosure.
        """
        await self.init_session()

        # Get current services using discovery
        services_config = await self.get_services()

        # Check cache first
        now = datetime.now(timezone.utc)
        if self.last_update and (now - self.last_update).total_seconds() < self.cache_ttl:
            # Update service IDs if they changed
            if set(self.cache["dashboard"].services.keys()) == set(services_config.keys()):
                return self.cache["dashboard"]
            else:
                logger.info("Service registry changed, bypassing cache")

        # Check all services in parallel
        tasks = [self.check_service_health(service_id, config) for service_id, config in services_config.items()]
        service_healths = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        services = []
        healthy_count = 0
        warning_count = 0
        critical_count = 0
        total_services = len(services_config)

        for service_id, result in zip(services_config.keys(), service_healths):
            if isinstance(result, Exception):
                # Handle task exceptions
                services.append(ServiceHealth(
                    name=f"Unknown ({service_id})",
                    status=HealthLevel.UNKNOWN,
                    message=f"Check failed: {str(result)[:50]}",
                    last_check=now,
                    adhd_optimized=False
                ))
                critical_count += 1
            else:
                # Create ServiceHealth with service ID
                health_result = ServiceHealth(
                    name=result.name if hasattr(result, 'name') else service_id.title(),
                    status=result.status if hasattr(result, 'status') else HealthLevel.UNKNOWN,
                    message=result.message if hasattr(result, 'message') else "Unknown status",
                    last_check=result.last_check if hasattr(result, 'last_check') else now,
                    response_time=result.response_time if hasattr(result, 'response_time') else None,
                    details=result.details if hasattr(result, 'details') else {},
                    adhd_optimized=services_config[service_id].get('adhd_optimized', False)
                )
                services.append(health_result)

                # Track performance if response time available
                if health_result.response_time is not None:
                    self._track_performance(service_id, health_result.response_time)

                # Attempt automated recovery for failed services
                if health_result.status in [HealthLevel.CRITICAL, HealthLevel.WARNING]:
                    await self._attempt_service_recovery(service_id, health_result, services_config[service_id])

                if health_result.status == HealthLevel.HEALTHY:
                    healthy_count += 1
                elif health_result.status == HealthLevel.WARNING:
                    warning_count += 1
                elif health_result.status == HealthLevel.CRITICAL:
                    critical_count += 1
                else:  # UNKNOWN
                    critical_count += 1

        # Determine overall health
        if critical_count > 0:
            overall_health = HealthLevel.CRITICAL
        elif warning_count > 0:
            overall_health = HealthLevel.WARNING
        else:
            overall_health = HealthLevel.HEALTHY

        # Create summary with performance metrics
        summary = {
            "total_services": total_services,
            "healthy_services": healthy_count,
            "warning_services": warning_count,
            "critical_services": critical_count,
            "discovery_sources": {
                "static": sum(1 for s in services_config.values() if s.get('discovery') == 'static'),
                "docker": sum(1 for s in services_config.values() if s.get('discovery') == 'docker')
            },
            "performance_summary": {
                "services_with_data": len([s for s in self.performance_history if len(s) > 0]),
                "avg_response_time_ms": None,
                "slow_responses": 0,
                "bottlenecks": [],
                "recommendations": []
            }
        }

        # Add performance analysis for services with sufficient data
        bottleneck_services = []
        slow_services = []
        recommendations = []

        for service_id in self.performance_history:
            if len(self.performance_history[service_id]) >= 3:  # Need at least 3 measurements
                perf_analysis = self._analyze_performance_trends(service_id)
                if perf_analysis["bottleneck"]:
                    bottleneck_services.append({
                        "service": service_id,
                        "avg_ms": perf_analysis["trend_data"]["avg_ms"],
                        "recommendation": perf_analysis["recommendation"]
                    })
                elif perf_analysis["status"] == "analyzed" and perf_analysis["avg_response_time"] > 0.5:
                    slow_services.append({
                        "service": service_id,
                        "avg_ms": perf_analysis["trend_data"]["avg_ms"],
                        "recommendation": perf_analysis["recommendation"]
                    })
                if perf_analysis["recommendation"]:
                    recommendations.append(perf_analysis["recommendation"])

        if bottleneck_services:
            summary["performance_summary"]["bottlenecks"] = bottleneck_services
            summary["performance_summary"]["avg_response_time_ms"] = sum([b["avg_ms"] for b in bottleneck_services]) / len(bottleneck_services)
        elif slow_services:
            summary["performance_summary"]["slow_services"] = slow_services
            summary["performance_summary"]["avg_response_time_ms"] = sum([s["avg_ms"] for s in slow_services]) / len(slow_services)

        summary["performance_summary"]["recommendations"] = recommendations[:3]  # Top 3 recommendations

        dashboard_data = DashboardResponse(
            overall_health=overall_health,
            total_services=total_services,
            healthy_services=healthy_count,
            warning_services=warning_count,
            critical_services=critical_count,
            last_update=now,
            services=services,
            summary=summary
        )

        # Cache the result
        self.cache["dashboard"] = dashboard_data
        self.last_update = now

        return dashboard_data

        # ADHD-optimized summary
        summary = {
            "healthy_percentage": round((healthy_count / len(services)) * 100, 1),
            "adhd_services_count": sum(1 for s in services if s.adhd_optimized),
            "adhd_services_healthy": sum(1 for s in services if s.adhd_optimized and s.status == HealthLevel.HEALTHY),
            "quick_status": "All good" if overall_health == HealthLevel.HEALTHY else "Needs attention" if overall_health == HealthLevel.WARNING else "Critical issues",
            "recommendation": self._get_adhd_recommendation(overall_health, warning_count, critical_count)
        }

        response = DashboardResponse(
            overall_health=overall_health,
            total_services=len(services),
            healthy_services=healthy_count,
            warning_services=warning_count,
            critical_services=critical_count,
            last_update=now,
            services=services,
            summary=summary
        )

        # Check for and generate alerts
        alert = await self.alert_system.check_and_generate_alerts(response)
        if alert:
            self.alert_history.append(alert)
            # Keep only last 10 alerts
            if len(self.alert_history) > 10:
                self.alert_history = self.alert_history[-10:]

            # Add current alert to response summary
            response.summary["current_alert"] = {
                "level": alert["level"],
                "message": alert["message"],
                "urgency": alert["urgency"],
                "break_suggestion": alert["break_suggestion"],
                "recommendation": alert["recommendation"]
            }

        # Cache response
        self.cache["dashboard"] = response
        self.last_update = now

        return response

    def _get_adhd_recommendation(self, overall_health: HealthLevel, warnings: int, criticals: int) -> str:
        """Get ADHD-friendly recommendations based on system state."""
        if overall_health == HealthLevel.HEALTHY:
            return "Everything looks good - great job maintaining system health!"

        if overall_health == HealthLevel.WARNING:
            if warnings <= 2:
                return "A few minor issues detected. Consider addressing when you have focused time."
            else:
                return "Several services need attention. Might be a good time for a short debugging session."

        if overall_health == HealthLevel.CRITICAL:
            if criticals == 1:
                return "One critical issue detected. This may impact your workflow - consider investigating soon."
            else:
                return f"{criticals} critical issues found. This could significantly impact development - prioritize fixing these."

        return "System status unclear - check individual services for details."

# Global dashboard instance
dashboard = MonitoringDashboard()

# FastAPI app
app = FastAPI(
    title="Dopemux Monitoring Dashboard",
    description="Unified health monitoring for 30+ services with ADHD-optimized progressive disclosure",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    await dashboard.init_session()
    # Initialize service discovery
    await dashboard.discover_services()

@app.on_event("shutdown")
async def shutdown_event():
    await dashboard.close_session()

@app.get("/health")
async def health_check():
    """Basic health check for the monitoring dashboard itself."""
    return {
        "status": "healthy",
        "message": "Monitoring dashboard operational",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get full dashboard data with progressive disclosure."""
    return await dashboard.get_dashboard_data()

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get ADHD-optimized summary view (minimal cognitive load)."""
    full_data = await dashboard.get_dashboard_data()

    return {
        "overall_health": full_data.overall_health,
        "quick_status": full_data.summary["quick_status"],
        "healthy_percentage": full_data.summary["healthy_percentage"],
        "recommendation": full_data.summary["recommendation"],
        "last_update": full_data.last_update,
        "critical_services": [s.name for s in full_data.services if s.status == HealthLevel.CRITICAL],
        "warning_services": [s.name for s in full_data.services if s.status == HealthLevel.WARNING]
    }

@app.get("/api/services/{service_name}")
async def get_service_details(service_name: str):
    """Get detailed information about a specific service."""
    full_data = await dashboard.get_dashboard_data()

    for service in full_data.services:
        if service.name.lower().replace(" ", "_") == service_name.lower():
            return service

    raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

@app.get("/api/alerts")
async def get_alerts():
    """Get current alerts and alert history."""
    return {
        "current_alert": dashboard.alert_system.last_alert_level if hasattr(dashboard.alert_system, 'last_alert_level') else None,
        "alert_history": dashboard.alert_history[-5:],  # Last 5 alerts
        "alert_thresholds": dashboard.alert_thresholds
    }

@app.get("/api/alerts/history")
async def get_alert_history():
    """Get complete alert history."""
    return {"alerts": dashboard.alert_history}

@app.get("/api/performance")
async def get_performance_metrics():
    """Get detailed performance metrics and bottleneck analysis."""
    performance_data = {}

    for service_id in dashboard.performance_history:
        if len(dashboard.performance_history[service_id]) >= 3:
            analysis = dashboard._analyze_performance_trends(service_id)
            performance_data[service_id] = {
                "analysis": analysis,
                "response_times": list(dashboard.performance_history[service_id])[-10:],  # Last 10 measurements
                "trend_status": "bottleneck" if analysis["bottleneck"] else "degraded" if analysis["degradation"] else "normal"
            }

    return {
        "services_analyzed": len(performance_data),
        "performance_data": performance_data,
        "system_summary": {
            "bottlenecks_count": sum(1 for s in performance_data.values() if s["analysis"]["bottleneck"]),
            "degraded_count": sum(1 for s in performance_data.values() if s["analysis"]["degradation"]),
            "total_measurements": sum(len(s["response_times"]) for s in performance_data.values())
        }
    }

@app.get("/api/recovery")
async def get_recovery_stats():
    """Get automated recovery system statistics and history."""
    return dashboard.recovery_manager.get_recovery_stats()

@app.get("/", response_class=HTMLResponse)
async def dashboard_ui():
    """Serve the ADHD-optimized dashboard UI."""
    # Simple HTML dashboard (could be enhanced with React/Vue later)
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dopemux Monitoring Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; background: #f5f5f5; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .summary { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .services { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
            .service { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.1); }
            .healthy { border-left: 4px solid #4caf50; }
            .warning { border-left: 4px solid #ff9800; }
            .critical { border-left: 4px solid #f44336; }
            .unknown { border-left: 4px solid #9e9e9e; }
            .adhd-badge { background: #e1f5fe; color: #0277bd; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧠 Dopemux Monitoring Dashboard</h1>
            <p>ADHD-Optimized Health Monitoring for 30+ Services</p>
        </div>

        <div class="summary">
            <h2>System Overview</h2>
            <div id="summary-content">Loading...</div>
        </div>

        <div class="services" id="services-content">
            Loading services...
        </div>

        <script>
            async function updateDashboard() {
                try {
                    const response = await fetch('/api/dashboard/summary');
                    const data = await response.json();

                    const healthColor = data.overall_health === 'healthy' ? '#4caf50' :
                                       data.overall_health === 'warning' ? '#ff9800' : '#f44336';

                    document.getElementById('summary-content').innerHTML = `
                        <div style="display: flex; gap: 20px; align-items: center;">
                            <div style="font-size: 2em; font-weight: bold; color: ${healthColor};">
                                ${data.overall_health.toUpperCase()}
                            </div>
                            <div>
                                <div style="font-size: 1.2em; margin-bottom: 5px;">${data.quick_status}</div>
                                <div style="color: #666;">${data.healthy_percentage}% services healthy</div>
                            </div>
                        </div>
                        <div style="margin-top: 15px; padding: 10px; background: #f9f9f9; border-radius: 5px;">
                            <strong>ADHD Recommendation:</strong> ${data.recommendation}
                        </div>
                        <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                            Last updated: ${new Date(data.last_update).toLocaleTimeString()}
                        </div>
                    `;

                    // Update services (simplified view)
                    const servicesResponse = await fetch('/api/dashboard');
                    const servicesData = await servicesResponse.json();

                    const servicesHtml = servicesData.services.map(service => {
                        const statusColor = service.status === 'healthy' ? '#4caf50' :
                                           service.status === 'warning' ? '#ff9800' :
                                           service.status === 'critical' ? '#f44336' : '#9e9e9e';

                        const adhdBadge = service.adhd_optimized ? '<span class="adhd-badge">ADHD</span>' : '';
                        const responseTime = service.response_time ?
                            `Response: ${service.response_time.toFixed(2)}s` : 'No response time';

                        return `
                            <div class="service ${service.status}">
                                <h3>${service.name} ${adhdBadge}</h3>
                                <div style="color: ${statusColor}; font-weight: bold;">
                                    ${service.status.toUpperCase()}
                                </div>
                                <div style="margin: 5px 0;">${service.message}</div>
                                <div style="font-size: 0.8em; color: #666;">
                                    ${responseTime}
                                </div>
                            </div>
                        `;
                    }).join('');

                    document.getElementById('services-content').innerHTML = servicesHtml;

                } catch (error) {
                    console.error('Dashboard update failed:', error);
                    document.getElementById('summary-content').innerHTML = 'Error loading dashboard data';
                }
            }

            // Update every 30 seconds
            updateDashboard();
            setInterval(updateDashboard, 30000);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    # Start the monitoring dashboard
    logger.info("🚀 Starting Dopemux Monitoring Dashboard on port 8098")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8098,
        reload=False,
        log_level="info"
    )

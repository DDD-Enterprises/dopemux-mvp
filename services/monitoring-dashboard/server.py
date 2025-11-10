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

class MonitoringDashboard:
    """
    Unified monitoring dashboard with ADHD-optimized progressive disclosure.
    """

    def __init__(self):
        self.services = {
            "adhd_engine": {
                "name": "ADHD Engine",
                "type": "web_api",
                "url": "http://localhost:8095/health",
                "timeout": 5.0,
                "adhd_optimized": True
            },
            "adhd_dashboard": {
                "name": "ADHD Dashboard",
                "type": "web_api",
                "url": "http://localhost:8097/health",
                "timeout": 5.0,
                "adhd_optimized": True
            },
            "conport": {
                "name": "ConPort Knowledge Graph",
                "type": "database_api",
                "url": "http://localhost:5455/health",
                "timeout": 10.0,  # Longer timeout for DB operations
                "adhd_optimized": False,
                "fallback_check": "process_check"  # Check if PostgreSQL process is running
            },
            "task_orchestrator": {
                "name": "Task Orchestrator (Leantime)",
                "type": "web_app",
                "url": "http://localhost:8080/health",
                "timeout": 5.0,
                "adhd_optimized": True,
                "auth_required": True,  # May redirect to login
                "fallback_check": "docker_check"  # Check if leantime container is running
            },
            "zen_mcp": {
                "name": "Zen MCP Server",
                "type": "mcp_server",
                "url": "http://localhost:3012/health",
                "timeout": 3.0,
                "adhd_optimized": True,
                "fallback_check": "mcp_ping"  # MCP protocol health check
            },
            "serena_mcp": {
                "name": "Serena MCP Server",
                "type": "mcp_server",
                "url": "http://localhost:3013/health",
                "timeout": 3.0,
                "adhd_optimized": True,
                "fallback_check": "mcp_ping"
            },
            "dope_context_mcp": {
                "name": "Dope-Context MCP Server",
                "type": "mcp_server",
                "url": "http://localhost:3014/health",
                "timeout": 3.0,
                "adhd_optimized": True,
                "fallback_check": "mcp_ping"
            },
            "gpt_researcher": {
                "name": "GPT Researcher",
                "type": "mcp_server",
                "url": "http://localhost:8010/health",
                "timeout": 5.0,
                "adhd_optimized": False,
                "fallback_check": "mcp_ping"
            },
            "monitoring_dashboard": {
                "name": "Monitoring Dashboard",
                "type": "web_api",
                "url": "http://localhost:8098/health",
                "timeout": 3.0,
                "adhd_optimized": True
            }
        }

        self.session = None
        self.last_update = None
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds cache

        # Initialize circuit breakers for resilience
        self.circuit_breakers = self._init_circuit_breakers()

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

    async def check_service_health(self, service_config: Dict[str, Any]) -> ServiceHealth:
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
                import subprocess
                result = subprocess.run(
                    ["pg_isready", "-h", "localhost", "-p", "5432"],
                    capture_output=True,
                    text=True,
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
                import subprocess
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=leantime", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
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

    async def get_dashboard_data(self) -> DashboardResponse:
        """
        Get comprehensive dashboard data with progressive disclosure.
        """
        await self.init_session()

        # Check cache first
        now = datetime.now(timezone.utc)
        if self.last_update and (now - self.last_update).total_seconds() < self.cache_ttl:
            return self.cache["dashboard"]

        # Check all services in parallel
        tasks = [self.check_service_health(config) for config in self.services.values()]
        service_healths = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        services = []
        healthy_count = 0
        warning_count = 0
        critical_count = 0

        for result in service_healths:
            if isinstance(result, Exception):
                # Handle task exceptions
                services.append(ServiceHealth(
                    name="Unknown",
                    status=HealthLevel.UNKNOWN,
                    message=f"Check failed: {str(result)[:50]}",
                    last_check=now,
                    adhd_optimized=False
                ))
                critical_count += 1
            else:
                services.append(result)
                if result.status == HealthLevel.HEALTHY:
                    healthy_count += 1
                elif result.status == HealthLevel.WARNING:
                    warning_count += 1
                elif result.status == HealthLevel.CRITICAL:
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
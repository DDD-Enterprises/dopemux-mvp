"""
Production Health Checks for All Dopemux Services

Provides unified health monitoring across the two-plane architecture.
ADHD-optimized: Quick status, clear indicators, automated alerts.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

import aiohttp
import asyncpg
from redis import asyncio as redis

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status for a single service."""
    service_name: str
    status: HealthStatus
    response_time_ms: Optional[float]
    details: Dict[str, any]
    checked_at: datetime
    error: Optional[str] = None


class HealthCheckOrchestrator:
    """
    Orchestrates health checks across all Dopemux services.

    Services Monitored:
    - ConPort MCP (port 3004)
    - Serena MCP (port 3001)
    - Task-Orchestrator (port 8002)
    - ADHD Engine (port 8001)
    - Dope-Context (Qdrant port 6333)
    - PostgreSQL (dopemux-postgres-age)
    - Redis (redis-primary)
    """

    def __init__(self):
        self.services = {
            'conport_mcp': 'http://localhost:3004/health',
            'serena_mcp': 'http://localhost:3001/health',
            'task_orchestrator': 'http://localhost:8002/health',
            'adhd_engine': 'http://localhost:8001/health',
            'dope_context': 'http://localhost:6333/collections',  # Qdrant
        }

        self.database_url = "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph"
        self.redis_url = "redis://localhost:6379"

    async def check_all(self) -> Dict[str, ServiceHealth]:
        """
        Check health of all services in parallel.

        Returns:
            Dict mapping service_name to ServiceHealth

        Performance: <2 seconds for all checks
        """
        start = datetime.now()

        # Run all checks in parallel
        tasks = {
            'conport_mcp': self._check_http('conport_mcp'),
            'serena_mcp': self._check_http('serena_mcp'),
            'task_orchestrator': self._check_http('task_orchestrator'),
            'adhd_engine': self._check_http('adhd_engine'),
            'dope_context': self._check_http('dope_context'),
            'postgresql': self._check_postgresql(),
            'redis': self._check_redis(),
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        health_status = {}
        for (service_name, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                health_status[service_name] = ServiceHealth(
                    service_name=service_name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=None,
                    details={},
                    checked_at=datetime.now(),
                    error=str(result)
                )
            else:
                health_status[service_name] = result

        elapsed_ms = (datetime.now() - start).total_seconds() * 1000
        logger.info(f"Health check completed in {elapsed_ms:.1f}ms")

        return health_status

    async def _check_http(self, service_name: str) -> ServiceHealth:
        """Check HTTP service health."""
        url = self.services[service_name]
        start = datetime.now()

        try:
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    response_time = (datetime.now() - start).total_seconds() * 1000

                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            return ServiceHealth(
                                service_name=service_name,
                                status=HealthStatus.HEALTHY,
                                response_time_ms=response_time,
                                details=data,
                                checked_at=datetime.now()
                            )
                        except Exception as e:
                            # Non-JSON response but 200 OK
                            return ServiceHealth(
                                service_name=service_name,
                                status=HealthStatus.HEALTHY,
                                response_time_ms=response_time,
                                details={'status': 'ok'},
                                checked_at=datetime.now()
                            )
                            logger.error(f"Error: {e}")
                    else:
                        return ServiceHealth(
                            service_name=service_name,
                            status=HealthStatus.DEGRADED,
                            response_time_ms=response_time,
                            details={'http_status': resp.status},
                            checked_at=datetime.now(),
                            error=f"HTTP {resp.status}"
                        )

        except asyncio.TimeoutError:
            return ServiceHealth(
                service_name=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=5000.0,
                details={},
                checked_at=datetime.now(),
                error="Timeout after 5s"
            )
        except Exception as e:
            return ServiceHealth(
                service_name=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                details={},
                checked_at=datetime.now(),
                error=str(e)
            )

            logger.error(f"Error: {e}")
    async def _check_postgresql(self) -> ServiceHealth:
        """Check PostgreSQL database health."""
        start = datetime.now()

        try:
            conn = await asyncpg.connect(self.database_url, timeout=5.0)

            # Quick health query
            count = await conn.fetchval("SELECT COUNT(*) FROM ag_catalog.decisions WHERE user_id = 'default'")

            response_time = (datetime.now() - start).total_seconds() * 1000

            await conn.close()

            return ServiceHealth(
                service_name='postgresql',
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    'total_decisions': count,
                    'schema': 'ag_catalog'
                },
                checked_at=datetime.now()
            )

        except Exception as e:
            return ServiceHealth(
                service_name='postgresql',
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                details={},
                checked_at=datetime.now(),
                error=str(e)
            )

            logger.error(f"Error: {e}")
    async def _check_redis(self) -> ServiceHealth:
        """Check Redis health."""
        start = datetime.now()

        try:
            client = redis.from_url(self.redis_url, socket_timeout=5.0)
            await client.ping()

            # Check stream status
            try:
                stream_len = await client.xlen("dopemux:events")
                details = {'stream_length': stream_len}
            except Exception as e:
                details = {}

                logger.error(f"Error: {e}")
            response_time = (datetime.now() - start).total_seconds() * 1000

            await client.aclose()

            return ServiceHealth(
                service_name='redis',
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details=details,
                checked_at=datetime.now()
            )

        except Exception as e:
            return ServiceHealth(
                service_name='redis',
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                details={},
                checked_at=datetime.now(),
                error=str(e)
            )

            logger.error(f"Error: {e}")
    def get_overall_status(self, health_results: Dict[str, ServiceHealth]) -> HealthStatus:
        """
        Determine overall system health.

        Rules:
        - Any UNHEALTHY → System DEGRADED
        - All HEALTHY → System HEALTHY
        - Mix of HEALTHY/DEGRADED → System DEGRADED
        """
        statuses = [h.status for h in health_results.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.DEGRADED

    def format_health_report(self, health_results: Dict[str, ServiceHealth]) -> str:
        """Format health check results for display."""
        overall = self.get_overall_status(health_results)

        report = [
            "=" * 70,
            f"Dopemux Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
            f"Overall Status: {overall.value.upper()}",
            "",
            "Service Details:",
            ""
        ]

        for service_name, health in sorted(health_results.items()):
            icon = "✅" if health.status == HealthStatus.HEALTHY else "❌" if health.status == HealthStatus.UNHEALTHY else "⚠️"
            time_str = f"{health.response_time_ms:.1f}ms" if health.response_time_ms else "N/A"

            report.append(f"{icon} {service_name:20} {health.status.value:12} {time_str:>10}")

            if health.error:
                report.append(f"   Error: {health.error}")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)


async def main():
    """Run health checks and display results."""
    orchestrator = HealthCheckOrchestrator()

    logger.info("Running Dopemux health checks...")
    health_results = await orchestrator.check_all()

    logger.info(orchestrator.format_health_report(health_results))

    # Exit code based on overall status
    overall = orchestrator.get_overall_status(health_results)
    return 0 if overall == HealthStatus.HEALTHY else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

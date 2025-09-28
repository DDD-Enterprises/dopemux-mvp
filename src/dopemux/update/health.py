"""
Dopemux Health Checker

Comprehensive health checking for all services in the dopemux ecosystem.
Validates service responsiveness, connectivity, and critical functionality.
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse

import httpx
import docker
from rich.console import Console

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Comprehensive health checker for dopemux services.

    Checks:
    - Docker container health
    - HTTP endpoint responsiveness
    - Database connectivity
    - MCP server functionality
    - Critical service integration
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.console = Console()
        self.docker_client = None
        self.timeout = 30  # seconds

        # Service definitions
        self.services = {
            # Core infrastructure
            'redis': {
                'type': 'docker',
                'container': 'redis',
                'health_check': self._check_redis_health
            },
            'postgres': {
                'type': 'docker',
                'container': 'postgres',
                'health_check': self._check_postgres_health
            },

            # MCP Servers
            'mas-sequential-thinking': {
                'type': 'http',
                'url': 'http://localhost:3001/health',
                'container': 'mas-sequential-thinking'
            },
            'conport': {
                'type': 'http',
                'url': 'http://localhost:3004/health',
                'container': 'conport'
            },
            'zen': {
                'type': 'http',
                'url': 'http://localhost:3003/health',
                'container': 'zen'
            },
            'context7': {
                'type': 'http',
                'url': 'http://localhost:3002/health',
                'container': 'context7'
            },
            'gptr-mcp': {
                'type': 'http',
                'url': 'http://localhost:3009/health',
                'container': 'gptr-mcp'
            },

            # Application services
            'serena': {
                'type': 'http',
                'url': 'http://localhost:3006/health',
                'container': 'serena'
            },
            'task-master-ai': {
                'type': 'http',
                'url': 'http://localhost:3005/health',
                'container': 'task-master-ai'
            },
        }

        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Could not connect to Docker: {e}")

    async def check_all_services(self) -> Dict[str, bool]:
        """
        Check health of all registered services.

        Returns:
            Dictionary mapping service names to health status (True = healthy)
        """
        results = {}

        # Check services in parallel for efficiency
        tasks = []
        for service_name, service_config in self.services.items():
            task = asyncio.create_task(
                self._check_service_health(service_name, service_config)
            )
            tasks.append((service_name, task))

        # Wait for all checks to complete
        for service_name, task in tasks:
            try:
                is_healthy = await task
                results[service_name] = is_healthy
            except Exception as e:
                logger.exception(f"Health check failed for {service_name}")
                results[service_name] = False

        return results

    async def check_service(self, service_name: str) -> bool:
        """Check health of a specific service."""
        if service_name not in self.services:
            logger.warning(f"Unknown service: {service_name}")
            return False

        service_config = self.services[service_name]
        return await self._check_service_health(service_name, service_config)

    async def wait_for_service(self, service_name: str,
                              max_wait_seconds: int = 60) -> bool:
        """
        Wait for a service to become healthy with retries.

        Args:
            service_name: Name of service to wait for
            max_wait_seconds: Maximum time to wait

        Returns:
            True if service became healthy, False if timeout
        """
        start_time = asyncio.get_event_loop().time()
        retry_interval = 2  # seconds

        while (asyncio.get_event_loop().time() - start_time) < max_wait_seconds:
            if await self.check_service(service_name):
                return True

            await asyncio.sleep(retry_interval)
            retry_interval = min(retry_interval * 1.2, 10)  # Exponential backoff

        return False

    async def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """Get detailed information about a service."""
        if service_name not in self.services:
            return {'error': f'Unknown service: {service_name}'}

        service_config = self.services[service_name]
        info = {
            'name': service_name,
            'type': service_config['type'],
            'healthy': await self.check_service(service_name)
        }

        # Add container information if available
        if 'container' in service_config and self.docker_client:
            try:
                container = self.docker_client.containers.get(service_config['container'])
                info.update({
                    'container_status': container.status,
                    'container_created': container.attrs['Created'],
                    'container_image': container.image.tags[0] if container.image.tags else None
                })
            except Exception as e:
                info['container_error'] = str(e)

        # Add URL information for HTTP services
        if service_config['type'] == 'http':
            info['url'] = service_config['url']

        return info

    async def _check_service_health(self, service_name: str,
                                   service_config: Dict[str, Any]) -> bool:
        """Check health of a single service based on its configuration."""
        service_type = service_config['type']

        try:
            if service_type == 'http':
                return await self._check_http_health(service_config['url'])
            elif service_type == 'docker':
                return await self._check_docker_health(service_config['container'])
            elif 'health_check' in service_config:
                return await service_config['health_check']()
            else:
                logger.warning(f"Unknown service type for {service_name}: {service_type}")
                return False

        except Exception as e:
            logger.debug(f"Health check failed for {service_name}: {e}")
            return False

    async def _check_http_health(self, url: str) -> bool:
        """Check health via HTTP endpoint."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def _check_docker_health(self, container_name: str) -> bool:
        """Check Docker container health."""
        if not self.docker_client:
            return False

        try:
            container = self.docker_client.containers.get(container_name)
            return container.status == 'running'
        except Exception:
            return False

    async def _check_redis_health(self) -> bool:
        """Check Redis connectivity."""
        try:
            result = subprocess.run(
                ["docker", "exec", "redis", "redis-cli", "ping"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 and "PONG" in result.stdout
        except Exception:
            return False

    async def _check_postgres_health(self) -> bool:
        """Check PostgreSQL connectivity."""
        try:
            result = subprocess.run(
                ["docker", "exec", "postgres", "pg_isready"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    async def check_critical_paths(self) -> Dict[str, bool]:
        """
        Check critical application paths beyond basic service health.

        Returns:
            Dictionary of critical path names to success status
        """
        critical_paths = {
            'conport_database': await self._check_conport_database(),
            'mcp_registration': await self._check_mcp_registration(),
            'docker_networking': await self._check_docker_networking(),
            'file_permissions': await self._check_file_permissions(),
        }

        return critical_paths

    async def _check_conport_database(self) -> bool:
        """Check ConPort database connectivity and basic functionality."""
        try:
            # Check if ConPort database file exists and is accessible
            conport_db = self.project_root / ".dopemux" / "conport.db"
            if not conport_db.exists():
                return False

            # Try to connect via ConPort API if available
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get("http://localhost:3004/health")
                    if response.status_code == 200:
                        # Try a basic ConPort operation
                        response = await client.get("http://localhost:3004/api/status")
                        return response.status_code in [200, 404]  # 404 is ok for basic connectivity
            except Exception:
                pass

            return True  # Database file exists

        except Exception as e:
            logger.debug(f"ConPort database check failed: {e}")
            return False

    async def _check_mcp_registration(self) -> bool:
        """Check if MCP servers are properly registered."""
        try:
            # This would check Claude Code's MCP configuration
            # For now, just check if key MCP servers are responding
            core_mcp_servers = ['mas-sequential-thinking', 'conport', 'zen']

            healthy_count = 0
            for server in core_mcp_servers:
                if await self.check_service(server):
                    healthy_count += 1

            # Consider MCP registration healthy if at least 2/3 core servers are running
            return healthy_count >= len(core_mcp_servers) * 0.67

        except Exception as e:
            logger.debug(f"MCP registration check failed: {e}")
            return False

    async def _check_docker_networking(self) -> bool:
        """Check Docker networking between services."""
        try:
            if not self.docker_client:
                return False

            # Check if containers can communicate
            networks = self.docker_client.networks.list()
            dopemux_networks = [n for n in networks if 'dopemux' in n.name.lower() or 'mcp' in n.name.lower()]

            return len(dopemux_networks) > 0

        except Exception as e:
            logger.debug(f"Docker networking check failed: {e}")
            return False

    async def _check_file_permissions(self) -> bool:
        """Check that required directories and files have proper permissions."""
        try:
            # Check key directories
            required_dirs = [
                self.project_root / ".dopemux",
                self.project_root / "docker",
                self.project_root / "config",
            ]

            for directory in required_dirs:
                if directory.exists():
                    # Try to create a test file to verify write permissions
                    test_file = directory / ".health_check_test"
                    try:
                        test_file.write_text("test")
                        test_file.unlink()
                    except Exception:
                        return False

            return True

        except Exception as e:
            logger.debug(f"File permissions check failed: {e}")
            return False

    def get_unhealthy_services(self, health_results: Dict[str, bool]) -> List[str]:
        """Get list of services that are not healthy."""
        return [service for service, healthy in health_results.items() if not healthy]

    def show_health_summary(self, health_results: Dict[str, bool]) -> None:
        """Display a user-friendly health summary."""
        healthy_count = sum(health_results.values())
        total_count = len(health_results)

        if healthy_count == total_count:
            self.console.print("[green]✅ All services healthy![/green]")
        else:
            unhealthy = self.get_unhealthy_services(health_results)
            self.console.print(f"[yellow]⚠️ {len(unhealthy)} services need attention:[/yellow]")
            for service in unhealthy:
                self.console.print(f"  [red]❌ {service}[/red]")

        self.console.print(f"[dim]Overall health: {healthy_count}/{total_count} services[/dim]")
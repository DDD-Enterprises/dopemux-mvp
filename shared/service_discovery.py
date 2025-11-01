"""
Service Discovery for ADHD Services

Provides dynamic service location and health monitoring for distributed
ADHD services architecture. Supports DNS-based discovery with Redis backup.
"""

import asyncio
import logging
import socket
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DOWN = "down"


@dataclass
class ServiceEndpoint:
    """Service endpoint information."""
    name: str
    host: str
    port: int
    protocol: str = "http"
    path: str = ""
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: float = 0
    response_time: Optional[float] = None
    metadata: Dict[str, Any] = None

    @property
    def url(self) -> str:
        """Get full service URL."""
        return f"{self.protocol}://{self.host}:{self.port}{self.path}"

    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == ServiceStatus.HEALTHY


class ServiceDiscovery:
    """
    Service discovery with DNS and Redis backup.

    Provides dynamic service location for ADHD services with health monitoring
    and automatic failover.
    """

    def __init__(self, redis_pool=None, dns_timeout: float = 5.0, health_check_interval: int = 30):
        """
        Initialize service discovery.

        Args:
            redis_pool: Shared Redis connection pool
            dns_timeout: DNS lookup timeout in seconds
            health_check_interval: Health check interval in seconds
        """
        self.redis_pool = redis_pool
        self.dns_timeout = dns_timeout
        self.health_check_interval = health_check_interval

        # Service registry (name -> list of endpoints)
        self.services: Dict[str, List[ServiceEndpoint]] = {}

        # DNS service mappings (service name -> DNS name)
        self.dns_mappings = {
            "adhd-engine": "adhd-engine",
            "activity-capture": "activity-capture",
            "break-suggester": "break-suggester",
            "workspace-watcher": "workspace-watcher",
            "adhd-dashboard": "adhd-dashboard",
            "adhd-notifier": "adhd-notifier",
            "complexity-coordinator": "complexity-coordinator",
            "context-switch-tracker": "context-switch-tracker",
            "energy-trends": "energy-trends",
            "redis-primary": "redis-primary",
        }

        # Default ports for services
        self.default_ports = {
            "adhd-engine": 8095,
            "activity-capture": 8096,
            "break-suggester": None,  # Background service
            "workspace-watcher": None,  # Background service
            "adhd-dashboard": 8097,
            "adhd-notifier": None,  # Background service
            "complexity-coordinator": None,  # Background service
            "context-switch-tracker": None,  # Background service
            "energy-trends": None,  # Background service
            "redis-primary": 6379,
        }

        # Health monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False

    async def initialize(self):
        """Initialize service discovery."""
        if not self.redis_pool:
            # Import shared Redis pool
            from .redis_pool import get_redis_pool
            self.redis_pool = await get_redis_pool()

        # Load service endpoints from Redis (backup registry)
        await self._load_from_redis()

        # Start health monitoring
        self.running = True
        self.monitoring_task = asyncio.create_task(self._health_monitor())

        logger.info("Service discovery initialized")

    async def close(self):
        """Close service discovery."""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        # Save service state to Redis
        await self._save_to_redis()

        logger.info("Service discovery closed")

    async def register_service(
        self,
        name: str,
        host: str,
        port: int,
        protocol: str = "http",
        path: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a service endpoint.

        Args:
            name: Service name
            host: Service host
            port: Service port
            protocol: Protocol (http, https)
            path: Base path
            metadata: Additional service metadata
        """
        endpoint = ServiceEndpoint(
            name=name,
            host=host,
            port=port,
            protocol=protocol,
            path=path,
            metadata=metadata or {}
        )

        if name not in self.services:
            self.services[name] = []

        # Check for duplicate endpoint
        existing = next(
            (ep for ep in self.services[name]
             if ep.host == host and ep.port == port),
            None
        )

        if existing:
            # Update existing endpoint
            existing.protocol = protocol
            existing.path = path
            existing.metadata = metadata or {}
        else:
            # Add new endpoint
            self.services[name].append(endpoint)

        # Save to Redis
        await self._save_service_to_redis(endpoint)

        logger.info(f"Registered service: {name} at {endpoint.url}")

    async def discover_service(self, name: str) -> Optional[ServiceEndpoint]:
        """
        Discover a healthy service endpoint.

        Args:
            name: Service name to discover

        Returns:
            Healthiest service endpoint or None if not found
        """
        endpoints = self.services.get(name, [])

        if not endpoints:
            # Try DNS discovery
            endpoint = await self._discover_via_dns(name)
            if endpoint:
                await self.register_service(
                    name=endpoint.name,
                    host=endpoint.host,
                    port=endpoint.port,
                    protocol=endpoint.protocol,
                    path=endpoint.path
                )
                return endpoint
            return None

        # Return healthiest endpoint
        healthy_endpoints = [ep for ep in endpoints if ep.is_healthy]
        if healthy_endpoints:
            # Return endpoint with best response time
            return min(healthy_endpoints, key=lambda ep: ep.response_time or float('inf'))

        # If no healthy endpoints, return first one (will be checked)
        return endpoints[0] if endpoints else None

    async def get_service_url(self, name: str, path: str = "") -> Optional[str]:
        """
        Get full URL for a service endpoint.

        Args:
            name: Service name
            path: Additional path to append

        Returns:
            Full service URL or None if not found
        """
        endpoint = await self.discover_service(name)
        if endpoint:
            base_url = endpoint.url.rstrip('/')
            full_path = f"{base_url}{path}"
            return full_path
        return None

    async def _discover_via_dns(self, name: str) -> Optional[ServiceEndpoint]:
        """
        Discover service via DNS lookup.

        Args:
            name: Service name

        Returns:
            Service endpoint from DNS or None
        """
        dns_name = self.dns_mappings.get(name)
        if not dns_name:
            return None

        try:
            # DNS lookup with timeout
            loop = asyncio.get_event_loop()
            addr_info = await asyncio.wait_for(
                loop.getaddrinfo(dns_name, None, family=socket.AF_INET),
                timeout=self.dns_timeout
            )

            if addr_info:
                # Use first resolved address
                host = addr_info[0][4][0]
                port = self.default_ports.get(name)

                if port:
                    return ServiceEndpoint(
                        name=name,
                        host=host,
                        port=port,
                        protocol="http"  # Assume HTTP for container services
                    )

        except (asyncio.TimeoutError, socket.gaierror) as e:
            logger.debug(f"DNS discovery failed for {name}: {e}")

        return None

    async def _health_monitor(self):
        """Background health monitoring for all services."""
        while self.running:
            try:
                # Check health of all registered services
                for service_name, endpoints in self.services.items():
                    for endpoint in endpoints:
                        await self._check_endpoint_health(endpoint)

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)

    async def _check_endpoint_health(self, endpoint: ServiceEndpoint):
        """
        Check health of a service endpoint.

        Args:
            endpoint: Service endpoint to check
        """
        try:
            import aiohttp

            # Simple health check - adjust based on service type
            if endpoint.name == "redis-primary":
                # Redis health check
                async with self.redis_pool.get_client() as client:
                    await client.ping()
                    endpoint.status = ServiceStatus.HEALTHY
                    endpoint.response_time = 0.001  # Mock low latency
            else:
                # HTTP health check
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    start_time = time.time()

                    try:
                        url = f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}/health"
                        async with session.get(url) as response:
                            response_time = time.time() - start_time

                            if response.status == 200:
                                endpoint.status = ServiceStatus.HEALTHY
                            else:
                                endpoint.status = ServiceStatus.UNHEALTHY

                            endpoint.response_time = response_time * 1000  # Convert to ms

                    except Exception:
                        endpoint.status = ServiceStatus.DOWN
                        endpoint.response_time = None

            endpoint.last_check = time.time()

        except Exception as e:
            logger.error(f"Health check failed for {endpoint.name}: {e}")
            endpoint.status = ServiceStatus.UNKNOWN

    async def _load_from_redis(self):
        """Load service registry from Redis backup."""
        try:
            async with self.redis_pool.get_client() as client:
                # Load all service endpoints
                pattern = "service:discovery:*"
                keys = await client.keys(pattern)

                for key in keys:
                    data = await client.get(key)
                    if data:
                        try:
                            import json
                            endpoint_data = json.loads(data)
                            endpoint = ServiceEndpoint(**endpoint_data)
                            service_name = endpoint.name

                            if service_name not in self.services:
                                self.services[service_name] = []
                            self.services[service_name].append(endpoint)

                        except Exception as e:
                            logger.error(f"Failed to load service from Redis: {e}")

        except Exception as e:
            logger.error(f"Failed to load services from Redis: {e}")

    async def _save_to_redis(self):
        """Save all service endpoints to Redis."""
        try:
            async with self.redis_pool.get_client() as client:
                # Save each endpoint
                for service_name, endpoints in self.services.items():
                    for endpoint in endpoints:
                        await self._save_service_to_redis(endpoint)

        except Exception as e:
            logger.error(f"Failed to save services to Redis: {e}")

    async def _save_service_to_redis(self, endpoint: ServiceEndpoint):
        """
        Save service endpoint to Redis.

        Args:
            endpoint: Service endpoint to save
        """
        try:
            import json
            async with self.redis_pool.get_client() as client:
                key = f"service:discovery:{endpoint.name}:{endpoint.host}:{endpoint.port}"
                data = {
                    "name": endpoint.name,
                    "host": endpoint.host,
                    "port": endpoint.port,
                    "protocol": endpoint.protocol,
                    "path": endpoint.path,
                    "status": endpoint.status.value,
                    "last_check": endpoint.last_check,
                    "response_time": endpoint.response_time,
                    "metadata": endpoint.metadata or {}
                }
                await client.set(key, json.dumps(data))

        except Exception as e:
            logger.error(f"Failed to save service {endpoint.name} to Redis: {e}")

    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service discovery metrics."""
        total_services = len(self.services)
        total_endpoints = sum(len(endpoints) for endpoints in self.services.values())
        healthy_endpoints = sum(
            1 for endpoints in self.services.values()
            for ep in endpoints if ep.is_healthy
        )

        return {
            "total_services": total_services,
            "total_endpoints": total_endpoints,
            "healthy_endpoints": healthy_endpoints,
            "health_rate": healthy_endpoints / max(total_endpoints, 1),
            "services": list(self.services.keys())
        }


# Global service discovery instance
_service_discovery: Optional[ServiceDiscovery] = None

async def get_service_discovery() -> ServiceDiscovery:
    """Get global service discovery instance."""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
        await _service_discovery.initialize()
    return _service_discovery

async def discover_service(name: str) -> Optional[ServiceEndpoint]:
    """Convenience function for service discovery."""
    sd = await get_service_discovery()
    return await sd.discover_service(name)

async def get_service_url(name: str, path: str = "") -> Optional[str]:
    """Convenience function for getting service URLs."""
    sd = await get_service_discovery()
    return await sd.get_service_url(name, path)
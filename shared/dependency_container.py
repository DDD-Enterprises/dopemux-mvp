"""
Dependency Injection Container for ADHD Services

Provides centralized dependency management and lifecycle control
for all ADHD services, eliminating global state and improving testability.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyContainer:
    """
    Centralized dependency injection container.

    Manages service lifecycles, dependencies, and provides clean
    injection patterns for ADHD services.
    """

    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.factories: Dict[str, Callable] = {}
        self.singletons: Dict[str, Any] = {}
        self.lifecycles: Dict[str, Callable] = {}

    async def initialize(self):
        """Initialize the dependency container."""
        logger.info("Initializing dependency container...")

        # Register core shared services
        await self._register_core_services()

        # Initialize singletons
        for name, factory in self.factories.items():
            if name in self.singletons:
                continue  # Already initialized

            try:
                instance = await factory()
                self.singletons[name] = instance
                logger.debug(f"Initialized singleton: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
                raise

        logger.info("Dependency container initialized")

    async def close(self):
        """Close the dependency container and cleanup resources."""
        logger.info("Closing dependency container...")

        # Run lifecycle cleanup in reverse order
        for name in reversed(list(self.lifecycles.keys())):
            if name in self.lifecycles:
                try:
                    cleanup_func = self.lifecycles[name]
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await cleanup_func()
                    else:
                        cleanup_func()
                    logger.debug(f"Cleaned up: {name}")
                except Exception as e:
                    logger.error(f"Error cleaning up {name}: {e}")

        # Clear all services
        self.services.clear()
        self.factories.clear()
        self.singletons.clear()
        self.lifecycles.clear()

        logger.info("Dependency container closed")

    def register_singleton(self, name: str, instance: Any):
        """
        Register a singleton instance.

        Args:
            name: Service name
            instance: Service instance
        """
        self.singletons[name] = instance
        self.services[name] = instance
        logger.debug(f"Registered singleton: {name}")

    def register_factory(self, name: str, factory: Callable, singleton: bool = True):
        """
        Register a service factory.

        Args:
            name: Service name
            factory: Factory function (async)
            singleton: Whether to create singleton instance
        """
        self.factories[name] = factory
        if singleton:
            self.singletons[name] = None  # Will be initialized later
        logger.debug(f"Registered factory: {name}")

    def register_lifecycle(self, name: str, cleanup_func: Callable):
        """
        Register a lifecycle cleanup function.

        Args:
            name: Service name
            cleanup_func: Cleanup function (sync or async)
        """
        self.lifecycles[name] = cleanup_func

    async def get_service(self, name: str) -> Any:
        """
        Get a service instance.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            KeyError: If service not found
        """
        # Check singletons first
        if name in self.singletons:
            if self.singletons[name] is None:
                # Initialize singleton
                factory = self.factories.get(name)
                if factory:
                    self.singletons[name] = await factory()
            return self.singletons[name]

        # Check factories for non-singleton services
        if name in self.factories:
            return await self.factories[name]()

        raise KeyError(f"Service not found: {name}")

    def has_service(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self.services or name in self.factories or name in self.singletons

    async def _register_core_services(self):
        """Register core shared services."""
        # Redis pool
        async def create_redis_pool():
            from .redis_pool import get_redis_pool
            return await get_redis_pool()

        self.register_factory("redis_pool", create_redis_pool)

        # Cache
        async def create_cache():
            from .cache import get_cache
            return await get_cache()

        self.register_factory("cache", create_cache)

        # Service discovery
        async def create_service_discovery():
            from .service_discovery import get_service_discovery
            return await get_service_discovery()

        self.register_factory("service_discovery", create_service_discovery)

        # Register lifecycle cleanup
        self.register_lifecycle("service_discovery", lambda: None)  # Will be handled by service itself
        self.register_lifecycle("cache", lambda: None)  # Will be handled by service itself
        self.register_lifecycle("redis_pool", lambda: None)  # Will be handled by service itself


class DependencyScope:
    """
    Dependency injection scope for request/service lifetime.

    Provides scoped service resolution with proper cleanup.
    """

    def __init__(self, container: DependencyContainer):
        self.container = container
        self.scoped_services: Dict[str, Any] = {}

    async def get_service(self, name: str) -> Any:
        """
        Get a service from this scope.

        Args:
            name: Service name

        Returns:
            Service instance
        """
        if name not in self.scoped_services:
            self.scoped_services[name] = await self.container.get_service(name)
        return self.scoped_services[name]

    async def close(self):
        """Close scoped services."""
        self.scoped_services.clear()


# Global container instance
_container: Optional[DependencyContainer] = None

async def get_container() -> DependencyContainer:
    """Get global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
        await _container.initialize()
    return _container

async def get_service(name: str) -> Any:
    """Get service from global container."""
    container = await get_container()
    return await container.get_service(name)

@asynccontextmanager
async def dependency_scope():
    """Context manager for dependency scope."""
    container = await get_container()
    scope = DependencyScope(container)
    try:
        yield scope
    finally:
        await scope.close()


# Service registration helpers

async def register_adhd_service(name: str, service_instance: Any):
    """
    Register an ADHD service instance.

    Args:
        name: Service name
        service_instance: Service instance
    """
    container = await get_container()
    container.register_singleton(name, service_instance)

async def get_adhd_service(name: str) -> Any:
    """
    Get an ADHD service instance.

    Args:
        name: Service name

    Returns:
        Service instance
    """
    return await get_service(name)
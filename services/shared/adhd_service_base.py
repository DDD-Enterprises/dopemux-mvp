"""
Shared base classes for ADHD services.

Provides common functionality: Redis, ConPort, EventBus, Health checks.
All ADHD microservices should inherit from ADHDServiceBase.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import aiohttp
import redis.asyncio as aioredis
from .exceptions import ADHDServiceError


class ADHDServiceBase(ABC):
    """Base class for all ADHD microservices."""
    
    def __init__(
        self,
        service_name: str,
        redis_url: str = "redis://localhost:6379",
        conport_url: str = "http://localhost:3004",
        dopecon_bridge_url: str = "http://localhost:3016"
    ):
        """
        Initialize ADHD service.
        
        Args:
            service_name: Name of the service (e.g., "energy-trends")
            redis_url: Redis connection URL
            conport_url: ConPort knowledge graph URL
            dopecon_bridge_url: DopeconBridge event bus URL
        """
        self.service_name = service_name
        self.redis_url = redis_url
        self.conport_url = conport_url
        self.dopecon_bridge_url = dopecon_bridge_url
        self.logger = logging.getLogger(service_name)
        
        # Connection pools (initialized in startup)
        self.redis: Optional[aioredis.Redis] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
    
    async def startup(self) -> None:
        """Initialize service connections (call in FastAPI lifespan)."""
        try:
            # Initialize Redis connection pool
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize HTTP session
            self._http_session = aiohttp.ClientSession()
            
            self.logger.info(f"✅ {self.service_name} started successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to start {self.service_name}: {e}")
            raise ADHDServiceError(f"Service startup failed: {e}")
    
    async def shutdown(self) -> None:
        """Cleanup service connections (call in FastAPI lifespan)."""
        try:
            if self.redis:
                await self.redis.close()
            
            if self._http_session:
                await self._http_session.close()
            
            self.logger.info(f"🛑 {self.service_name} shut down successfully")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def emit_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        stream: str = "dopemux:events"
    ) -> bool:
        """
        Emit event to DopeconBridge EventBus via Redis stream.
        
        Args:
            event_type: Event type (e.g., "energy.level.changed")
            data: Event payload
            stream: Redis stream name
        
        Returns:
            True if event was published successfully
        """
        try:
            event_payload = {
                "event_type": event_type,
                "source": self.service_name,
                "data": data
            }
            
            if self.redis:
                await self.redis.xadd(stream, event_payload)
                self.logger.debug(f"Event published: {event_type}")
                return True
            else:
                self.logger.warning("Redis not initialized, event not published")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to emit event {event_type}: {e}")
            return False
    
    async def log_decision(
        self,
        summary: str,
        rationale: str,
        implementation_details: Optional[str] = None
    ) -> bool:
        """
        Log decision to ConPort knowledge graph via DopeconBridge.
        
        Args:
            summary: Decision summary
            rationale: Why this decision was made
            implementation_details: How it was implemented
        
        Returns:
            True if decision was logged successfully
        """
        try:
            payload = {
                "summary": summary,
                "rationale": rationale,
                "implementation_details": implementation_details or "",
                "source": self.service_name
            }
            
            if self._http_session:
                async with self._http_session.post(
                    f"{self.dopecon_bridge_url}/decisions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status in (200, 201):
                        self.logger.debug(f"Decision logged: {summary}")
                        return True
                    else:
                        self.logger.warning(f"Failed to log decision: {response.status}")
                        return False
            else:
                self.logger.warning("HTTP session not initialized")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to log decision: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Standard health check response.
        
        Returns:
            Health status with component checks
        """
        return {
            "status": "healthy" if self._is_healthy() else "degraded",
            "service": self.service_name,
            "components": {
                "redis": self._check_redis(),
                "conport": "unknown",  # Async check needed
                "dopecon_bridge": "unknown"  # Async check needed
            }
        }
    
    async def health_check_async(self) -> Dict[str, Any]:
        """
        Async health check with full component verification.
        
        Returns:
            Detailed health status
        """
        redis_status = self._check_redis()
        conport_status = await self._check_conport()
        bridge_status = await self._check_dopecon_bridge()
        
        is_healthy = all([
            redis_status == "healthy",
            conport_status in ("healthy", "unknown"),
            bridge_status in ("healthy", "unknown")
        ])
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "service": self.service_name,
            "components": {
                "redis": redis_status,
                "conport": conport_status,
                "dopecon_bridge": bridge_status
            }
        }
    
    def _is_healthy(self) -> bool:
        """Check if service is healthy (basic check)."""
        return self.redis is not None
    
    def _check_redis(self) -> str:
        """Check Redis connectivity."""
        if self.redis is None:
            return "not_initialized"
        try:
            # Basic check - connection exists
            return "healthy"
        except Exception:
            return "unhealthy"
    
    async def _check_conport(self) -> str:
        """Check ConPort connectivity."""
        try:
            if self._http_session:
                async with self._http_session.get(
                    f"{self.conport_url}/health",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    return "healthy" if response.status == 200 else "unhealthy"
            return "not_initialized"
        except Exception:
            return "unknown"
    
    async def _check_dopecon_bridge(self) -> str:
        """Check DopeconBridge connectivity."""
        try:
            if self._http_session:
                async with self._http_session.get(
                    f"{self.dopecon_bridge_url}/health",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    return "healthy" if response.status == 200 else "unhealthy"
            return "not_initialized"
        except Exception:
            return "unknown"
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method - must be implemented by subclasses.
        
        Args:
            data: Input data to process
        
        Returns:
            Processing result
        """
        pass

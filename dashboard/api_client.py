"""
Unified API Client Infrastructure
Provides retry logic, caching, and graceful degradation for dashboard data fetching
"""

from typing import Optional, Dict, Any, List, TypeVar, Generic, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    NO_CACHE = "no_cache"
    SHORT = "short"           # 5 seconds - real-time state
    MEDIUM = "medium"         # 30 seconds - metrics
    LONG = "long"             # 5 minutes - historical data
    PERSISTENT = "persistent"  # 24 hours - static data


@dataclass
class CacheEntry(Generic[T]):
    """Cached data with metadata"""
    data: T
    cached_at: datetime
    ttl_seconds: int
    
    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.now() - self.cached_at).total_seconds()
        return age < self.ttl_seconds


@dataclass
class APIConfig:
    """Configuration for API client"""
    base_url: str
    timeout: float = 5.0
    max_retries: int = 3
    retry_delay: float = 0.5
    cache_strategy: CacheStrategy = CacheStrategy.MEDIUM
    fallback_enabled: bool = True


class APIClient:
    """
    Base API client with built-in retry, caching, and error handling
    
    Features:
    - Automatic retry with exponential backoff
    - Response caching with TTL
    - Graceful fallback to cached/default data
    - Request deduplication (prevent duplicate in-flight requests)
    - Comprehensive error logging
    
    Example:
        >>> config = APIConfig(base_url="http://localhost:8000")
        >>> client = APIClient(config)
        >>> data = await client.get("/api/v1/status")
    """
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            follow_redirects=True
        )
        self._cache: Dict[str, CacheEntry] = {}
        self._in_flight: Dict[str, asyncio.Task] = {}
        
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        fallback_data: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute GET request with retry and caching
        
        Args:
            endpoint: API endpoint (e.g., '/api/v1/energy-level/user123')
            params: Query parameters
            cache_key: Key for caching (default: endpoint)
            fallback_data: Data to return if all retries fail
            
        Returns:
            Response data or fallback_data or None
        """
        cache_key = cache_key or endpoint
        
        # Check cache first
        if cached := self._get_from_cache(cache_key):
            logger.debug(f"Cache hit: {cache_key}")
            return cached
        
        # Check if request already in flight (deduplication)
        if cache_key in self._in_flight:
            logger.debug(f"Request already in flight: {cache_key}")
            try:
                return await self._in_flight[cache_key]
            except Exception as e:
                logger.error(f"In-flight request failed: {e}")
                return fallback_data
        
        # Create new request task
        task = asyncio.create_task(
            self._execute_with_retry(endpoint, params, fallback_data)
        )
        self._in_flight[cache_key] = task
        
        try:
            result = await task
            if result is not None:
                self._store_in_cache(cache_key, result)
            return result
        finally:
            self._in_flight.pop(cache_key, None)
    
    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        fallback_data: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute POST request with retry (no caching)
        
        Args:
            endpoint: API endpoint
            json_data: JSON body
            fallback_data: Data to return if all retries fail
            
        Returns:
            Response data or fallback_data or None
        """
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post(url, json=json_data)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Endpoint not found: {url}")
                    return fallback_data
                else:
                    logger.warning(
                        f"POST attempt {attempt + 1}/{self.config.max_retries} "
                        f"failed with status {response.status_code}"
                    )
            except httpx.TimeoutException:
                logger.warning(
                    f"POST attempt {attempt + 1}/{self.config.max_retries} "
                    f"timed out for {url}"
                )
            except Exception as e:
                logger.error(
                    f"POST attempt {attempt + 1}/{self.config.max_retries} "
                    f"failed with error: {e}"
                )
            
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        # All retries failed
        if self.config.fallback_enabled:
            logger.error(
                f"All POST retries failed for {url}, returning fallback data"
            )
            return fallback_data
        
        return None
    
    async def _execute_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        fallback_data: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute request with exponential backoff retry"""
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Endpoint not found: {url}")
                    return fallback_data
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries} "
                        f"failed with status {response.status_code}"
                    )
            except httpx.TimeoutException:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries} "
                    f"timed out for {url}"
                )
            except Exception as e:
                logger.error(
                    f"Attempt {attempt + 1}/{self.config.max_retries} "
                    f"failed with error: {e}"
                )
            
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        # All retries failed
        if self.config.fallback_enabled:
            logger.error(
                f"All retries failed for {url}, returning fallback data"
            )
            return fallback_data
        
        return None
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry.is_valid():
            return entry.data
        
        # Expired, remove from cache
        del self._cache[key]
        return None
    
    def _store_in_cache(self, key: str, data: Any) -> None:
        """Store data in cache with TTL"""
        ttl_map = {
            CacheStrategy.SHORT: 5,
            CacheStrategy.MEDIUM: 30,
            CacheStrategy.LONG: 300,
            CacheStrategy.PERSISTENT: 86400,  # 24 hours
        }
        
        ttl = ttl_map.get(self.config.cache_strategy, 30)
        
        self._cache[key] = CacheEntry(
            data=data,
            cached_at=datetime.now(),
            ttl_seconds=ttl
        )
    
    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry or all cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            if hasattr(self, 'client'):
                asyncio.get_event_loop().create_task(self.client.aclose())
        except Exception:
            pass

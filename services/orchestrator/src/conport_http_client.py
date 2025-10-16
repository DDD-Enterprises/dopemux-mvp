"""
ConPort HTTP Client - Production-Ready Integration Bridge Client

Async HTTP client with ADHD optimizations:
- 5-second fast-fail timeout (no waiting)
- Circuit breaker with JSON fallback (silent degradation)
- Connection pooling and retry logic
- Clean error handling with visual feedback
"""

import httpx
import asyncio
import json
import threading
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking."""
    failures: int = 0
    last_failure: Optional[datetime] = None
    is_open: bool = False
    half_open_test_time: Optional[datetime] = None


class ConPortHTTPClient:
    """
    Production HTTP client for ConPort Integration Bridge.

    Features:
    - Async httpx with connection pooling
    - 5s ADHD timeout (connect + read combined)
    - Circuit breaker (3 failures → fallback for 30s)
    - JSON file fallback for degraded mode
    - Automatic retry for transient failures
    """

    def __init__(
        self,
        workspace_id: str,
        bridge_url: Optional[str] = None,
        fallback_dir: Optional[Path] = None
    ):
        """
        Initialize HTTP client.

        Args:
            workspace_id: Absolute path to workspace
            bridge_url: Integration Bridge URL (default: http://localhost:3016)
            fallback_dir: Directory for JSON fallback (default: /tmp/dopemux_fallback)
        """
        self.workspace_id = workspace_id
        self.bridge_url = bridge_url or "http://localhost:3016"
        self.fallback_dir = fallback_dir or Path("/tmp/dopemux_fallback")
        self.fallback_dir.mkdir(parents=True, exist_ok=True)

        # Circuit breaker state
        self.circuit = CircuitBreakerState()
        self.failure_threshold = 3  # Open circuit after 3 failures
        self.half_open_wait = timedelta(seconds=30)  # Wait 30s before retry

        # Create async HTTP client with ADHD-optimized settings
        self.client = self._create_client()

    def _create_client(self) -> httpx.AsyncClient:
        """Create httpx client with production settings."""
        # ADHD timeout: 5s total (connect + read)
        timeout = httpx.Timeout(
            connect=2.0,  # 2s to establish connection
            read=3.0,     # 3s to read response
            write=2.0,    # 2s to write request
            pool=1.0      # 1s to get connection from pool
        )

        # Connection pooling
        limits = httpx.Limits(
            max_keepalive_connections=5,  # Keep 5 connections alive
            max_connections=10            # Max 10 total
        )

        # Retry transport (auto-retry on connection errors)
        transport = httpx.AsyncHTTPTransport(
            retries=1  # Retry once on connection failures
        )

        return httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            transport=transport,
            follow_redirects=True
        )

    async def _check_circuit(self) -> bool:
        """
        Check if circuit breaker allows request.

        Returns:
            True if request allowed, False if circuit open
        """
        if not self.circuit.is_open:
            return True

        # Check if we should test half-open state
        if self.circuit.half_open_test_time and datetime.now() >= self.circuit.half_open_test_time:
            logger.info("Circuit breaker: Testing half-open state")
            self.circuit.is_open = False
            self.circuit.failures = 0
            return True

        return False

    def _record_success(self):
        """Record successful request (reset circuit breaker)."""
        if self.circuit.failures > 0:
            logger.info(f"Circuit breaker: Success after {self.circuit.failures} failures")
        self.circuit.failures = 0
        self.circuit.is_open = False
        self.circuit.last_failure = None
        self.circuit.half_open_test_time = None

    def _record_failure(self):
        """Record failed request (update circuit breaker)."""
        self.circuit.failures += 1
        self.circuit.last_failure = datetime.now()

        if self.circuit.failures >= self.failure_threshold:
            self.circuit.is_open = True
            self.circuit.half_open_test_time = datetime.now() + self.half_open_wait
            logger.warning(
                f"Circuit breaker OPEN: {self.circuit.failures} failures. "
                f"Will retry at {self.circuit.half_open_test_time.strftime('%H:%M:%S')}"
            )

    async def _fallback_save(self, category: str, key: str, value: dict) -> Path:
        """Save to JSON fallback."""
        file_path = self.fallback_dir / f"{category}_{key}.json"
        data = {
            "workspace_id": self.workspace_id,
            "category": category,
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        file_path.write_text(json.dumps(data, indent=2))
        return file_path

    async def _fallback_load(self, category: str, key: Optional[str] = None) -> List[dict]:
        """Load from JSON fallback."""
        pattern = f"{category}_*.json" if key is None else f"{category}_{key}.json"
        files = list(self.fallback_dir.glob(pattern))

        results = []
        for file_path in sorted(files, reverse=True):
            try:
                data = json.loads(file_path.read_text())
                results.append(data)
            except Exception as e:
                logger.warning(f"Failed to load fallback {file_path}: {e}")

        return results

    async def log_custom_data(
        self,
        category: str,
        key: str,
        value: dict
    ) -> Dict[str, Any]:
        """
        Save custom data to ConPort (with fallback).

        Args:
            category: Data category (e.g., "adhd_checkpoints")
            key: Unique key within category
            value: JSON-serializable data

        Returns:
            Result dict with success status
        """
        # Check circuit breaker
        if not await self._check_circuit():
            logger.info(f"Circuit breaker open, using fallback for {category}/{key}")
            fallback_path = await self._fallback_save(category, key, value)
            return {
                "success": True,
                "mode": "fallback",
                "path": str(fallback_path),
                "circuit_open": True
            }

        # Try HTTP request
        try:
            response = await self.client.post(
                f"{self.bridge_url}/conport/custom_data",
                json={
                    "workspace_id": self.workspace_id,
                    "category": category,
                    "key": key,
                    "value": value
                },
                headers={"X-Source-Plane": "cognitive_plane"}
            )
            response.raise_for_status()

            self._record_success()
            return {
                "success": True,
                "mode": "http",
                "response": response.json()
            }

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            logger.warning(f"HTTP request failed: {e}, using fallback")

            # Silent degradation: save to fallback
            fallback_path = await self._fallback_save(category, key, value)
            return {
                "success": True,  # Still success from user perspective
                "mode": "fallback",
                "path": str(fallback_path),
                "error": str(e)
            }

    async def get_custom_data(
        self,
        category: str,
        key: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """
        Retrieve custom data from ConPort (with fallback).

        Args:
            category: Data category
            key: Specific key (optional)
            limit: Max results

        Returns:
            List of custom data entries
        """
        # Check circuit breaker
        if not await self._check_circuit():
            logger.info(f"Circuit breaker open, using fallback for query {category}/{key}")
            return await self._fallback_load(category, key)

        # Try HTTP request
        try:
            params = {
                "workspace_id": self.workspace_id,
                "category": category,
                "limit": limit
            }
            if key:
                params["key"] = key

            response = await self.client.get(
                f"{self.bridge_url}/conport/custom_data",
                params=params,
                headers={"X-Source-Plane": "cognitive_plane"}
            )
            response.raise_for_status()

            self._record_success()
            return response.json().get("data", [])

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            logger.warning(f"HTTP request failed: {e}, using fallback")
            return await self._fallback_load(category, key)

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filter_types: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Semantic search across ConPort data.

        Args:
            query: Natural language query
            top_k: Number of results
            filter_types: Filter by item types

        Returns:
            Search results
        """
        # Check circuit breaker
        if not await self._check_circuit():
            logger.info("Circuit breaker open, semantic search unavailable")
            return []

        # Try HTTP request
        try:
            response = await self.client.post(
                f"{self.bridge_url}/conport/semantic_search",
                json={
                    "workspace_id": self.workspace_id,
                    "query_text": query,
                    "top_k": top_k,
                    "filter_item_types": filter_types or []
                },
                headers={"X-Source-Plane": "cognitive_plane"}
            )
            response.raise_for_status()

            self._record_success()
            return response.json().get("results", [])

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            logger.warning(f"Semantic search failed: {e}")
            return []

    async def log_decision(
        self,
        summary: str,
        rationale: str,
        implementation_details: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """
        Log architectural decision to ConPort.

        Args:
            summary: Decision summary
            rationale: Why this decision
            implementation_details: How to implement
            tags: Categorization tags

        Returns:
            Decision record
        """
        # Check circuit breaker
        if not await self._check_circuit():
            logger.info("Circuit breaker open, decision logging unavailable")
            return {"success": False, "error": "circuit_open"}

        # Try HTTP request
        try:
            response = await self.client.post(
                f"{self.bridge_url}/conport/decision",
                json={
                    "workspace_id": self.workspace_id,
                    "summary": summary,
                    "rationale": rationale,
                    "implementation_details": implementation_details,
                    "tags": tags
                },
                headers={"X-Source-Plane": "cognitive_plane"}
            )
            response.raise_for_status()

            self._record_success()
            return {
                "success": True,
                "mode": "http",
                "response": response.json()
            }

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            logger.warning(f"Decision logging failed: {e}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Integration Bridge health.

        Returns:
            Health status
        """
        try:
            response = await self.client.get(
                f"{self.bridge_url}/health",
                timeout=2.0  # Quick health check
            )
            response.raise_for_status()

            self._record_success()
            return {
                "healthy": True,
                "response": response.json()
            }

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            return {
                "healthy": False,
                "error": str(e),
                "circuit_failures": self.circuit.failures,
                "circuit_open": self.circuit.is_open
            }

    async def close(self):
        """Close HTTP client and cleanup."""
        await self.client.aclose()
        logger.info("ConPort HTTP client closed")


# Async context manager support
class ConPortHTTPClientContext:
    """Context manager for ConPortHTTPClient."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.client = None

    async def __aenter__(self):
        self.client = ConPortHTTPClient(*self.args, **self.kwargs)
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()


# Singleton for easy access (with thread safety)
_http_client: Optional[ConPortHTTPClient] = None
_http_client_lock = threading.Lock()


def get_http_client(workspace_id: str) -> ConPortHTTPClient:
    """
    Get singleton HTTP client (async version).

    Thread-safe implementation using double-checked locking pattern.
    """
    global _http_client

    # First check (no lock - fast path)
    if _http_client is not None and _http_client.workspace_id == workspace_id:
        return _http_client

    # Acquire lock for initialization
    with _http_client_lock:
        # Second check (with lock - ensure only one thread creates instance)
        if _http_client is None or _http_client.workspace_id != workspace_id:
            _http_client = ConPortHTTPClient(workspace_id)

    return _http_client


class ConPortHTTPClientSync:
    """
    Synchronous HTTP client for ConPort Integration Bridge.

    Use this for threading-based code (like checkpoint_manager.py).
    Same features as async version but with blocking calls.
    """

    def __init__(
        self,
        workspace_id: str,
        bridge_url: Optional[str] = None,
        fallback_dir: Optional[Path] = None
    ):
        """Initialize sync HTTP client."""
        self.workspace_id = workspace_id
        self.bridge_url = bridge_url or "http://localhost:3016"
        self.fallback_dir = fallback_dir or Path("/tmp/dopemux_fallback")
        self.fallback_dir.mkdir(parents=True, exist_ok=True)

        # Circuit breaker state
        self.circuit = CircuitBreakerState()
        self.failure_threshold = 3
        self.half_open_wait = timedelta(seconds=30)

        # Create sync HTTP client
        self.client = self._create_client()

    def _create_client(self) -> httpx.Client:
        """Create sync httpx client."""
        timeout = httpx.Timeout(
            connect=2.0,
            read=3.0,
            write=2.0,
            pool=1.0
        )

        limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10
        )

        transport = httpx.HTTPTransport(retries=1)

        return httpx.Client(
            timeout=timeout,
            limits=limits,
            transport=transport,
            follow_redirects=True
        )

    def _check_circuit(self) -> bool:
        """Check if circuit breaker allows request."""
        if not self.circuit.is_open:
            return True

        if self.circuit.half_open_test_time and datetime.now() >= self.circuit.half_open_test_time:
            logger.info("Circuit breaker: Testing half-open state")
            self.circuit.is_open = False
            self.circuit.failures = 0
            return True

        return False

    def _record_success(self):
        """Record successful request."""
        if self.circuit.failures > 0:
            logger.info(f"Circuit breaker: Success after {self.circuit.failures} failures")
        self.circuit.failures = 0
        self.circuit.is_open = False
        self.circuit.last_failure = None
        self.circuit.half_open_test_time = None

    def _record_failure(self):
        """Record failed request."""
        self.circuit.failures += 1
        self.circuit.last_failure = datetime.now()

        if self.circuit.failures >= self.failure_threshold:
            self.circuit.is_open = True
            self.circuit.half_open_test_time = datetime.now() + self.half_open_wait
            logger.warning(
                f"Circuit breaker OPEN: {self.circuit.failures} failures. "
                f"Will retry at {self.circuit.half_open_test_time.strftime('%H:%M:%S')}"
            )

    def _fallback_save(self, category: str, key: str, value: dict) -> Path:
        """Save to JSON fallback (sync)."""
        file_path = self.fallback_dir / f"{category}_{key}.json"
        data = {
            "workspace_id": self.workspace_id,
            "category": category,
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        file_path.write_text(json.dumps(data, indent=2))
        return file_path

    def _fallback_load(self, category: str, key: Optional[str] = None) -> List[dict]:
        """Load from JSON fallback (sync)."""
        pattern = f"{category}_*.json" if key is None else f"{category}_{key}.json"
        files = list(self.fallback_dir.glob(pattern))

        results = []
        for file_path in sorted(files, reverse=True):
            try:
                data = json.loads(file_path.read_text())
                results.append(data)
            except Exception as e:
                logger.warning(f"Failed to load fallback {file_path}: {e}")

        return results

    def log_custom_data(
        self,
        category: str,
        key: str,
        value: dict
    ) -> Dict[str, Any]:
        """Save custom data (sync)."""
        if not self._check_circuit():
            logger.info(f"Circuit breaker open, using fallback for {category}/{key}")
            fallback_path = self._fallback_save(category, key, value)
            return {
                "success": True,
                "mode": "fallback",
                "path": str(fallback_path),
                "circuit_open": True
            }

        try:
            response = self.client.post(
                f"{self.bridge_url}/conport/custom_data",
                json={
                    "workspace_id": self.workspace_id,
                    "category": category,
                    "key": key,
                    "value": value
                },
                headers={"X-Source-Plane": "cognitive_plane"}
            )
            response.raise_for_status()

            self._record_success()
            return {
                "success": True,
                "mode": "http",
                "response": response.json()
            }

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            logger.warning(f"HTTP request failed: {e}, using fallback")

            fallback_path = self._fallback_save(category, key, value)
            return {
                "success": True,
                "mode": "fallback",
                "path": str(fallback_path),
                "error": str(e)
            }

    def get_custom_data(
        self,
        category: str,
        key: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """Retrieve custom data (sync)."""
        if not self._check_circuit():
            logger.info(f"Circuit breaker open, using fallback for query {category}/{key}")
            return self._fallback_load(category, key)

        try:
            params = {
                "workspace_id": self.workspace_id,
                "category": category,
                "limit": limit
            }
            if key:
                params["key"] = key

            response = self.client.get(
                f"{self.bridge_url}/conport/custom_data",
                params=params,
                headers={"X-Source-Plane": "cognitive_plane"}
            )
            response.raise_for_status()

            self._record_success()
            return response.json().get("data", [])

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            logger.warning(f"HTTP request failed: {e}, using fallback")
            return self._fallback_load(category, key)

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filter_types: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Semantic search across ConPort data (sync).

        Args:
            query: Natural language query
            top_k: Number of results
            filter_types: Filter by item types

        Returns:
            Search results
        """
        if not self._check_circuit():
            logger.info("Circuit breaker open, semantic search unavailable")
            return []

        try:
            response = self.client.post(
                f"{self.bridge_url}/conport/semantic_search",
                json={
                    "workspace_id": self.workspace_id,
                    "query_text": query,
                    "top_k": top_k,
                    "filter_item_types": filter_types or []
                },
                headers={"X-Source-Plane": "cognitive_plane"}
            )
            response.raise_for_status()

            self._record_success()
            return response.json().get("results", [])

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            self._record_failure()
            logger.warning(f"Semantic search failed: {e}")
            return []

    def close(self):
        """Close HTTP client."""
        self.client.close()
        logger.info("ConPort HTTP client closed")


# Singleton for sync client (with thread safety)
_sync_client: Optional[ConPortHTTPClientSync] = None
_sync_client_lock = threading.Lock()


def get_sync_http_client(workspace_id: str) -> ConPortHTTPClientSync:
    """
    Get singleton sync HTTP client (for threading code).

    Thread-safe implementation using double-checked locking pattern.
    """
    global _sync_client

    # First check (no lock - fast path)
    if _sync_client is not None and _sync_client.workspace_id == workspace_id:
        return _sync_client

    # Acquire lock for initialization
    with _sync_client_lock:
        # Second check (with lock - ensure only one thread creates instance)
        if _sync_client is None or _sync_client.workspace_id != workspace_id:
            _sync_client = ConPortHTTPClientSync(workspace_id)

    return _sync_client


if __name__ == "__main__":
    """Test HTTP client (both sync and async)."""

    print("Testing Sync ConPort HTTP Client:")
    print("=" * 60)

    client = ConPortHTTPClientSync("/Users/hue/code/dopemux-mvp")

    try:
        # Test saving
        print("\n1. Saving custom data...")
        result = client.log_custom_data(
            category="test_sync",
            key=f"test_{datetime.now().timestamp()}",
            value={"message": "Hello from sync client!", "timestamp": datetime.now().isoformat()}
        )
        print(f"   Mode: {result['mode']}, Success: {result['success']}")

        # Test querying
        print("\n2. Querying custom data...")
        results = client.get_custom_data(category="test_sync", limit=5)
        print(f"   Found: {len(results)} items")

        print("\n✅ Sync HTTP client test complete")
        print(f"   Circuit breaker failures: {client.circuit.failures}")
        print(f"   Circuit breaker open: {client.circuit.is_open}")

    finally:
        client.close()

    print("\n" + "=" * 60)
    print("Testing Async ConPort HTTP Client:")
    print("=" * 60)

    async def test_async():
        async with ConPortHTTPClientContext("/Users/hue/code/dopemux-mvp") as client:
            # Test saving
            print("\n1. Saving custom data...")
            result = await client.log_custom_data(
                category="test_async",
                key=f"test_{datetime.now().timestamp()}",
                value={"message": "Hello from async client!", "timestamp": datetime.now().isoformat()}
            )
            print(f"   Mode: {result['mode']}, Success: {result['success']}")

            # Test querying
            print("\n2. Querying custom data...")
            results = await client.get_custom_data(category="test_async", limit=5)
            print(f"   Found: {len(results)} items")

            print("\n✅ Async HTTP client test complete")
            print(f"   Circuit breaker failures: {client.circuit.failures}")
            print(f"   Circuit breaker open: {client.circuit.is_open}")

    asyncio.run(test_async())

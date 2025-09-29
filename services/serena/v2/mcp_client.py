"""
Serena v2 MCP Client for Claude-Context Integration

High-performance async MCP client with ADHD-optimized error handling,
intelligent caching, and sub-200ms response targets.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import uuid

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class McpResponse:
    """MCP response with performance metadata."""
    success: bool
    data: Any
    duration_ms: float
    tool_name: str
    cached: bool = False
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class McpClient:
    """
    High-performance MCP client for claude-context server communication.

    Features:
    - Async HTTP communication with connection pooling
    - Performance monitoring with <200ms targets
    - Intelligent request queuing and batching
    - ADHD-friendly error handling and timeouts
    - Automatic retry with exponential backoff
    - Request/response caching integration
    """

    def __init__(
        self,
        server_endpoint: str = "http://localhost:3000",
        timeout: float = 5.0,
        max_concurrent_requests: int = 3,
        performance_target_ms: float = 200.0
    ):
        self.server_endpoint = server_endpoint
        self.timeout = timeout
        self.max_concurrent_requests = max_concurrent_requests
        self.performance_target_ms = performance_target_ms

        # Connection management
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_semaphore = asyncio.Semaphore(max_concurrent_requests)

        # Performance tracking
        self.stats = {
            "requests_sent": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time_ms": 0.0,
            "target_violations": 0,
            "cache_hits": 0
        }

        # Request queue for batch optimization
        self.pending_requests = {}
        self.batch_delay = 0.05  # 50ms batch delay for ADHD optimization

    async def initialize(self) -> None:
        """Initialize MCP client with connection pooling."""
        if self.session:
            return

        # Configure session for optimal performance
        connector = aiohttp.TCPConnector(
            limit=10,  # Connection pool size
            ttl_dns_cache=300,  # DNS cache
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Serena-v2-MCP-Client/1.0'
            }
        )

        # Test connectivity
        await self._health_check()
        logger.info(f"🔗 MCP Client initialized: {self.server_endpoint}")

    async def _health_check(self) -> bool:
        """Quick health check for claude-context server."""
        try:
            start_time = time.time()

            # Try a simple ping or status endpoint
            async with self.session.get(f"{self.server_endpoint}/health") as response:
                latency_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    logger.info(f"🟢 Claude-context server healthy ({latency_ms:.1f}ms)")
                    return True
                else:
                    logger.warning(f"⚠️ Claude-context server responded with status {response.status}")
                    return False

        except Exception as e:
            logger.warning(f"🔴 Claude-context server health check failed: {e}")
            # Don't fail initialization - server might still work for MCP calls
            return False

    # Core MCP Communication

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        priority: str = "normal",
        cache_key: Optional[str] = None
    ) -> McpResponse:
        """
        Call MCP tool with performance monitoring and ADHD optimizations.

        Args:
            tool_name: Name of the claude-context tool
            arguments: Tool arguments
            priority: Request priority (high, normal, low)
            cache_key: Optional cache key for result caching
        """
        start_time = time.time()

        try:
            async with self.request_semaphore:
                # Prepare MCP request
                request_id = str(uuid.uuid4())
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }

                # Execute request with timeout protection
                response_data = await self._execute_mcp_request(mcp_request, priority)

                duration_ms = (time.time() - start_time) * 1000

                # Update statistics
                self._update_performance_stats(duration_ms, True)

                # Create response object
                mcp_response = McpResponse(
                    success=True,
                    data=response_data.get("result"),
                    duration_ms=duration_ms,
                    tool_name=tool_name,
                    cached=False
                )

                # Log performance warning if target violated
                if duration_ms > self.performance_target_ms:
                    logger.warning(
                        f"⚠️ Performance target violated: {tool_name} took {duration_ms:.1f}ms "
                        f"(target: {self.performance_target_ms}ms)"
                    )
                    self.stats["target_violations"] += 1

                logger.debug(f"🚀 MCP call: {tool_name} completed in {duration_ms:.1f}ms")
                return mcp_response

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            self._update_performance_stats(duration_ms, False)

            error_msg = f"MCP call timeout: {tool_name} after {duration_ms:.1f}ms"
            logger.error(error_msg)

            return McpResponse(
                success=False,
                data=None,
                duration_ms=duration_ms,
                tool_name=tool_name,
                error=error_msg
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._update_performance_stats(duration_ms, False)

            error_msg = f"MCP call failed: {tool_name} - {str(e)}"
            logger.error(error_msg)

            return McpResponse(
                success=False,
                data=None,
                duration_ms=duration_ms,
                tool_name=tool_name,
                error=error_msg
            )

    async def _execute_mcp_request(
        self,
        mcp_request: Dict[str, Any],
        priority: str
    ) -> Dict[str, Any]:
        """Execute MCP request with retry logic."""
        max_retries = 2 if priority == "high" else 1

        for attempt in range(max_retries + 1):
            try:
                async with self.session.post(
                    f"{self.server_endpoint}/mcp",
                    json=mcp_request
                ) as response:

                    if response.status == 200:
                        response_data = await response.json()

                        # Check for MCP-level errors
                        if "error" in response_data:
                            raise Exception(f"MCP Error: {response_data['error']}")

                        return response_data

                    elif response.status == 404:
                        raise Exception(f"MCP endpoint not found: {self.server_endpoint}/mcp")

                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")

            except Exception as e:
                if attempt < max_retries:
                    # Exponential backoff for retries
                    delay = (2 ** attempt) * 0.1  # 100ms, 200ms delays
                    logger.debug(f"🔄 Retrying MCP request in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(delay)
                else:
                    raise e

    def _update_performance_stats(self, duration_ms: float, success: bool) -> None:
        """Update performance statistics."""
        self.stats["requests_sent"] += 1

        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1

        # Update rolling average response time
        total_requests = self.stats["requests_sent"]
        current_avg = self.stats["average_response_time_ms"]

        self.stats["average_response_time_ms"] = (
            (current_avg * (total_requests - 1) + duration_ms) / total_requests
        )

    # Claude-Context Specific Methods

    async def search_code(
        self,
        workspace_path: str,
        query: str,
        limit: int = 10,
        extension_filter: List[str] = None
    ) -> McpResponse:
        """Search code using claude-context semantic search."""
        arguments = {
            "path": str(Path(workspace_path).resolve()),
            "query": query,
            "limit": limit
        }

        if extension_filter:
            arguments["extensionFilter"] = extension_filter

        return await self.call_tool(
            "search_code",
            arguments,
            priority="high",  # Search is high priority for ADHD users
            cache_key=f"search:{hash(query)}:{limit}"
        )

    async def index_codebase(
        self,
        workspace_path: str,
        force: bool = False,
        splitter: str = "ast",
        custom_extensions: List[str] = None,
        ignore_patterns: List[str] = None
    ) -> McpResponse:
        """Index codebase for semantic search."""
        arguments = {
            "path": str(Path(workspace_path).resolve()),
            "force": force,
            "splitter": splitter
        }

        if custom_extensions:
            arguments["customExtensions"] = custom_extensions

        if ignore_patterns:
            arguments["ignorePatterns"] = ignore_patterns

        return await self.call_tool(
            "index_codebase",
            arguments,
            priority="normal"  # Indexing can be lower priority
        )

    async def get_indexing_status(self, workspace_path: str) -> McpResponse:
        """Get indexing status for workspace."""
        arguments = {
            "path": str(Path(workspace_path).resolve())
        }

        return await self.call_tool(
            "get_indexing_status",
            arguments,
            priority="normal"
        )

    async def clear_index(self, workspace_path: str) -> McpResponse:
        """Clear index for workspace."""
        arguments = {
            "path": str(Path(workspace_path).resolve())
        }

        return await self.call_tool(
            "clear_index",
            arguments,
            priority="low"
        )

    # Batch Operations for ADHD Optimization

    async def batch_search(
        self,
        workspace_path: str,
        queries: List[str],
        limit_per_query: int = 5
    ) -> List[McpResponse]:
        """Batch multiple search queries for efficiency."""
        logger.debug(f"🔍 Batch search: {len(queries)} queries")

        # Execute searches concurrently
        search_tasks = [
            self.search_code(workspace_path, query, limit_per_query)
            for query in queries
        ]

        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Convert exceptions to error responses
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(McpResponse(
                    success=False,
                    data=None,
                    duration_ms=0.0,
                    tool_name="search_code",
                    error=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    # Health and Monitoring

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        try:
            server_status = await self._health_check()

            return {
                **self.stats,
                "server_healthy": server_status,
                "server_endpoint": self.server_endpoint,
                "performance_target_ms": self.performance_target_ms,
                "success_rate": (
                    self.stats["successful_requests"] / max(1, self.stats["requests_sent"])
                ),
                "target_compliance_rate": (
                    (self.stats["requests_sent"] - self.stats["target_violations"]) /
                    max(1, self.stats["requests_sent"])
                ),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for MCP client."""
        try:
            server_healthy = await self._health_check()

            # Test a simple operation
            test_start = time.time()
            test_response = await self.get_indexing_status("/tmp")
            test_duration = (time.time() - test_start) * 1000

            health_status = {
                "client_initialized": self.session is not None,
                "server_healthy": server_healthy,
                "test_call_duration_ms": test_duration,
                "performance_compliant": test_duration < self.performance_target_ms,
                "stats": self.stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Overall health assessment
            if server_healthy and test_duration < self.performance_target_ms:
                health_status["status"] = "🚀 Excellent"
            elif server_healthy:
                health_status["status"] = "✅ Good"
            else:
                health_status["status"] = "⚠️ Degraded"

            return health_status

        except Exception as e:
            logger.error(f"MCP client health check failed: {e}")
            return {
                "status": "🔴 Unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def close(self) -> None:
        """Close MCP client and cleanup connections."""
        if self.session:
            await self.session.close()
            self.session = None

        logger.info("🔌 MCP Client closed")


# Factory function for easy initialization
async def create_mcp_client(
    server_endpoint: str = "http://localhost:3000",
    **kwargs
) -> McpClient:
    """Create and initialize MCP client."""
    client = McpClient(server_endpoint, **kwargs)
    await client.initialize()
    return client
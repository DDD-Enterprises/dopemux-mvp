"""
MCP Parallel Executor for Dopemux

Provides parallel execution of MCP (Model Context Protocol) tool calls and file operations
to improve efficiency and reduce latency in ADHD-optimized development workflows.

Key Features:
- asyncio.gather for concurrent MCP calls
- Semaphore-based rate limiting to respect server constraints
- Error isolation with return_exceptions=True
- Integration with ConPort for execution logging
- Backward compatibility with existing sequential patterns
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class MCPParallelExecutor:
    """
    Executor for parallel MCP tool calls with rate limiting and error handling.

    Designed for ADHD-optimized workflows by reducing wait times and providing
    progress feedback while maintaining system stability.
    """

    def __init__(self, max_concurrent: int = 5, timeout: float = 30.0):
        """
        Initialize the parallel executor.

        Args:
            max_concurrent: Maximum concurrent MCP calls (default 5 to respect server limits)
            timeout: Timeout per individual call in seconds
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._active_calls = 0

    @asynccontextmanager
    async def _rate_limit(self):
        """Context manager for rate limiting MCP calls."""
        async with self.semaphore:
            self._active_calls += 1
            try:
                yield
            finally:
                self._active_calls -= 1

    async def _execute_single_call(
        self,
        mcp_client: Any,
        method_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a single MCP call with timeout and error handling.

        Args:
            mcp_client: The MCP client instance (e.g., ConPortMCPClient)
            method_name: Name of the method to call (e.g., 'log_progress')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result of the MCP call or Exception if failed
        """
        async with self._rate_limit():
            try:
                method = getattr(mcp_client, method_name)
                if not asyncio.iscoroutinefunction(method):
                    # Handle sync methods by running in thread pool
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, method, *args, **kwargs),
                        timeout=self.timeout
                    )
                else:
                    # Handle async methods directly
                    result = await asyncio.wait_for(
                        method(*args, **kwargs),
                        timeout=self.timeout
                    )
                logger.debug(f"MCP call {method_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"MCP call {method_name} failed: {e}")
                return e

    async def execute_batch(
        self,
        mcp_client: Any,
        calls: List[Dict[str, Any]],
        return_exceptions: bool = True
    ) -> List[Any]:
        """
        Execute a batch of MCP calls in parallel.

        Args:
            mcp_client: The MCP client instance
            calls: List of call specifications, each dict with:
                - 'method': method name (str)
                - 'args': positional args (list, optional)
                - 'kwargs': keyword args (dict, optional)
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            List of results in the same order as calls. Failed calls return Exception objects
            if return_exceptions=True, otherwise raises the first exception.

        Example:
            calls = [
                {'method': 'log_progress', 'kwargs': {'status': 'DONE', 'description': 'Task 1'}},
                {'method': 'update_progress', 'kwargs': {'progress_id': 123, 'status': 'IN_PROGRESS'}}
            ]
            results = await executor.execute_batch(conport_client, calls)
        """
        if not calls:
            return []

        logger.info(f"Executing batch of {len(calls)} MCP calls with max {self.max_concurrent} concurrent")

        # Create coroutines for each call
        coros = []
        for call_spec in calls:
            method_name = call_spec['method']
            args = call_spec.get('args', [])
            kwargs = call_spec.get('kwargs', {})

            coro = self._execute_single_call(mcp_client, method_name, *args, **kwargs)
            coros.append(coro)

        # Execute all calls concurrently
        results = await asyncio.gather(*coros, return_exceptions=return_exceptions)

        # Log batch completion
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        logger.info(f"Batch completed: {successful} successful, {failed} failed")

        if not return_exceptions and failed > 0:
            # Find first exception and raise it
            for result in results:
                if isinstance(result, Exception):
                    raise result

        return results

    async def execute_homogeneous_batch(
        self,
        mcp_client: Any,
        method_name: str,
        call_specs: List[Dict[str, Any]],
        return_exceptions: bool = True
    ) -> List[Any]:
        """
        Execute multiple calls to the same MCP method with different parameters.

        This is a convenience method for common patterns like batch logging progress entries.

        Args:
            mcp_client: The MCP client instance
            method_name: The method name to call on all items
            call_specs: List of parameter dicts for each call
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            List of results, one per call_spec

        Example:
            # Batch log multiple progress entries
            progress_specs = [
                {'status': 'DONE', 'description': 'Feature A complete'},
                {'status': 'IN_PROGRESS', 'description': 'Feature B in progress'}
            ]
            results = await executor.execute_homogeneous_batch(
                conport_client, 'log_progress', progress_specs
            )
        """
        calls = [
            {'method': method_name, 'kwargs': spec}
            for spec in call_specs
        ]
        return await self.execute_batch(mcp_client, calls, return_exceptions)

    def get_active_call_count(self) -> int:
        """Get the current number of active MCP calls."""
        return self._active_calls

    def is_available(self) -> bool:
        """Check if the executor can accept new calls (not at max concurrency)."""
        return self._active_calls < self.max_concurrent

    async def wait_for_availability(self) -> None:
        """Wait until at least one slot is available for new calls."""
        while not self.is_available():
            await asyncio.sleep(0.1)  # Small delay to avoid busy waiting


# Convenience functions for common Dopemux patterns
async def batch_log_progress(
    conport_client: Any,
    progress_entries: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Any]:
    """
    Batch log multiple progress entries to ConPort.

    Args:
        conport_client: ConPortMCPClient instance
        progress_entries: List of progress entry dicts
        max_concurrent: Max concurrent calls

    Returns:
        List of results (one per entry)
    """
    executor = MCPParallelExecutor(max_concurrent=max_concurrent)
    return await executor.execute_homogeneous_batch(
        conport_client, 'log_progress', progress_entries
    )


async def batch_update_progress(
    conport_client: Any,
    updates: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Any]:
    """
    Batch update multiple progress entries in ConPort.

    Args:
        conport_client: ConPortMCPClient instance
        updates: List of update dicts (must include progress_id)
        max_concurrent: Max concurrent calls

    Returns:
        List of results (one per update)
    """
    executor = MCPParallelExecutor(max_concurrent=max_concurrent)
    return await executor.execute_homogeneous_batch(
        conport_client, 'update_progress', updates
    )
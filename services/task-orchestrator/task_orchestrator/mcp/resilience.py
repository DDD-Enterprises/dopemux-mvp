"""Resilience wrapper for MCP tools - graceful degradation when services are unavailable."""

import functools
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


def graceful_degradation(fallback_fn: Optional[Callable] = None):
    """Decorator: try real implementation, fall back to local-only mode.

    Wraps async MCP tool functions so that connection failures to external
    services (Redis, ConPort, Leantime) return a degraded-but-useful response
    instead of crashing the tool.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            try:
                return await func(*args, **kwargs)
            except (ConnectionError, ConnectionRefusedError, OSError) as e:
                logger.warning(f"Service unavailable for {func.__name__}: {e}")
                if fallback_fn:
                    return await fallback_fn(*args, **kwargs)
                return {
                    "result": "degraded",
                    "message": f"Running in offline mode - {func.__name__}",
                    "error": str(e),
                }
            except TimeoutError as e:
                logger.warning(f"Timeout for {func.__name__}: {e}")
                if fallback_fn:
                    return await fallback_fn(*args, **kwargs)
                return {
                    "result": "degraded",
                    "message": f"Service timeout - {func.__name__}",
                    "error": str(e),
                }
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                return {
                    "result": "error",
                    "message": f"Tool error - {func.__name__}",
                    "error": str(e),
                }

        return wrapper

    return decorator

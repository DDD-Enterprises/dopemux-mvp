"""
Error Handling & Retry System for DopeconBridge

Provides robust error handling with:
- Error categorization (retryable vs fatal)
- Exponential backoff retry (1s, 2s, 4s, 8s, 16s max)
- Dead letter queue for manual intervention
- Graceful degradation strategies

Features:
- Smart retry logic based on error type
- DLQ for failed events requiring human review
- Metrics tracking for error patterns
- Circuit breaker integration
- ADHD-friendly: Clear error messages with action steps
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Awaitable

import redis.asyncio as redis

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorCategory(str, Enum):
    """Error categories for handling strategy"""
    RETRYABLE = "retryable"  # Can retry with backoff
    FATAL = "fatal"  # Cannot retry, needs intervention
    TRANSIENT = "transient"  # Temporary, retry immediately
    RATE_LIMIT = "rate_limit"  # Rate limited, wait and retry


class ErrorHandler:
    """
    Handles errors with exponential backoff and dead letter queue.

    Retry Strategy:
    - Attempt 1: Immediate
    - Attempt 2: Wait 1s
    - Attempt 3: Wait 2s
    - Attempt 4: Wait 4s
    - Attempt 5: Wait 8s
    - Attempt 6: Wait 16s (max backoff)
    - After 6 attempts: Move to dead letter queue

    Example:
        handler = ErrorHandler(redis_client)

        result = await handler.execute_with_retry(
            operation=lambda: conport.log_decision(...),
            error_context={"operation": "log_decision", "workspace_id": "..."}
        )
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_retries: int = 5,
        max_backoff_seconds: int = 16,
        dlq_enabled: bool = True
    ):
        """
        Initialize error handler.

        Args:
            redis_client: Redis client for DLQ storage
            max_retries: Maximum retry attempts (default: 5)
            max_backoff_seconds: Maximum backoff time (default: 16)
            dlq_enabled: Enable dead letter queue (default: True)
        """
        self.redis_client = redis_client
        self.max_retries = max_retries
        self.max_backoff_seconds = max_backoff_seconds
        self.dlq_enabled = dlq_enabled

        # Metrics
        self.operations_attempted = 0
        self.operations_succeeded = 0
        self.operations_failed = 0
        self.retries_performed = 0
        self.dlq_items = 0

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize error for handling strategy.

        Args:
            error: Exception to categorize

        Returns:
            ErrorCategory determining retry strategy
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Network/connection errors - retryable
        if any(x in error_str for x in ["connection", "timeout", "network", "unavailable"]):
            return ErrorCategory.RETRYABLE

        # Rate limiting - wait and retry
        if "rate limit" in error_str or "429" in error_str or "quota" in error_str:
            return ErrorCategory.RATE_LIMIT

        # Transient errors - retry quickly
        if any(x in error_str for x in ["temporary", "busy", "locked"]):
            return ErrorCategory.TRANSIENT

        # Validation errors - fatal (don't retry)
        if any(x in error_type.lower() for x in ["validation", "value", "type", "assertion"]):
            return ErrorCategory.FATAL

        # Default: retryable
        return ErrorCategory.RETRYABLE

    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Retry attempt number (0-based)

        Returns:
            Backoff delay in seconds
        """
        if attempt == 0:
            return 0  # No delay on first attempt

        # Exponential: 1, 2, 4, 8, 16, 16, ...
        backoff = min(2 ** (attempt - 1), self.max_backoff_seconds)
        return float(backoff)

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        error_context: Optional[Dict[str, Any]] = None,
        custom_categorizer: Optional[Callable[[Exception], ErrorCategory]] = None
    ) -> Optional[T]:
        """
        Execute operation with retry logic.

        Args:
            operation: Async operation to execute
            error_context: Context for error logging (operation name, params, etc.)
            custom_categorizer: Optional custom error categorizer

        Returns:
            Operation result, or None if all retries failed
        """
        self.operations_attempted += 1
        categorizer = custom_categorizer or self.categorize_error

        for attempt in range(self.max_retries + 1):
            try:
                result = await operation()
                self.operations_succeeded += 1
                return result

            except Exception as e:
                # Categorize error
                category = categorizer(e)

                # Log error
                logger.error(
                    f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}",
                    extra={"error_context": error_context, "error_category": category.value}
                )

                # Fatal errors - don't retry
                if category == ErrorCategory.FATAL:
                    logger.error("Fatal error - moving to DLQ")
                    await self._add_to_dlq(operation, error_context, e)
                    self.operations_failed += 1
                    return None

                # Last attempt - move to DLQ
                if attempt >= self.max_retries:
                    logger.error("Max retries exceeded - moving to DLQ")
                    await self._add_to_dlq(operation, error_context, e)
                    self.operations_failed += 1
                    return None

                # Calculate backoff
                backoff = self.calculate_backoff(attempt)
                self.retries_performed += 1

                logger.info(f"Retrying after {backoff}s (category: {category.value})")

                # Wait before retry
                if backoff > 0:
                    await asyncio.sleep(backoff)

        return None

    async def _add_to_dlq(
        self,
        operation: Callable,
        context: Optional[Dict[str, Any]],
        error: Exception
    ):
        """
        Add failed operation to dead letter queue.

        Args:
            operation: Failed operation (for context)
            context: Operation context
            error: Exception that caused failure
        """
        if not self.dlq_enabled:
            return

        try:
            dlq_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(error),
                "error_type": type(error).__name__,
                "context": context or {},
                "operation_name": operation.__name__ if hasattr(operation, '__name__') else "unknown"
            }

            # Add to Redis list
            await self.redis_client.lpush(
                "dopecon_bridge:dlq",
                json.dumps(dlq_entry)
            )

            # Trim to keep last 1000 entries
            await self.redis_client.ltrim("dopecon_bridge:dlq", 0, 999)

            self.dlq_items += 1

            logger.warning(
                f"Added to DLQ: {dlq_entry['operation_name']} - {error}",
                extra={"dlq_entry": dlq_entry}
            )

        except Exception as e:
            logger.error(f"Failed to add to DLQ: {e}")

    async def get_dlq_items(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent dead letter queue items.

        Args:
            count: Number of items to retrieve (default: 10)

        Returns:
            List of DLQ entries
        """
        try:
            items_raw = await self.redis_client.lrange("dopecon_bridge:dlq", 0, count - 1)

            items = []
            for item_raw in items_raw:
                try:
                    item = json.loads(item_raw)
                    items.append(item)
                except:
                    pass

            return items

        except Exception as e:
            logger.error(f"Failed to get DLQ items: {e}")
            return []

    async def clear_dlq(self):
        """Clear all dead letter queue items"""
        try:
            await self.redis_client.delete("dopecon_bridge:dlq")
            logger.info("DLQ cleared")
        except Exception as e:
            logger.error(f"Failed to clear DLQ: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get error handling metrics"""
        success_rate = (
            (self.operations_succeeded / self.operations_attempted * 100)
            if self.operations_attempted > 0
            else 0.0
        )

        retry_rate = (
            (self.retries_performed / self.operations_attempted)
            if self.operations_attempted > 0
            else 0.0
        )

        return {
            "operations_attempted": self.operations_attempted,
            "operations_succeeded": self.operations_succeeded,
            "operations_failed": self.operations_failed,
            "success_rate_percent": round(success_rate, 2),
            "retries_performed": self.retries_performed,
            "avg_retries_per_operation": round(retry_rate, 2),
            "dlq_items": self.dlq_items,
            "max_retries": self.max_retries,
            "max_backoff_seconds": self.max_backoff_seconds
        }

    def reset_metrics(self):
        """Reset metrics counters"""
        self.operations_attempted = 0
        self.operations_succeeded = 0
        self.operations_failed = 0
        self.retries_performed = 0
        self.dlq_items = 0

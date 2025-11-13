"""
Tests for Error Handling & Retry System
Validates exponential backoff, DLQ, and error categorization
"""

import asyncio
import pytest
import time

import redis.asyncio as redis

from error_handler import ErrorHandler, ErrorCategory


class TestErrorHandler:
    """Test ErrorHandler retry logic"""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        client = redis.from_url(
            "redis://localhost:6379",
            db=10,  # Error handler test database
            decode_responses=True
        )

        # Clear test database
        await client.flushdb()

        yield client

        # Cleanup
        await client.flushdb()
        await client.aclose()

    @pytest.fixture
    def handler(self, redis_client):
        """Create ErrorHandler"""
        return ErrorHandler(
            redis_client=redis_client,
            max_retries=3,  # Lower for faster testing
            max_backoff_seconds=8
        )

    def test_categorizes_connection_errors_as_retryable(self, handler):
        """Test connection errors categorized as retryable"""
        error = Exception("Connection refused to database")

        category = handler.categorize_error(error)

        assert category == ErrorCategory.RETRYABLE

    def test_categorizes_rate_limit_errors(self, handler):
        """Test rate limit errors categorized correctly"""
        error = Exception("Rate limit exceeded, please retry later")

        category = handler.categorize_error(error)

        assert category == ErrorCategory.RATE_LIMIT

    def test_categorizes_validation_errors_as_fatal(self, handler):
        """Test validation errors categorized as fatal"""
        error = ValueError("Invalid input parameter")

        category = handler.categorize_error(error)

        assert category == ErrorCategory.FATAL

    def test_calculates_exponential_backoff(self, handler):
        """Test exponential backoff calculation"""
        assert handler.calculate_backoff(0) == 0  # No delay first attempt
        assert handler.calculate_backoff(1) == 1  # 1s
        assert handler.calculate_backoff(2) == 2  # 2s
        assert handler.calculate_backoff(3) == 4  # 4s
        assert handler.calculate_backoff(4) == 8  # 8s (max for this handler)
        assert handler.calculate_backoff(5) == 8  # Capped at max

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self, handler):
        """Test successful operation on first attempt"""
        async def successful_operation():
            return "success"

        result = await handler.execute_with_retry(successful_operation)

        assert result == "success"
        assert handler.operations_succeeded == 1
        assert handler.retries_performed == 0

    @pytest.mark.asyncio
    async def test_retries_on_failure(self, handler):
        """Test retry logic on failures"""
        attempt_count = 0

        async def failing_then_succeeding():
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count < 3:
                raise Exception("Temporary failure")

            return "success"

        start_time = time.time()
        result = await handler.execute_with_retry(failing_then_succeeding)
        elapsed = time.time() - start_time

        assert result == "success"
        assert attempt_count == 3  # Failed 2 times, succeeded on 3rd
        assert handler.retries_performed == 2
        assert elapsed >= 1.0  # At least 1s backoff (1s + 2s delays)

    @pytest.mark.asyncio
    async def test_fatal_errors_not_retried(self, handler):
        """Test that fatal errors go straight to DLQ"""
        async def fatal_operation():
            raise ValueError("Invalid parameter")

        result = await handler.execute_with_retry(fatal_operation)

        assert result is None
        assert handler.operations_failed == 1
        assert handler.retries_performed == 0  # No retries
        assert handler.dlq_items == 1  # Added to DLQ

    @pytest.mark.asyncio
    async def test_max_retries_then_dlq(self, handler):
        """Test that operation goes to DLQ after max retries"""
        async def always_failing():
            raise Exception("Always fails")

        result = await handler.execute_with_retry(always_failing)

        assert result is None
        assert handler.operations_failed == 1
        assert handler.retries_performed == 3  # max_retries
        assert handler.dlq_items == 1

    @pytest.mark.asyncio
    async def test_dlq_stores_error_context(self, handler):
        """Test that DLQ stores error context"""
        async def failing_op():
            raise Exception("Test error")

        await handler.execute_with_retry(
            failing_op,
            error_context={"operation": "test", "data": "context"}
        )

        # Retrieve from DLQ
        dlq_items = await handler.get_dlq_items(count=1)

        assert len(dlq_items) == 1
        assert dlq_items[0]["error"] == "Test error"
        assert dlq_items[0]["context"]["operation"] == "test"

    @pytest.mark.asyncio
    async def test_get_dlq_items(self, handler):
        """Test retrieving DLQ items"""
        # Add some items to DLQ
        for i in range(5):
            async def fail():
                raise ValueError(f"Error {i}")

            await handler.execute_with_retry(fail)

        dlq_items = await handler.get_dlq_items(count=3)

        assert len(dlq_items) == 3  # Requested 3

    @pytest.mark.asyncio
    async def test_clear_dlq(self, handler):
        """Test clearing DLQ"""
        # Add item to DLQ
        async def fail():
            raise ValueError("Error")

        await handler.execute_with_retry(fail)

        # Clear DLQ
        await handler.clear_dlq()

        # Verify empty
        dlq_items = await handler.get_dlq_items()
        assert len(dlq_items) == 0

    def test_metrics_tracking(self, handler):
        """Test error handler metrics"""
        handler.reset_metrics()

        # Manually set metrics
        handler.operations_attempted = 10
        handler.operations_succeeded = 8
        handler.operations_failed = 2
        handler.retries_performed = 5

        metrics = handler.get_metrics()

        assert metrics["operations_attempted"] == 10
        assert metrics["operations_succeeded"] == 8
        assert metrics["success_rate_percent"] == 80.0
        assert metrics["avg_retries_per_operation"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

#!/usr/bin/env python3
"""
Mock Factories
==============

Factory functions for creating mock HTTP responses, server behaviors, and test doubles.

**Use Cases**:
- Testing without running full Infrastructure (Redis, PostgreSQL)
- Simulating specific failure scenarios (timeouts, 503 errors)
- Performance testing with controlled latencies
- Parallel test execution without resource conflicts
"""

from typing import Dict, Any, List, Optional, Callable
from unittest.mock import AsyncMock, MagicMock, Mock
import json
import asyncio


class MockHTTPResponse:
    """Mock aiohttp.ClientResponse for testing HTTP clients."""

    def __init__(
        self,
        status: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text_data: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_exception: Optional[Exception] = None,
        delay_seconds: float = 0.0
    ):
        """
        Create mock HTTP response.

        Args:
            status: HTTP status code
            json_data: JSON response body
            text_data: Text response body
            headers: Response headers
            raise_exception: Exception to raise on access
            delay_seconds: Simulate network latency
        """
        self.status = status
        self._json_data = json_data
        self._text_data = text_data
        self.headers = headers or {}
        self._raise_exception = raise_exception
        self._delay_seconds = delay_seconds

    async def json(self) -> Dict[str, Any]:
        """Return JSON response body."""
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        if self._raise_exception:
            raise self._raise_exception
        return self._json_data or {}

    async def text(self) -> str:
        """Return text response body."""
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        if self._raise_exception:
            raise self._raise_exception
        return self._text_data or ""

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class MockClientSession:
    """Mock aiohttp.ClientSession for testing HTTP clients."""

    def __init__(self, responses: Optional[Dict[str, MockHTTPResponse]] = None):
        """
        Create mock client session.

        Args:
            responses: URL -> MockHTTPResponse mapping
        """
        self.responses = responses or {}
        self.request_history: List[Dict[str, Any]] = []

    def get(self, url: str, **kwargs) -> MockHTTPResponse:
        """Mock GET request."""
        self.request_history.append({
            "method": "GET",
            "url": url,
            "kwargs": kwargs
        })

        # Return configured response or default 200
        return self.responses.get(url, MockHTTPResponse(status=200, json_data={}))

    def post(self, url: str, **kwargs) -> MockHTTPResponse:
        """Mock POST request."""
        self.request_history.append({
            "method": "POST",
            "url": url,
            "kwargs": kwargs
        })
        return self.responses.get(url, MockHTTPResponse(status=201, json_data={}))

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class RedisStreamMockFactory:
    """Factory for mocking Redis Streams behavior."""

    @staticmethod
    def create_mock_client(
        stream_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        connection_error: bool = False
    ) -> MagicMock:
        """
        Create mock Redis client with stream operations.

        Args:
            stream_data: Pre-populated stream data (stream_name -> events)
            connection_error: Simulate connection failure
        """
        mock_client = MagicMock()

        if connection_error:
            mock_client.ping.side_effect = Exception("Redis connection failed")
            return mock_client

        # Mock ping
        mock_client.ping.return_value = True

        # Mock xadd (add event to stream)
        def mock_xadd(stream_name: str, fields: Dict[str, Any], *args, **kwargs):
            """Mock adding event to stream."""
            message_id = f"{int(asyncio.get_event_loop().time() * 1000)}-0"
            if stream_data is not None:
                if stream_name not in stream_data:
                    stream_data[stream_name] = []
                stream_data[stream_name].append({"id": message_id, "data": fields})
            return message_id

        mock_client.xadd.side_effect = mock_xadd

        # Mock xread (read events from stream)
        def mock_xread(streams: Dict[str, str], count: int = None, block: int = None):
            """Mock reading events from stream."""
            results = []
            for stream_name, start_id in streams.items():
                if stream_data and stream_name in stream_data:
                    stream_events = stream_data[stream_name]
                    # Filter events after start_id
                    filtered = [
                        (evt["id"], evt["data"])
                        for evt in stream_events
                        if evt["id"] > start_id or start_id == "0-0"
                    ]
                    if filtered:
                        results.append((stream_name, filtered[:count] if count else filtered))
            return results

        mock_client.xread.side_effect = mock_xread

        return mock_client


class IntegrationBridgeMockFactory:
    """Factory for mocking Integration Bridge HTTP responses."""

    @staticmethod
    def create_mock_session(
        tasks: Optional[List[Dict[str, Any]]] = None,
        adhd_state: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[Dict[str, Any]]] = None,
        session_status: Optional[Dict[str, Any]] = None,
        sprint_info: Optional[Dict[str, Any]] = None,
        simulate_errors: bool = False,
        latency_ms: int = 0
    ) -> MockClientSession:
        """
        Create mock Integration Bridge client session.

        Args:
            tasks: Task list to return
            adhd_state: ADHD state to return
            recommendations: Recommendations to return
            session_status: Session status to return
            sprint_info: Sprint info to return
            simulate_errors: Return 503 errors
            latency_ms: Simulate network latency
        """
        from .test_data_generators import TaskGenerator, ADHDStateGenerator, RecommendationGenerator

        # Default data if not provided
        tasks = tasks or TaskGenerator.generate_task_list(count=10)
        adhd_state = adhd_state or ADHDStateGenerator.generate_state()
        recommendations = recommendations or RecommendationGenerator.generate_recommendation_list(count=5)
        session_status = session_status or {
            "session_id": "session-test-001",
            "active": True,
            "duration_minutes": 45,
            "break_count": 0,
            "tasks_completed": 3
        }
        sprint_info = sprint_info or {
            "sprint_id": "S-2025.10",
            "name": "Architecture 3.0 Implementation",
            "total_tasks": 20,
            "completed_tasks": 11,
            "in_progress_tasks": 3
        }

        delay = latency_ms / 1000.0

        # Build response mapping
        responses = {}

        if simulate_errors:
            # Return 503 Service Unavailable for all endpoints
            for url in [
                "http://localhost:3016/orchestrator/tasks",
                "http://localhost:3016/orchestrator/adhd-state",
                "http://localhost:3016/orchestrator/recommendations",
                "http://localhost:3016/orchestrator/session",
                "http://localhost:3016/orchestrator/active-sprint"
            ]:
                responses[url] = MockHTTPResponse(
                    status=503,
                    text_data="Task-Orchestrator unavailable",
                    delay_seconds=delay
                )
        else:
            # Return success responses
            responses["http://localhost:3016/orchestrator/tasks"] = MockHTTPResponse(
                status=200, json_data=tasks, delay_seconds=delay
            )
            responses["http://localhost:3016/orchestrator/adhd-state"] = MockHTTPResponse(
                status=200, json_data=adhd_state, delay_seconds=delay
            )
            responses["http://localhost:3016/orchestrator/recommendations"] = MockHTTPResponse(
                status=200, json_data=recommendations, delay_seconds=delay
            )
            responses["http://localhost:3016/orchestrator/session"] = MockHTTPResponse(
                status=200, json_data=session_status, delay_seconds=delay
            )
            responses["http://localhost:3016/orchestrator/active-sprint"] = MockHTTPResponse(
                status=200, json_data=sprint_info, delay_seconds=delay
            )

        return MockClientSession(responses=responses)


class PerformanceScenarioFactory:
    """Factory for creating performance test scenarios."""

    @staticmethod
    def create_fast_scenario() -> Dict[str, Any]:
        """
        Create scenario with all components meeting ADHD targets.

        Expected latencies:
        - HTTP queries: < 70ms
        - Event propagation: < 100ms
        - State sync: < 150ms
        """
        return {
            "name": "fast_scenario",
            "description": "All components meet ADHD performance targets",
            "http_latency_ms": 50,
            "event_latency_ms": 80,
            "state_sync_latency_ms": 120,
            "expected_adhd_safe": True
        }

    @staticmethod
    def create_slow_scenario() -> Dict[str, Any]:
        """
        Create scenario with degraded performance.

        Expected latencies:
        - HTTP queries: > 200ms (exceeds target)
        - Event propagation: > 150ms (exceeds target)
        - State sync: > 300ms (exceeds target)
        """
        return {
            "name": "slow_scenario",
            "description": "Performance degraded, exceeds ADHD targets",
            "http_latency_ms": 250,
            "event_latency_ms": 180,
            "state_sync_latency_ms": 350,
            "expected_adhd_safe": False
        }

    @staticmethod
    def create_variable_scenario() -> Dict[str, Any]:
        """
        Create scenario with variable performance (P95 issues).

        Expected latencies:
        - Average: Within targets
        - P95: Exceeds targets (attention safety risk)
        """
        return {
            "name": "variable_scenario",
            "description": "Average OK, but P95 exceeds ADHD targets",
            "http_latency_ms_avg": 70,
            "http_latency_ms_p95": 220,
            "event_latency_ms_avg": 90,
            "event_latency_ms_p95": 180,
            "expected_adhd_safe": False  # P95 failures
        }


class FailureScenarioFactory:
    """Factory for creating failure test scenarios."""

    @staticmethod
    def create_redis_unavailable() -> Dict[str, Any]:
        """Scenario: Redis unavailable (Component 3 failure)."""
        return {
            "name": "redis_unavailable",
            "description": "Redis connection failed, event bus down",
            "redis_available": False,
            "postgres_available": True,
            "http_available": True,
            "expected_behavior": "Event propagation fails, HTTP queries succeed"
        }

    @staticmethod
    def create_orchestrator_unavailable() -> Dict[str, Any]:
        """Scenario: Task-Orchestrator unavailable (Component 5 failure)."""
        return {
            "name": "orchestrator_unavailable",
            "description": "Task-Orchestrator HTTP server down",
            "redis_available": True,
            "postgres_available": True,
            "http_available": False,
            "expected_behavior": "HTTP queries return 503, fallback to mock data"
        }

    @staticmethod
    def create_postgres_unavailable() -> Dict[str, Any]:
        """Scenario: PostgreSQL unavailable (Component 4 failure)."""
        return {
            "name": "postgres_unavailable",
            "description": "PostgreSQL/ConPort unavailable",
            "redis_available": True,
            "postgres_available": False,
            "http_available": True,
            "expected_behavior": "ConPort MCP calls fail, state sync degraded"
        }

    @staticmethod
    def create_timeout_scenario() -> Dict[str, Any]:
        """Scenario: Requests timeout (network issues)."""
        return {
            "name": "timeout_scenario",
            "description": "Requests timeout after 5 seconds",
            "timeout_seconds": 5.0,
            "expected_behavior": "Timeout errors, graceful degradation"
        }


class ADHDWorkflowMockFactory:
    """Factory for mocking complete ADHD-aware workflows."""

    @staticmethod
    def create_morning_high_energy_workflow() -> Dict[str, Any]:
        """
        Workflow: Morning high-energy session (9-12 AM).

        Expected behavior:
        - High complexity tasks recommended
        - Long session duration (60-120 min)
        - Fewer break prompts
        """
        from .test_data_generators import ADHDStateGenerator, RecommendationGenerator, TaskGenerator

        # Morning high-energy state
        adhd_state = ADHDStateGenerator.generate_state(
            energy_level="high",
            attention_level="focused",
            time_since_break=20  # Fresh from morning routine
        )

        # Recommend high-complexity tasks
        high_complexity_tasks = [
            TaskGenerator.generate_task(complexity=0.8),
            TaskGenerator.generate_task(complexity=0.7),
            TaskGenerator.generate_task(complexity=0.6)
        ]
        recommendations = [
            RecommendationGenerator.generate_recommendation(task=task, confidence=0.85, priority=i+1)
            for i, task in enumerate(high_complexity_tasks)
        ]

        return {
            "workflow": "morning_high_energy",
            "adhd_state": adhd_state,
            "recommendations": recommendations,
            "expected_session_duration": 90,
            "expected_break_frequency": "60-90 minutes"
        }

    @staticmethod
    def create_afternoon_dip_workflow() -> Dict[str, Any]:
        """
        Workflow: Afternoon energy dip (12-15 PM).

        Expected behavior:
        - Low complexity tasks recommended
        - Shorter session duration (25-45 min)
        - More frequent break prompts
        """
        from .test_data_generators import ADHDStateGenerator, RecommendationGenerator, TaskGenerator

        # Afternoon dip state
        adhd_state = ADHDStateGenerator.generate_state(
            energy_level="low",
            attention_level="transitioning",
            time_since_break=45  # Been working for a while
        )

        # Recommend low-complexity tasks
        low_complexity_tasks = [
            TaskGenerator.generate_task(complexity=0.2),
            TaskGenerator.generate_task(complexity=0.3),
            TaskGenerator.generate_task(complexity=0.25)
        ]
        recommendations = [
            RecommendationGenerator.generate_recommendation(task=task, confidence=0.75, priority=i+1)
            for i, task in enumerate(low_complexity_tasks)
        ]

        return {
            "workflow": "afternoon_dip",
            "adhd_state": adhd_state,
            "recommendations": recommendations,
            "expected_session_duration": 30,
            "expected_break_frequency": "25-30 minutes"
        }

    @staticmethod
    def create_hyperfocus_workflow() -> Dict[str, Any]:
        """
        Workflow: Hyperfocus state (variable timing).

        Expected behavior:
        - Complex tasks recommended
        - Extended session duration (120+ min)
        - Break reminders ignored initially
        """
        from .test_data_generators import ADHDStateGenerator, RecommendationGenerator, TaskGenerator

        # Hyperfocus state
        adhd_state = ADHDStateGenerator.generate_state(
            energy_level="hyperfocus",
            attention_level="hyperfocused",
            time_since_break=90  # In deep flow, haven't broken
        )

        # Recommend complex, engaging tasks
        complex_tasks = [
            TaskGenerator.generate_task(complexity=0.9),
            TaskGenerator.generate_task(complexity=0.85)
        ]
        recommendations = [
            RecommendationGenerator.generate_recommendation(task=task, confidence=0.95, priority=i+1)
            for i, task in enumerate(complex_tasks)
        ]

        return {
            "workflow": "hyperfocus",
            "adhd_state": adhd_state,
            "recommendations": recommendations,
            "expected_session_duration": 150,
            "expected_break_frequency": "90-120 minutes (gentle reminders)",
            "warning": "Monitor for burnout, enforce breaks after 120 min"
        }

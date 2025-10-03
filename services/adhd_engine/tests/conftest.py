"""
Pytest configuration and fixtures for ADHD Engine tests.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from adhd_engine.models import ADHDProfile, EnergyLevel, AttentionState
from adhd_engine.engine import ADHDAccommodationEngine
from adhd_engine.activity_tracker import ActivityTracker


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = AsyncMock()
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.lpush = AsyncMock(return_value=1)
    redis_mock.lrange = AsyncMock(return_value=[])
    redis_mock.ltrim = AsyncMock(return_value=True)
    redis_mock.keys = AsyncMock(return_value=[])
    redis_mock.close = AsyncMock(return_value=None)
    return redis_mock


@pytest.fixture
def sample_adhd_profile():
    """Sample ADHD profile for testing."""
    return ADHDProfile(
        user_id="test_user",
        hyperfocus_tendency=0.7,
        distraction_sensitivity=0.6,
        optimal_task_duration=25,
        max_task_duration=90,
        peak_hours=[9, 10, 14, 15]
    )


@pytest.fixture
def sample_task_data():
    """Sample task data for assessment testing."""
    return {
        "complexity_score": 0.6,
        "estimated_minutes": 25,
        "description": "implement authentication system",
        "dependencies": []
    }


@pytest.fixture
async def engine_with_mocks(mock_redis):
    """ADHD engine with mocked dependencies."""
    engine = ADHDAccommodationEngine()
    engine.redis_client = mock_redis
    engine.running = True

    # Skip actual monitor startup for tests
    engine.monitoring_tasks = [MagicMock(done=MagicMock(return_value=False)) for _ in range(6)]

    yield engine

    # Cleanup
    engine.running = False


@pytest.fixture
def mock_conport_client():
    """Mock ConPort client for testing."""
    client_mock = MagicMock()

    # Mock progress entries
    client_mock.get_progress_entries = MagicMock(return_value=[
        {"id": 1, "status": "DONE", "description": "Task 1", "timestamp": datetime.now(timezone.utc).isoformat()},
        {"id": 2, "status": "IN_PROGRESS", "description": "Task 2", "timestamp": datetime.now(timezone.utc).isoformat()},
        {"id": 3, "status": "TODO", "description": "Task 3", "timestamp": datetime.now(timezone.utc).isoformat()},
    ])

    # Mock custom data
    client_mock.get_custom_data = MagicMock(return_value={
        "context_switches": 3,
        "context_switches_per_hour": 5,
        "abandoned_tasks": 1,
        "average_focus_duration": 22,
        "distraction_events": 3
    })

    return client_mock

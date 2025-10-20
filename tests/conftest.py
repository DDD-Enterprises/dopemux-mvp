"""
Pytest configuration and shared fixtures.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Legacy imports - commenting out as these modules have been refactored
# from dopemux.event_bus import RedisStreamsAdapter, InMemoryAdapter
# from dopemux.attention_mediator import AttentionMediator
# from dopemux.instance_registry import InstanceRegistry


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "version": "1.0",
        "adhd_profile": {
            "focus_duration_avg": 25,
            "break_interval": 5,
            "distraction_sensitivity": 0.5,
            "hyperfocus_tendency": False,
            "notification_style": "gentle",
            "visual_complexity": "minimal",
        },
        "mcp_servers": {
            "test-server": {
                "enabled": True,
                "command": "python",
                "args": ["test.py"],
                "env": {},
                "timeout": 30,
                "auto_restart": True,
            }
        },
        "attention": {
            "enabled": True,
            "sample_interval": 5,
            "keystroke_threshold": 2.0,
            "context_switch_threshold": 3,
            "adaptation_enabled": True,
        },
        "context": {
            "enabled": True,
            "auto_save_interval": 30,
            "max_sessions": 50,
            "compression": True,
            "backup_enabled": True,
        },
    }


@pytest.fixture
def config_manager(temp_config_dir, sample_config_data):
    """Create a ConfigManager instance for testing."""
    config_file = temp_config_dir / "config.yaml"

    with patch("dopemux.config.manager.ConfigManager._init_paths") as mock_init_paths:
        from dopemux.config.manager import ConfigPaths

        mock_init_paths.return_value = ConfigPaths(
            global_config=temp_config_dir / "global.yaml",
            user_config=config_file,
            project_config=temp_config_dir / "project.yaml",
            cache_dir=temp_config_dir / "cache",
            data_dir=temp_config_dir / "data",
        )

        manager = ConfigManager()
        # Mock the default config
        with patch.object(
            manager, "_get_default_config", return_value=sample_config_data
        ):
            yield manager


@pytest.fixture
def context_manager(temp_project_dir):
    """Create a ContextManager instance for testing."""
    return ContextManager(temp_project_dir)


@pytest.fixture
def attention_monitor(temp_project_dir):
    """Create an AttentionMonitor instance for testing."""
    return AttentionMonitor(temp_project_dir)


@pytest.fixture
def task_decomposer(temp_project_dir):
    """Create a TaskDecomposer instance for testing."""
    return TaskDecomposer(temp_project_dir)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls."""
    with patch("subprocess.run") as mock_run:
        # Default successful git commands
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main\n"
        yield mock_run


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    with patch("dopemux.adhd.context_manager.datetime") as mock_dt:
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        yield mock_dt


@pytest.fixture
def sample_context_data():
    """Sample context data for testing."""
    return {
        "session_id": "test-session-123",
        "timestamp": "2024-01-01T12:00:00",
        "working_directory": "/test/project",
        "open_files": [
            {
                "path": "src/main.py",
                "absolute_path": "/test/project/src/main.py",
                "last_modified": "2024-01-01T11:30:00",
                "cursor_position": {"line": 10, "column": 5},
                "scroll_position": 0,
                "unsaved_changes": False,
            }
        ],
        "current_goal": "Implement feature X",
        "mental_model": {
            "approach": "Using pattern Y",
            "next_steps": ["Step 1", "Step 2"],
            "blockers": [],
        },
        "git_state": {
            "branch": "feature-branch",
            "status": "",
            "has_changes": False,
            "last_commit": "abc123 Last commit message",
        },
        "recent_commands": ["git status", "python test.py"],
        "decisions": [
            {
                "timestamp": "2024-01-01T11:45:00",
                "decision": "Use approach A over B",
                "rationale": "Better performance",
            }
        ],
        "attention_state": "focused",
        "focus_duration": 25,
        "context_switches": 2,
        "unsaved_changes": False,
        "message": "Working on feature implementation",
    }


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "EXA_API_KEY": "test-exa-key",
    }

    with patch.dict("os.environ", env_vars):
        yield env_vars


# ========================================
# Architecture 3.0 Fixtures
# ========================================

import redis
import asyncio
from typing import Dict, Any
from tests.utils.test_data_generators import (
    TaskGenerator,
    ADHDStateGenerator,
    EventGenerator,
    RecommendationGenerator
)
from tests.utils.mock_factories import (
    RedisStreamMockFactory,
    IntegrationBridgeMockFactory,
    PerformanceScenarioFactory,
    ADHDWorkflowMockFactory
)


# Infrastructure Fixtures
@pytest.fixture(scope="session")
def redis_host() -> str:
    """Redis host for integration testing."""
    return "localhost"


@pytest.fixture(scope="session")
def redis_port() -> int:
    """Redis port for integration testing."""
    return 6379


@pytest.fixture
def redis_client_integration(redis_host, redis_port):
    """Real Redis client for integration tests."""
    client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    yield client
    # Cleanup test keys
    test_keys = client.keys("test:*")
    if test_keys:
        client.delete(*test_keys)
    client.close()


@pytest.fixture
def mock_redis_streams():
    """Mock Redis Streams client for unit tests."""
    return RedisStreamMockFactory.create_mock_client()


# Test Data Fixtures
@pytest.fixture
def sample_task() -> Dict[str, Any]:
    """Generate sample task with ADHD metadata."""
    return TaskGenerator.generate_task()


@pytest.fixture
def sample_task_list() -> list[Dict[str, Any]]:
    """Generate list of sample tasks."""
    return TaskGenerator.generate_task_list(count=10)


@pytest.fixture
def high_complexity_task() -> Dict[str, Any]:
    """Generate high-complexity task (ADHD challenge)."""
    return TaskGenerator.generate_task(complexity=0.8)


@pytest.fixture
def low_complexity_task() -> Dict[str, Any]:
    """Generate low-complexity task (ADHD-friendly)."""
    return TaskGenerator.generate_task(complexity=0.2)


@pytest.fixture
def sample_adhd_state() -> Dict[str, Any]:
    """Generate sample ADHD state."""
    return ADHDStateGenerator.generate_state()


@pytest.fixture
def morning_high_energy_state() -> Dict[str, Any]:
    """Morning high-energy ADHD state."""
    return ADHDStateGenerator.generate_state(
        energy_level="high",
        attention_level="focused",
        time_since_break=20
    )


@pytest.fixture
def afternoon_dip_state() -> Dict[str, Any]:
    """Afternoon energy dip ADHD state."""
    return ADHDStateGenerator.generate_state(
        energy_level="low",
        attention_level="transitioning",
        time_since_break=45
    )


@pytest.fixture
def hyperfocus_state() -> Dict[str, Any]:
    """Hyperfocus ADHD state."""
    return ADHDStateGenerator.generate_state(
        energy_level="hyperfocus",
        attention_level="hyperfocused",
        time_since_break=90
    )


@pytest.fixture
def sample_event() -> Dict[str, Any]:
    """Generate sample event for Redis Streams."""
    return EventGenerator.generate_event()


@pytest.fixture
def sample_event_sequence() -> list[Dict[str, Any]]:
    """Generate event sequence."""
    return EventGenerator.generate_event_sequence(count=10)


@pytest.fixture
def sample_recommendations() -> list[Dict[str, Any]]:
    """Generate task recommendations."""
    return RecommendationGenerator.generate_recommendation_list(count=5)


# Mock HTTP Fixtures
@pytest.fixture
def mock_integration_bridge_success():
    """Mock Integration Bridge HTTP client (success)."""
    return IntegrationBridgeMockFactory.create_mock_session(simulate_errors=False)


@pytest.fixture
def mock_integration_bridge_errors():
    """Mock Integration Bridge HTTP client (503 errors)."""
    return IntegrationBridgeMockFactory.create_mock_session(simulate_errors=True)


@pytest.fixture
def mock_integration_bridge_slow():
    """Mock Integration Bridge HTTP client (250ms latency)."""
    return IntegrationBridgeMockFactory.create_mock_session(latency_ms=250)


@pytest.fixture
def mock_integration_bridge_fast():
    """Mock Integration Bridge HTTP client (50ms latency)."""
    return IntegrationBridgeMockFactory.create_mock_session(latency_ms=50)


# Performance Scenario Fixtures
@pytest.fixture
def fast_performance_scenario() -> Dict[str, Any]:
    """Fast performance (meets ADHD targets)."""
    return PerformanceScenarioFactory.create_fast_scenario()


@pytest.fixture
def slow_performance_scenario() -> Dict[str, Any]:
    """Slow performance (exceeds ADHD targets)."""
    return PerformanceScenarioFactory.create_slow_scenario()


@pytest.fixture
def variable_performance_scenario() -> Dict[str, Any]:
    """Variable performance (P95 issues)."""
    return PerformanceScenarioFactory.create_variable_scenario()


# ADHD Workflow Fixtures
@pytest.fixture
def morning_workflow() -> Dict[str, Any]:
    """Morning high-energy workflow."""
    return ADHDWorkflowMockFactory.create_morning_high_energy_workflow()


@pytest.fixture
def afternoon_workflow() -> Dict[str, Any]:
    """Afternoon energy dip workflow."""
    return ADHDWorkflowMockFactory.create_afternoon_dip_workflow()


@pytest.fixture
def hyperfocus_workflow() -> Dict[str, Any]:
    """Hyperfocus workflow."""
    return ADHDWorkflowMockFactory.create_hyperfocus_workflow()


# Pytest Configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: integration test (requires infrastructure)")
    config.addinivalue_line("markers", "unit: unit test (no external dependencies)")
    config.addinivalue_line("markers", "performance: performance test (validates ADHD targets)")
    config.addinivalue_line("markers", "slow: slow test (> 5 seconds)")
    config.addinivalue_line("markers", "adhd: ADHD-specific test (energy/attention validation)")


def pytest_collection_modifyitems(config, items):
    """Auto-add markers based on test location/name."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        if "performance" in item.nodeid or "latency" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "adhd" in item.nodeid.lower():
            item.add_marker(pytest.mark.adhd)

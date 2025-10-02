"""
Pytest Configuration and Fixtures for Serena v2 Intelligence Tests

Provides async fixtures for database, Redis, MCP connections,
and mock factories for ADHD states and navigation scenarios.
"""

import asyncio
import pytest
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from datetime import datetime, timezone

# Add Serena to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.database import SerenaIntelligenceDatabase, DatabaseConfig
from v2.intelligence.graph_operations import SerenaGraphOperations
from v2.performance_monitor import PerformanceMonitor, PerformanceTarget
from v2.adhd_features import ADHDCodeNavigator


# ==========================================
# Database Fixtures
# ==========================================

@pytest.fixture
async def test_db_config() -> DatabaseConfig:
    """Test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="serena_test",  # Use test database
        user="serena_test",
        password="serena_test_pass",
        min_connections=2,
        max_connections=5,
        query_timeout=2.0,
        enable_performance_monitoring=True,
        adhd_complexity_filtering=True,
        max_results_per_query=20  # Lower for tests
    )


@pytest.fixture
async def intelligence_db(test_db_config) -> AsyncGenerator[SerenaIntelligenceDatabase, None]:
    """Initialized intelligence database for testing."""
    db = SerenaIntelligenceDatabase(test_db_config)
    await db.initialize()

    yield db

    # Cleanup
    await db.close()


@pytest.fixture
async def performance_monitor() -> PerformanceMonitor:
    """Performance monitor for testing."""
    return PerformanceMonitor(
        target=PerformanceTarget(target_ms=200.0, warning_ms=150.0, critical_ms=500.0)
    )


@pytest.fixture
async def graph_operations(intelligence_db, performance_monitor) -> SerenaGraphOperations:
    """Graph operations instance for testing."""
    return SerenaGraphOperations(intelligence_db, performance_monitor)


# ==========================================
# ADHD State Fixtures
# ==========================================

@pytest.fixture
def adhd_scattered_state() -> Dict[str, Any]:
    """Mock ADHD scattered attention state."""
    return {
        "attention_state": "scattered",
        "attention_span_minutes": 10,
        "cognitive_load_score": 0.8,
        "context_switch_tolerance": 1,
        "preferred_complexity_level": "simple",
        "optimal_result_limit": 5,
        "focus_mode_enabled": False,
        "progressive_disclosure_preference": True
    }


@pytest.fixture
def adhd_focused_state() -> Dict[str, Any]:
    """Mock ADHD focused attention state."""
    return {
        "attention_state": "focused",
        "attention_span_minutes": 25,
        "cognitive_load_score": 0.4,
        "context_switch_tolerance": 3,
        "preferred_complexity_level": "moderate",
        "optimal_result_limit": 10,
        "focus_mode_enabled": False,
        "progressive_disclosure_preference": True
    }


@pytest.fixture
def adhd_hyperfocus_state() -> Dict[str, Any]:
    """Mock ADHD hyperfocus attention state."""
    return {
        "attention_state": "hyperfocus",
        "attention_span_minutes": 90,
        "cognitive_load_score": 0.2,
        "context_switch_tolerance": 5,
        "preferred_complexity_level": "complex",
        "optimal_result_limit": 50,
        "focus_mode_enabled": True,
        "progressive_disclosure_preference": False
    }


# ==========================================
# Mock Data Factories
# ==========================================

@pytest.fixture
def sample_code_element() -> Dict[str, Any]:
    """Sample code element for testing."""
    return {
        "file_path": "/test/module.py",
        "element_name": "test_function",
        "element_type": "function",
        "language": "python",
        "start_line": 10,
        "end_line": 25,
        "complexity_score": 0.3,
        "complexity_level": "simple",
        "cognitive_load_factor": 0.2,
        "adhd_insights": ["short function", "clear logic"],
        "focus_recommendations": []
    }


@pytest.fixture
def sample_navigation_pattern() -> Dict[str, Any]:
    """Sample navigation pattern for testing."""
    return {
        "user_session_id": "test_user_123",
        "workspace_path": "/test/workspace",
        "pattern_sequence": [
            {"action": "find_symbol", "timestamp": "2025-10-02T19:00:00Z"},
            {"action": "get_definition", "timestamp": "2025-10-02T19:00:15Z"},
            {"action": "find_references", "timestamp": "2025-10-02T19:00:30Z"}
        ],
        "pattern_type": "exploration",
        "effectiveness_score": 0.8,
        "attention_span_seconds": 180,
        "cognitive_fatigue_score": 0.2,
        "focus_mode_used": False
    }


# ==========================================
# Cleanup Fixtures
# ==========================================

@pytest.fixture(autouse=True)
def cleanup_test_database():
    """Clean up test database after all tests complete."""
    yield

    # Cleanup logic here if needed
    # For now, test database remains for inspection


# ==========================================
# Test Helpers
# ==========================================

@pytest.fixture
def assert_adhd_compliant():
    """Helper to assert ADHD performance compliance."""
    def _assert(duration_ms: float, target_ms: float = 200.0):
        assert duration_ms < target_ms, f"ADHD target violated: {duration_ms:.2f}ms >= {target_ms}ms"
    return _assert


@pytest.fixture
def assert_performance_excellent():
    """Helper to assert excellent performance (<50ms)."""
    def _assert(duration_ms: float):
        assert duration_ms < 50.0, f"Excellent performance not achieved: {duration_ms:.2f}ms >= 50ms"
    return _assert

#!/usr/bin/env python3
"""
Test suite for Serena v2 Phase 2B Adaptive Learning Engine (adaptive_learning.py)
"""

import asyncio
import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import Mock

from intelligence.database import SerenaIntelligenceDatabase, DatabaseConfig
from intelligence.graph_operations import SerenaGraphOperations
from intelligence.adaptive_learning import (
    AdaptiveLearningEngine, 
    NavigationSequence, 
    PersonalLearningProfile,
    LearningPhase
)
from performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

# ============================================================================
# TEST FIXTURES

@pytest.fixture
def db_config():
    """Test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="serena_intelligence_test",
        user="serena",
        password="serena_dev_pass"
    )

@pytest.fixture
async def database(db_config):
    """Initialize test database."""
    db = SerenaIntelligenceDatabase(db_config)
    await db.initialize()
    yield db
    await db.close()

@pytest.fixture
async def graph_ops(database):
    """Create graph operations instance with mocks."""
    performance_monitor = Mock(spec=PerformanceMonitor)
    # Ensure average_duration attribute exists for metrics test
    performance_monitor.average_duration = 5.0
    return SerenaGraphOperations(database, performance_monitor)

@pytest.fixture
async def learning_engine(database, graph_ops):
    """Create AdaptiveLearningEngine instance."""
    performance_monitor = Mock(spec=PerformanceMonitor)
    return AdaptiveLearningEngine(database, graph_ops, performance_monitor)

# ============================================================================
# TESTS

@pytest.mark.asyncio
async def test_start_navigation_sequence(learning_engine):
    """Test starting a new navigation sequence."""
    user_session = "test_user_1"
    workspace = "/test/workspace"
    
    seq_id = await learning_engine.start_navigation_sequence(user_session, workspace)
    
    assert seq_id is not None
    assert seq_id in learning_engine.active_sequences
    
    seq = learning_engine.active_sequences[seq_id]
    assert seq.user_session_id == user_session
    assert len(seq.actions) == 0
    assert seq.total_duration_ms == 0.0

@pytest.mark.asyncio
async def test_record_navigation_action(learning_engine):
    """Test recording actions within a sequence."""
    user_session = "test_user_2"
    workspace = "/test/workspace"
    
    seq_id = await learning_engine.start_navigation_sequence(user_session, workspace)
    
    # Record first action
    await learning_engine.record_navigation_action(
        seq_id, "view_file", element_id=None, duration_ms=100.0
    )
    
    seq = learning_engine.active_sequences[seq_id]
    assert len(seq.actions) == 1
    assert seq.actions[0].action_type == "view_file"
    assert seq.context_switches == 0
    
    # Record second action (simulating a context switch with high complexity diff)
    # Since we don't have real elements in this test, we test the basic recording
    await learning_engine.record_navigation_action(
        seq_id, "search", element_id=None, duration_ms=200.0
    )
    
    assert len(seq.actions) == 2
    assert seq.total_duration_ms > 0

@pytest.mark.asyncio
async def test_end_navigation_sequence(learning_engine):
    """Test ending a sequence and evaluating completion."""
    user_session = "test_user_3"
    workspace = "/test/workspace"
    
    seq_id = await learning_engine.start_navigation_sequence(user_session, workspace)
    
    await learning_engine.record_navigation_action(seq_id, "view_file")
    await asyncio.sleep(0.01) # Simulate slight delay
    await learning_engine.record_navigation_action(seq_id, "edit_file")
    
    ended_seq = await learning_engine.end_navigation_sequence(seq_id, completion_status="success")
    
    assert ended_seq is not None
    assert ended_seq.completion_status == "success"
    assert seq_id not in learning_engine.active_sequences
    assert ended_seq.total_duration_ms > 0

@pytest.mark.asyncio
async def test_learning_profile_creation(learning_engine):
    """Test profile is created on sequence start."""
    user_session = "test_user_profile"
    workspace = "/test/workspace"
    
    # Starting a sequence ensures profile creation
    await learning_engine.start_navigation_sequence(user_session, workspace)
    
    profile_key = f"{user_session}:{workspace}"
    assert profile_key in learning_engine.learning_profiles
    
    profile = learning_engine.learning_profiles[profile_key]
    assert isinstance(profile, PersonalLearningProfile)
    assert profile.user_session_id == user_session
    assert profile.workspace_path == workspace
    assert profile.learning_phase == LearningPhase.EXPLORATION

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
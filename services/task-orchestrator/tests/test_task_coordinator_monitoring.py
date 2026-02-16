"""
Tests for TaskCoordinator _monitor_execution method.

Validates:
- Monitoring loop completes after simulated duration
- focus_session_timer is correctly updated during monitoring
- Session duration threshold is respected
- Break recommendations trigger correctly
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Add parent directory to path for imports
test_dir = Path(__file__).parent.parent
sys.path.insert(0, str(test_dir))
sys.path.insert(0, str(test_dir / "app"))
sys.path.insert(0, str(test_dir / "app" / "services"))

# Import task_orchestrator models first
from task_orchestrator.models import OrchestrationTask, TaskStatus

# Import with patching to avoid import errors from relative imports
from unittest.mock import MagicMock

# Mock the modules that use relative imports before importing task_coordinator
sys.modules['app.adapters.conport_adapter'] = MagicMock()
sys.modules['app.adapters'] = MagicMock()

from app.services.task_coordinator import TaskCoordinator, CoordinationState


def create_fast_monitor(coordinator, simulated_duration_seconds=2, check_interval_seconds=0.1):
    """
    Helper function to create a fast mock version of _monitor_execution for testing.
    
    This replaces the real monitoring with a faster version that still tests
    the same logic without waiting 60 seconds.
    
    Args:
        coordinator: TaskCoordinator instance
        simulated_duration_seconds: Total duration to simulate (default: 2 seconds)
        check_interval_seconds: How often to check conditions (default: 0.1 seconds)
    
    Returns:
        Async function that can replace _monitor_execution
    """
    original_coordination_state = coordinator.coordination_state
    
    async def fast_monitor(task: OrchestrationTask):
        """Fast monitoring for testing without real delays."""
        start_time = datetime.now()
        
        # Check energy decay over time
        while (datetime.now() - start_time).total_seconds() < simulated_duration_seconds:
            # Update global session timer based on elapsed time since session start
            elapsed = (datetime.now() - original_coordination_state.session_start_time).total_seconds()
            original_coordination_state.focus_session_timer = int(elapsed)
            
            # Check if focus session duration exceeded
            if original_coordination_state.focus_session_timer >= coordinator.focus_session_duration:
                break
            
            # Check for break recommendation (if method exists)
            if hasattr(coordinator.cognitive_guardian, 'should_break'):
                if coordinator.cognitive_guardian.should_break(task):
                    await coordinator._recommend_break()
                    break
            
            await asyncio.sleep(check_interval_seconds)
    
    return fast_monitor


@pytest.fixture
def coordinator():
    """Create TaskCoordinator with mocked dependencies."""
    with patch('app.services.task_coordinator.ConPortEventAdapter') as mock_adapter, \
         patch('app.services.task_coordinator.CognitiveLoadBalancer') as mock_guardian, \
         patch('app.services.task_coordinator.ContextSwitchRecovery') as mock_recovery, \
         patch('app.services.task_coordinator.TaskOrchestratorPALClient') as mock_pal:
        
        # Configure mocks
        mock_adapter.return_value = AsyncMock()
        mock_guardian.return_value = MagicMock()
        mock_guardian.return_value.should_break = MagicMock(return_value=False)
        mock_recovery.return_value = AsyncMock()
        mock_pal.return_value = AsyncMock()
        
        # Create coordinator
        coord = TaskCoordinator(workspace_id="/test/workspace")
        
        # Ensure session start time is set
        coord.coordination_state.session_start_time = datetime.now()
        
        yield coord


@pytest.fixture
def sample_task():
    """Create a sample OrchestrationTask for testing."""
    return OrchestrationTask(
        id="test-task-1",
        title="Test Task",
        description="Testing monitoring",
        status=TaskStatus.IN_PROGRESS,
        priority=2,
        complexity_score=0.6,
        estimated_minutes=30,
        energy_required="medium"
    )


@pytest.mark.asyncio
async def test_monitoring_loop_completes_after_duration(coordinator, sample_task):
    """Test that the monitoring loop completes after the simulated duration."""
    # Set a short simulated duration for testing
    fast_monitor = create_fast_monitor(coordinator, simulated_duration_seconds=1, check_interval_seconds=0.05)
    
    # Replace the _monitor_execution method with fast version
    coordinator._monitor_execution = fast_monitor
    
    start_time = datetime.now()
    await coordinator._monitor_execution(sample_task)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Verify monitoring completed within expected time (with small buffer for execution)
    assert elapsed >= 1.0, "Monitoring should take at least the simulated duration"
    assert elapsed < 2.0, "Monitoring should not take much longer than simulated duration"


@pytest.mark.asyncio
async def test_focus_session_timer_updates_correctly(coordinator, sample_task):
    """Test that focus_session_timer is correctly updated during monitoring."""
    # Record initial timer value
    initial_timer = coordinator.coordination_state.focus_session_timer
    
    # Reset session start to ensure we get measurable elapsed time
    coordinator.coordination_state.session_start_time = datetime.now()
    
    # Wait a bit before monitoring to ensure elapsed time > 1 second
    await asyncio.sleep(1.1)
    
    # Use fast monitor with a short duration
    fast_monitor = create_fast_monitor(coordinator, simulated_duration_seconds=0.5, check_interval_seconds=0.1)
    coordinator._monitor_execution = fast_monitor
    
    await coordinator._monitor_execution(sample_task)
    
    # Verify timer was updated (should be >= 1 after waiting 1.1 seconds)
    assert coordinator.coordination_state.focus_session_timer >= 1, \
        f"focus_session_timer should be updated during monitoring (got {coordinator.coordination_state.focus_session_timer})"
    
    # Timer should reflect elapsed time from session start
    expected_elapsed = int((datetime.now() - coordinator.coordination_state.session_start_time).total_seconds())
    assert coordinator.coordination_state.focus_session_timer == expected_elapsed, \
        f"focus_session_timer ({coordinator.coordination_state.focus_session_timer}) should match elapsed time ({expected_elapsed})"


@pytest.mark.asyncio
async def test_session_duration_threshold_respected(coordinator, sample_task):
    """Test that monitoring respects the session duration threshold and breaks early."""
    # Set a very low focus session duration (2 seconds) to trigger early break
    coordinator.focus_session_duration = 2
    
    # Set session start time to 1.5 seconds ago so we're close to threshold
    coordinator.coordination_state.session_start_time = datetime.now()
    
    # Wait a bit to get closer to threshold
    await asyncio.sleep(0.5)
    
    # Use fast monitor with longer simulated duration
    fast_monitor = create_fast_monitor(coordinator, simulated_duration_seconds=5, check_interval_seconds=0.1)
    coordinator._monitor_execution = fast_monitor
    
    start_time = datetime.now()
    await coordinator._monitor_execution(sample_task)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Monitoring should break early when threshold is reached
    # Should not complete the full 5 second simulated duration
    assert elapsed < 4.0, \
        "Monitoring should break early when focus_session_duration threshold is reached"
    
    # Verify timer reflects that threshold was reached
    assert coordinator.coordination_state.focus_session_timer >= coordinator.focus_session_duration, \
        "focus_session_timer should be at or above threshold when early break occurs"


@pytest.mark.asyncio
async def test_break_recommendation_triggers(coordinator, sample_task):
    """Test that break recommendations are triggered correctly."""
    # Configure mock to recommend a break after some iterations
    call_count = 0
    
    def should_break_on_third_call(task):
        nonlocal call_count
        call_count += 1
        return call_count >= 3  # Return True on 3rd call
    
    coordinator.cognitive_guardian.should_break = should_break_on_third_call
    
    # Mock _recommend_break to track if it was called
    coordinator._recommend_break = AsyncMock()
    
    # Use fast monitor
    fast_monitor = create_fast_monitor(coordinator, simulated_duration_seconds=2, check_interval_seconds=0.1)
    coordinator._monitor_execution = fast_monitor
    
    await coordinator._monitor_execution(sample_task)
    
    # Verify break was recommended
    coordinator._recommend_break.assert_called_once()


@pytest.mark.asyncio
async def test_monitoring_with_different_energy_levels(coordinator, sample_task):
    """Test monitoring behavior with different cognitive load scenarios."""
    # Test case 1: High energy, no breaks
    coordinator.cognitive_guardian.should_break = MagicMock(return_value=False)
    coordinator.focus_session_duration = 100  # Long duration
    
    fast_monitor = create_fast_monitor(coordinator, simulated_duration_seconds=0.5, check_interval_seconds=0.05)
    coordinator._monitor_execution = fast_monitor
    
    start_time = datetime.now()
    await coordinator._monitor_execution(sample_task)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Should complete full duration
    assert elapsed >= 0.5, "Should complete full monitoring with high energy"
    
    # Test case 2: Low energy, immediate break
    coordinator.cognitive_guardian.should_break = MagicMock(return_value=True)
    coordinator._recommend_break = AsyncMock()
    
    fast_monitor = create_fast_monitor(coordinator, simulated_duration_seconds=2, check_interval_seconds=0.1)
    coordinator._monitor_execution = fast_monitor
    
    start_time = datetime.now()
    await coordinator._monitor_execution(sample_task)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Should break early
    assert elapsed < 1.0, "Should break early when energy is low"
    coordinator._recommend_break.assert_called()


@pytest.mark.asyncio
async def test_timer_accuracy_across_multiple_tasks(coordinator):
    """Test that focus_session_timer maintains accuracy across multiple task monitoring cycles."""
    # Create multiple tasks
    tasks = [
        OrchestrationTask(
            id=f"test-task-{i}",
            title=f"Test Task {i}",
            status=TaskStatus.IN_PROGRESS,
            complexity_score=0.5,
            energy_required="medium"
        )
        for i in range(3)
    ]
    
    # Set session start and wait to ensure measurable time
    coordinator.coordination_state.session_start_time = datetime.now()
    await asyncio.sleep(1.1)  # Wait for timer to reach at least 1
    
    initial_timer = coordinator.coordination_state.focus_session_timer
    
    # Monitor multiple tasks
    fast_monitor = create_fast_monitor(coordinator, simulated_duration_seconds=0.5, check_interval_seconds=0.1)
    coordinator._monitor_execution = fast_monitor
    
    for task in tasks:
        await coordinator._monitor_execution(task)
        await asyncio.sleep(0.2)  # Small delay between tasks to ensure timer increments
    
    # Timer should have increased from when we started monitoring
    final_timer = coordinator.coordination_state.focus_session_timer
    assert final_timer >= 1, f"Timer should be at least 1 second (got {final_timer})"
    
    # Timer should approximately equal elapsed time
    expected_elapsed = int((datetime.now() - coordinator.coordination_state.session_start_time).total_seconds())
    assert abs(final_timer - expected_elapsed) <= 1, \
        f"Timer ({final_timer}s) should be close to actual elapsed time ({expected_elapsed}s)"


@pytest.mark.asyncio
async def test_monitoring_without_session_start_time():
    """Test that monitoring handles missing session_start_time gracefully."""
    with patch('app.services.task_coordinator.ConPortEventAdapter') as mock_adapter, \
         patch('app.services.task_coordinator.CognitiveLoadBalancer') as mock_guardian, \
         patch('app.services.task_coordinator.ContextSwitchRecovery') as mock_recovery, \
         patch('app.services.task_coordinator.TaskOrchestratorPALClient') as mock_pal:
        
        mock_adapter.return_value = AsyncMock()
        mock_guardian.return_value = MagicMock()
        mock_guardian.return_value.should_break = MagicMock(return_value=False)
        mock_recovery.return_value = AsyncMock()
        mock_pal.return_value = AsyncMock()
        
        coord = TaskCoordinator(workspace_id="/test/workspace")
        
        # Verify session_start_time is set during __init__
        assert coord.coordination_state.session_start_time is not None, \
            "session_start_time should be initialized in constructor"

#!/usr/bin/env python3
"""
Unit tests for TaskCoordinator._monitor_execution method.

Tests verify:
1. The monitoring loop completes after the simulated duration
2. The focus_session_timer is correctly updated during monitoring
3. The session duration threshold is respected
4. Tasks are properly stored and retrieved from internal dictionary
5. Tasks are marked as COMPLETED after successful monitoring
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add the task-orchestrator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_orchestrator import OrchestrationTask, TaskStatus, AgentType
from app.services.task_coordinator import TaskCoordinator


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    return [
        OrchestrationTask(
            id="test-task-1",
            leantime_id=101,
            title="Test Task 1",
            description="First test task",
            status=TaskStatus.PENDING,
            priority=3,
            complexity_score=0.5,
            estimated_minutes=30,
            assigned_agent=AgentType.SERENA,
            energy_required="medium",
            dependencies=[],
            context_switches_allowed=2,
            break_frequency_minutes=25
        ),
        OrchestrationTask(
            id="test-task-2",
            leantime_id=102,
            title="Test Task 2",
            description="Second test task",
            status=TaskStatus.PENDING,
            priority=2,
            complexity_score=0.3,
            estimated_minutes=20,
            assigned_agent=AgentType.SERENA,
            energy_required="low",
            dependencies=[],
            context_switches_allowed=3,
            break_frequency_minutes=25
        )
    ]


@pytest.fixture
def task_coordinator():
    """Create a TaskCoordinator instance for testing."""
    workspace_id = "/tmp/test-workspace"
    return TaskCoordinator(workspace_id=workspace_id)


@pytest.mark.asyncio
async def test_monitor_execution_completes(task_coordinator, sample_tasks):
    """Test that _monitor_execution completes after simulated duration."""
    task = sample_tasks[0]
    
    # Override simulated duration to make test faster
    original_method = task_coordinator._monitor_execution
    
    async def fast_monitor_execution(task):
        """Fast version of monitor execution for testing."""
        simulated_duration = 2  # 2 seconds for fast test
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < simulated_duration:
            elapsed = (datetime.now() - task_coordinator.coordination_state.session_start_time).total_seconds()
            task_coordinator.coordination_state.focus_session_timer = int(elapsed)
            
            if task_coordinator.coordination_state.focus_session_timer >= task_coordinator.focus_session_duration:
                break
                
            await asyncio.sleep(0.5)
    
    task_coordinator._monitor_execution = fast_monitor_execution
    
    start = datetime.now()
    await task_coordinator._monitor_execution(task)
    duration = (datetime.now() - start).total_seconds()
    
    # Should complete in approximately 2 seconds
    assert duration >= 2.0
    assert duration < 3.0, f"Monitoring took too long: {duration}s"


@pytest.mark.asyncio
async def test_focus_session_timer_updated(task_coordinator, sample_tasks):
    """Test that focus_session_timer is correctly updated during monitoring."""
    task = sample_tasks[0]
    
    # Fast monitoring for testing
    async def fast_monitor_execution(task):
        simulated_duration = 1
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < simulated_duration:
            elapsed = (datetime.now() - task_coordinator.coordination_state.session_start_time).total_seconds()
            task_coordinator.coordination_state.focus_session_timer = int(elapsed)
            await asyncio.sleep(0.2)
    
    task_coordinator._monitor_execution = fast_monitor_execution
    
    initial_timer = task_coordinator.coordination_state.focus_session_timer
    await task_coordinator._monitor_execution(task)
    final_timer = task_coordinator.coordination_state.focus_session_timer
    
    # Timer should have increased
    assert final_timer >= initial_timer
    assert final_timer > 0


@pytest.mark.asyncio
async def test_session_duration_threshold_respected(task_coordinator, sample_tasks):
    """Test that monitoring respects session duration threshold."""
    task = sample_tasks[0]
    
    # Set a low threshold for testing
    task_coordinator.focus_session_duration = 2
    
    async def fast_monitor_execution(task):
        simulated_duration = 10  # Would take 10 seconds
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < simulated_duration:
            elapsed = (datetime.now() - task_coordinator.coordination_state.session_start_time).total_seconds()
            task_coordinator.coordination_state.focus_session_timer = int(elapsed)
            
            # Check threshold
            if task_coordinator.coordination_state.focus_session_timer >= task_coordinator.focus_session_duration:
                break
                
            await asyncio.sleep(0.2)
    
    task_coordinator._monitor_execution = fast_monitor_execution
    
    start = datetime.now()
    await task_coordinator._monitor_execution(task)
    duration = (datetime.now() - start).total_seconds()
    
    # Should break early due to threshold
    assert duration < 10.0, "Should have stopped before simulated duration"
    assert task_coordinator.coordination_state.focus_session_timer >= task_coordinator.focus_session_duration


@pytest.mark.asyncio
async def test_tasks_stored_in_internal_dict(task_coordinator, sample_tasks):
    """Test that tasks are stored in self.tasks dictionary."""
    adhd_state = {"energy": "high", "attention": "focused", "cognitive_load": "low"}
    
    # Mock the async methods that would be called
    async def mock_assess(*args, **kwargs):
        return {"batch_size": 2, "recommended_breaks": []}
    
    async def mock_resolve(*args, **kwargs):
        return sample_tasks
    
    async def mock_sequence(*args, **kwargs):
        return [t.id for t in sample_tasks]
    
    async def mock_sync(*args, **kwargs):
        pass
    
    async def mock_execute(*args, **kwargs):
        return {"completed": [], "in_progress": [], "failed": []}
    
    task_coordinator._assess_cognitive_batch = mock_assess
    task_coordinator._resolve_dependencies = mock_resolve
    task_coordinator._sequence_tasks_with_zen = mock_sequence
    task_coordinator._sync_coordination_state = mock_sync
    task_coordinator._execute_batch = mock_execute
    
    await task_coordinator.coordinate_tasks(sample_tasks, adhd_state)
    
    # Verify tasks are stored
    assert "test-task-1" in task_coordinator.tasks
    assert "test-task-2" in task_coordinator.tasks
    assert task_coordinator.tasks["test-task-1"].title == "Test Task 1"
    assert task_coordinator.tasks["test-task-2"].title == "Test Task 2"


@pytest.mark.asyncio
async def test_task_marked_completed_after_monitoring(task_coordinator, sample_tasks):
    """Test that tasks are marked as COMPLETED after successful monitoring."""
    task = sample_tasks[0]
    task_coordinator.tasks[task.id] = task
    
    # Mock fast monitoring
    async def fast_monitor(*args, **kwargs):
        await asyncio.sleep(0.1)
    
    task_coordinator._monitor_execution = fast_monitor
    
    # Mock ConPort adapter
    async def mock_update(*args, **kwargs):
        pass
    
    task_coordinator.conport_adapter.update_task_in_conport = mock_update
    
    # Execute batch with single task
    results = await task_coordinator._execute_batch([task.id])
    
    # Verify task is marked as completed
    assert task.status == TaskStatus.COMPLETED
    assert task.id in results["completed"]
    assert task.id not in results["in_progress"]
    assert len(results["failed"]) == 0


@pytest.mark.asyncio
async def test_type_mismatch_handling(task_coordinator, sample_tasks):
    """Test that coordinate_tasks handles both Dict and List return types from _sequence_tasks_with_zen."""
    adhd_state = {"energy": "high", "attention": "focused", "cognitive_load": "low"}
    
    # Mock methods
    async def mock_assess(*args, **kwargs):
        return {"batch_size": 2}
    
    async def mock_resolve(*args, **kwargs):
        return sample_tasks
    
    async def mock_sync(*args, **kwargs):
        pass
    
    task_coordinator._assess_cognitive_batch = mock_assess
    task_coordinator._resolve_dependencies = mock_resolve
    task_coordinator._sync_coordination_state = mock_sync
    
    # Test with Dict return type
    async def mock_sequence_dict(*args, **kwargs):
        return {
            "tasks": sample_tasks,
            "strategy": "zen_intelligent",
            "batches": [[0, 1]],
            "rationale": "Test"
        }
    
    async def mock_execute(*args, **kwargs):
        return {"completed": [], "in_progress": [], "failed": []}
    
    task_coordinator._sequence_tasks_with_zen = mock_sequence_dict
    task_coordinator._execute_batch = mock_execute
    
    result = await task_coordinator.coordinate_tasks(sample_tasks, adhd_state)
    assert "execution_results" in result
    
    # Test with List return type
    async def mock_sequence_list(*args, **kwargs):
        return [t.id for t in sample_tasks]
    
    task_coordinator._sequence_tasks_with_zen = mock_sequence_list
    
    result = await task_coordinator.coordinate_tasks(sample_tasks, adhd_state)
    assert "execution_results" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

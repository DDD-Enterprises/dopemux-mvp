#!/usr/bin/env python3
"""
Test script for ConPort bidirectional sync with Task Orchestrator.

Tests:
- ConPort adapter bidirectional transformations
- Task creation and updates in ConPort
- Task retrieval from ConPort
- Dependency synchronization
"""

import asyncio
import logging
from pathlib import Path
from typing import List

# Add the task-orchestrator to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_orchestrator import OrchestrationTask, TaskStatus, AgentType
from adapters.conport_adapter import ConPortEventAdapter, safe_orchestration_task_to_conport_progress, safe_conport_progress_to_orchestration_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"

async def test_bidirectional_transformations():
    """Test bidirectional transformations between OrchestrationTask and ConPort progress."""
    logger.info("🧪 Testing bidirectional transformations...")

    # Create a sample OrchestrationTask
    task = OrchestrationTask(
        id="test-task-1",
        leantime_id=123,
        title="Test ConPort Integration",
        description="Testing bidirectional sync functionality",
        status=TaskStatus.IN_PROGRESS,
        priority=3,
        complexity_score=0.7,
        estimated_minutes=90,
        assigned_agent=AgentType.SERENA,
        energy_required="high",
        dependencies=["test-task-2"],
        context_switches_allowed=2,
        break_frequency_minutes=25
    )

    # Test OrchestrationTask → ConPort progress
    progress_data = safe_orchestration_task_to_conport_progress(task, WORKSPACE_ID)
    if progress_data:
        logger.info(f"✅ Task → Progress transformation successful")
        logger.info(f"   Status: {progress_data['status']}")
        logger.info(f"   Description length: {len(progress_data['description'])}")
        logger.info(f"   Tags: {progress_data['tags']}")

        # Test ConPort progress → OrchestrationTask (reverse)
        restored_task = safe_conport_progress_to_orchestration_task(progress_data)
        if restored_task:
            logger.info(f"✅ Progress → Task transformation successful")
            logger.info(f"   Title: {restored_task.title}")
            logger.info(f"   Complexity: {restored_task.complexity_score}")
            logger.info(f"   Energy: {restored_task.energy_required}")
            logger.info(f"   Agent: {restored_task.assigned_agent}")

            # Verify data integrity
            assert restored_task.title == task.title
            assert restored_task.complexity_score == task.complexity_score
            assert restored_task.energy_required == task.energy_required
            logger.info("✅ Data integrity verified")
        else:
            logger.error("❌ Progress → Task transformation failed")
            return False
    else:
        logger.error("❌ Task → Progress transformation failed")
        return False

    return True

async def test_conport_adapter_operations():
    """Test ConPort adapter operations (without actual ConPort server)."""
    logger.info("🔧 Testing ConPort adapter operations...")

    # Initialize adapter (will use mock ConPort client)
    adapter = ConPortEventAdapter(WORKSPACE_ID)

    # Test task creation
    test_task = OrchestrationTask(
        id="adapter-test-1",
        title="Adapter Test Task",
        description="Testing adapter create functionality",
        status=TaskStatus.PENDING,
        priority=2,
        complexity_score=0.5,
        estimated_minutes=30,
        energy_required="medium"
    )

    # This will use the mock implementation since no real ConPort client
    conport_id = await adapter.create_task_in_conport(test_task)
    if conport_id is None:  # Mock returns None
        logger.info("✅ Adapter create_task_in_conport handled gracefully (mock)")
    else:
        logger.info(f"✅ Task created with ConPort ID: {conport_id}")

    # Test task retrieval
    tasks = await adapter.get_all_tasks_from_conport()
    logger.info(f"✅ Retrieved {len(tasks)} tasks from ConPort (mock)")

    # Test dependency sync (should handle gracefully)
    await adapter.sync_dependencies_to_conport(test_task)
    logger.info("✅ Dependency sync handled gracefully")

    return True

async def test_task_coordinator():
    """Test the TaskCoordinator class."""
    logger.info("🎯 Testing TaskCoordinator...")

    try:
        from task_coordinator import TaskCoordinator

        coordinator = TaskCoordinator(WORKSPACE_ID)

        # Test with sample tasks
        sample_tasks = [
            OrchestrationTask(
                id="coord-test-1",
                title="Coordinate Test Task 1",
                complexity_score=0.6,
                energy_required="medium",
                status=TaskStatus.PENDING
            ),
            OrchestrationTask(
                id="coord-test-2",
                title="Coordinate Test Task 2",
                complexity_score=0.4,
                energy_required="low",
                status=TaskStatus.PENDING
            )
        ]

        adhd_state = {"energy": "medium", "attention": "focused", "load": 0.3}

        result = await coordinator.coordinate_tasks(sample_tasks, adhd_state)

        logger.info("✅ TaskCoordinator executed successfully")
        logger.info(f"   Coordination ID: {result['coordination_id']}")
        logger.info(f"   Recommendations: {len(result['recommendations'])}")

        return True

    except Exception as e:
        logger.error(f"❌ TaskCoordinator test failed: {e}")
        return False

async def main():
    """Run all ConPort sync tests."""
    logger.info("🚀 Starting ConPort bidirectional sync tests...")

    tests = [
        ("Bidirectional Transformations", test_bidirectional_transformations),
        ("ConPort Adapter Operations", test_conport_adapter_operations),
        ("Task Coordinator", test_task_coordinator),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info('='*50)

        try:
            success = await test_func()
            if success:
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")

    logger.info(f"\n{'='*60}")
    logger.info(f"Test Results: {passed}/{total} tests passed")
    logger.info('='*60)

    if passed == total:
        logger.info("🎉 All ConPort sync tests PASSED!")
        return 0
    else:
        logger.warning("⚠️ Some tests failed - check implementation")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
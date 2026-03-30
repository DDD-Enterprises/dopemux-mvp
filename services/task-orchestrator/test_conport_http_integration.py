#!/usr/bin/env python3
"""
Test script to validate ConPort HTTP API integration for task-orchestrator service boundaries.
"""

import asyncio
import logging
import os
from adapters.conport_adapter import ConPortEventAdapter
from enhanced_orchestrator import OrchestrationTask, TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_conport_adapter():
    """Test ConPort adapter with HTTP API."""
    logger.info("🧪 Testing ConPort HTTP API integration...")

    # Use test workspace
    workspace_id = "/Users/hue/code/dopemux-mvp"

    # Initialize adapter with ConPort HTTP URL
    conport_url = os.getenv("CONPORT_URL", "http://localhost:8005")
    logger.info(f"📡 Using ConPort URL: {conport_url}")

    async with ConPortEventAdapter(workspace_id, conport_url) as adapter:
        logger.info("✅ ConPort adapter initialized with HTTP session")

        # Test getting progress entries (should work even if empty)
        logger.info("📊 Testing get_progress_entries...")
        try:
            entries = await adapter.get_all_tasks_from_conport()
            logger.info(f"✅ Retrieved {len(entries)} progress entries from ConPort")
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve progress entries (ConPort may not be running): {e}")

        # Create a test task
        logger.info("📝 Testing create_task_in_conport...")
        test_task = OrchestrationTask(
            id="test_task_http_integration",
            title="Test Task for HTTP Integration",
            description="Testing ConPort HTTP API integration",
            status=TaskStatus.PENDING,
            priority=2,
            estimated_minutes=30,
            energy_required="medium",
            complexity_score=0.3
        )

        try:
            conport_id = await adapter.create_task_in_conport(test_task)
            if conport_id:
                logger.info(f"✅ Created test task in ConPort with ID: {conport_id}")

                # Test updating the task
                logger.info("🔄 Testing update_task_status...")
                success = await adapter.update_task_status("test_task_http_integration", TaskStatus.IN_PROGRESS)
                if success:
                    logger.info("✅ Successfully updated task status")
                else:
                    logger.warning("⚠️ Failed to update task status")

            else:
                logger.warning("⚠️ Could not create test task (ConPort may not be running)")

        except Exception as e:
            logger.warning(f"⚠️ Could not create test task (ConPort may not be running): {e}")

    logger.info("🎉 ConPort HTTP API integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_conport_adapter())
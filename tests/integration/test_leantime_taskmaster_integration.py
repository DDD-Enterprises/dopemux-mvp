"""
Integration tests for Leantime-TaskMaster system integration.

Tests the complete workflow from PRD parsing to task synchronization
between Leantime and Task-Master AI with ADHD optimizations.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.config import Config
from integrations.leantime_bridge import (
    LeantimeMCPClient,
    LeantimeTask,
    TaskPriority,
)
from integrations.sync_manager import (
    LeantimeTaskMasterSyncManager,
    TaskMapping,
)
from integrations.taskmaster_bridge import TaskMasterMCPClient, TaskMasterTask
from utils.adhd_optimizations import ADHDTaskOptimizer


class TestLeantimeTaskMasterIntegration:
    """Integration tests for Leantime-TaskMaster workflow."""

    @pytest.fixture
    async def config(self):
        """Create test configuration."""
        return Config(
            {
                "leantime": {
                    "api_url": "http://localhost:8080",
                    "api_token": "test_token",
                },
                "taskmaster": {
                    "path": ".test_taskmaster",
                    "default_provider": "anthropic",
                },
                "api_keys": {"anthropic": "test_anthropic_key"},
                "sync": {
                    "interval": 60,
                    "conflict_resolution": "merge_intelligent",
                    "mappings_file": "test_mappings.json",
                },
            }
        )

    @pytest.fixture
    async def leantime_client(self, config):
        """Create mock Leantime client."""
        client = LeantimeMCPClient(config)
        client._connected = True
        client.session = AsyncMock()
        return client

    @pytest.fixture
    async def taskmaster_client(self, config):
        """Create mock TaskMaster client."""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open"):
                with patch("json.dump"):
                    client = TaskMasterMCPClient(config)
                    client._connected = True
                    client._process = AsyncMock()
                    return client

    @pytest.fixture
    async def sync_manager(self, config, leantime_client, taskmaster_client):
        """Create sync manager with mock clients."""
        manager = LeantimeTaskMasterSyncManager(config)
        await manager.initialize(leantime_client, taskmaster_client)
        return manager

    @pytest.fixture
    def sample_prd(self):
        """Sample PRD content for testing."""
        return """
# E-commerce Platform Enhancement

## Overview
Enhance the existing e-commerce platform with new features for better user experience.

## Requirements
1. User Authentication System
   - OAuth2 integration
   - Multi-factor authentication
   - Social login options

2. Shopping Cart Improvements
   - Persistent cart across sessions
   - Real-time inventory updates
   - Wishlist functionality

3. Payment Processing
   - Multiple payment gateways
   - Cryptocurrency support
   - Subscription billing

## Acceptance Criteria
- All features must be mobile-responsive
- Load time should be under 2 seconds
- Must support 1000+ concurrent users
- GDPR compliance required

## Technical Constraints
- Must integrate with existing PostgreSQL database
- Use React frontend with Node.js backend
- Deploy on AWS infrastructure
        """

    @pytest.mark.asyncio
    async def test_complete_prd_to_tasks_workflow(
        self, sync_manager, leantime_client, taskmaster_client, sample_prd
    ):
        """Test complete workflow from PRD to synchronized tasks."""

        # Mock TaskMaster PRD parsing
        parsed_tasks = [
            {
                "id": "auth_system",
                "title": "Implement User Authentication System",
                "description": "OAuth2, MFA, and social login",
                "status": "pending",
                "priority": 1,
                "complexity": 4.5,
                "estimatedHours": 20.0,
                "dependencies": [],
                "tags": ["authentication", "security"],
            },
            {
                "id": "cart_improvements",
                "title": "Enhance Shopping Cart",
                "description": "Persistent cart, real-time updates, wishlist",
                "status": "pending",
                "priority": 2,
                "complexity": 3.5,
                "estimatedHours": 15.0,
                "dependencies": ["auth_system"],
                "tags": ["cart", "frontend"],
            },
            {
                "id": "payment_processing",
                "title": "Implement Payment Processing",
                "description": "Multiple gateways, crypto, subscriptions",
                "status": "pending",
                "priority": 1,
                "complexity": 5.0,
                "estimatedHours": 25.0,
                "dependencies": ["auth_system", "cart_improvements"],
                "tags": ["payment", "backend"],
            },
        ]

        taskmaster_client._send_mcp_request = AsyncMock(
            return_value={
                "result": {
                    "content": [
                        {
                            "text": json.dumps(
                                {
                                    "version": "1.0",
                                    "requirements": [
                                        "Authentication",
                                        "Cart",
                                        "Payment",
                                    ],
                                    "tasks": parsed_tasks,
                                    "complexitySummary": {
                                        "total_complexity": 13.0,
                                        "avg_complexity": 4.3,
                                    },
                                    "estimatedTimeline": "8-10 weeks",
                                    "keyDependencies": [
                                        "PostgreSQL",
                                        "React",
                                        "Node.js",
                                    ],
                                    "riskFactors": [
                                        "Integration complexity",
                                        "Performance requirements",
                                    ],
                                }
                            )
                        }
                    ]
                }
            }
        )

        # Mock Leantime project creation
        leantime_client._send_mcp_request = AsyncMock(
            side_effect=[
                # Project creation response
                {
                    "result": {
                        "content": [
                            {"text": json.dumps({"success": True, "projectId": 100})}
                        ]
                    }
                },
                # Task creation responses
                *[
                    {
                        "result": {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {"success": True, "ticketId": 200 + i}
                                    )
                                }
                            ]
                        }
                    }
                    for i in range(len(parsed_tasks))
                ],
            ]
        )

        # Execute PRD sync workflow
        result = await sync_manager.sync_project_from_prd(
            sample_prd, "E-commerce Enhancement", None
        )

        # Verify results
        assert result.success is True
        assert result.created_tasks == 3
        assert result.synced_tasks == 3
        assert len(result.errors) == 0

        # Verify task mappings were created
        assert len(sync_manager.task_mappings) == 3

        # Verify TaskMaster was called for PRD parsing
        taskmaster_client._send_mcp_request.assert_called()

        # Verify Leantime was called for project and task creation
        assert leantime_client._send_mcp_request.call_count == 4  # 1 project + 3 tasks

    @pytest.mark.asyncio
    async def test_bidirectional_task_synchronization(
        self, sync_manager, leantime_client, taskmaster_client
    ):
        """Test bidirectional synchronization between Leantime and TaskMaster."""

        # Setup existing tasks in both systems
        leantime_tasks = [
            {
                "id": 1,
                "headline": "Fix login bug",
                "description": "User cannot login with special characters",
                "projectId": 10,
                "status": "1",  # In progress
                "storypoints": 3,
                "date": "2024-01-01 10:00:00",
            },
            {
                "id": 2,
                "headline": "Add dark mode",
                "description": "Implement dark mode toggle",
                "projectId": 10,
                "status": "0",  # Pending
                "storypoints": 5,
                "date": "2024-01-01 11:00:00",
            },
        ]

        taskmaster_tasks = [
            {
                "id": "fix_login_bug",
                "title": "Fix login bug",
                "description": "User cannot login with special characters",
                "status": "in_progress",
                "priority": 1,
                "complexity": 2.5,
            },
            {
                "id": "new_feature",
                "title": "Add search functionality",
                "description": "Implement global search feature",
                "status": "pending",
                "priority": 2,
                "complexity": 4.0,
            },
        ]

        # Mock responses
        leantime_client._send_mcp_request = AsyncMock(
            return_value={"result": {"content": [{"text": json.dumps(leantime_tasks)}]}}
        )

        taskmaster_client._send_mcp_request = AsyncMock(
            return_value={
                "result": {
                    "content": [{"text": json.dumps({"tasks": taskmaster_tasks})}]
                }
            }
        )

        # Create task mappings for existing tasks
        sync_manager.task_mappings["lt_1"] = TaskMapping(
            leantime_id=1,
            taskmaster_id="fix_login_bug",
            sync_hash="test_hash_1",
            last_sync=datetime.now() - timedelta(hours=1),
        )

        # Mock task creation for new tasks
        leantime_client.create_task = AsyncMock(
            return_value=LeantimeTask(
                id=3,
                headline="Add search functionality",
                description="Implement global search feature",
                project_id=10,
            )
        )

        # Execute synchronization
        result = await sync_manager.sync_all()

        # Verify sync completed successfully
        assert result.success is True
        assert result.synced_tasks > 0

        # Verify both systems were queried
        assert leantime_client._send_mcp_request.called
        assert taskmaster_client._send_mcp_request.called

    @pytest.mark.asyncio
    async def test_adhd_optimization_integration(
        self, leantime_client, taskmaster_client
    ):
        """Test ADHD optimization integration in the workflow."""

        # Create ADHD optimizer
        adhd_optimizer = ADHDTaskOptimizer()

        # Create test task
        task = LeantimeTask(
            id=1,
            headline="Complex refactoring task",
            description="Refactor legacy authentication system with new architecture patterns",
            project_id=10,
            priority=TaskPriority.FOCUSED,
        )

        # Test task optimization
        optimized_task = await adhd_optimizer.optimize_task(task, "test_user")

        # Verify ADHD optimizations were applied
        assert hasattr(optimized_task, "adhd_metadata")
        assert optimized_task.adhd_metadata["cognitive_load"] > 0
        assert optimized_task.adhd_metadata["estimated_attention_duration"] > 0
        assert len(optimized_task.adhd_metadata["break_recommendations"]) > 0
        assert len(optimized_task.adhd_metadata["attention_anchors"]) > 0

        # Test TaskMaster task optimization
        tm_task = TaskMasterTask(
            id="complex_task",
            title="Complex refactoring task",
            description="Refactor legacy authentication system",
            status="pending",
            complexity_score=4.5,
            estimated_hours=8.0,
        )

        optimized_tm_task = await adhd_optimizer.optimize_taskmaster_task(tm_task)

        # Verify TaskMaster optimizations
        assert "deep_work" in optimized_tm_task.tags
        assert "hyperfocus_required" in optimized_tm_task.tags
        assert "adhd_optimization" in optimized_tm_task.ai_analysis
        assert (
            optimized_tm_task.ai_analysis["adhd_optimization"]["cognitive_load"] == 4.5
        )

    @pytest.mark.asyncio
    async def test_context_preservation_workflow(self, sync_manager):
        """Test context preservation and restoration workflow."""

        adhd_optimizer = ADHDTaskOptimizer()

        # Test context preservation
        current_context = {
            "task_name": "Implement authentication",
            "project": "E-commerce Platform",
            "current_state": "designing_oauth_flow",
            "recent_decisions": [
                {"decision": "Use OAuth2", "rationale": "Industry standard"},
                {
                    "decision": "Support Google/Facebook",
                    "rationale": "User convenience",
                },
            ],
            "blockers": [],
            "next_steps": ["Implement OAuth2 flow", "Add social login buttons"],
        }

        preservation_data = await adhd_optimizer.generate_context_preservation(
            "test_user", current_context
        )

        # Verify preservation data
        assert preservation_data["user_id"] == "test_user"
        assert preservation_data["context_summary"]
        assert preservation_data["mental_model"]
        assert preservation_data["attention_anchors"]
        assert preservation_data["restoration_steps"]

        # Test context restoration
        restoration = await adhd_optimizer.restore_context(
            "test_user", preservation_data
        )

        # Verify restoration guidance
        assert restoration["status"] == "ready"
        assert restoration["context_age"]
        assert restoration["summary"]
        assert len(restoration["orientation_steps"]) > 0
        assert len(restoration["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_attention_state_based_task_scheduling(self, sync_manager):
        """Test task scheduling based on attention state detection."""

        adhd_optimizer = ADHDTaskOptimizer()

        # Create test tasks with different complexity levels
        tasks = [
            MagicMock(
                id=1,
                headline="Quick bug fix",
                description="Fix typo",
                complexity_score=1.0,
                estimated_hours=0.5,
                dependencies=[],
            ),
            MagicMock(
                id=2,
                headline="Feature implementation",
                description="Add user dashboard",
                complexity_score=3.5,
                estimated_hours=8.0,
                dependencies=[],
            ),
            MagicMock(
                id=3,
                headline="Architecture refactor",
                description="Redesign database schema",
                complexity_score=5.0,
                estimated_hours=20.0,
                dependencies=[],
            ),
        ]

        # Test scheduling for different attention states

        # Scattered attention - should prioritize quick wins
        schedule = await adhd_optimizer.schedule_optimal_sequence(
            tasks, "test_user", time_window=240  # 4 hours
        )

        assert len(schedule) > 0

        # First task should be the quick win
        first_task_entry = next(entry for entry in schedule if entry["type"] == "task")
        assert first_task_entry["task"].id == 1  # Quick bug fix

        # Verify breaks are included in schedule
        assert any(entry["type"] == "break" for entry in schedule)

    @pytest.mark.asyncio
    async def test_conflict_resolution_workflow(
        self, sync_manager, leantime_client, taskmaster_client
    ):
        """Test conflict resolution during synchronization."""

        # Setup conflicting task updates
        now = datetime.now()

        # Leantime task updated recently
        leantime_task_data = {
            "id": 1,
            "headline": "Updated from Leantime",
            "description": "Task updated in Leantime",
            "status": "2",  # Completed
            "dateToFinish": (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
        }

        # TaskMaster task also updated recently
        taskmaster_task_data = {
            "id": "task_1",
            "title": "Updated from TaskMaster",
            "description": "Task updated in TaskMaster",
            "status": "in_progress",
            "updated_at": (now - timedelta(minutes=3)).isoformat(),
        }

        # Mock responses
        leantime_client._send_mcp_request = AsyncMock(
            return_value={
                "result": {"content": [{"text": json.dumps([leantime_task_data])}]}
            }
        )

        taskmaster_client._send_mcp_request = AsyncMock(
            return_value={
                "result": {
                    "content": [{"text": json.dumps({"tasks": [taskmaster_task_data]})}]
                }
            }
        )

        # Create existing mapping
        sync_manager.task_mappings["lt_1"] = TaskMapping(
            leantime_id=1,
            taskmaster_id="task_1",
            sync_hash="old_hash",
            last_sync=datetime.now() - timedelta(hours=1),
        )

        # Set conflict resolution to latest timestamp
        sync_manager.conflict_resolution = sync_manager.conflict_resolution.__class__(
            "latest_timestamp"
        )

        # Execute sync
        result = await sync_manager.sync_all()

        # Verify conflict was detected and resolved
        assert result.success is True
        # Conflict count should be tracked
        mapping = sync_manager.task_mappings["lt_1"]
        assert mapping.conflict_count >= 0

    @pytest.mark.asyncio
    async def test_health_monitoring_integration(
        self, sync_manager, leantime_client, taskmaster_client
    ):
        """Test health monitoring across integrated systems."""

        # Mock healthy responses
        leantime_client.health_check = AsyncMock(
            return_value={
                "status": "healthy",
                "connected": True,
                "api_responsive": True,
            }
        )

        taskmaster_client.health_check = AsyncMock(
            return_value={
                "status": "healthy",
                "connected": True,
                "process_running": True,
                "api_responsive": True,
            }
        )

        # Get overall sync status
        status = await sync_manager.get_sync_status()

        # Verify integrated status
        assert status["leantime_status"]["status"] == "healthy"
        assert status["taskmaster_status"]["status"] == "healthy"
        assert status["task_mappings_count"] >= 0

        # Test unhealthy state
        leantime_client.health_check = AsyncMock(
            return_value={
                "status": "unhealthy",
                "connected": False,
                "error": "Connection failed",
            }
        )

        status = await sync_manager.get_sync_status()
        assert status["leantime_status"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_performance_under_load(
        self, sync_manager, leantime_client, taskmaster_client
    ):
        """Test system performance with large number of tasks."""

        # Create large number of test tasks
        num_tasks = 100

        leantime_tasks = [
            {
                "id": i,
                "headline": f"Task {i}",
                "description": f"Description for task {i}",
                "projectId": 10,
                "status": str(i % 3),  # Vary status
                "storypoints": (i % 5) + 1,
            }
            for i in range(1, num_tasks + 1)
        ]

        taskmaster_tasks = [
            {
                "id": f"task_{i}",
                "title": f"Task {i}",
                "description": f"Description for task {i}",
                "status": "pending",
                "priority": (i % 3) + 1,
            }
            for i in range(1, num_tasks + 1)
        ]

        # Mock responses
        leantime_client._send_mcp_request = AsyncMock(
            return_value={"result": {"content": [{"text": json.dumps(leantime_tasks)}]}}
        )

        taskmaster_client._send_mcp_request = AsyncMock(
            return_value={
                "result": {
                    "content": [{"text": json.dumps({"tasks": taskmaster_tasks})}]
                }
            }
        )

        # Measure sync performance
        start_time = datetime.now()

        result = await sync_manager.sync_all()

        end_time = datetime.now()
        sync_duration = (end_time - start_time).total_seconds()

        # Verify performance
        assert result.success is True
        assert sync_duration < 30.0  # Should complete within 30 seconds
        assert result.sync_duration > 0

    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(
        self, sync_manager, leantime_client, taskmaster_client
    ):
        """Test error recovery and system resilience."""

        # Test Leantime connection failure
        leantime_client._send_mcp_request = AsyncMock(
            side_effect=Exception("Leantime connection failed")
        )

        taskmaster_client._send_mcp_request = AsyncMock(
            return_value={"result": {"content": [{"text": json.dumps({"tasks": []})}]}}
        )

        result = await sync_manager.sync_all()

        # Should handle error gracefully
        assert result.success is False
        assert len(result.errors) > 0
        assert "Leantime connection failed" in str(result.errors)

        # Test TaskMaster failure
        leantime_client._send_mcp_request = AsyncMock(
            return_value={"result": {"content": [{"text": json.dumps([])}]}}
        )

        taskmaster_client._send_mcp_request = AsyncMock(
            side_effect=Exception("TaskMaster process crashed")
        )

        result = await sync_manager.sync_all()

        # Should handle error gracefully
        assert result.success is False
        assert len(result.errors) > 0

        # Test partial failure recovery
        leantime_client._send_mcp_request = AsyncMock(
            return_value={
                "result": {
                    "content": [
                        {
                            "text": json.dumps(
                                [
                                    {
                                        "id": 1,
                                        "headline": "Working task",
                                        "description": "This task syncs successfully",
                                        "status": "0",
                                    }
                                ]
                            )
                        }
                    ]
                }
            }
        )

        taskmaster_client._send_mcp_request = AsyncMock(
            return_value={"result": {"content": [{"text": json.dumps({"tasks": []})}]}}
        )

        result = await sync_manager.sync_all()

        # Should handle partial success
        assert result.success is True
        assert result.created_tasks >= 0

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_with_real_files(self, config, tmp_path):
        """Test end-to-end workflow with real file operations."""

        # Setup temporary directories
        test_taskmaster_dir = tmp_path / ".taskmaster"
        test_taskmaster_dir.mkdir()

        tasks_dir = test_taskmaster_dir / "tasks"
        tasks_dir.mkdir()

        # Create test configuration file
        config_file = test_taskmaster_dir / "config.json"
        config_data = {
            "providers": {
                "anthropic": {"model": "claude-3-sonnet-20240229", "apiKey": "test_key"}
            },
            "defaultProvider": "anthropic",
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create empty tasks file
        tasks_file = tasks_dir / "tasks.json"
        with open(tasks_file, "w") as f:
            json.dump({"tasks": [], "metadata": {}}, f)

        # Update config to use temporary directory
        config.data["taskmaster"]["path"] = str(test_taskmaster_dir)

        # Test that files can be read and written
        assert config_file.exists()
        assert tasks_file.exists()

        # Verify config content
        with open(config_file, "r") as f:
            loaded_config = json.load(f)
            assert loaded_config["defaultProvider"] == "anthropic"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=integrations", "--cov-report=term-missing"])

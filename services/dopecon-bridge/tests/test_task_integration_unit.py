import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from dopecon_bridge.services.task_integration import TaskIntegrationService
from dopecon_bridge.models import Task, TaskStatus, TaskPriority

@pytest.mark.asyncio
async def test_sync_tasks_to_leantime_parallel_execution():
    service = TaskIntegrationService()

    # Mock MCP manager
    mock_mcp = AsyncMock()

    # Track calls to ensure they are what we expect
    async def side_effect(service_name, tool_name, params):
        if tool_name == "create_ticket":
            # Return unique IDs based on headline
            return {"id": f"leantime_{params['headline']}"}
        return {}

    mock_mcp.call_tool.side_effect = side_effect
    service.mcp_manager = mock_mcp

    # Mock DB manager
    mock_db = AsyncMock()
    mock_session = AsyncMock()
    # Mock the context manager
    mock_session.__aenter__.return_value = mock_session
    mock_db.get_session.return_value = mock_session
    service.db_manager = mock_db

    tasks = [
        Task(
            id=f"task_{i}",
            title=f"Task {i}",
            description=f"Description {i}",
            status=TaskStatus.PLANNED,
            priority=TaskPriority.MEDIUM,
            project_id="1",
            tags=[]
        ) for i in range(3)
    ]

    await service._sync_tasks_to_leantime(tasks)

    # Verify MCP calls
    assert mock_mcp.call_tool.call_count == 3

    # Verify tasks were updated with tags
    assert tasks[0].tags == ["leantime_id:leantime_Task 0"]
    assert tasks[1].tags == ["leantime_id:leantime_Task 1"]
    assert tasks[2].tags == ["leantime_id:leantime_Task 2"]

    # Verify DB update was called
    assert mock_session.execute.called
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_sync_tasks_to_leantime_handles_partial_failure():
    service = TaskIntegrationService()

    # Mock MCP manager
    mock_mcp = AsyncMock()

    async def side_effect(service_name, tool_name, params):
        if params['headline'] == "Task 1":
            raise Exception("Sync failed")
        return {"id": f"leantime_{params['headline']}"}

    mock_mcp.call_tool.side_effect = side_effect
    service.mcp_manager = mock_mcp

    # Mock DB manager
    mock_db = AsyncMock()
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_db.get_session.return_value = mock_session
    service.db_manager = mock_db

    tasks = [
        Task(id="0", title="Task 0", description="", status=TaskStatus.PLANNED, priority=TaskPriority.MEDIUM, project_id="1", tags=[]),
        Task(id="1", title="Task 1", description="", status=TaskStatus.PLANNED, priority=TaskPriority.MEDIUM, project_id="1", tags=[]),
        Task(id="2", title="Task 2", description="", status=TaskStatus.PLANNED, priority=TaskPriority.MEDIUM, project_id="1", tags=[]),
    ]

    await service._sync_tasks_to_leantime(tasks)

    # Task 0 and 2 should be synced, Task 1 failed
    assert tasks[0].tags == ["leantime_id:leantime_Task 0"]
    assert tasks[1].tags == []
    assert tasks[2].tags == ["leantime_id:leantime_Task 2"]

    # DB update should still be called for successful ones
    assert mock_session.execute.called
    # Check that only 2 update params were sent
    args, kwargs = mock_session.execute.call_args
    update_params = args[1]
    assert len(update_params) == 2
    assert update_params[0]["b_id"] == "0"
    assert update_params[1]["b_id"] == "2"

@pytest.mark.asyncio
async def test_sync_tasks_to_leantime_empty_list():
    service = TaskIntegrationService()
    service.mcp_manager = AsyncMock()

    await service._sync_tasks_to_leantime([])

    assert not service.mcp_manager.call_tool.called

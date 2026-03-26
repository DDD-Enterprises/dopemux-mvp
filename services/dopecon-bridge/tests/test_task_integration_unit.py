import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dopecon_bridge.services.task_integration import TaskIntegrationService
from dopecon_bridge.models import Task, TaskStatus, TaskPriority


class DummyResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status = status
        self._payload = payload or {}
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self._payload

    async def text(self):
        return self._text

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

    # DB update was removed
    assert not mock_session.execute.called
    assert not mock_session.commit.called

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

    # DB update was removed
    assert not mock_session.execute.called

@pytest.mark.asyncio
async def test_sync_tasks_to_leantime_empty_list():
    service = TaskIntegrationService()
    service.mcp_manager = AsyncMock()

    await service._sync_tasks_to_leantime([])

    assert not service.mcp_manager.call_tool.called


@pytest.mark.asyncio
async def test_get_priority_queue_routes_through_task_orchestrator_http():
    service = TaskIntegrationService()
    service.mcp_manager = AsyncMock()
    service.mcp_manager.initialize = AsyncMock()
    service.mcp_manager.session = MagicMock()
    service.mcp_manager.session.get.return_value = DummyResponse(
        status=200,
        payload={
            "canonical_backend": "task-orchestrator",
            "project_id": "proj-123",
            "legality_result": "allowed",
            "queue_items": [{"id": "wf-1", "title": "Canonical task"}],
        },
    )

    result = await service.get_priority_queue("proj-123")

    assert result["canonical_backend"] == "task-orchestrator"
    assert result["queue_items"][0]["id"] == "wf-1"


@pytest.mark.asyncio
async def test_update_task_status_requires_allowed_transition_result():
    service = TaskIntegrationService()
    service.mcp_manager = AsyncMock()
    service.mcp_manager.initialize = AsyncMock()
    service.mcp_manager.session = MagicMock()
    service.mcp_manager.session.post.return_value = DummyResponse(
        status=200,
        payload={"legality_result": "unavailable"},
    )

    with pytest.raises(RuntimeError, match="non-authoritative transition result"):
        await service.update_task_status("task-123", TaskStatus.IN_PROGRESS)

    assert not service.mcp_manager.call_tool.called


@pytest.mark.asyncio
async def test_update_task_status_uses_project_scoped_deterministic_idempotency_key():
    service = TaskIntegrationService()
    service.mcp_manager = AsyncMock()
    service.mcp_manager.initialize = AsyncMock()
    service.mcp_manager.session = MagicMock()
    service.mcp_manager.session.post.return_value = DummyResponse(
        status=200,
        payload={"legality_result": "allowed"},
    )
    service.mcp_manager.call_tool = AsyncMock(return_value={"id": "lt-1"})

    result = await service.update_task_status(
        "task-123",
        TaskStatus.IN_PROGRESS,
        assigned_to="alex",
        project_id="proj-123",
    )

    post_url = service.mcp_manager.session.post.call_args.args[0]
    post_payload = service.mcp_manager.session.post.call_args.kwargs["json"]

    assert "/api/projects/proj-123/workflow/transition" in post_url
    assert post_payload["idempotency_key"] == "bridge-trans-proj-123-task-123-in_progress-alex"
    assert result["project_id"] == "proj-123"

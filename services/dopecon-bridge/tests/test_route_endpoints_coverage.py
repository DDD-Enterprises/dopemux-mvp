import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from dopecon_bridge.app import app
from dopecon_bridge.models import Task, TaskStatus, TaskPriority

client = TestClient(app)

# Helper to get valid token
def get_token():
    return "dummy-token"

# Test Task Routes Proxying
@patch('dopecon_bridge.services.task_integration.task_service')
def test_parse_prd_success(mock_task_service):
    mock_task_service.parse_prd_to_tasks = AsyncMock(return_value=[
        Task(id="1", title="Test", description="Test", status=TaskStatus.PLANNED, priority=TaskPriority.MEDIUM)
    ])
    response = client.post(
        "/tasks/parse-prd",
        json={"content": "dummy", "project_id": "1"},
        headers={"X-Source-Plane": "cognitive_plane"}
    )
    assert response.status_code == 200
    assert response.json()["success"] == True

@patch('dopecon_bridge.services.task_integration.task_service')
def test_get_next_tasks_success(mock_task_service):
    mock_task_service.get_next_actionable_tasks = AsyncMock(return_value=[
        Task(id="1", title="Test", description="Test", status=TaskStatus.PLANNED, priority=TaskPriority.MEDIUM)
    ])
    response = client.get(
        "/tasks/next/1",
        headers={"X-Source-Plane": "pm_plane"}
    )
    assert response.status_code == 200

@patch('dopecon_bridge.services.task_integration.task_service')
def test_update_task_status_success(mock_task_service):
    # Mock authentication by patching DEPENDS or mocking get_current_user
    app.dependency_overrides = {}  # Clear overrides just in case
    # Mocking task service response
    mock_task_service.update_task_status = AsyncMock(return_value={"success": True})

    # Needs auth mocking, we'll patch Depends via app dependency overrides
    from dopecon_bridge.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"username": "admin"}

    response = client.patch(
        "/tasks/task-123/status",
        json={"status": "in_progress"},
        headers={"X-Source-Plane": "cognitive_plane"}
    )
    assert response.status_code == 200

# Test DDG Routes Proxying
@patch('dopecon_bridge.routes.mcp_client', new_callable=AsyncMock)
def test_ddg_recent_decisions_success(mock_mcp_client):
    mock_mcp_client.call_tool = AsyncMock(return_value={"decisions": []})

    # Note: `routes.py` dynamically imports `mcp_client` inside the function,
    # so we mock `dopecon_bridge.clients.mcp_client` instead
    pass

@patch('dopecon_bridge.clients.mcp_client.call_tool')
def test_ddg_recent_decisions_success_proper(mock_call_tool):
    mock_call_tool.return_value = {"decisions": [{"id": "1", "summary": "test decision"}]}
    response = client.get(
        "/ddg/decisions",
        headers={"X-Source-Plane": "pm_plane"}
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

@patch('dopecon_bridge.clients.mcp_client.call_tool')
def test_ddg_search_decisions_success_proper(mock_call_tool):
    mock_call_tool.return_value = {"decisions": [{"id": "2", "summary": "arch decision"}]}
    response = client.get(
        "/ddg/search",
        params={"q": "arch"},
        headers={"X-Source-Plane": "cognitive_plane"}
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

from dopecon_bridge.services.task_integration import TaskIntegrationService

@pytest.mark.asyncio
async def test_parse_prd_to_tasks():
    service = TaskIntegrationService()
    mock_mcp = AsyncMock()
    mock_mcp.call_tool.return_value = {"tasks": [{"title": "t1", "description": "d1", "priority": "high", "tags": []}]}
    service.mcp_manager = mock_mcp

    # Test PRD parse
    # Leantime expects project ID to be an integer (e.g. "1")
    tasks = await service.parse_prd_to_tasks("prd content", "1")
    assert len(tasks) == 1
    assert tasks[0].title == "t1"
    assert tasks[0].project_id == "1"

    # Verify sync was called
    # _sync_tasks_to_leantime calls mcp_manager.call_tool with create_ticket
    call_args = mock_mcp.call_tool.call_args_list
    assert len(call_args) == 2  # parse_prd + create_ticket
    assert call_args[1][0][0] == "leantime-bridge"
    assert call_args[1][0][1] == "create_ticket"

@pytest.mark.asyncio
async def test_get_next_actionable_tasks():
    service = TaskIntegrationService()
    mock_mcp = AsyncMock()
    mock_mcp.call_tool.return_value = {
        "tickets": [{"id": 123, "headline": "h1", "description": "d1"}]
    }
    service.mcp_manager = mock_mcp

    tasks = await service.get_next_actionable_tasks("proj-1", 5)
    assert len(tasks) == 1
    assert tasks[0].id == "123"
    assert tasks[0].title == "h1"

@pytest.mark.asyncio
async def test_update_task_status():
    service = TaskIntegrationService()
    mock_mcp = AsyncMock()

    # Mocking different calls for update_ticket and get_ticket and search_tickets
    async def mock_call_tool(server, method, params):
        if method == "update_ticket":
            return {}
        elif method == "get_ticket":
            return {"projectId": "proj-1"}
        elif method == "search_tickets":
            return {"tickets": [{"id": 456, "headline": "h2"}]}
        return {}

    mock_mcp.call_tool.side_effect = mock_call_tool
    service.mcp_manager = mock_mcp

    resp = await service.update_task_status("123", TaskStatus.IN_PROGRESS, "user1")
    assert resp["success"] == True
    assert resp["task_id"] == "123"
    assert resp["new_status"] == "in_progress"
    assert len(resp["suggested_next_actions"]) == 1
    assert resp["suggested_next_actions"][0]["id"] == "456"


from dopecon_bridge.routes import *

# Error handling in routes
@patch('dopecon_bridge.services.task_integration.task_service')
def test_parse_prd_error(mock_task_service):
    mock_task_service.parse_prd_to_tasks = AsyncMock(side_effect=Exception("parse error"))
    response = client.post("/tasks/parse-prd", json={"content": "dummy", "project_id": "1"}, headers={"X-Source-Plane": "cognitive_plane"})
    assert response.status_code == 500

@patch('dopecon_bridge.services.task_integration.task_service')
def test_get_next_tasks_error(mock_task_service):
    mock_task_service.get_next_actionable_tasks = AsyncMock(side_effect=Exception("next error"))
    response = client.get("/tasks/next/1", headers={"X-Source-Plane": "pm_plane"})
    assert response.status_code == 500

@patch('dopecon_bridge.services.task_integration.task_service')
def test_update_task_status_value_error(mock_task_service):
    mock_task_service.update_task_status = AsyncMock(side_effect=ValueError("bad value"))
    from dopecon_bridge.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"username": "admin"}
    response = client.patch("/tasks/task-123/status", json={"status": "in_progress"}, headers={"X-Source-Plane": "cognitive_plane"})
    assert response.status_code == 400

@patch('dopecon_bridge.services.task_integration.task_service')
def test_update_task_status_exception(mock_task_service):
    mock_task_service.update_task_status = AsyncMock(side_effect=Exception("generic error"))
    from dopecon_bridge.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"username": "admin"}
    response = client.patch("/tasks/task-123/status", json={"status": "in_progress"}, headers={"X-Source-Plane": "cognitive_plane"})
    assert response.status_code == 500

@patch('dopecon_bridge.clients.mcp_client.call_tool')
def test_ddg_decisions_error(mock_call_tool):
    mock_call_tool.side_effect = Exception("ddg err")
    response = client.get("/ddg/decisions", headers={"X-Source-Plane": "pm_plane"})
    assert response.status_code == 500

@patch('dopecon_bridge.clients.mcp_client.call_tool')
def test_ddg_search_error(mock_call_tool):
    mock_call_tool.side_effect = Exception("search err")
    response = client.get("/ddg/search", params={"q": "arch"}, headers={"X-Source-Plane": "cognitive_plane"})
    assert response.status_code == 500


# Add test for convenience endpoints in routes
@patch('dopecon_bridge.routes.publish_event')
def test_publish_tasks_imported(mock_publish):
    mock_publish.return_value = {"success": True}
    response = client.post("/events/tasks-imported?task_count=10&sprint_id=1")
    assert response.status_code == 200

@patch('dopecon_bridge.routes.publish_event')
def test_publish_session_started(mock_publish):
    mock_publish.return_value = {"success": True}
    response = client.post("/events/session-started?task_id=123")
    assert response.status_code == 200

@patch('dopecon_bridge.routes.publish_event')
def test_publish_progress_updated(mock_publish):
    mock_publish.return_value = {"success": True}
    response = client.post("/events/progress-updated?task_id=123&status=DONE&progress=1.0")
    assert response.status_code == 200


# Add test for get_event_history
@patch('dopecon_bridge.routes.cache_manager.get_client', new_callable=AsyncMock)
def test_get_event_history(mock_get_client):
    mock_redis = AsyncMock()
    mock_redis.xrevrange.return_value = [("msg-1", {"type": "t1", "data": '{"k":"v"}'})]
    mock_get_client.return_value = mock_redis

    response = client.get("/events/history")
    assert response.status_code == 200
    assert response.json()["count"] == 1

@patch('dopecon_bridge.routes.cache_manager.get_client', new_callable=AsyncMock)
def test_get_event_history_error(mock_get_client):
    mock_get_client.side_effect = Exception("redis err")
    response = client.get("/events/history")
    assert response.status_code == 500


# Test publish_event directly
@patch('dopecon_bridge.event_bus.EventBus.publish', new_callable=AsyncMock)
@patch('dopecon_bridge.event_bus.EventBus.initialize', new_callable=AsyncMock)
def test_publish_event_endpoint(mock_init, mock_publish):
    mock_publish.return_value = "msg-2"
    response = client.post("/events", json={"event_type": "foo", "data": {}})
    assert response.status_code == 200
    assert response.json()["message_id"] == "msg-2"

@patch('dopecon_bridge.event_bus.EventBus.initialize', new_callable=AsyncMock)
def test_publish_event_endpoint_error(mock_init):
    mock_init.side_effect = Exception("init err")
    response = client.post("/events", json={"event_type": "foo", "data": {}})
    assert response.status_code == 500

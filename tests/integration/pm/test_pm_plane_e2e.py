"""End-to-end integration tests for the PM Plane."""

import pytest
import httpx
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from dopemux.pm.models import PMTask, PMTaskStatus
from dopemux.pm.store import InMemoryPMTaskStore
from services.taskmaster.bridge_adapter import TaskMasterBridgeAdapter
from src.dopemux.adhd.task_decomposer import TaskDecomposer

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

@pytest.fixture
def mock_httpx():
    with patch("httpx.AsyncClient", autospec=True) as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        default_resp = MockResponse({"success": True, "status": "published", "entry_id": "test-entry", "id": "test-id"})
        mock_client.request = AsyncMock(return_value=default_resp)
        mock_client.post = AsyncMock(return_value=default_resp)
        mock_client.get = AsyncMock(return_value=default_resp)
        
        yield mock_client

@pytest.mark.asyncio
async def test_taskmaster_to_pm_e2e_flow(mock_httpx):
    """Test flow: TaskMaster -> PM Plane -> Backends."""
    adapter = TaskMasterBridgeAdapter(workspace_id="test-ws")
    
    result = await adapter.create_task(
        title="Integration Test Task",
        description="Verify E2E flow",
        tags=["e2e", "integration"]
    )
    
    assert result.get("canonical_id") is not None
    task_id = result["canonical_id"]
    
    # 4. Update Task Status
    mock_httpx.post.reset_mock()
    success = await adapter.update_task_status(task_id, "IN_PROGRESS")
    assert success is True
    
    # Verify status update event was published to the bridge
    event_published = False
    for call in mock_httpx.post.call_args_list:
        args, kwargs = call
        url = args[0] if args else kwargs.get("url", "")
        if "/events" in str(url):
            payload = kwargs.get("json", {})
            if payload.get("event_type") == "taskmaster.task.status_updated":
                event_published = True
                assert payload["data"]["new_status"] == "IN_PROGRESS"
            
    assert event_published is True

@pytest.mark.asyncio
async def test_cli_to_pm_e2e_flow(mock_httpx, tmp_path):
    """Test flow: CLI Decomposer -> PM Plane -> Backends."""
    decomposer = TaskDecomposer(workspace=tmp_path)
    task_id = decomposer.add_task("CLI Integration Task")
    assert task_id is not None
    success = decomposer.start_task(task_id)
    assert success is True

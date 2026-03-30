"""End-to-end integration tests for the PM Plane."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from dopemux.pm.models import PMTask, PMTaskStatus
from dopemux.pm.store import InMemoryPMTaskStore
from services.taskmaster.bridge_adapter import (
    TaskMasterBridgeAdapter,
    SyncLeantimeBridgeClient,
    SyncOrchestratorBridgeClient,
    SyncConportBridgeClient,
    SyncMemoryBridgeClient
)
from src.dopemux.adhd.task_decomposer import TaskDecomposer
from dopemux.pm.writes import PMWriteConfig
from dopecon_bridge_client import DopeconBridgeConfig

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
    with patch("httpx.AsyncClient", autospec=True) as mock_async_cls, \
         patch("httpx.Client", autospec=True) as mock_sync_cls:
        
        mock_async_client = mock_async_cls.return_value
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_sync_client = mock_sync_cls.return_value
        mock_sync_client.__enter__ = MagicMock(return_value=mock_sync_client)
        mock_sync_client.__exit__ = MagicMock(return_value=None)
        
        default_resp = MockResponse({"success": True, "status": "published", "entry_id": "test-entry", "id": "test-id"})
        
        mock_async_client.request = AsyncMock(return_value=default_resp)
        mock_async_client.post = AsyncMock(return_value=default_resp)
        mock_async_client.get = AsyncMock(return_value=default_resp)
        
        mock_sync_client.request = MagicMock(return_value=default_resp)
        mock_sync_client.post = MagicMock(return_value=default_resp)
        mock_sync_client.get = MagicMock(return_value=default_resp)
        
        # Attach the sync mock to the async mock so tests can check both if needed
        mock_async_client.sync_client = mock_sync_client
        
        yield mock_async_client

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
    
    # Verify PM Plane writes (sync)
    assert mock_httpx.sync_client.post.call_count >= 2
    
    # 4. Update Task Status
    mock_httpx.post.reset_mock()
    mock_httpx.sync_client.post.reset_mock()
    success = await adapter.update_task_status(task_id, "IN_PROGRESS")
    assert success is True
    
    # Verify status update event was published to the bridge (async)
    event_published = False
    for call in mock_httpx.post.call_args_list:
        args, kwargs = call
        url = args[0] if args else kwargs.get("url", "")
        if "/events" in str(url):
            payload = kwargs.get("json", {})
            if payload.get("event_type") == "taskmaster.task.status_updated":
                event_published = True
                
    assert event_published is True
    
    # Verify PM Plane transition (sync)
    transition_called = False
    for call in mock_httpx.sync_client.post.call_args_list:
        args, kwargs = call
        url = args[0] if args else kwargs.get("url", "")
        if "/api/projects/test-ws/workflow/transition" in str(url):
            payload = kwargs.get("json", {})
            if payload.get("workflow_id") == task_id:
                transition_called = True

    assert transition_called is True


@pytest.mark.asyncio
async def test_taskmaster_transition_uses_project_scoped_workflow_endpoint(mock_httpx):
    adapter = TaskMasterBridgeAdapter(workspace_id="test-ws")
    created = await adapter.create_task(
        title="Scoped transition task",
        description="Ensure project-scoped transition path is used",
    )
    task_id = created["canonical_id"]

    await adapter.update_task_status(task_id, "IN_PROGRESS")

    transition_called = False
    for call in mock_httpx.sync_client.post.call_args_list:
        args, kwargs = call
        url = args[0] if args else kwargs.get("url", "")
        if "/api/projects/test-ws/workflow/transition" in str(url):
            payload = kwargs.get("json", {})
            if payload.get("workflow_id") == task_id:
                transition_called = True

    assert transition_called is True


@pytest.mark.asyncio
async def test_cli_to_pm_e2e_flow(mock_httpx, tmp_path):
    """Test flow: CLI Decomposer -> PM Plane -> Backends."""
    # 1. Setup decomposer with real sync stubs (calling mocked httpx)
    config = DopeconBridgeConfig(base_url="http://bridge:8000", token="test")
    pm_config = PMWriteConfig(
        leantime_client=SyncLeantimeBridgeClient(config),
        orchestrator_client=SyncOrchestratorBridgeClient(config),
        conport_client=SyncConportBridgeClient(config),
        memory_client=SyncMemoryBridgeClient(config)
    )
    decomposer = TaskDecomposer(workspace=tmp_path, pm_config=pm_config)
    
    # 2. Create Task
    task_id = decomposer.add_task("CLI Integration Task")
    assert task_id is not None
    
    # Verify PM Plane writes (sync)
    assert mock_httpx.sync_client.post.call_count >= 2
    
    # 3. Start Task (Transition)
    mock_httpx.sync_client.post.reset_mock()
    success = decomposer.start_task(task_id)
    assert success is True
    
    # Verify PM Plane transition (sync)
    transition_called = False
    for call in mock_httpx.sync_client.post.call_args_list:
        args, kwargs = call
        url = args[0] if args else kwargs.get("url", "")
        if "/api/projects/default/workflow/transition" in str(url):
            payload = kwargs.get("json", {})
            if payload.get("workflow_id") == task_id:
                transition_called = True

    assert transition_called is True

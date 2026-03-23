"""End-to-end integration tests for the PM Plane."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from dopemux.pm.models import PMTask, PMTaskStatus
from dopemux.pm.store import InMemoryPMTaskStore
from services.taskmaster.bridge_adapter import TaskMasterBridgeAdapter
from src.dopemux.adhd.task_decomposer import TaskDecomposer


@pytest.fixture
def mock_httpx():
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value.__aenter__.return_value = client
        yield client


@pytest.mark.asyncio
async def test_taskmaster_to_pm_e2e_flow(mock_httpx):
    """
    Test flow: TaskMaster -> PM Plane -> Backends (Orchestrator/ConPort/Memory).
    """
    # 1. Setup adapter
    adapter = TaskMasterBridgeAdapter(workspace_id="test-ws")
    
    # 2. Mock Backend Responses
    # We need to make sure the mocked request returns an object that is awaited properly
    # httpx.AsyncClient.request returns a Response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "entry_id": "test-entry"}
    
    mock_httpx.request.return_value = mock_response
    
    # 3. Create Task (Triggers PM Plane tools)
    result = await adapter.create_task(
        title="Integration Test Task",
        description="Verify E2E flow",
        tags=["e2e", "integration"]
    )
    
    assert result["canonical_id"] is not None
    task_id = result["canonical_id"]
    
    # Verify ConPort/Memory was called via pm_log_progress
    # (Two calls expected: one for ConPort save_custom_data, one for Dope-Memory append)
    assert mock_httpx.request.call_count >= 2
    
    # 4. Update Task Status (Triggers transition flow)
    # Reset mock to track new calls
    mock_httpx.request.reset_mock()
    
    # We need to make sure the task is in the adapter's local store
    success = await adapter.update_task_status(task_id, "IN_PROGRESS")
    assert success is True
    
    # Verify Orchestrator was called for transition
    # Check that at least one call went to /api/projects/default/workflow/transition
    transition_called = False
    for call in mock_httpx.request.call_args_list:
        args, kwargs = call
        if "/workflow/transition" in args[1]:
            transition_called = True
            assert args[0] == "POST"
            assert kwargs["json"]["transition"] == "in_progress"
            
    assert transition_called is True


@pytest.mark.asyncio
async def test_cli_to_pm_e2e_flow(mock_httpx, tmp_path):
    """
    Test flow: CLI Decomposer -> PM Plane -> Backends.
    """
    # 1. Setup decomposer with temporary workspace
    decomposer = TaskDecomposer(workspace=tmp_path)
    
    # 2. Mock Backend Responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "entry_id": "test-entry"}
    mock_httpx.request.return_value = mock_response
    
    # 3. Create Task
    task_id = await decomposer.add_task("CLI Integration Task")
    assert task_id is not None
    
    # Verify backend logging
    assert mock_httpx.request.call_count >= 2
    
    # 3. Start Task (Transition)
    mock_httpx.request.reset_mock()
    success = await decomposer.start_task(task_id)
    assert success is True
    
    # Verify Orchestrator transition
    transition_called = False
    for call in mock_httpx.request.call_args_list:
        args, kwargs = call
        if "/workflow/transition" in args[1]:
            transition_called = True
            
    assert transition_called is True

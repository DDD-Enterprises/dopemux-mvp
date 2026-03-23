import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.taskmaster.bridge_adapter import TaskMasterBridgeAdapter

@pytest.fixture
def mock_pm_config():
    with patch("services.taskmaster.bridge_adapter.PMWriteConfig") as MockConfig:
        config_instance = MockConfig.return_value
        yield config_instance

@pytest.fixture
def mock_client():
    with patch("services.taskmaster.bridge_adapter.AsyncDopeconBridgeClient") as MockClient:
        client_instance = AsyncMock()
        MockClient.return_value = client_instance
        yield client_instance

@pytest.fixture
async def adapter(mock_pm_config, mock_client):
    with patch("services.taskmaster.bridge_adapter.SyncLeantimeBridgeClient"), \
         patch("services.taskmaster.bridge_adapter.SyncOrchestratorBridgeClient"), \
         patch("services.taskmaster.bridge_adapter.SyncConportBridgeClient"), \
         patch("services.taskmaster.bridge_adapter.SyncMemoryBridgeClient"):
         async with TaskMasterBridgeAdapter(workspace_id="test_workspace") as ad:
            yield ad

@pytest.mark.asyncio
async def test_create_task(adapter):
    with patch("services.taskmaster.bridge_adapter.pm_log_progress") as mock_log_progress:
        result = await adapter.create_task(title="Test Task", description="Test Description")

        assert "canonical_id" in result
        assert result["title"] == "Test Task"
        assert result["status"] == "TODO"

        mock_log_progress.assert_called_once()
        adapter.client.publish_event.assert_called_once()

@pytest.mark.asyncio
async def test_update_task_status(adapter):
    # First create a task
    result = await adapter.create_task(title="Test Task", description="Test Description")
    task_id = result["canonical_id"]

    with patch("services.taskmaster.bridge_adapter.pm_transition_work_item") as mock_transition:
        success = await adapter.update_task_status(task_id, "DONE")

        assert success is True
        mock_transition.assert_called_once()
        # Verify status is correctly mapped
        call_args = mock_transition.call_args[1]
        assert call_args["new_status"].value == "DONE"

@pytest.mark.asyncio
async def test_sync_to_pm_plane(adapter):
    # Create a task first
    result = await adapter.create_task(title="Test Sync Task", description="Sync Description")
    task_id = result["canonical_id"]

    # Mock route_pm response
    adapter.client.route_pm.return_value = MagicMock(success=True, data={"pm_task_id": "real-leantime-id-123"})

    with patch("services.taskmaster.bridge_adapter.pm_update_work_item") as mock_update:
        success = await adapter.sync_to_pm_plane(task_id)

        assert success is True
        mock_update.assert_called_once()
        call_args = mock_update.call_args[1]
        assert call_args["updates"]["linked_ids"]["leantime"] == "real-leantime-id-123"

@pytest.mark.asyncio
async def test_add_task_comment(adapter):
    # Create a task first
    result = await adapter.create_task(title="Test Task", description="Test Description")
    task_id = result["canonical_id"]

    with patch("services.taskmaster.bridge_adapter.pm_log_progress") as mock_log:
        success = await adapter.add_task_comment(task_id, "This is a comment", "Hue")

        assert success is True
        mock_log.assert_called_once()
        adapter.client.publish_event.assert_called()

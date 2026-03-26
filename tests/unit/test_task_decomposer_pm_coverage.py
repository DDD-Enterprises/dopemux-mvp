import pytest
import tempfile
from unittest.mock import MagicMock, patch
from pathlib import Path
from dopemux.adhd.task_decomposer import TaskDecomposer, TaskStatus
from dopemux.pm.writes import PMWriteConfig
from dopemux.pm.models import PMTaskStatus

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def pm_config():
    config = MagicMock(spec=PMWriteConfig)
    config.leantime_client = MagicMock()
    config.orchestrator_client = MagicMock()
    config.conport_client = MagicMock()
    config.memory_client = MagicMock()
    return config

def test_backfill_exception(temp_workspace, pm_config):
    decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
    t1 = decomposer.add_task("Offline 1")
    
    with patch.object(decomposer, "_sync_to_pm_plane", side_effect=Exception("mock backfill failure")):
        count = decomposer.backfill_to_pm_plane()
        assert count == 0

def test_update_progress_invalid_id(temp_workspace, pm_config):
    decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
    assert not decomposer.update_progress("invalid", 0.5)

def test_start_task_invalid_id(temp_workspace, pm_config):
    decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
    assert not decomposer.start_task("invalid")

def test_complete_task_invalid_id(temp_workspace, pm_config):
    decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
    assert not decomposer.complete_task("invalid")

def test_fallback_workspace_permission_error():
    # Attempt to mock out Path.resolve to raise PermissionError
    # We should get a temp directory fallback 
    with patch("pathlib.Path.resolve", side_effect=PermissionError("mock perm error")):
        decomposer = TaskDecomposer("/root/dopemux-forbidden-test")
        assert "/root/dopemux-forbidden-test" not in str(decomposer.workspace)
        assert "dopemux-tasks-" in str(decomposer.workspace)

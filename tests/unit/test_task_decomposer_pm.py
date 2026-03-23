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

def test_add_task_syncs_to_pm(temp_workspace, pm_config):
    with patch("dopemux.adhd.task_decomposer.pm_transition_work_item") as mock_transition:
        decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
        task_id = decomposer.add_task("Test PM Task")

        mock_transition.assert_called_once()
        args, kwargs = mock_transition.call_args
        assert kwargs["task_id"] == task_id
        assert kwargs["new_status"] == PMTaskStatus.TODO
        assert kwargs["config"] == pm_config

def test_start_task_syncs_to_pm(temp_workspace, pm_config):
    with patch("dopemux.adhd.task_decomposer.pm_transition_work_item") as mock_transition:
        decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
        task_id = decomposer.add_task("Test PM Task")
        mock_transition.reset_mock()

        decomposer.start_task(task_id)
        mock_transition.assert_called_once()
        args, kwargs = mock_transition.call_args
        assert kwargs["task_id"] == task_id
        assert kwargs["new_status"] == PMTaskStatus.IN_PROGRESS

def test_complete_task_syncs_to_pm(temp_workspace, pm_config):
    with patch("dopemux.adhd.task_decomposer.pm_transition_work_item") as mock_transition:
        decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
        task_id = decomposer.add_task("Test PM Task")
        mock_transition.reset_mock()

        decomposer.complete_task(task_id)
        mock_transition.assert_called_once()
        args, kwargs = mock_transition.call_args
        assert kwargs["task_id"] == task_id
        assert kwargs["new_status"] == PMTaskStatus.DONE

def test_update_progress_syncs_to_pm(temp_workspace, pm_config):
    with patch("dopemux.adhd.task_decomposer.pm_transition_work_item") as mock_transition:
        decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)
        task_id = decomposer.add_task("Test PM Task")
        mock_transition.reset_mock()

        decomposer.update_progress(task_id, 0.5)
        mock_transition.assert_called_once()
        args, kwargs = mock_transition.call_args
        assert kwargs["task_id"] == task_id
        assert kwargs["new_status"] == PMTaskStatus.IN_PROGRESS

def test_backfill_to_pm_plane(temp_workspace, pm_config):
    # Create offline without pm_config
    decomposer_offline = TaskDecomposer(temp_workspace)
    t1 = decomposer_offline.add_task("Offline 1")
    t2 = decomposer_offline.add_task("Offline 2")
    decomposer_offline.start_task(t1)

    with patch("dopemux.adhd.task_decomposer.pm_transition_work_item") as mock_transition:
        # Re-initialize online with pm_config
        decomposer_online = TaskDecomposer(temp_workspace, pm_config=pm_config)

        count = decomposer_online.backfill_to_pm_plane()
        assert count == 2

        assert mock_transition.call_count == 2
        # Verify offline state was retained and synced
        synced_statuses = [call.kwargs["new_status"] for call in mock_transition.call_args_list]
        assert PMTaskStatus.IN_PROGRESS in synced_statuses
        assert PMTaskStatus.TODO in synced_statuses

def test_degraded_mode(temp_workspace, pm_config):
    with patch("dopemux.adhd.task_decomposer.pm_transition_work_item") as mock_transition:
        mock_transition.side_effect = Exception("PM backend down")
        decomposer = TaskDecomposer(temp_workspace, pm_config=pm_config)

        # Should not raise exception (fail-closed, local disk acts as queue)
        task_id = decomposer.add_task("Test Degraded Task")

        assert task_id in decomposer._tasks
        assert decomposer._tasks[task_id].description == "Test Degraded Task"

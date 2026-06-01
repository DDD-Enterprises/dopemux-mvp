import os
import shutil
import tempfile
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from filelock import FileLock, Timeout

from dopemux.pm.adapters.conport import ConPortAdapter


class TestConPortAdapterRecordProgress:
    @pytest.fixture(autouse=True)
    def setup_temp_xdg(self):
        # Redirect XDG_DATA_HOME/home for testing to avoid contaminating the actual ~/.local
        self.temp_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get("HOME")
        os.environ["HOME"] = self.temp_dir
        
        yield
        
        shutil.rmtree(self.temp_dir)
        if self.original_home is not None:
            os.environ["HOME"] = self.original_home
        else:
            os.environ.pop("HOME", None)

    @pytest.mark.asyncio
    @patch("dopemux.pm.adapters.conport.ConPortAdapter._request")
    async def test_record_progress_writes_local_journal_and_calls_http(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"status": "success"})
        mock_request.return_value = mock_response

        adapter = ConPortAdapter()
        result = await adapter.record_progress(
            task_id="task-123",
            progress_notes="Completed Phase 1 test suite",
            is_decision=False,
            idempotency_key="idem-key-1"
        )

        assert result == {"status": "success"}
        mock_request.assert_called_once()
        
        # Verify local journal was written
        journal_path = os.path.expanduser("~/.local/share/dopemux/progress_log.json")
        assert os.path.exists(journal_path)

    @pytest.mark.asyncio
    @patch("dopemux.pm.adapters.conport.ConPortAdapter._request")
    async def test_record_progress_lock_timeout(self, mock_request):
        adapter = ConPortAdapter()
        
        # Manually hold the file lock to trigger a timeout
        journal_path = os.path.expanduser("~/.local/share/dopemux/progress_log.json")
        os.makedirs(os.path.dirname(journal_path), exist_ok=True)
        lock_path = journal_path + ".lock"
        
        lock = FileLock(lock_path)
        with lock:
            # Attempting to call record_progress with timeout=1 should raise filelock.Timeout
            with pytest.raises(Timeout):
                await adapter.record_progress(
                    task_id="task-123",
                    progress_notes="This should fail",
                    is_decision=False,
                    idempotency_key="idem-key-2",
                    timeout=1
                )

        # After the move of journal write to after the HTTP call, the request will be made
        # even if the journal write later times out.
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    @patch("dopemux.pm.adapters.conport.ConPortAdapter._request")
    async def test_concurrent_writes_no_corruption(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"status": "success"})
        mock_request.return_value = mock_response

        adapter = ConPortAdapter()
        
        # Execute 5 concurrent progress records
        tasks = [
            adapter.record_progress(
                task_id=f"task-{i}",
                progress_notes=f"Progress entry {i}",
                is_decision=False,
                idempotency_key=f"idem-{i}"
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(r == {"status": "success"} for r in results)

        # Verify all 5 entries are recorded in the local journal
        journal_path = os.path.expanduser("~/.local/share/dopemux/progress_log.json")
        import json
        with open(journal_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert len(data) == 5
        task_ids = {entry["task_id"] for entry in data}
        assert task_ids == {f"task-{i}" for i in range(5)}

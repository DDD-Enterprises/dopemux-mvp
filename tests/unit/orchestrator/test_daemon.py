import os
import shutil
import tempfile
import pytest

from dopemux.orchestrator.automation.daemon import AutomationDaemon


class TestAutomationDaemon:
    @pytest.fixture(autouse=True)
    def setup_temp_xdg(self):
        # Redirect HOME to avoid writing to real XDG share in tests
        self.temp_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get("HOME")
        os.environ["HOME"] = self.temp_dir
        
        yield
        
        shutil.rmtree(self.temp_dir)
        if self.original_home is not None:
            os.environ["HOME"] = self.original_home
        else:
            os.environ.pop("HOME", None)

    def test_daemon_initialization_shares_xdg_db(self):
        daemon = AutomationDaemon()
        
        # Verify the daemon shares the persistent idempotency store
        assert daemon.idempotency_store is not None
        
        db_path = daemon.idempotency_store.db_path
        expected_dir = os.path.expanduser("~/.local/share/dopemux")
        assert os.path.dirname(db_path) == expected_dir
        assert os.path.basename(db_path) == "idempotency.db"

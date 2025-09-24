"""
Tests for the context manager module.
"""

import json
import sqlite3
from unittest.mock import Mock, patch

from dopemux.adhd.context_manager import ContextSnapshot


class TestContextSnapshot:
    """Test ContextSnapshot class."""

    def test_default_initialization(self):
        """Test ContextSnapshot with default values."""
        snapshot = ContextSnapshot()

        assert snapshot.session_id  # Should have generated UUID
        assert snapshot.timestamp  # Should have current timestamp
        assert snapshot.working_directory
        assert snapshot.open_files == []
        assert snapshot.current_goal == ""
        assert isinstance(snapshot.mental_model, dict)

    def test_custom_initialization(self, sample_context_data):
        """Test ContextSnapshot with custom values."""
        snapshot = ContextSnapshot(**sample_context_data)

        assert snapshot.session_id == sample_context_data["session_id"]
        assert snapshot.current_goal == sample_context_data["current_goal"]
        assert snapshot.open_files == sample_context_data["open_files"]

    def test_to_dict(self, sample_context_data):
        """Test converting snapshot to dictionary."""
        snapshot = ContextSnapshot(**sample_context_data)
        result = snapshot.to_dict()

        assert isinstance(result, dict)
        assert result["session_id"] == sample_context_data["session_id"]
        assert result["current_goal"] == sample_context_data["current_goal"]

    def test_from_dict(self, sample_context_data):
        """Test creating snapshot from dictionary."""
        snapshot = ContextSnapshot.from_dict(sample_context_data)

        assert snapshot.session_id == sample_context_data["session_id"]
        assert snapshot.current_goal == sample_context_data["current_goal"]


class TestContextManager:
    """Test ContextManager class."""

    def test_initialization(self, context_manager, temp_project_dir):
        """Test ContextManager initialization."""
        assert context_manager.project_path == temp_project_dir
        assert context_manager.dopemux_dir == temp_project_dir / ".dopemux"
        assert context_manager.db_path == temp_project_dir / ".dopemux" / "context.db"

    def test_initialize_creates_directories(self, context_manager):
        """Test that initialize creates required directories."""
        context_manager.initialize()

        assert context_manager.dopemux_dir.exists()
        assert context_manager.sessions_dir.exists()
        assert context_manager.db_path.exists()

    def test_database_schema(self, context_manager):
        """Test that database schema is created correctly."""
        context_manager.initialize()

        with sqlite3.connect(context_manager.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "context_snapshots" in tables
            assert "session_metadata" in tables

    @patch("dopemux.adhd.context_manager.datetime")
    def test_save_context(self, mock_datetime, context_manager, mock_subprocess):
        """Test saving context."""
        # Setup mocks
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        context_manager.initialize()

        # Save context
        session_id = context_manager.save_context(message="Test save")

        assert session_id
        assert len(session_id) > 0

        # Verify it was saved to database
        with sqlite3.connect(context_manager.db_path) as conn:
            cursor = conn.execute(
                "SELECT session_id FROM context_snapshots WHERE session_id = ?",
                (session_id,),
            )
            result = cursor.fetchone()
            assert result is not None

    def test_restore_session(self, context_manager, sample_context_data):
        """Test restoring a specific session."""
        context_manager.initialize()

        # Store a context first
        data = sample_context_data.copy()
        data["working_directory"] = str(
            context_manager.project_path
        )  # Fix working directory
        snapshot = ContextSnapshot(**data)
        context_manager._store_context(snapshot)

        # Restore it
        restored = context_manager.restore_session(sample_context_data["session_id"])

        assert restored is not None
        assert restored["session_id"] == sample_context_data["session_id"]
        assert restored["current_goal"] == sample_context_data["current_goal"]

    def test_restore_nonexistent_session(self, context_manager):
        """Test restoring a non-existent session."""
        context_manager.initialize()

        restored = context_manager.restore_session("nonexistent-id")
        assert restored is None

    def test_restore_latest(self, context_manager, sample_context_data):
        """Test restoring the latest session."""
        context_manager.initialize()

        # Store multiple contexts
        for i in range(3):
            data = sample_context_data.copy()
            data["session_id"] = f"session-{i}"
            data["timestamp"] = f"2024-01-01T12:0{i}:00"
            data["working_directory"] = str(
                context_manager.project_path
            )  # Fix working directory
            snapshot = ContextSnapshot(**data)
            context_manager._store_context(snapshot)

        # Restore latest
        restored = context_manager.restore_latest()

        assert restored is not None
        assert restored["session_id"] == "session-2"  # Latest one

    def test_list_sessions(self, context_manager, sample_context_data):
        """Test listing sessions."""
        context_manager.initialize()

        # Store multiple sessions
        for i in range(5):
            data = sample_context_data.copy()
            data["session_id"] = f"session-{i}"
            data["current_goal"] = f"Goal {i}"
            data["working_directory"] = str(
                context_manager.project_path
            )  # Fix working directory
            snapshot = ContextSnapshot(**data)
            context_manager._store_context(snapshot)

        sessions = context_manager.list_sessions(limit=3)

        assert len(sessions) == 3
        assert all("id" in session for session in sessions)
        assert all("current_goal" in session for session in sessions)

    def test_get_current_context(self, context_manager, mock_subprocess):
        """Test getting current context."""
        context_manager.initialize()

        with patch.object(context_manager, "_capture_current_state") as mock_capture:
            mock_snapshot = Mock()
            mock_snapshot.to_dict.return_value = {"test": "data"}
            mock_capture.return_value = mock_snapshot

            current = context_manager.get_current_context()
            assert current == {"test": "data"}

    def test_start_stop_auto_save(self, context_manager):
        """Test auto-save functionality."""
        context_manager.start_auto_save(interval=10)
        assert context_manager._auto_save_enabled is True

        context_manager.stop_auto_save()
        assert context_manager._auto_save_enabled is False

    def test_cleanup_old_sessions(self, context_manager, sample_context_data):
        """Test cleaning up old sessions."""
        from datetime import datetime, timedelta

        context_manager.initialize()

        # Store old session (simulate by setting old timestamp)
        old_timestamp = (datetime.now() - timedelta(days=5)).isoformat()  # 5 days ago
        old_data = sample_context_data.copy()
        old_data["timestamp"] = old_timestamp
        old_data["working_directory"] = str(
            context_manager.project_path
        )  # Fix working directory
        old_snapshot = ContextSnapshot(**old_data)
        context_manager._store_context(old_snapshot)

        # Store recent session
        recent_timestamp = (
            datetime.now() - timedelta(hours=12)
        ).isoformat()  # 12 hours ago
        recent_data = sample_context_data.copy()
        recent_data["session_id"] = "recent-session"
        recent_data["timestamp"] = recent_timestamp
        recent_data["working_directory"] = str(
            context_manager.project_path
        )  # Fix working directory
        recent_snapshot = ContextSnapshot(**recent_data)
        context_manager._store_context(recent_snapshot)

        # Clean up (keep only 1 day)
        deleted_count = context_manager.cleanup_old_sessions(days=1)

        assert deleted_count > 0

        # Verify recent session still exists
        sessions = context_manager.list_sessions()
        session_ids = [s["id"] for s in sessions]
        assert "recent-session" in session_ids

    @patch("subprocess.run")
    def test_get_git_state(self, mock_run, context_manager):
        """Test getting git repository state."""
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout="main\n"),  # git branch
            Mock(returncode=0, stdout=" M file.py\n"),  # git status
            Mock(returncode=0, stdout="abc123 Last commit\n"),  # git log
        ]

        git_state = context_manager._get_git_state()

        assert git_state["branch"] == "main"
        assert git_state["has_changes"] is True
        assert git_state["last_commit"] == "abc123 Last commit"

    @patch("subprocess.run")
    def test_get_git_state_error(self, mock_run, context_manager):
        """Test handling git command errors."""
        # Mock git command failure
        mock_run.side_effect = [Mock(returncode=1, stdout="", stderr="Not a git repo")]

        git_state = context_manager._get_git_state()

        # Should return empty dict on error
        assert isinstance(git_state, dict)

    def test_get_open_files(self, context_manager, temp_project_dir):
        """Test getting list of open files."""
        # Create some test files
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()

        test_file = src_dir / "test.py"
        test_file.write_text('print("hello")')

        open_files = context_manager._get_open_files()

        assert isinstance(open_files, list)
        # Should find the .py file we created
        python_files = [f for f in open_files if f["path"].endswith(".py")]
        assert len(python_files) > 0

    def test_emergency_save(self, context_manager, mock_subprocess):
        """Test emergency context save."""
        context_manager.initialize()

        context_manager._emergency_save()

        emergency_file = context_manager.dopemux_dir / "emergency_context.json"
        assert emergency_file.exists()

        # Verify content
        with open(emergency_file) as f:
            data = json.load(f)
            assert "session_id" in data
            assert "timestamp" in data

    def test_has_context_changed(self, context_manager):
        """Test context change detection."""
        snapshot = ContextSnapshot()

        # Currently always returns True (placeholder implementation)
        changed = context_manager._has_context_changed(snapshot)
        assert changed is True

    def test_store_and_retrieve_context(self, context_manager, sample_context_data):
        """Test full context storage and retrieval cycle."""
        context_manager.initialize()

        # Store context
        data = sample_context_data.copy()
        data["working_directory"] = str(
            context_manager.project_path
        )  # Fix working directory
        snapshot = ContextSnapshot(**data)
        context_manager._store_context(snapshot)

        # Retrieve from database
        with sqlite3.connect(context_manager.db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM context_snapshots WHERE session_id = ?",
                (sample_context_data["session_id"],),
            )
            row = cursor.fetchone()

            assert row is not None
            stored_data = json.loads(row[0])
            assert stored_data["session_id"] == sample_context_data["session_id"]

    def test_session_metadata_tracking(self, context_manager):
        """Test session metadata updates."""
        context_manager.initialize()

        session_id = "test-session-123"
        context_manager._update_session_metadata(session_id)

        # Verify metadata was stored
        with sqlite3.connect(context_manager.db_path) as conn:
            cursor = conn.execute(
                "SELECT project_path FROM session_metadata WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == str(context_manager.project_path)

    def test_save_session_file(self, context_manager, sample_context_data):
        """Test saving detailed session files."""
        context_manager.initialize()

        snapshot = ContextSnapshot(**sample_context_data)
        context_manager._save_session_file(snapshot)

        session_file = (
            context_manager.sessions_dir / f"session-{snapshot.session_id}.json"
        )
        assert session_file.exists()

        # Verify content
        with open(session_file) as f:
            data = json.load(f)
            assert data["session_id"] == sample_context_data["session_id"]

    def test_capture_current_state_integration(self, context_manager, mock_subprocess):
        """Test capturing current state with all components."""
        context_manager.initialize()

        snapshot = context_manager._capture_current_state()

        assert isinstance(snapshot, ContextSnapshot)
        assert snapshot.session_id
        assert snapshot.working_directory == str(context_manager.project_path)
        assert isinstance(snapshot.open_files, list)
        assert isinstance(snapshot.git_state, dict)

    def test_force_save_context(self, context_manager, mock_subprocess):
        """Test forcing context save even without changes."""
        context_manager.initialize()

        # Mock _has_context_changed to return False
        with patch.object(context_manager, "_has_context_changed", return_value=False):
            # Save without force - should return early
            session_id1 = context_manager.save_context(force=False)

            # Save with force - should actually save
            session_id2 = context_manager.save_context(force=True)

            # Both should return session IDs but force should create new entry
            assert session_id1
            assert session_id2

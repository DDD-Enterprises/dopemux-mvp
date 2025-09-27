#!/usr/bin/env python3
"""
Unit tests for session management slash commands.

Tests the SessionFormatter, SlashCommandProcessor session commands,
and ContextManager enhancements for ADHD-friendly session management.
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add the scripts directory to path for importing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from session_formatter import SessionFormatter
from slash_commands import SlashCommandProcessor
from dopemux.adhd.context_manager import ContextManager, ContextSnapshot


class TestSessionFormatter:
    """Test SessionFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = SessionFormatter()

    def test_format_save_confirmation(self):
        """Test session save confirmation formatting."""
        session_data = {
            "session_id": "test-session-123",
            "message": "Test save message",
            "current_goal": "Implement session management",
            "open_files": [
                {"path": "test1.py"},
                {"path": "test2.py"}
            ],
            "timestamp": datetime.now().isoformat()
        }

        result = self.formatter.format_save_confirmation(session_data)

        assert "💾 Session Saved Successfully!" in str(result)
        assert "test-sessi" in str(result)  # Truncated ID
        assert "Test save message" in str(result)
        assert "2 files saved" in str(result)

    def test_format_session_gallery_empty(self):
        """Test session gallery with no sessions."""
        result = self.formatter.format_session_gallery([])

        assert "No sessions found" in str(result)
        assert "Use '/save' to create your first session!" in str(result)

    def test_format_session_gallery_with_sessions(self):
        """Test session gallery with multiple sessions."""
        now = datetime.now()
        sessions = [
            {
                "id": "session1",
                "timestamp": now.isoformat(),
                "current_goal": "Feature implementation",
                "open_files": [{"path": "feature.py"}],
                "git_branch": "feature-branch",
                "focus_duration": 30,
                "message": "Working on new feature"
            },
            {
                "id": "session2",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "current_goal": "Bug fix",
                "open_files": [{"path": "bug.py"}],
                "git_branch": "main",
                "focus_duration": 15,
                "message": "Fixing critical bug"
            }
        ]

        result = self.formatter.format_session_gallery(sessions)

        assert "Recent Sessions" in str(result)
        assert "Working on new feature" in str(result)
        assert "Fixing critical bug" in str(result)

    def test_detect_session_type(self):
        """Test session type detection."""
        # Feature session
        session_data = {"message": "implement new feature", "open_files": []}
        session_type = self.formatter._detect_session_type(session_data)
        assert session_type in ["feature", "general"]

        # Bug fix session
        session_data = {"message": "fix critical bug", "open_files": []}
        session_type = self.formatter._detect_session_type(session_data)
        assert session_type in ["bugfix", "general"]

    def test_group_sessions_by_time(self):
        """Test time-based session grouping."""
        now = datetime.now()
        sessions = [
            {"timestamp": now.isoformat()},
            {"timestamp": (now - timedelta(days=1)).isoformat()},
            {"timestamp": (now - timedelta(days=3)).isoformat()},
            {"timestamp": (now - timedelta(days=10)).isoformat()}
        ]

        grouped = self.formatter._group_sessions_by_time(sessions)

        assert "Today" in grouped
        assert "Yesterday" in grouped
        assert "This Week" in grouped
        assert "Older" in grouped
        assert len(grouped["Today"]) == 1
        assert len(grouped["Yesterday"]) == 1

    def test_format_relative_time(self):
        """Test relative time formatting."""
        now = datetime.now()

        # Just now
        result = self.formatter._format_relative_time(now.isoformat())
        assert result == "just now"

        # Minutes ago
        past = now - timedelta(minutes=30)
        result = self.formatter._format_relative_time(past.isoformat())
        assert "min ago" in result

        # Hours ago
        past = now - timedelta(hours=3)
        result = self.formatter._format_relative_time(past.isoformat())
        assert "h ago" in result

    def test_calculate_session_completion(self):
        """Test session completion calculation."""
        session = {
            "open_files": [{"path": "test1.py"}, {"path": "test2.py"}],
            "current_goal": "Implement feature",
            "message": "Progress update",
            "focus_duration": 25
        }

        completion = self.formatter._calculate_session_completion(session)
        assert 0.0 <= completion <= 1.0


class TestSlashCommandProcessorSessions:
    """Test session commands in SlashCommandProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.processor = SlashCommandProcessor(self.temp_dir)

        # Initialize the context manager database
        self.processor.context_manager.initialize()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('dopemux.adhd.context_manager.subprocess.run')
    def test_save_session_command(self, mock_subprocess):
        """Test save session command."""
        # Mock git commands
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "main"

        result = self.processor.process_command("save", ["--message", "Test save"])

        assert result["success"] is True
        assert result["command"] == "save"
        assert "session_id" in result
        assert "formatted_output" in result

    @patch('dopemux.adhd.context_manager.subprocess.run')
    def test_save_session_with_tags(self, mock_subprocess):
        """Test save session command with tags."""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "main"

        result = self.processor.process_command("save", [
            "--message", "Feature work",
            "--tag", "feature",
            "--tag", "python"
        ])

        assert result["success"] is True
        assert "tags" in result["session_data"]

    def test_list_sessions_empty(self):
        """Test list sessions when no sessions exist."""
        result = self.processor.process_command("sessions")

        assert result["success"] is True
        assert result["command"] == "sessions"
        assert result["sessions"] == []

    @patch('dopemux.adhd.context_manager.subprocess.run')
    def test_list_sessions_with_data(self, mock_subprocess):
        """Test list sessions with existing sessions."""
        # Mock git commands
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "main"

        # Create a test session first
        save_result = self.processor.process_command("save", ["--message", "Test session"])
        assert save_result["success"] is True

        # Now list sessions
        result = self.processor.process_command("sessions")

        assert result["success"] is True
        assert len(result["sessions"]) == 1
        assert "formatted_output" in result

    def test_list_sessions_with_search(self):
        """Test list sessions with search filter."""
        result = self.processor.process_command("sessions", ["--search", "feature"])

        assert result["success"] is True
        assert result["command"] == "sessions"

    def test_list_sessions_with_limit(self):
        """Test list sessions with limit."""
        result = self.processor.process_command("sessions", ["--limit", "5"])

        assert result["success"] is True
        assert result["command"] == "sessions"

    def test_restore_session_not_found(self):
        """Test restore session when session doesn't exist."""
        result = self.processor.process_command("restore", ["nonexistent"])

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_restore_latest_no_sessions(self):
        """Test restore latest when no sessions exist."""
        result = self.processor.process_command("restore")

        assert result["success"] is False
        assert "No sessions found" in result["error"]

    @patch('dopemux.adhd.context_manager.subprocess.run')
    def test_restore_session_preview(self, mock_subprocess):
        """Test restore session with preview mode."""
        # Mock git commands
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "main"

        # Create a session first
        save_result = self.processor.process_command("save", ["--message", "Test session"])
        assert save_result["success"] is True
        session_id = save_result["session_id"]

        # Test preview
        result = self.processor.process_command("restore", [session_id, "--preview"])

        assert result["success"] is True
        assert "Ready to Restore Session" in result["formatted_output"]

    def test_session_details_no_args(self):
        """Test session details without arguments."""
        result = self.processor.process_command("session-details", [])

        assert result["success"] is False
        assert "Session ID required" in result["error"]

    def test_session_details_not_found(self):
        """Test session details for non-existent session."""
        result = self.processor.process_command("session-details", ["nonexistent"])

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('dopemux.adhd.context_manager.subprocess.run')
    def test_session_details_found(self, mock_subprocess):
        """Test session details for existing session."""
        # Mock git commands
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "main"

        # Create a session first
        save_result = self.processor.process_command("save", ["--message", "Test session"])
        assert save_result["success"] is True
        session_id = save_result["session_id"]

        # Get details
        result = self.processor.process_command("session-details", [session_id[:8]])

        assert result["success"] is True
        assert "formatted_output" in result

    def test_unknown_command(self):
        """Test unknown command returns error."""
        result = self.processor.process_command("unknown-command")

        assert result["success"] is False
        assert "Unknown command" in result["error"]
        assert "save" in result["available_commands"]
        assert "restore" in result["available_commands"]


class TestContextManagerEnhancements:
    """Test ContextManager smart tagging and description features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.context_manager = ContextManager(self.temp_dir)
        self.context_manager.initialize()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_smart_description_from_git_changes(self):
        """Test smart description generation from git changes."""
        context = ContextSnapshot(
            git_state={
                "status": "M  test.py\\nA  new_feature.py"
            },
            current_goal="Default goal"
        )

        description = self.context_manager.generate_smart_description(context)
        assert "Added new_feature.py" in description

    def test_generate_smart_description_from_goal(self):
        """Test smart description generation from goal."""
        context = ContextSnapshot(
            git_state={},
            current_goal="Implement user authentication system"
        )

        description = self.context_manager.generate_smart_description(context)
        assert "authentication" in description.lower()

    def test_auto_tag_session_python(self):
        """Test automatic tagging for Python sessions."""
        context = ContextSnapshot(
            git_state={"status": "M  main.py\\nM  utils.py"},
            open_files=[{"path": "test.py"}],
            message="Working on Python feature"
        )

        tags = self.context_manager.auto_tag_session(context)
        assert "python" in tags

    def test_auto_tag_session_feature(self):
        """Test automatic tagging for feature sessions."""
        context = ContextSnapshot(
            git_state={},
            open_files=[{"path": "feature/new_api.py"}],
            message="Implementing new API feature"
        )

        tags = self.context_manager.auto_tag_session(context)
        assert "feature" in tags

    def test_auto_tag_session_time_based(self):
        """Test time-based automatic tagging."""
        context = ContextSnapshot()

        tags = self.context_manager.auto_tag_session(context)

        # Should have at least one time-based tag
        time_tags = ["morning", "afternoon", "evening", "late-night"]
        assert any(tag in tags for tag in time_tags)

    def test_detect_session_type_feature(self):
        """Test session type detection for features."""
        context = ContextSnapshot(
            message="implement new user dashboard",
            git_state={}
        )

        session_type = self.context_manager.detect_session_type(context)
        assert session_type == "feature"

    def test_detect_session_type_bugfix(self):
        """Test session type detection for bug fixes."""
        context = ContextSnapshot(
            message="fix login error bug",
            git_state={}
        )

        session_type = self.context_manager.detect_session_type(context)
        assert session_type == "bugfix"

    def test_detect_session_type_from_commit(self):
        """Test session type detection from commit messages."""
        context = ContextSnapshot(
            message="",
            git_state={"last_commit": "abc123 feat: add user profile page"}
        )

        session_type = self.context_manager.detect_session_type(context)
        assert session_type == "feature"

    def test_detect_session_type_from_files(self):
        """Test session type detection from file types."""
        context = ContextSnapshot(
            message="",
            open_files=[
                {"path": "test_user.py"},
                {"path": "test_auth.py"}
            ]
        )

        session_type = self.context_manager.detect_session_type(context)
        assert session_type == "testing"

    def test_add_and_get_session_tags(self):
        """Test adding and retrieving session tags."""
        session_id = "test-session-123"
        tags = ["python", "feature", "morning"]

        self.context_manager.add_session_tags(session_id, tags)
        retrieved_tags = self.context_manager.get_session_tags(session_id)

        assert set(retrieved_tags) == set(tags)

    @patch('dopemux.adhd.context_manager.subprocess.run')
    def test_search_sessions_by_tag(self, mock_subprocess):
        """Test searching sessions by tag."""
        # Mock git commands
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "main"

        # Create a test session with tags
        session_id = self.context_manager.save_context(message="Python feature work")
        self.context_manager.add_session_tags(session_id, ["python", "feature"])

        # Search by tag
        results = self.context_manager.search_sessions_by_tag("python")

        assert len(results) == 1
        assert "python" in results[0]["tags"]

    def test_enhanced_context_snapshot(self):
        """Test enhanced ContextSnapshot with new fields."""
        context = ContextSnapshot(
            tags=["python", "feature"],
            auto_description="Working on authentication",
            session_type="feature"
        )

        data = context.to_dict()
        assert data["tags"] == ["python", "feature"]
        assert data["auto_description"] == "Working on authentication"
        assert data["session_type"] == "feature"

    def test_context_snapshot_from_dict(self):
        """Test creating ContextSnapshot from dictionary."""
        data = {
            "session_id": "test-123",
            "tags": ["python"],
            "auto_description": "Test description",
            "session_type": "testing"
        }

        context = ContextSnapshot.from_dict(data)
        assert context.tags == ["python"]
        assert context.auto_description == "Test description"
        assert context.session_type == "testing"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
"""
Pytest configuration and shared fixtures.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dopemux.adhd import AttentionMonitor, ContextManager, TaskDecomposer
from dopemux.config import ConfigManager


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "version": "1.0",
        "adhd_profile": {
            "focus_duration_avg": 25,
            "break_interval": 5,
            "distraction_sensitivity": 0.5,
            "hyperfocus_tendency": False,
            "notification_style": "gentle",
            "visual_complexity": "minimal",
        },
        "mcp_servers": {
            "test-server": {
                "enabled": True,
                "command": "python",
                "args": ["test.py"],
                "env": {},
                "timeout": 30,
                "auto_restart": True,
            }
        },
        "attention": {
            "enabled": True,
            "sample_interval": 5,
            "keystroke_threshold": 2.0,
            "context_switch_threshold": 3,
            "adaptation_enabled": True,
        },
        "context": {
            "enabled": True,
            "auto_save_interval": 30,
            "max_sessions": 50,
            "compression": True,
            "backup_enabled": True,
        },
    }


@pytest.fixture
def config_manager(temp_config_dir, sample_config_data):
    """Create a ConfigManager instance for testing."""
    config_file = temp_config_dir / "config.yaml"

    with patch("dopemux.config.manager.ConfigManager._init_paths") as mock_init_paths:
        from dopemux.config.manager import ConfigPaths

        mock_init_paths.return_value = ConfigPaths(
            global_config=temp_config_dir / "global.yaml",
            user_config=config_file,
            project_config=temp_config_dir / "project.yaml",
            cache_dir=temp_config_dir / "cache",
            data_dir=temp_config_dir / "data",
        )

        manager = ConfigManager()
        # Mock the default config
        with patch.object(
            manager, "_get_default_config", return_value=sample_config_data
        ):
            yield manager


@pytest.fixture
def context_manager(temp_project_dir):
    """Create a ContextManager instance for testing."""
    return ContextManager(temp_project_dir)


@pytest.fixture
def attention_monitor(temp_project_dir):
    """Create an AttentionMonitor instance for testing."""
    return AttentionMonitor(temp_project_dir)


@pytest.fixture
def task_decomposer(temp_project_dir):
    """Create a TaskDecomposer instance for testing."""
    return TaskDecomposer(temp_project_dir)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls."""
    with patch("subprocess.run") as mock_run:
        # Default successful git commands
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main\n"
        yield mock_run


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    with patch("dopemux.adhd.context_manager.datetime") as mock_dt:
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        yield mock_dt


@pytest.fixture
def sample_context_data():
    """Sample context data for testing."""
    return {
        "session_id": "test-session-123",
        "timestamp": "2024-01-01T12:00:00",
        "working_directory": "/test/project",
        "open_files": [
            {
                "path": "src/main.py",
                "absolute_path": "/test/project/src/main.py",
                "last_modified": "2024-01-01T11:30:00",
                "cursor_position": {"line": 10, "column": 5},
                "scroll_position": 0,
                "unsaved_changes": False,
            }
        ],
        "current_goal": "Implement feature X",
        "mental_model": {
            "approach": "Using pattern Y",
            "next_steps": ["Step 1", "Step 2"],
            "blockers": [],
        },
        "git_state": {
            "branch": "feature-branch",
            "status": "",
            "has_changes": False,
            "last_commit": "abc123 Last commit message",
        },
        "recent_commands": ["git status", "python test.py"],
        "decisions": [
            {
                "timestamp": "2024-01-01T11:45:00",
                "decision": "Use approach A over B",
                "rationale": "Better performance",
            }
        ],
        "attention_state": "focused",
        "focus_duration": 25,
        "context_switches": 2,
        "unsaved_changes": False,
        "message": "Working on feature implementation",
    }


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "EXA_API_KEY": "test-exa-key",
    }

    with patch.dict("os.environ", env_vars):
        yield env_vars

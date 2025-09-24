"""
Unit tests for Claude Auto Responder integration.
"""

import subprocess
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dopemux.config.manager import ClaudeAutoResponderConfig, ConfigManager
from integrations.claude_autoresponder import (
    AutoResponderMetrics,
    AutoResponderStatus,
    ClaudeAutoResponderManager,
    create_autoresponder_manager,
)


class TestClaudeAutoResponderConfig:
    """Test Claude Auto Responder configuration model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ClaudeAutoResponderConfig()

        assert config.enabled is False
        assert config.terminal_scope == "current"
        assert config.response_delay == 0.0
        assert config.timeout_minutes == 30
        assert config.whitelist_tools is True
        assert config.debug_mode is False

    def test_config_validation_response_delay(self):
        """Test response delay validation."""
        # Valid delays
        config = ClaudeAutoResponderConfig(response_delay=0.0)
        assert config.response_delay == 0.0

        config = ClaudeAutoResponderConfig(response_delay=5.0)
        assert config.response_delay == 5.0

        config = ClaudeAutoResponderConfig(response_delay=10.0)
        assert config.response_delay == 10.0

        # Invalid delays
        with pytest.raises(ValueError):
            ClaudeAutoResponderConfig(response_delay=-1.0)

        with pytest.raises(ValueError):
            ClaudeAutoResponderConfig(response_delay=11.0)

    def test_config_validation_terminal_scope(self):
        """Test terminal scope validation."""
        # Valid scopes
        for scope in ["current", "all", "project"]:
            config = ClaudeAutoResponderConfig(terminal_scope=scope)
            assert config.terminal_scope == scope

        # Invalid scope
        with pytest.raises(ValueError):
            ClaudeAutoResponderConfig(terminal_scope="invalid")


class TestAutoResponderMetrics:
    """Test auto responder metrics tracking."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        start_time = datetime.now()
        metrics = AutoResponderMetrics(start_time=start_time)

        assert metrics.start_time == start_time
        assert metrics.responses_sent == 0
        assert metrics.last_response_time is None
        assert metrics.errors_count == 0
        assert metrics.status == AutoResponderStatus.STOPPED

    def test_uptime_calculation(self):
        """Test uptime calculation."""
        start_time = datetime.now() - timedelta(minutes=5)
        metrics = AutoResponderMetrics(start_time=start_time)

        # Should be approximately 5 minutes
        assert 4.9 <= metrics.uptime_minutes <= 5.1

    def test_responses_per_minute_calculation(self):
        """Test responses per minute calculation."""
        start_time = datetime.now() - timedelta(minutes=10)
        metrics = AutoResponderMetrics(start_time=start_time, responses_sent=20)

        # Should be approximately 2 responses per minute
        assert 1.8 <= metrics.responses_per_minute <= 2.2

    def test_responses_per_minute_zero_uptime(self):
        """Test responses per minute with zero uptime."""
        start_time = datetime.now()
        metrics = AutoResponderMetrics(start_time=start_time, responses_sent=5)

        # Should handle division by zero
        assert metrics.responses_per_minute >= 0


class TestClaudeAutoResponderManager:
    """Test Claude Auto Responder manager."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / ".dopemux").mkdir()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config_manager(self, temp_project_dir):
        """Create mock config manager."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_claude_autoresponder_config.return_value = (
            ClaudeAutoResponderConfig()
        )
        return config_manager

    @pytest.fixture
    def autoresponder_manager(self, mock_config_manager, temp_project_dir):
        """Create auto responder manager instance."""
        return ClaudeAutoResponderManager(mock_config_manager, temp_project_dir)

    def test_initialization(self, autoresponder_manager, temp_project_dir):
        """Test manager initialization."""
        assert autoresponder_manager.project_path == temp_project_dir
        assert (
            autoresponder_manager.data_dir
            == temp_project_dir / ".dopemux" / "autoresponder"
        )
        assert autoresponder_manager.data_dir.exists()
        assert not autoresponder_manager.is_running()

    @patch("subprocess.run")
    def test_setup_autoresponder_success(self, mock_run, autoresponder_manager):
        """Test successful auto responder setup."""
        mock_run.return_value = Mock()

        # Mock the repository and setup files
        car_repo = autoresponder_manager.car_repo_path
        car_repo.mkdir(parents=True)
        (car_repo / "setup.py").touch()

        result = autoresponder_manager.setup_autoresponder()

        assert result is True
        assert (car_repo / "whitelisted_tools.txt").exists()

    @patch("subprocess.run")
    def test_setup_autoresponder_clone_failure(self, mock_run, autoresponder_manager):
        """Test auto responder setup with clone failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = autoresponder_manager.setup_autoresponder()

        assert result is False

    def test_whitelist_setup(self, autoresponder_manager, mock_config_manager):
        """Test whitelist configuration setup."""
        # Setup repository
        car_repo = autoresponder_manager.car_repo_path
        car_repo.mkdir(parents=True)

        # Configure whitelist enabled
        config = ClaudeAutoResponderConfig(whitelist_tools=True)
        mock_config_manager.get_claude_autoresponder_config.return_value = config

        autoresponder_manager._setup_whitelist()

        whitelist_file = car_repo / "whitelisted_tools.txt"
        assert whitelist_file.exists()

        content = whitelist_file.read_text()
        assert "Read" in content
        assert "Write" in content
        assert "Bash" in content

    def test_build_command_basic(self, autoresponder_manager, mock_config_manager):
        """Test command building with basic configuration."""
        config = ClaudeAutoResponderConfig()
        mock_config_manager.get_claude_autoresponder_config.return_value = config

        cmd = autoresponder_manager._build_command(config)

        assert cmd[0] == "python3"
        assert str(autoresponder_manager.car_executable) in cmd
        assert "--single-window" in cmd

    def test_build_command_all_options(
        self, autoresponder_manager, mock_config_manager
    ):
        """Test command building with all options."""
        config = ClaudeAutoResponderConfig(
            response_delay=2.0,
            terminal_scope="all",
            debug_mode=True,
            whitelist_tools=True,
        )
        mock_config_manager.get_claude_autoresponder_config.return_value = config

        # Setup whitelist file
        car_repo = autoresponder_manager.car_repo_path
        car_repo.mkdir(parents=True)
        (car_repo / "whitelisted_tools.txt").touch()

        cmd = autoresponder_manager._build_command(config)

        assert "--delay" in cmd
        assert "2.0" in cmd
        assert "--multi-window" in cmd
        assert "--debug" in cmd
        assert "--whitelist" in cmd

    @patch("subprocess.Popen")
    def test_start_success(
        self, mock_popen, autoresponder_manager, mock_config_manager
    ):
        """Test successful start."""
        # Setup config
        config = ClaudeAutoResponderConfig(enabled=True)
        mock_config_manager.get_claude_autoresponder_config.return_value = config

        # Setup executable
        autoresponder_manager.car_executable.parent.mkdir(parents=True)
        autoresponder_manager.car_executable.touch()

        # Mock process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        result = autoresponder_manager.start()

        assert result is True
        assert autoresponder_manager.is_running()
        assert autoresponder_manager._metrics.status == AutoResponderStatus.RUNNING

    def test_start_disabled(self, autoresponder_manager, mock_config_manager):
        """Test start with disabled configuration."""
        config = ClaudeAutoResponderConfig(enabled=False)
        mock_config_manager.get_claude_autoresponder_config.return_value = config

        result = autoresponder_manager.start()

        assert result is False
        assert not autoresponder_manager.is_running()

    def test_start_already_running(self, autoresponder_manager):
        """Test start when already running."""
        # Mock running state
        autoresponder_manager._process = Mock()
        autoresponder_manager._process.poll.return_value = None
        autoresponder_manager._metrics.status = AutoResponderStatus.RUNNING

        result = autoresponder_manager.start()

        assert result is True

    def test_stop_success(self, autoresponder_manager):
        """Test successful stop."""
        # Setup running state
        mock_process = Mock()
        autoresponder_manager._process = mock_process
        autoresponder_manager._metrics.status = AutoResponderStatus.RUNNING
        autoresponder_manager._stop_event = threading.Event()

        result = autoresponder_manager.stop()

        assert result is True
        assert autoresponder_manager._metrics.status == AutoResponderStatus.STOPPED
        mock_process.terminate.assert_called_once()

    def test_stop_not_running(self, autoresponder_manager):
        """Test stop when not running."""
        result = autoresponder_manager.stop()
        assert result is True

    def test_stop_force_kill(self, autoresponder_manager):
        """Test stop with force kill after timeout."""
        # Setup running state
        mock_process = Mock()
        mock_process.wait.side_effect = [subprocess.TimeoutExpired("test", 5), None]
        autoresponder_manager._process = mock_process
        autoresponder_manager._metrics.status = AutoResponderStatus.RUNNING
        autoresponder_manager._stop_event = threading.Event()

        result = autoresponder_manager.stop()

        assert result is True
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_get_status(self, autoresponder_manager, mock_config_manager):
        """Test status retrieval."""
        config = ClaudeAutoResponderConfig()
        mock_config_manager.get_claude_autoresponder_config.return_value = config

        autoresponder_manager._metrics.responses_sent = 5
        autoresponder_manager._attention_state = "focused"

        status = autoresponder_manager.get_status()

        assert status["status"] == "stopped"
        assert status["running"] is False
        assert status["responses_sent"] == 5
        assert status["attention_state"] == "focused"
        assert "config" in status

    def test_update_attention_state(self, autoresponder_manager):
        """Test attention state updates."""
        autoresponder_manager.update_attention_state("scattered")

        assert autoresponder_manager._attention_state == "scattered"
        # Should update last activity time
        assert autoresponder_manager._last_activity is not None

    def test_restart(self, autoresponder_manager):
        """Test restart functionality."""
        with patch.object(autoresponder_manager, "stop") as mock_stop, patch.object(
            autoresponder_manager, "start"
        ) as mock_start:

            mock_stop.return_value = True
            mock_start.return_value = True

            result = autoresponder_manager.restart()

            assert result is True
            mock_stop.assert_called_once()
            mock_start.assert_called_once()

    def test_update_config(self, autoresponder_manager, mock_config_manager):
        """Test configuration updates."""
        with patch.object(autoresponder_manager, "restart") as mock_restart:
            # Not running - shouldn't restart
            mock_restart.return_value = True
            autoresponder_manager._process = None

            result = autoresponder_manager.update_config(enabled=True)

            assert result is True
            mock_config_manager.update_claude_autoresponder.assert_called_once_with(
                enabled=True
            )
            mock_restart.assert_not_called()

    def test_update_config_running(self, autoresponder_manager, mock_config_manager):
        """Test configuration updates when running."""
        with patch.object(
            autoresponder_manager, "restart"
        ) as mock_restart, patch.object(
            autoresponder_manager, "is_running"
        ) as mock_is_running:

            mock_restart.return_value = True
            mock_is_running.return_value = True

            result = autoresponder_manager.update_config(enabled=True)

            assert result is True
            mock_restart.assert_called_once()


class TestConfigManagerIntegration:
    """Test integration with ConfigManager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    def test_config_manager_claude_autoresponder_methods(self, temp_config_dir):
        """Test ConfigManager auto responder methods."""
        config_manager = ConfigManager()
        config_manager.paths.user_config = temp_config_dir / "config.yaml"

        # Test get default config
        config = config_manager.get_claude_autoresponder_config()
        assert isinstance(config, ClaudeAutoResponderConfig)
        assert config.enabled is False

        # Test update
        config_manager.update_claude_autoresponder(enabled=True, response_delay=1.0)
        updated_config = config_manager.get_claude_autoresponder_config()
        assert updated_config.enabled is True
        assert updated_config.response_delay == 1.0

    def test_config_manager_default_config_includes_autoresponder(self):
        """Test that default config includes auto responder settings."""
        config_manager = ConfigManager()
        default_config = config_manager._get_default_config()

        assert "claude_autoresponder" in default_config
        autoresponder_config = default_config["claude_autoresponder"]
        assert autoresponder_config["enabled"] is False
        assert autoresponder_config["terminal_scope"] == "current"


class TestFactoryFunction:
    """Test factory function."""

    def test_create_autoresponder_manager(self, temp_project_dir):
        """Test factory function creates manager correctly."""
        config_manager = Mock(spec=ConfigManager)

        manager = create_autoresponder_manager(config_manager, temp_project_dir)

        assert isinstance(manager, ClaudeAutoResponderManager)
        assert manager.config_manager == config_manager
        assert manager.project_path == temp_project_dir


class TestMonitorThread:
    """Test monitoring thread functionality."""

    def test_monitor_process_timeout(self, autoresponder_manager, mock_config_manager):
        """Test monitor thread timeout functionality."""
        # Setup configuration with short timeout
        config = ClaudeAutoResponderConfig(timeout_minutes=1)
        mock_config_manager.get_claude_autoresponder_config.return_value = config

        # Set last activity to more than timeout ago
        autoresponder_manager._last_activity = datetime.now() - timedelta(minutes=2)

        # Setup process
        autoresponder_manager._process = Mock()
        autoresponder_manager._process.poll.return_value = None
        autoresponder_manager._stop_event = threading.Event()

        with patch.object(autoresponder_manager, "stop") as mock_stop:
            # Start monitor thread manually for testing
            autoresponder_manager._monitor_process()

            # Should have called stop due to timeout
            mock_stop.assert_called_once()

    def test_monitor_process_handles_dead_process(self, autoresponder_manager):
        """Test monitor thread handles dead process."""
        # Setup dead process
        autoresponder_manager._process = Mock()
        autoresponder_manager._process.poll.return_value = (
            1  # Exit code indicating dead
        )
        autoresponder_manager._stop_event = threading.Event()
        autoresponder_manager._metrics = AutoResponderMetrics(start_time=datetime.now())

        # Run monitor briefly
        autoresponder_manager._stop_event.set()  # Signal to stop immediately
        autoresponder_manager._monitor_process()

        # Should detect error state
        assert autoresponder_manager._metrics.status == AutoResponderStatus.ERROR
        assert autoresponder_manager._metrics.errors_count > 0

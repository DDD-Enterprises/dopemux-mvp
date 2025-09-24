"""
Integration tests for Claude Auto Responder with Dopemux components.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from dopemux.cli import cli
from dopemux.config.manager import ConfigManager
from integrations.claude_autoresponder import create_autoresponder_manager


class TestCLIIntegration:
    """Test CLI integration for auto responder commands."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project with Dopemux structure."""
        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / ".dopemux").mkdir()
        (temp_dir / ".claude").mkdir()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_autoresponder_config_command(self, runner, temp_project):
        """Test autoresponder config command."""
        with runner.isolated_filesystem():
            # Change to temp project directory
            import os

            os.chdir(str(temp_project))

            # Test showing current config
            result = runner.invoke(cli, ["autoresponder", "config"])
            assert result.exit_code == 0
            assert "Auto Responder Configuration" in result.output
            assert "Enabled" in result.output
            assert "No" in result.output  # Default is disabled

    def test_autoresponder_config_update(self, runner, temp_project):
        """Test updating autoresponder configuration."""
        with runner.isolated_filesystem():
            import os

            os.chdir(str(temp_project))

            # Update configuration
            result = runner.invoke(
                cli,
                [
                    "autoresponder",
                    "config",
                    "--enabled",
                    "--delay",
                    "1.0",
                    "--terminal-scope",
                    "all",
                ],
            )
            assert result.exit_code == 0
            assert "Configuration updated" in result.output

    def test_autoresponder_setup_command(self, runner, temp_project):
        """Test autoresponder setup command."""
        with runner.isolated_filesystem():
            import os

            os.chdir(str(temp_project))

            with patch(
                "integrations.claude_autoresponder.ClaudeAutoResponderManager.setup_autoresponder"
            ) as mock_setup:
                mock_setup.return_value = True

                result = runner.invoke(cli, ["autoresponder", "setup"])
                assert result.exit_code == 0
                assert "ClaudeAutoResponder setup complete" in result.output

    def test_autoresponder_start_command(self, runner, temp_project):
        """Test autoresponder start command."""
        with runner.isolated_filesystem():
            import os

            os.chdir(str(temp_project))

            with patch(
                "integrations.claude_autoresponder.ClaudeAutoResponderManager.start"
            ) as mock_start:
                mock_start.return_value = True

                result = runner.invoke(cli, ["autoresponder", "start"])
                assert result.exit_code == 0
                assert "Claude Auto Responder is now active" in result.output

    def test_autoresponder_start_command_with_options(self, runner, temp_project):
        """Test autoresponder start command with options."""
        with runner.isolated_filesystem():
            import os

            os.chdir(str(temp_project))

            with patch(
                "integrations.claude_autoresponder.ClaudeAutoResponderManager.start"
            ) as mock_start:
                mock_start.return_value = True

                result = runner.invoke(
                    cli,
                    [
                        "autoresponder",
                        "start",
                        "--terminal-scope",
                        "all",
                        "--delay",
                        "2.0",
                        "--timeout",
                        "60",
                        "--whitelist",
                        "--debug",
                    ],
                )
                assert result.exit_code == 0

    def test_autoresponder_stop_command(self, runner, temp_project):
        """Test autoresponder stop command."""
        with runner.isolated_filesystem():
            import os

            os.chdir(str(temp_project))

            with patch(
                "integrations.claude_autoresponder.ClaudeAutoResponderManager.is_running"
            ) as mock_running, patch(
                "integrations.claude_autoresponder.ClaudeAutoResponderManager.stop"
            ) as mock_stop, patch(
                "integrations.claude_autoresponder.ClaudeAutoResponderManager.get_status"
            ) as mock_status:

                mock_running.return_value = True
                mock_stop.return_value = True
                mock_status.return_value = {
                    "uptime_minutes": 15.5,
                    "responses_sent": 10,
                    "responses_per_minute": 0.65,
                }

                result = runner.invoke(cli, ["autoresponder", "stop"])
                assert result.exit_code == 0
                assert "Claude Auto Responder stopped" in result.output
                assert "Session Statistics" in result.output

    def test_autoresponder_status_command(self, runner, temp_project):
        """Test autoresponder status command."""
        with runner.isolated_filesystem():
            import os

            os.chdir(str(temp_project))

            with patch(
                "integrations.claude_autoresponder.ClaudeAutoResponderManager.get_status"
            ) as mock_status:
                mock_status.return_value = {
                    "status": "running",
                    "running": True,
                    "uptime_minutes": 30.0,
                    "responses_sent": 25,
                    "responses_per_minute": 0.83,
                    "attention_state": "focused",
                    "last_response": "2024-01-01T12:00:00",
                    "config": {
                        "enabled": True,
                        "terminal_scope": "current",
                        "response_delay": 0.0,
                        "timeout_minutes": 30,
                        "whitelist_tools": True,
                        "debug_mode": False,
                    },
                }

                result = runner.invoke(cli, ["autoresponder", "status"])
                assert result.exit_code == 0
                assert "Claude Auto Responder Status" in result.output
                assert "Running" in result.output
                assert "Configuration" in result.output

    def test_autoresponder_commands_require_project(self, runner):
        """Test that autoresponder commands require a Dopemux project."""
        with runner.isolated_filesystem():
            # No .dopemux directory
            result = runner.invoke(cli, ["autoresponder", "status"])
            assert result.exit_code == 1
            assert "No Dopemux project found" in result.output


class TestConfigManagerIntegration:
    """Test integration between auto responder and config manager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    def test_config_persistence(self, temp_config_dir):
        """Test configuration persistence across sessions."""
        config_path = temp_config_dir / "config.yaml"
        config_manager = ConfigManager(str(config_path))

        # Update auto responder config
        config_manager.update_claude_autoresponder(
            enabled=True,
            terminal_scope="all",
            response_delay=2.5,
            timeout_minutes=60,
            whitelist_tools=False,
            debug_mode=True,
        )

        # Create new config manager instance (simulating restart)
        new_config_manager = ConfigManager(str(config_path))
        loaded_config = new_config_manager.get_claude_autoresponder_config()

        # Verify settings persisted
        assert loaded_config.enabled is True
        assert loaded_config.terminal_scope == "all"
        assert loaded_config.response_delay == 2.5
        assert loaded_config.timeout_minutes == 60
        assert loaded_config.whitelist_tools is False
        assert loaded_config.debug_mode is True

    def test_config_in_default_config(self):
        """Test auto responder config included in default configuration."""
        config_manager = ConfigManager()
        default_config = config_manager._get_default_config()

        assert "claude_autoresponder" in default_config
        car_config = default_config["claude_autoresponder"]

        # Verify default values
        assert car_config["enabled"] is False
        assert car_config["terminal_scope"] == "current"
        assert car_config["response_delay"] == 0.0
        assert car_config["timeout_minutes"] == 30
        assert car_config["whitelist_tools"] is True
        assert car_config["debug_mode"] is False


class TestManagerIntegration:
    """Test auto responder manager integration with other components."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project."""
        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / ".dopemux").mkdir()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config_manager(self):
        """Create config manager for testing."""
        return ConfigManager()

    def test_manager_creation(self, config_manager, temp_project):
        """Test manager creation and initialization."""
        manager = create_autoresponder_manager(config_manager, temp_project)

        assert manager.config_manager == config_manager
        assert manager.project_path == temp_project
        assert manager.data_dir.exists()
        assert manager.data_dir == temp_project / ".dopemux" / "autoresponder"

    def test_data_directory_structure(self, config_manager, temp_project):
        """Test data directory structure creation."""
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Check that required directories exist
        assert manager.data_dir.exists()
        assert manager.data_dir.is_dir()

        # Check repository path is correct
        expected_repo = manager.data_dir / "ClaudeAutoResponder"
        assert manager.car_repo_path == expected_repo

    @patch("subprocess.run")
    def test_setup_integration(self, mock_run, config_manager, temp_project):
        """Test setup integration with git and filesystem."""
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Mock successful git clone
        mock_run.return_value = Mock()

        # Create fake repository structure after "clone"
        def create_repo_structure(*args, **kwargs):
            manager.car_repo_path.mkdir(parents=True, exist_ok=True)
            (manager.car_repo_path / "setup.py").touch()
            (manager.car_repo_path / "claude_auto_responder.py").touch()

        mock_run.side_effect = create_repo_structure

        result = manager.setup_autoresponder()

        assert result is True
        assert manager.car_repo_path.exists()
        assert manager.car_executable.exists()
        assert (manager.car_repo_path / "whitelisted_tools.txt").exists()

    def test_configuration_integration(self, config_manager, temp_project):
        """Test configuration integration."""
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Update configuration
        manager.update_config(enabled=True, terminal_scope="all", response_delay=1.5)

        # Verify configuration was updated
        config = config_manager.get_claude_autoresponder_config()
        assert config.enabled is True
        assert config.terminal_scope == "all"
        assert config.response_delay == 1.5

    def test_attention_state_integration(self, config_manager, temp_project):
        """Test attention state integration."""
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Test different attention states
        attention_states = ["focused", "scattered", "hyperfocus", "distracted"]

        for state in attention_states:
            manager.update_attention_state(state)
            status = manager.get_status()
            assert status["attention_state"] == state

    def test_metrics_tracking(self, config_manager, temp_project):
        """Test metrics tracking functionality."""
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Initial metrics
        status = manager.get_status()
        assert status["responses_sent"] == 0
        assert status["running"] is False

        # Simulate metrics updates
        manager._metrics.responses_sent = 10
        manager._metrics.errors_count = 1

        updated_status = manager.get_status()
        assert updated_status["responses_sent"] == 10


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project."""
        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / ".dopemux").mkdir()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    def test_setup_failure_handling(self, temp_project):
        """Test handling of setup failures."""
        config_manager = ConfigManager()
        manager = create_autoresponder_manager(config_manager, temp_project)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            result = manager.setup_autoresponder()
            assert result is False

    def test_start_without_setup(self, temp_project):
        """Test starting without proper setup."""
        config_manager = ConfigManager()
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Enable auto responder but don't setup
        manager.update_config(enabled=True)

        result = manager.start()
        assert result is False

    def test_invalid_configuration_handling(self, temp_project):
        """Test handling of invalid configuration."""
        config_manager = ConfigManager()
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Test invalid delay
        with pytest.raises(ValueError):
            manager.update_config(response_delay=15.0)  # Too high

        # Test invalid scope
        with pytest.raises(ValueError):
            manager.update_config(terminal_scope="invalid")

    def test_process_monitoring_error_handling(self, temp_project):
        """Test error handling in process monitoring."""
        config_manager = ConfigManager()
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Setup mock process that fails
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Indicates process died
        manager._process = mock_process

        # Run monitor briefly
        import threading

        manager._stop_event = threading.Event()
        manager._stop_event.set()  # Stop immediately

        # This should handle the error gracefully
        manager._monitor_process()

        assert manager._metrics.errors_count > 0


class TestPerformanceIntegration:
    """Test performance aspects of integration."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project."""
        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / ".dopemux").mkdir()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    def test_concurrent_operations(self, temp_project):
        """Test concurrent operations handling."""
        config_manager = ConfigManager()
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Test multiple rapid status calls
        import threading

        results = []

        def get_status_worker():
            try:
                status = manager.get_status()
                results.append(status["status"])
            except Exception as e:
                results.append(f"Error: {e}")

        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_status_worker)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=1)

        # All should succeed
        assert len(results) == 5
        assert all("stopped" in str(result) for result in results)

    def test_memory_cleanup(self, temp_project):
        """Test memory cleanup on stop."""
        config_manager = ConfigManager()
        manager = create_autoresponder_manager(config_manager, temp_project)

        # Simulate starting and stopping
        manager._process = Mock()
        manager._monitor_thread = Mock()
        manager._stop_event = Mock()

        manager.stop()

        # Check cleanup
        assert manager._process is None
        assert manager._monitor_thread is None

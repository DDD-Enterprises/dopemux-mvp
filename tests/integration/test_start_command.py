import os
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

import pytest

from dopemux.cli import cli


@pytest.mark.integration
class TestStartCommandIntegration:
    """Integration tests for start command environment and process launching."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_project(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".dopemux").mkdir()
        return project_root

    @pytest.fixture
    def mock_launcher(self):
        with patch("dopemux.cli.ClaudeLauncher") as mock:
            instance = mock.return_value
            # Mock launch to return a fake process
            mock_process = MagicMock()
            mock_process.wait.return_value = None
            instance.launch.return_value = mock_process
            yield instance

    def test_start_basic_environment(self, runner, mock_project, mock_launcher):
        """Test basic start command sets up environment correctly."""
        with patch("dopemux.cli.Path.cwd", return_value=mock_project), \
             patch("dopemux.cli.AttentionMonitor"), \
             patch("dopemux.cli.ContextManager") as mock_ctx:

            # Setup context restoration
            mock_ctx.return_value.restore_latest.return_value = {"session_id": "test"}

            result = runner.invoke(cli, ["start", "--no-mcp"])

            assert result.exit_code == 0

            # Verify launcher was called
            mock_launcher.launch.assert_called_once()

            # Verify context was restored
            call_args = mock_launcher.launch.call_args[1]
            assert call_args.get("context") == {"session_id": "test"}

            # Verify project path
            assert call_args.get("project_path") == mock_project

    def test_start_with_litellm_flag(self, runner, mock_project, mock_launcher):
        """Test --litellm flag configures environment."""
        with patch("dopemux.cli.Path.cwd", return_value=mock_project), \
             patch("dopemux.cli.AttentionMonitor"), \
             patch("dopemux.cli.ContextManager"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test-key"}, clear=True), \
             patch("dopemux.cli.LiteLLMProxyManager") as mock_proxy_mgr, \
             patch("dopemux.cli.DopeBrainzRouterManager") as mock_router_mgr, \
             patch("dopemux.cli._load_litellm_models", return_value=["openrouter/anthropic/claude-sonnet-4"]):

            # Setup proxy mock
            mock_proxy_info = MagicMock()
            mock_proxy_info.base_url = "http://127.0.0.1:4000"
            mock_proxy_info.db_enabled = True
            mock_proxy_mgr.return_value.ensure_started.return_value = mock_proxy_info

            # Mock env builder
            mock_proxy_mgr.return_value.build_client_env.return_value = {
                "ANTHROPIC_BASE_URL": "http://127.0.0.1:4000",
                "DOPEMUX_CLAUDE_VIA_LITELLM": "1",
            }

            mock_router_info = MagicMock()
            mock_router_info.base_url = "http://127.0.0.1:3456"
            mock_router_info.already_running = False
            mock_router_mgr.return_value.ensure_started.return_value = mock_router_info
            mock_router_mgr.return_value.build_client_env.return_value = {
                "ANTHROPIC_BASE_URL": "http://127.0.0.1:3456",
                "ANTHROPIC_API_KEY": "router-key",
            }

            result = runner.invoke(cli, ["start", "--litellm", "--no-mcp", "--background"])

            assert result.exit_code == 0

            # Verify proxy manager was initialized and started
            mock_proxy_mgr.assert_called_once()
            mock_proxy_mgr.return_value.ensure_started.assert_called_once()
            mock_router_mgr.assert_called_once()
            mock_router_mgr.return_value.ensure_started.assert_called_once()

            # Verify environment variables were set
            assert os.environ.get("DOPEMUX_CLAUDE_VIA_LITELLM") == "1"
            assert os.environ.get("ANTHROPIC_BASE_URL") == "http://127.0.0.1:3456"

    def test_start_dangerous_mode(self, runner, mock_project, mock_launcher):
        """Test --dangerous flag activation."""
        with patch("dopemux.cli.Path.cwd", return_value=mock_project), \
             patch("dopemux.cli.AttentionMonitor"), \
             patch("dopemux.cli.ContextManager"), \
             patch("dopemux.cli.click.confirm", return_value=True):  # Auto-confirm dangerous prompts
            with patch.dict(os.environ, {}, clear=False):
                result = runner.invoke(cli, ["start", "--dangerous", "--no-mcp"])

                assert result.exit_code == 0

                # Verify dangerous flags
                assert os.environ.get("DOPEMUX_DANGEROUS_MODE") == "true"
                assert os.environ.get("CLAUDE_CODE_SKIP_PERMISSIONS") == "true"
                assert os.environ.get("HOOKS_ENABLE_ADAPTIVE_SECURITY") == "0"

    def test_start_no_mcp(self, runner, mock_project, mock_launcher):
        """Test --no-mcp flag behavior."""
        with patch("dopemux.cli.Path.cwd", return_value=mock_project), \
             patch("dopemux.cli.AttentionMonitor"), \
             patch("dopemux.cli.ContextManager"), \
             patch("dopemux.cli._start_mcp_servers_with_progress") as mock_start_mcp:

            result = runner.invoke(cli, ["start", "--no-mcp"])

            assert result.exit_code == 0

            # Verify start_mcp was NOT called
            mock_start_mcp.assert_not_called()

    def test_start_auto_configures_mcp(self, runner, mock_project, mock_launcher):
        """Test start command triggers auto-configuration."""
        with patch("dopemux.cli.Path.cwd", return_value=mock_project), \
             patch("dopemux.cli.AttentionMonitor"), \
             patch("dopemux.cli.ContextManager"), \
             patch("dopemux.cli._start_mcp_servers_with_progress"), \
             patch("dopemux.auto_configurator.WorktreeAutoConfigurator.configure_workspace") as mock_auto_config:

            mock_auto_config.return_value = (True, "Configured")

            result = runner.invoke(cli, ["start"])

            assert result.exit_code == 0

            # Verify auto-config was called
            mock_auto_config.assert_called_once()

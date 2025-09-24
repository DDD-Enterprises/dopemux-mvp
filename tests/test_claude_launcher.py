"""
Tests for the Claude launcher module.
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from dopemux.claude.launcher import ClaudeLauncher, ClaudeNotFoundError


class TestClaudeLauncher:
    """Test ClaudeLauncher class."""

    def test_initialization(self, config_manager):
        """Test ClaudeLauncher initialization."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)
            assert launcher.config_manager == config_manager
            assert launcher.claude_path is None

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_detect_claude_in_path(self, mock_run, mock_which, config_manager):
        """Test detecting Claude Code in PATH."""
        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = Mock(returncode=0, stdout="claude version 1.0")

        launcher = ClaudeLauncher(config_manager)

        assert launcher.claude_path == Path("/usr/local/bin/claude")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_detect_claude_not_found(self, mock_run, mock_which, config_manager):
        """Test when Claude Code is not found."""
        mock_which.return_value = None
        mock_run.side_effect = subprocess.SubprocessError()

        launcher = ClaudeLauncher(config_manager)

        assert launcher.claude_path is None

    @patch("shutil.which")
    def test_detect_claude_from_config(self, mock_which, config_manager):
        """Test detecting Claude Code from configuration."""
        mock_which.return_value = None

        # Mock config to return a custom path
        with patch.object(config_manager, "load_config") as mock_load:
            mock_config = Mock()
            mock_config.claude_path = "/custom/path/claude"
            mock_load.return_value = mock_config

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    launcher = ClaudeLauncher(config_manager)
                    assert str(launcher.claude_path) == "/custom/path/claude"

    def test_is_available(self, config_manager):
        """Test checking if Claude Code is available."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

            launcher.claude_path = None
            assert launcher.is_available() is False

            launcher.claude_path = Path("/usr/local/bin/claude")
            assert launcher.is_available() is True

    def test_get_installation_instructions(self, config_manager):
        """Test getting installation instructions."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

            instructions = launcher.get_installation_instructions()

            assert "claude.ai/code" in instructions
            assert "installation" in instructions.lower()

    def test_launch_claude_not_available(self, config_manager, temp_project_dir):
        """Test launching when Claude Code is not available."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)
            launcher.claude_path = None

            with pytest.raises(ClaudeNotFoundError):
                launcher.launch(temp_project_dir)

    @patch("subprocess.Popen")
    @patch("tempfile.mkstemp")
    def test_launch_interactive(
        self, mock_mkstemp, mock_popen, config_manager, temp_project_dir
    ):
        """Test launching Claude Code in interactive mode."""
        # Setup mocks
        mock_mkstemp.return_value = (1, "/tmp/settings.json")
        mock_process = Mock()
        mock_popen.return_value = mock_process

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)
            launcher.claude_path = Path("/usr/local/bin/claude")

        with patch("builtins.open", mock_open()):
            with patch("os.fdopen"):
                process = launcher.launch(temp_project_dir, background=False)

                assert process == mock_process
                mock_popen.assert_called_once()

                # Check command structure
                call_args = mock_popen.call_args[0][0]
                assert "/usr/local/bin/claude" in call_args
                assert "--settings" in call_args
                assert str(temp_project_dir) in call_args

    @patch("subprocess.Popen")
    @patch("tempfile.mkstemp")
    def test_launch_background(
        self, mock_mkstemp, mock_popen, config_manager, temp_project_dir
    ):
        """Test launching Claude Code in background mode."""
        mock_mkstemp.return_value = (1, "/tmp/settings.json")
        mock_process = Mock()
        mock_popen.return_value = mock_process

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)
            launcher.claude_path = Path("/usr/local/bin/claude")

        with patch("builtins.open", mock_open()):
            with patch("os.fdopen"):
                process = launcher.launch(temp_project_dir, background=True)

                # Check background process options
                call_kwargs = mock_popen.call_args[1]
                assert call_kwargs["stdout"] == subprocess.DEVNULL
                assert call_kwargs["stderr"] == subprocess.DEVNULL
                assert call_kwargs["start_new_session"] is True

    @patch("subprocess.Popen")
    @patch("tempfile.mkstemp")
    def test_launch_with_debug(
        self, mock_mkstemp, mock_popen, config_manager, temp_project_dir
    ):
        """Test launching Claude Code with debug flag."""
        mock_mkstemp.return_value = (1, "/tmp/settings.json")
        mock_process = Mock()
        mock_popen.return_value = mock_process

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)
            launcher.claude_path = Path("/usr/local/bin/claude")

        with patch("builtins.open", mock_open()):
            with patch("os.fdopen"):
                launcher.launch(temp_project_dir, debug=True)

                call_args = mock_popen.call_args[0][0]
                assert "--debug" in call_args

    def test_generate_claude_config(self, config_manager, temp_project_dir):
        """Test generating Claude Code configuration."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        config = launcher._generate_claude_config(temp_project_dir)

        assert "env" in config
        assert "mcpServers" in config
        assert config["env"]["DOPEMUX_ENABLED"] == "true"
        assert config["env"]["DOPEMUX_PROJECT"] == str(temp_project_dir)

    def test_generate_claude_config_with_context(
        self, config_manager, temp_project_dir
    ):
        """Test generating Claude config with context information."""
        context = {"current_goal": "Implement feature X", "session_id": "session-123"}

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        config = launcher._generate_claude_config(temp_project_dir, context)

        assert config["env"]["DOPEMUX_CONTEXT_AVAILABLE"] == "true"
        assert config["env"]["DOPEMUX_LAST_GOAL"] == "Implement feature X"
        assert config["env"]["DOPEMUX_SESSION_ID"] == "session-123"

    def test_create_settings_file(self, config_manager):
        """Test creating temporary settings file."""
        test_config = {"test": "config"}

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        with patch("tempfile.mkstemp") as mock_mkstemp:
            mock_mkstemp.return_value = (1, "/tmp/test.json")

            with patch("os.fdopen") as mock_fdopen:
                mock_file = Mock()
                mock_fdopen.return_value.__enter__.return_value = mock_file

                result = launcher._create_settings_file(test_config)

                assert result == Path("/tmp/test.json")
                mock_file.write.assert_called_once()

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "test-openai", "ANTHROPIC_API_KEY": "test-anthropic"},
    )
    def test_prepare_environment(self, config_manager):
        """Test preparing environment variables."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        env = launcher._prepare_environment()

        assert env["DOPEMUX_VERSION"] == "0.1.0"
        assert env["DOPEMUX_ACTIVE"] == "true"
        assert env["OPENAI_API_KEY"] == "test-openai"

    @patch.dict("os.environ", {}, clear=True)
    def test_prepare_environment_missing_keys(self, config_manager):
        """Test preparing environment with missing API keys."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        with patch("rich.console.Console.print") as mock_print:
            launcher._prepare_environment()

            # Should warn about missing keys
            mock_print.assert_called()
            warning_calls = [
                call
                for call in mock_print.call_args_list
                if "Missing API keys" in str(call)
            ]
            assert len(warning_calls) > 0

    def test_resolve_env_vars(self, config_manager):
        """Test resolving environment variables in MCP server config."""
        env_dict = {
            "API_KEY": "${TEST_API_KEY}",
            "FALLBACK": "${MISSING_KEY:default_value}",
            "NORMAL": "no_substitution",
        }

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        with patch.dict("os.environ", {"TEST_API_KEY": "secret_key"}):
            resolved = launcher._resolve_env_vars(env_dict)

            assert resolved["API_KEY"] == "secret_key"
            assert resolved["FALLBACK"] == "default_value"
            assert resolved["NORMAL"] == "no_substitution"

    def test_get_status(self, config_manager):
        """Test getting launcher status."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)
            launcher.claude_path = Path("/usr/local/bin/claude")

        status = launcher.get_status()

        assert status["claude_available"] is True
        assert status["claude_path"] == "/usr/local/bin/claude"
        assert "mcp_servers_configured" in status
        assert status["adhd_optimizations"] is True

    @patch("shutil.which")
    def test_validate_mcp_servers(self, mock_which, config_manager):
        """Test validating MCP server configurations."""
        mock_which.return_value = "/usr/bin/python"

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        with patch.dict("os.environ", {"TEST_KEY": "test_value"}):
            results = launcher.validate_mcp_servers()

            assert isinstance(results, list)
            assert len(results) > 0

            # Check first server result structure
            result = results[0]
            assert "name" in result
            assert "enabled" in result
            assert "command_available" in result
            assert "env_vars_set" in result
            assert "issues" in result

    @patch("shutil.which")
    def test_validate_mcp_servers_missing_command(self, mock_which, config_manager):
        """Test validating MCP servers with missing commands."""
        mock_which.return_value = None  # Command not found

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        results = launcher.validate_mcp_servers()

        # Should detect missing commands
        for result in results:
            if not result["command_available"]:
                assert len(result["issues"]) > 0
                assert any("not found" in issue for issue in result["issues"])

    @patch.dict("os.environ", {}, clear=True)
    def test_validate_mcp_servers_missing_env_vars(self, config_manager):
        """Test validating MCP servers with missing environment variables."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        with patch("shutil.which", return_value="/usr/bin/python"):
            results = launcher.validate_mcp_servers()

            # Should detect missing environment variables
            env_issues = []
            for result in results:
                if not result["env_vars_set"]:
                    env_issues.extend(result["issues"])

            assert len(env_issues) > 0
            assert any("not set" in issue for issue in env_issues)

    @patch("subprocess.run")
    def test_install_mcp_dependencies_success(self, mock_run, config_manager):
        """Test successful MCP dependency installation."""
        mock_run.return_value = Mock(returncode=0)

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        result = launcher.install_mcp_dependencies()
        assert result is True

        # Should have called npm and pip install commands
        assert mock_run.call_count > 0

    @patch("subprocess.run")
    def test_install_mcp_dependencies_failure(self, mock_run, config_manager):
        """Test MCP dependency installation with failures."""
        mock_run.side_effect = Exception("Installation failed")

        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        result = launcher.install_mcp_dependencies()
        assert result is False

    def test_adhd_environment_variables(self, config_manager, temp_project_dir):
        """Test that ADHD profile settings are included in environment."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        config = launcher._generate_claude_config(temp_project_dir)

        # Check ADHD-specific environment variables
        env = config["env"]
        assert "ADHD_FOCUS_DURATION" in env
        assert "ADHD_BREAK_INTERVAL" in env
        assert "ADHD_DISTRACTION_SENSITIVITY" in env
        assert "ADHD_HYPERFOCUS_TENDENCY" in env
        assert "ADHD_NOTIFICATION_STYLE" in env
        assert "ADHD_VISUAL_COMPLEXITY" in env

    def test_mcp_server_configuration_generation(
        self, config_manager, temp_project_dir
    ):
        """Test MCP server configuration generation."""
        with patch.object(ClaudeLauncher, "_detect_claude"):
            launcher = ClaudeLauncher(config_manager)

        config = launcher._generate_claude_config(temp_project_dir)

        # Should include MCP servers from config
        mcp_servers = config["mcpServers"]
        assert isinstance(mcp_servers, dict)

        # Check that enabled servers are included
        for server_name, server_config in mcp_servers.items():
            assert "type" in server_config
            assert "command" in server_config
            assert server_config["type"] == "stdio"

    def test_mcp_server_timeout_configuration(self, config_manager, temp_project_dir):
        """Test that custom timeouts are included in MCP server config."""
        # Mock config with custom timeout
        with patch.object(config_manager, "load_config") as mock_load:
            mock_config = Mock()
            mock_config.adhd_profile = Mock()
            mock_config.adhd_profile.focus_duration_avg = 25
            mock_config.adhd_profile.break_interval = 5
            mock_config.adhd_profile.distraction_sensitivity = 0.5
            mock_config.adhd_profile.hyperfocus_tendency = False
            mock_config.adhd_profile.notification_style = "gentle"
            mock_config.adhd_profile.visual_complexity = "minimal"

            # Create server with custom timeout
            server_config = Mock()
            server_config.enabled = True
            server_config.command = "python"
            server_config.args = ["test.py"]
            server_config.env = {}
            server_config.timeout = 60  # Custom timeout

            mock_config.mcp_servers = {"test-server": server_config}
            mock_load.return_value = mock_config

            with patch.object(ClaudeLauncher, "_detect_claude"):
                launcher = ClaudeLauncher(config_manager)

            config = launcher._generate_claude_config(temp_project_dir)

            # Should include custom timeout
            test_server = config["mcpServers"]["test-server"]
            assert test_server["timeout"] == 60

    def test_disabled_mcp_servers_excluded(self, config_manager, temp_project_dir):
        """Test that disabled MCP servers are excluded from configuration."""
        # Mock config with disabled server
        with patch.object(config_manager, "load_config") as mock_load:
            mock_config = Mock()
            mock_config.adhd_profile = Mock()
            mock_config.adhd_profile.focus_duration_avg = 25
            mock_config.adhd_profile.break_interval = 5
            mock_config.adhd_profile.distraction_sensitivity = 0.5
            mock_config.adhd_profile.hyperfocus_tendency = False
            mock_config.adhd_profile.notification_style = "gentle"
            mock_config.adhd_profile.visual_complexity = "minimal"

            disabled_server = Mock()
            disabled_server.enabled = False
            disabled_server.command = "python"
            disabled_server.args = []
            disabled_server.env = {}

            enabled_server = Mock()
            enabled_server.enabled = True
            enabled_server.command = "node"
            enabled_server.args = []
            enabled_server.env = {}
            enabled_server.timeout = 30

            mock_config.mcp_servers = {
                "disabled-server": disabled_server,
                "enabled-server": enabled_server,
            }
            mock_load.return_value = mock_config

            with patch.object(ClaudeLauncher, "_detect_claude"):
                launcher = ClaudeLauncher(config_manager)

            config = launcher._generate_claude_config(temp_project_dir)

            # Only enabled server should be included
            mcp_servers = config["mcpServers"]
            assert "disabled-server" not in mcp_servers
            assert "enabled-server" in mcp_servers

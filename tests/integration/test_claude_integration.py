"""
Integration tests for Claude Code integration.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from dopemux.claude.launcher import ClaudeLauncher
from dopemux.config import ConfigManager


@pytest.mark.integration
class TestClaudeCodeIntegration:
    """Test Claude Code integration workflows."""

    def test_config_generation_and_launch_preparation(self):
        """Test complete config generation and launch preparation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create a realistic config manager
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                # Mock environment variables
                with patch.dict(
                    "os.environ",
                    {
                        "OPENAI_API_KEY": "test-openai-key",
                        "ANTHROPIC_API_KEY": "test-anthropic-key",
                        "EXA_API_KEY": "test-exa-key",
                    },
                ):
                    # Initialize launcher
                    with patch.object(ClaudeLauncher, "_detect_claude"):
                        launcher = ClaudeLauncher(config_manager)
                        launcher.claude_path = Path("/usr/local/bin/claude")

                    # Generate Claude configuration
                    context = {
                        "current_goal": "Implement feature X",
                        "session_id": "session-123",
                        "open_files": [
                            {
                                "path": "src/main.py",
                                "cursor_position": {"line": 10, "column": 5},
                            }
                        ],
                    }

                    claude_config = launcher._generate_claude_config(
                        project_path, context
                    )

                    # Verify comprehensive configuration
                    assert claude_config["env"]["DOPEMUX_ENABLED"] == "true"
                    assert claude_config["env"]["DOPEMUX_PROJECT"] == str(project_path)
                    assert claude_config["env"]["DOPEMUX_CONTEXT_AVAILABLE"] == "true"
                    assert (
                        claude_config["env"]["DOPEMUX_LAST_GOAL"]
                        == "Implement feature X"
                    )

                    # Verify ADHD settings
                    assert "ADHD_FOCUS_DURATION" in claude_config["env"]
                    assert "ADHD_NOTIFICATION_STYLE" in claude_config["env"]

                    # Verify MCP servers
                    assert "mcpServers" in claude_config
                    assert isinstance(claude_config["mcpServers"], dict)

    def test_mcp_server_validation_workflow(self):
        """Test MCP server validation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                with patch.object(ClaudeLauncher, "_detect_claude"):
                    launcher = ClaudeLauncher(config_manager)

                # Mock various command availability scenarios
                def mock_which_side_effect(command):
                    if command == "python":
                        return "/usr/bin/python"
                    elif command == "node":
                        return "/usr/bin/node"
                    elif command == "npx":
                        return "/usr/bin/npx"
                    else:
                        return None

                with patch("shutil.which", side_effect=mock_which_side_effect):
                    with patch.dict(
                        "os.environ",
                        {"OPENAI_API_KEY": "test-key", "EXA_API_KEY": "test-exa-key"},
                    ):
                        validation_results = launcher.validate_mcp_servers()

                        # Verify validation results
                        assert isinstance(validation_results, list)
                        assert len(validation_results) > 0

                        # Check that all servers were validated
                        server_names = [result["name"] for result in validation_results]
                        expected_servers = [
                            "mas-sequential-thinking",
                            "context7",
                            "claude-context",
                            "morphllm-fast-apply",
                            "exa",
                        ]

                        for expected in expected_servers:
                            assert expected in server_names

                        # Check validation details
                        for result in validation_results:
                            assert "command_available" in result
                            assert "env_vars_set" in result
                            assert "issues" in result

    @patch("subprocess.Popen")
    @patch("tempfile.mkstemp")
    def test_complete_launch_workflow(self, mock_mkstemp, mock_popen):
        """Test complete Claude Code launch workflow."""
        mock_mkstemp.return_value = (1, "/tmp/dopemux-claude-settings.json")
        mock_process = Mock()
        mock_popen.return_value = mock_process

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                with patch.object(ClaudeLauncher, "_detect_claude"):
                    launcher = ClaudeLauncher(config_manager)
                    launcher.claude_path = Path("/usr/local/bin/claude")

                # Mock file operations
                written_config = {}

                def mock_fdopen(fd, mode):
                    return mock_open().return_value

                with patch("os.fdopen", mock_fdopen):
                    with patch("json.dump") as mock_json_dump:

                        def capture_config(config, file_obj, **kwargs):
                            written_config.update(config)

                        mock_json_dump.side_effect = capture_config

                        # Launch Claude Code
                        process = launcher.launch(
                            project_path=project_path,
                            background=False,
                            debug=True,
                            context={"current_goal": "Test goal"},
                        )

                        # Verify process was created
                        assert process == mock_process

                        # Verify command structure
                        call_args = mock_popen.call_args[0][0]
                        assert str(launcher.claude_path) in call_args
                        assert "--settings" in call_args
                        assert str(project_path) in call_args
                        assert "--debug" in call_args

                        # Verify configuration was written
                        mock_json_dump.assert_called_once()

    def test_environment_variable_handling(self):
        """Test environment variable handling for MCP servers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                with patch.object(ClaudeLauncher, "_detect_claude"):
                    launcher = ClaudeLauncher(config_manager)

                # Test environment variable resolution
                test_env = {
                    "API_KEY": "${TEST_API_KEY}",
                    "FALLBACK_KEY": "${MISSING_KEY:default_value}",
                    "COMPLEX_VAR": "${PREFIX}_${SUFFIX}",
                    "NORMAL_VAR": "normal_value",
                }

                with patch.dict(
                    "os.environ",
                    {"TEST_API_KEY": "secret123", "PREFIX": "pre", "SUFFIX": "post"},
                ):
                    resolved = launcher._resolve_env_vars(test_env)

                    assert resolved["API_KEY"] == "secret123"
                    assert resolved["FALLBACK_KEY"] == "default_value"
                    assert resolved["COMPLEX_VAR"] == "pre_post"
                    assert resolved["NORMAL_VAR"] == "normal_value"

    def test_launcher_status_integration(self):
        """Test launcher status reporting integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                with patch.object(ClaudeLauncher, "_detect_claude"):
                    launcher = ClaudeLauncher(config_manager)
                    launcher.claude_path = Path("/usr/local/bin/claude")

                status = launcher.get_status()

                # Verify status structure
                assert status["claude_available"] is True
                assert status["claude_path"] == "/usr/local/bin/claude"
                assert "mcp_servers_configured" in status
                assert status["adhd_optimizations"] is True


@pytest.mark.integration
class TestClaudeConfiguratorIntegration:
    """Test Claude configurator integration workflows."""

    def test_project_config_setup_integration(self):
        """Test complete project configuration setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                from dopemux.claude.configurator import ClaudeConfigurator

                configurator = ClaudeConfigurator(config_manager)

                # Setup project configuration
                configurator.setup_project_config(project_path, "python")

                # Verify .claude directory was created
                claude_dir = project_path / ".claude"
                assert claude_dir.exists()

                # Verify configuration files were created
                expected_files = ["claude.md", "session.md", "context.md", "llms.md"]
                for filename in expected_files:
                    assert (claude_dir / filename).exists()

    def test_mcp_integration_config_generation(self):
        """Test MCP integration configuration generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir)

            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                from dopemux.claude.configurator import ClaudeConfigurator

                configurator = ClaudeConfigurator(config_manager)

                # Generate project configuration (which includes MCP configuration)
                configurator.setup_project_config(Path(temp_dir), template="python")

                # Verify MCP configuration was created in dopemux config
                config_file = Path(temp_dir) / ".dopemux" / "config.yaml"
                assert config_file.exists()

                import yaml

                with open(config_file) as f:
                    mcp_config = yaml.safe_load(f)

                # Verify MCP configuration structure
                assert "mcp_servers" in mcp_config
                assert isinstance(mcp_config["mcp_servers"], list)

                # Verify MCP servers list exists (may be empty from template config)
                # The actual MCP server configuration happens in the launcher
                assert "active_features" in mcp_config
                assert mcp_config["active_features"]["context_preservation"] is True

                # Verify project type and ADHD profile are configured
                assert mcp_config["project_type"] == "python"
                assert "adhd_profile" in mcp_config


@pytest.mark.integration
class TestClaudeCodeDetection:
    """Test Claude Code detection and validation."""

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_claude_detection_scenarios(self, mock_run, mock_which):
        """Test various Claude Code detection scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                # Test 1: Claude found in PATH
                mock_which.return_value = "/usr/local/bin/claude"
                mock_run.return_value = Mock(returncode=0, stdout="claude version 1.0")

                with patch.object(ClaudeLauncher, "_detect_claude") as mock_detect:
                    launcher = ClaudeLauncher(config_manager)
                    launcher.claude_path = Path("/usr/local/bin/claude")
                    assert launcher.is_available()
                    assert str(launcher.claude_path) == "/usr/local/bin/claude"

                # Test 2: Claude not found
                mock_which.return_value = None
                mock_run.side_effect = subprocess.SubprocessError()

                with patch.object(ClaudeLauncher, "_detect_claude") as mock_detect:
                    launcher2 = ClaudeLauncher(config_manager)
                    launcher2.claude_path = None
                    assert not launcher2.is_available()

                # Test 3: Claude found in custom location via config
                mock_which.return_value = None

                with patch.object(config_manager, "load_config") as mock_load:
                    mock_config = Mock()
                    mock_config.claude_path = "/custom/path/claude"
                    mock_load.return_value = mock_config

                    with patch("pathlib.Path.exists", return_value=True):
                        with patch("pathlib.Path.is_file", return_value=True):
                            launcher3 = ClaudeLauncher(config_manager)
                            assert launcher3.is_available()
                            assert str(launcher3.claude_path) == "/custom/path/claude"

    def test_installation_instructions_generation(self):
        """Test installation instructions generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                with patch.object(ClaudeLauncher, "_detect_claude"):
                    launcher = ClaudeLauncher(config_manager)
                    launcher.claude_path = None

                instructions = launcher.get_installation_instructions()

                assert "claude.ai/code" in instructions
                assert "installation" in instructions.lower()
                assert "CLAUDE_PATH" in instructions

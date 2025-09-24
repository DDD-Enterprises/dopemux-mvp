"""
Tests for the configuration manager module.
"""

from unittest.mock import patch

import pytest
import yaml

from dopemux.config.manager import (
    ADHDProfile,
    ConfigManager,
    DopemuxConfig,
    MCPServerConfig,
)


class TestADHDProfile:
    """Test ADHD profile configuration."""

    def test_default_values(self):
        """Test default ADHD profile values."""
        profile = ADHDProfile()
        assert profile.focus_duration_avg == 25
        assert profile.break_interval == 5
        assert profile.distraction_sensitivity == 0.5
        assert profile.hyperfocus_tendency is False
        assert profile.notification_style == "gentle"
        assert profile.visual_complexity == "minimal"

    def test_validation(self):
        """Test ADHD profile validation."""
        # Valid sensitivity
        profile = ADHDProfile(distraction_sensitivity=0.8)
        assert profile.distraction_sensitivity == 0.8

        # Invalid sensitivity
        with pytest.raises(ValueError):
            ADHDProfile(distraction_sensitivity=1.5)

        with pytest.raises(ValueError):
            ADHDProfile(distraction_sensitivity=-0.1)


class TestMCPServerConfig:
    """Test MCP server configuration."""

    def test_default_values(self):
        """Test default MCP server config values."""
        config = MCPServerConfig(command="python")
        assert config.enabled is True
        assert config.command == "python"
        assert config.args == []
        assert config.env == {}
        assert config.timeout == 30
        assert config.auto_restart is True

    def test_custom_values(self):
        """Test custom MCP server config values."""
        config = MCPServerConfig(
            command="node",
            args=["server.js"],
            env={"NODE_ENV": "production"},
            timeout=60,
            enabled=False,
        )
        assert config.command == "node"
        assert config.args == ["server.js"]
        assert config.env == {"NODE_ENV": "production"}
        assert config.timeout == 60
        assert config.enabled is False


class TestConfigManager:
    """Test configuration manager."""

    def test_init(self, temp_config_dir):
        """Test ConfigManager initialization."""
        config_file = str(temp_config_dir / "config.yaml")

        with patch("dopemux.config.manager.ConfigManager._init_paths") as mock_init:
            from dopemux.config.manager import ConfigPaths

            mock_init.return_value = ConfigPaths(
                global_config=temp_config_dir / "global.yaml",
                user_config=temp_config_dir / "config.yaml",
                project_config=temp_config_dir / "project.yaml",
                cache_dir=temp_config_dir / "cache",
                data_dir=temp_config_dir / "data",
            )

            manager = ConfigManager(config_file)
            assert manager.paths.user_config == temp_config_dir / "config.yaml"

    def test_load_default_config(self, config_manager):
        """Test loading default configuration."""
        config = config_manager.load_config()
        assert isinstance(config, DopemuxConfig)
        assert config.version == "1.0"
        assert isinstance(config.adhd_profile, ADHDProfile)

    def test_load_user_config(self, temp_config_dir, sample_config_data):
        """Test loading user configuration."""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_data, f)

        with patch("dopemux.config.manager.ConfigManager._init_paths") as mock_init:
            from dopemux.config.manager import ConfigPaths

            mock_init.return_value = ConfigPaths(
                global_config=temp_config_dir / "global.yaml",
                user_config=config_file,
                project_config=temp_config_dir / "project.yaml",
                cache_dir=temp_config_dir / "cache",
                data_dir=temp_config_dir / "data",
            )

            manager = ConfigManager()
            with patch.object(manager, "_get_default_config", return_value={}):
                config = manager.load_config()
                assert config.version == "1.0"

    def test_save_user_config(self, config_manager, temp_config_dir):
        """Test saving user configuration."""
        config = config_manager.load_config()
        config.adhd_profile.focus_duration_avg = 30

        # Mock the user config path
        config_manager.paths.user_config = temp_config_dir / "config.yaml"

        config_manager.save_user_config(config)
        assert config_manager.paths.user_config.exists()

        # Verify content
        with open(config_manager.paths.user_config) as f:
            saved_data = yaml.safe_load(f)
            assert "adhd_profile" in saved_data

    def test_mcp_server_management(self, config_manager):
        """Test MCP server configuration management."""
        # Add server
        server_config = MCPServerConfig(
            command="python", args=["test.py"], enabled=True
        )

        config_manager.add_mcp_server("test-server", server_config)
        servers = config_manager.get_mcp_servers()
        assert "test-server" in servers

        # Remove server
        result = config_manager.remove_mcp_server("test-server")
        assert result is True

        result = config_manager.remove_mcp_server("nonexistent")
        assert result is False

    def test_adhd_profile_update(self, config_manager):
        """Test ADHD profile updates."""
        config_manager.update_adhd_profile(
            focus_duration_avg=30, notification_style="bold"
        )

        config = config_manager.load_config()
        assert config.adhd_profile.focus_duration_avg == 30
        assert config.adhd_profile.notification_style == "bold"

    def test_claude_settings_generation(self, config_manager):
        """Test Claude Code settings generation."""
        settings = config_manager.get_claude_settings()

        assert "mcpServers" in settings
        assert "env" in settings
        assert settings["env"]["MCP_TOOL_TIMEOUT"] == "40000"

    def test_environment_variable_substitution(self, config_manager):
        """Test environment variable substitution."""
        test_data = {
            "api_key": "${TEST_API_KEY}",
            "fallback": "${MISSING_KEY:default_value}",
            "nested": {"value": "${NESTED_VAR}"},
            "normal": "no_substitution",
        }

        with patch.dict(
            "os.environ", {"TEST_API_KEY": "secret", "NESTED_VAR": "nested_value"}
        ):
            result = config_manager._substitute_env_vars(test_data)

            assert result["api_key"] == "secret"
            assert result["fallback"] == "default_value"
            assert result["nested"]["value"] == "nested_value"
            assert result["normal"] == "no_substitution"

    def test_deep_merge(self, config_manager):
        """Test deep dictionary merging."""
        base = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

        override = {"b": {"c": 20, "f": 6}, "g": 7}

        result = config_manager._deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"]["c"] == 20  # overridden
        assert result["b"]["d"] == 3  # preserved
        assert result["b"]["f"] == 6  # added
        assert result["e"] == 4
        assert result["g"] == 7

    def test_ensure_directories(self, config_manager, temp_config_dir):
        """Test directory creation."""
        config_manager.paths.cache_dir = temp_config_dir / "cache"
        config_manager.paths.data_dir = temp_config_dir / "data"
        config_manager.paths.user_config = temp_config_dir / "user" / "config.yaml"

        config_manager.ensure_directories()

        assert config_manager.paths.cache_dir.exists()
        assert config_manager.paths.data_dir.exists()
        assert config_manager.paths.user_config.parent.exists()

    def test_get_data_path(self, config_manager, temp_config_dir):
        """Test data path utilities."""
        config_manager.paths.data_dir = temp_config_dir

        path = config_manager.get_data_path("subdir", "file.txt")
        expected = temp_config_dir / "subdir" / "file.txt"
        assert path == expected

    def test_get_cache_path(self, config_manager, temp_config_dir):
        """Test cache path utilities."""
        config_manager.paths.cache_dir = temp_config_dir

        path = config_manager.get_cache_path("cache_file.dat")
        expected = temp_config_dir / "cache_file.dat"
        assert path == expected

    def test_load_invalid_config_file(self, config_manager, temp_config_dir):
        """Test handling of invalid config files."""
        # Create invalid YAML file
        invalid_file = temp_config_dir / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: [")

        result = config_manager._load_file(invalid_file)
        assert result == {}  # Should return empty dict on error

    def test_config_caching(self, config_manager):
        """Test configuration caching."""
        # First load
        config1 = config_manager.load_config()

        # Second load should return cached version
        config2 = config_manager.load_config()

        assert config1 is config2  # Same object reference

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "EXA_API_KEY": "exa-key"})
    def test_default_mcp_servers(self, config_manager):
        """Test default MCP server configurations."""
        defaults = config_manager._get_default_mcp_servers()

        assert "mas-sequential-thinking" in defaults
        assert "context7" in defaults
        assert "claude-context" in defaults

        # Check environment variable substitution works
        claude_context = defaults["claude-context"]
        assert "${OPENROUTER_API_KEY}" in str(claude_context["env"])

    def test_project_templates(self, config_manager):
        """Test project template configurations."""
        templates = config_manager._get_project_templates()

        assert "python" in templates
        assert "javascript" in templates
        assert "rust" in templates

        python_template = templates["python"]
        assert "files" in python_template
        assert "mcp_servers" in python_template
        assert "adhd_adaptations" in python_template

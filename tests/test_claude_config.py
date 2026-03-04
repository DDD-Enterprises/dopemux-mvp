"""
Tests for Claude configuration management.

Tests config reading, writing, backup, rollback, and profile application.
"""

import json
import tempfile
from pathlib import Path

import pytest

from dopemux.claude_config import (
    ClaudeConfig,
    ClaudeConfigError,
    MCP_NAME_MAPPING,
)
from dopemux.profile_models import Profile


# Sample Claude config for testing
SAMPLE_CLAUDE_CONFIG = {
    "env": {
        "MCP_TOOL_TIMEOUT": "120000",
        "MAX_MCP_OUTPUT_TOKENS": "50000"
    },
    "statusLine": {
        "type": "command",
        "command": "~/.claude/statusline-command.sh"
    },
    "alwaysThinkingEnabled": False,
    "mcpServers": {
        "dopemux-conport": {
            "type": "stdio",
            "command": "uvx",
            "args": ["--from", "context-portal-mcp", "conport-mcp"]
        },
        "dopemux-serena": {
            "type": "stdio",
            "command": "python3",
            "args": ["/path/to/serena/server.py"]
        },
        "dopemux-zen": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "python", "server.py"],
            "cwd": "/path/to/zen"
        },
        "dopemux-pal": {
            "type": "stdio",
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/BeehiveInnovations/pal-mcp-server.git",
                "pal-mcp-server"
            ]
        },
        "dopemux-gpt-researcher": {
            "type": "stdio",
            "command": "python3",
            "args": ["/path/to/gpt-researcher/server.py"]
        }
    }
}


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def claude_config_file(temp_config_dir):
    """Create a temporary Claude config file."""
    config_path = temp_config_dir / "settings.json"
    with open(config_path, "w") as f:
        json.dump(SAMPLE_CLAUDE_CONFIG, f, indent=2)
    return config_path


@pytest.fixture
def claude_config(claude_config_file):
    """Create ClaudeConfig instance with temporary config."""
    return ClaudeConfig(config_path=claude_config_file)


class TestClaudeConfig:
    """Test ClaudeConfig class."""

    def test_init_default_path(self):
        """Test initialization with default path."""
        config = ClaudeConfig()
        assert config.config_path == Path.home() / ".claude" / "settings.json"
        assert config.backup_dir == Path.home() / ".claude" / "backups"

    def test_init_custom_path(self, claude_config_file):
        """Test initialization with custom path."""
        config = ClaudeConfig(config_path=claude_config_file)
        assert config.config_path == claude_config_file
        assert config.backup_dir == claude_config_file.parent / "backups"

    def test_read_config(self, claude_config):
        """Test reading configuration file."""
        config = claude_config.read_config()

        assert "mcpServers" in config
        assert "env" in config
        assert config["alwaysThinkingEnabled"] is False
        assert "dopemux-conport" in config["mcpServers"]

    def test_read_config_not_found(self, temp_config_dir):
        """Test reading non-existent config file."""
        config_path = temp_config_dir / "nonexistent.json"
        config = ClaudeConfig(config_path=config_path)

        with pytest.raises(ClaudeConfigError) as exc_info:
            config.read_config()
        assert "not found" in str(exc_info.value).lower()

    def test_read_config_invalid_json(self, temp_config_dir):
        """Test reading invalid JSON config."""
        config_path = temp_config_dir / "invalid.json"
        config_path.write_text("{ invalid json }")

        config = ClaudeConfig(config_path=config_path)
        with pytest.raises(ClaudeConfigError) as exc_info:
            config.read_config()
        assert "invalid json" in str(exc_info.value).lower()

    def test_backup_config(self, claude_config):
        """Test creating config backup."""
        backup_path = claude_config.backup_config()

        assert backup_path.exists()
        assert backup_path.parent == claude_config.backup_dir
        assert backup_path.name.startswith("settings_")
        assert backup_path.suffix == ".json"

        # Verify backup contents match original
        with open(backup_path) as f:
            backup_config = json.load(f)
        original_config = claude_config.read_config()
        assert backup_config == original_config

    def test_backup_config_not_found(self, temp_config_dir):
        """Test backing up non-existent config."""
        config_path = temp_config_dir / "nonexistent.json"
        config = ClaudeConfig(config_path=config_path)

        with pytest.raises(ClaudeConfigError) as exc_info:
            config.backup_config()
        assert "cannot backup" in str(exc_info.value).lower()

    def test_write_config(self, claude_config):
        """Test writing configuration file."""
        new_config = SAMPLE_CLAUDE_CONFIG.copy()
        new_config["testField"] = "test_value"

        claude_config.write_config(new_config, create_backup=False)

        # Verify written config
        written_config = claude_config.read_config()
        assert written_config["testField"] == "test_value"

    def test_write_config_with_backup(self, claude_config):
        """Test writing config with automatic backup."""
        new_config = SAMPLE_CLAUDE_CONFIG.copy()
        new_config["modified"] = True

        backup_path = claude_config.write_config(new_config, create_backup=True)

        assert backup_path is not None
        assert backup_path.exists()

        # Verify backup contains original config
        with open(backup_path) as f:
            backup_config = json.load(f)
        assert "modified" not in backup_config

    def test_get_mcp_servers(self, claude_config):
        """Test getting MCP servers from config."""
        servers = claude_config.get_mcp_servers()

        assert isinstance(servers, dict)
        assert "dopemux-conport" in servers
        assert "dopemux-serena" in servers
        assert "dopemux-zen" in servers

    def test_filter_mcp_servers_for_profile(self, claude_config):
        """Test filtering MCP servers for a profile."""
        profile = Profile(
            name="developer",
            display_name="Developer",
            description="Test",
            mcps=["conport", "serena-v2", "zen"]  # serena-v2 maps to serena
        )

        filtered = claude_config.filter_mcp_servers_for_profile(profile)

        assert len(filtered) == 3
        assert "dopemux-conport" in filtered
        assert "dopemux-serena" in filtered
        assert "dopemux-zen" in filtered

    def test_filter_mcp_servers_missing(self, claude_config):
        """Test filtering with missing MCP servers."""
        profile = Profile(
            name="test",
            display_name="Test",
            description="Test",
            mcps=["conport", "unknown-mcp"]
        )

        with pytest.raises(ClaudeConfigError) as exc_info:
            claude_config.filter_mcp_servers_for_profile(profile)
        assert "not configured" in str(exc_info.value).lower()
        assert "unknown-mcp" in str(exc_info.value)

    def test_apply_profile(self, claude_config):
        """Test applying a profile to config."""
        profile = Profile(
            name="minimal",
            display_name="Minimal",
            description="Minimal profile",
            mcps=["conport", "zen"]
        )

        new_config = claude_config.apply_profile(profile, create_backup=False)

        # Should only have 2 MCP servers
        assert len(new_config["mcpServers"]) == 2
        assert "dopemux-conport" in new_config["mcpServers"]
        assert "dopemux-zen" in new_config["mcpServers"]

        # Should preserve other settings
        assert new_config["env"] == SAMPLE_CLAUDE_CONFIG["env"]
        assert new_config["statusLine"] == SAMPLE_CLAUDE_CONFIG["statusLine"]

        # Should add profile metadata
        assert new_config["_dopemux_active_profile"] == "minimal"

    def test_apply_profile_dry_run(self, claude_config):
        """Test dry run mode doesn't write config."""
        original_config = claude_config.read_config()

        profile = Profile(
            name="test",
            display_name="Test",
            description="Test",
            mcps=["conport"]
        )

        new_config = claude_config.apply_profile(profile, dry_run=True)

        # Should return new config
        assert len(new_config["mcpServers"]) == 1

        # Should NOT modify file
        current_config = claude_config.read_config()
        assert current_config == original_config

    def test_apply_profile_returns_backup_path_when_requested(self, claude_config):
        """Test optional backup-path return for rollback-safe workflows."""
        profile = Profile(
            name="minimal",
            display_name="Minimal",
            description="Minimal profile",
            mcps=["conport", "zen"],
        )

        new_config, backup_path = claude_config.apply_profile(
            profile,
            create_backup=True,
            return_backup_path=True,
        )

        assert new_config["_dopemux_active_profile"] == "minimal"
        assert backup_path is not None
        assert backup_path.exists()

    def test_rollback_to_backup(self, claude_config):
        """Test rolling back to a backup."""
        # Create a backup
        backup_path = claude_config.backup_config()

        # Modify config
        new_config = SAMPLE_CLAUDE_CONFIG.copy()
        new_config["modified"] = True
        claude_config.write_config(new_config, create_backup=False)

        # Verify modification
        assert claude_config.read_config()["modified"] is True

        # Rollback
        claude_config.rollback_to_backup(backup_path)

        # Verify rollback
        restored_config = claude_config.read_config()
        assert "modified" not in restored_config

    def test_rollback_to_nonexistent_backup(self, claude_config):
        """Test rollback with non-existent backup fails."""
        fake_backup = claude_config.backup_dir / "fake_backup.json"

        with pytest.raises(ClaudeConfigError) as exc_info:
            claude_config.rollback_to_backup(fake_backup)
        assert "not found" in str(exc_info.value).lower()

    def test_list_backups(self, claude_config):
        """Test listing backup files."""
        import time

        # Initially no backups
        backups = claude_config.list_backups()
        initial_count = len(backups)

        # Create some backups with small delay to ensure unique timestamps
        claude_config.backup_config()
        time.sleep(1.1)  # Sleep just over 1 second to ensure different timestamp
        claude_config.backup_config()

        # Should list backups (newest first)
        backups = claude_config.list_backups()
        assert len(backups) == initial_count + 2

    def test_list_backups_limit(self, claude_config):
        """Test listing backups with limit."""
        # Create several backups
        for _ in range(5):
            claude_config.backup_config()

        # Request only 2
        backups = claude_config.list_backups(limit=2)
        assert len(backups) <= 2

    def test_get_available_mcp_servers(self, claude_config):
        """Test getting list of available MCP servers."""
        servers = claude_config.get_available_mcp_servers()

        assert isinstance(servers, list)
        assert "dopemux-conport" in servers
        assert "dopemux-serena" in servers
        assert "dopemux-zen" in servers

    def test_validate_profile_against_config(self, claude_config):
        """Test validating profile against config."""
        profile = Profile(
            name="test",
            display_name="Test",
            description="Test",
            mcps=["conport", "serena-v2", "unknown-mcp"]
        )

        result = claude_config.validate_profile_against_config(profile)

        assert "conport" in result["available"]
        assert "serena-v2" in result["available"]  # Maps to serena
        assert "unknown-mcp" in result["missing"]


class TestMCPNameMapping:
    """Test MCP name mapping dictionary."""

    def test_mapping_contains_common_servers(self):
        """Test mapping includes common MCP servers."""
        assert "conport" in MCP_NAME_MAPPING
        assert "serena-v2" in MCP_NAME_MAPPING
        assert "zen" in MCP_NAME_MAPPING
        assert "pal" in MCP_NAME_MAPPING

    def test_mapping_bidirectional(self):
        """Test mapping works correctly."""
        # serena-v2 maps to serena
        assert MCP_NAME_MAPPING["serena-v2"] == "dopemux-serena"

        # Direct mappings map to themselves
        assert MCP_NAME_MAPPING["conport"] == "dopemux-conport"
        assert MCP_NAME_MAPPING["zen"] == "dopemux-zen"

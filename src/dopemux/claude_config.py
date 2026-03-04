"""
Claude configuration management for Dopemux profiles.

Handles reading, writing, and backing up Claude's settings.json file with
profile-based MCP server filtering.

Config Location: ~/.claude/settings.json
"""

from __future__ import annotations
import logging


import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .profile_models import Profile


logger = logging.getLogger(__name__)

# Mapping from profile-friendly names to actual Claude config names
MCP_NAME_MAPPING = {
    # Profile name -> Claude config name (with dopemux- prefix)
    "serena-v2": "dopemux-serena",
    "serena": "dopemux-serena",
    "tavily": "dopemux-exa",  # Exa is what's actually in the config
    "exa": "dopemux-exa",
    "dope-context": "dopemux-claude-context",  # Canonicalize legacy key to claude-context
    "dope-context-legacy": "dopemux-dope-context",
    "mas-sequential-thinking": "dopemux-mas-sequential-thinking",
    # Direct mappings (prefixed)
    "conport": "dopemux-conport",
    "zen": "dopemux-zen",
    "pal": "dopemux-pal",
    "gpt-researcher": "dopemux-gpt-researcher",
    "gpt-researcher-legacy": "gpt-researcher",  # Old name fallback
    "claude-context": "dopemux-claude-context",
    "desktop-commander": "dopemux-desktop-commander",
    "magic-mcp": "magic-mcp",
    "playwright": "playwright",
    "sequential_thinking": "dopemux-mas-sequential-thinking",
    # Legacy unprefixed names (for backwards compatibility)
    "leantime-bridge": "dopemux-leantime-bridge",
}


class ClaudeConfigError(Exception):
    """Raised when Claude configuration operations fail."""
    pass


class ClaudeConfig:
    """Manager for Claude settings.json configuration.

    Provides safe reading, writing, and backup of Claude's configuration
    with profile-based MCP server filtering.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize Claude config manager.

        Args:
            config_path: Path to Claude settings.json (default: ~/.claude/settings.json)
        """
        if config_path is None:
            config_path = Path.home() / ".claude" / "settings.json"

        self.config_path = Path(config_path)
        self.backup_dir = self.config_path.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def read_config(self) -> Dict[str, Any]:
        """Read the current Claude configuration.

        Returns:
            Dictionary containing Claude configuration

        Raises:
            ClaudeConfigError: If config file doesn't exist or is invalid JSON
        """
        if not self.config_path.exists():
            raise ClaudeConfigError(
                f"Claude config not found at {self.config_path}. "
                f"Please ensure Claude is installed."
            )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ClaudeConfigError(
                f"Invalid JSON in Claude config: {e}"
            )
        except Exception as e:
            raise ClaudeConfigError(
                f"Failed to read Claude config: {e}"
            )

            logger.error(f"Error: {e}")
    def backup_config(self) -> Path:
        """Create a timestamped backup of the current configuration.

        Returns:
            Path to the backup file

        Raises:
            ClaudeConfigError: If backup fails
        """
        if not self.config_path.exists():
            raise ClaudeConfigError(
                f"Cannot backup: config file not found at {self.config_path}"
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"settings_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(self.config_path, backup_path)
            return backup_path
        except Exception as e:
            raise ClaudeConfigError(
                f"Failed to create backup: {e}"
            )

            logger.error(f"Error: {e}")
    def write_config(self, config: Dict[str, Any], create_backup: bool = True) -> Optional[Path]:
        """Write configuration to Claude settings.json.

        Args:
            config: Configuration dictionary to write
            create_backup: Whether to create a backup first (default: True)

        Returns:
            Path to backup file if created, None otherwise

        Raises:
            ClaudeConfigError: If write fails
        """
        backup_path = None

        # Create backup if requested and file exists
        if create_backup and self.config_path.exists():
            backup_path = self.backup_config()

        # Sanitize config before writing
        config = self._sanitize_config(config)

        # Validate config structure before writing
        self._validate_config_structure(config)

        try:
            # Write to temporary file first (atomic write)
            temp_path = self.config_path.with_suffix(".json.tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Add trailing newline

            # Atomic replace
            temp_path.replace(self.config_path)

            return backup_path

        except Exception as e:
            # If we created a backup, restore it
            if backup_path and backup_path.exists():
                try:
                    shutil.copy2(backup_path, self.config_path)
                except Exception as backup_exc:
                    logger.error(f"Error: {backup_exc}")
            raise ClaudeConfigError(
                f"Failed to write config: {e}"
            )

    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure before writing.

        Ensures that the configuration matches expected schema and constraints.
        JSON does not allow comments, and json.dump handles that, but this
        checks for logical validity.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ClaudeConfigError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ClaudeConfigError("Configuration must be a dictionary")

        # Validate mcpServers if present
        if "mcpServers" in config:
            if not isinstance(config["mcpServers"], dict):
                raise ClaudeConfigError("'mcpServers' must be a dictionary")
            
            for name, server_config in config["mcpServers"].items():
                if not isinstance(server_config, dict):
                    raise ClaudeConfigError(f"Configuration for MCP server '{name}' must be a dictionary")
                # Basic keys expected for stdio/network
                if "command" not in server_config and "url" not in server_config:
                   # This might be too strict if there are other types, but good for now for safety
                   pass # Relaxing this check as external configs might vary

        # Helper to check for mistakenly stringified JSON or comments
        # (Though checks on dictionary values are limited)


    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize Claude configuration based on environment and schema requirements."""
        # Work on a copy to avoid mutating the input
        config = config.copy()

        # 1. Handle DOPEMUX_DISABLE_CLAUDE_HOOKS
        if os.environ.get("DOPEMUX_DISABLE_CLAUDE_HOOKS") == "1":
            if "hooks" in config:
                logger.info("DOPEMUX_DISABLE_CLAUDE_HOOKS is set. Removing hooks section.")
                del config["hooks"]
            return config

        # 2. Fix UserPromptSubmit schema if present
        if "hooks" in config and isinstance(config["hooks"], dict):
            if "UserPromptSubmit" in config["hooks"]:
                ups = config["hooks"]["UserPromptSubmit"]
                if isinstance(ups, list):
                    for entry in ups:
                        if isinstance(entry, dict) and "hooks" in entry and "matcher" not in entry:
                            logger.info("Fixing missing matcher in UserPromptSubmit hook entry.")
                            entry["matcher"] = ".*"

        return config

    def get_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get the mcpServers section from config.

        Returns:
            Dictionary of MCP server configurations
        """
        config = self.read_config()
        return config.get("mcpServers", {})

    def filter_mcp_servers_for_profile(
        self,
        profile: Profile
    ) -> Dict[str, Dict[str, Any]]:
        """Filter MCP servers based on profile.

        Args:
            profile: Profile with list of MCP servers to include

        Returns:
            Dictionary of filtered MCP server configurations

        Raises:
            ClaudeConfigError: If required MCP servers are missing from config
        """
        all_servers = self.get_mcp_servers()
        filtered_servers = {}
        missing_servers = []

        for profile_mcp_name in profile.mcps:
            # Map profile name to Claude config name
            config_name = MCP_NAME_MAPPING.get(profile_mcp_name, profile_mcp_name)

            if config_name is None:
                # MCP not yet configured
                missing_servers.append(profile_mcp_name)
                continue

            if config_name not in all_servers:
                missing_servers.append(f"{profile_mcp_name} (maps to '{config_name}')")
                continue

            filtered_servers[config_name] = all_servers[config_name]

        if missing_servers:
            raise ClaudeConfigError(
                f"Profile '{profile.name}' requires MCP servers that are not configured:\n" +
                "\n".join(f"  • {name}" for name in missing_servers) +
                f"\n\nPlease configure these servers in {self.config_path}"
            )

        return filtered_servers

    def apply_profile(
        self,
        profile: Profile,
        create_backup: bool = True,
        dry_run: bool = False,
        return_backup_path: bool = False,
    ) -> Union[Dict[str, Any], Tuple[Dict[str, Any], Optional[Path]]]:
        """Apply a profile to Claude configuration.

        Filters MCP servers to only those specified in the profile while
        preserving all other configuration settings.

        Args:
            profile: Profile to apply
            create_backup: Whether to backup before writing (default: True)
            dry_run: If True, return what would be written without writing (default: False)
            return_backup_path: If True, return tuple (new_config, backup_path)

        Returns:
            The new configuration that was (or would be) written.
            When return_backup_path=True, returns (new_config, backup_path).

        Raises:
            ClaudeConfigError: If profile cannot be applied
        """
        # Read current config
        current_config = self.read_config()

        # Filter MCP servers for profile
        filtered_servers = self.filter_mcp_servers_for_profile(profile)

        # Create new config with filtered servers
        new_config = current_config.copy()
        new_config["mcpServers"] = filtered_servers

        # Add profile metadata comment (for reference)
        # Note: JSON doesn't support comments, but we can add a field
        new_config["_dopemux_active_profile"] = profile.name

        backup_path: Optional[Path] = None
        if not dry_run:
            backup_path = self.write_config(new_config, create_backup=create_backup)

        if return_backup_path:
            return new_config, backup_path
        return new_config

    def rollback_to_backup(self, backup_path: Path) -> None:
        """Restore configuration from a backup file.

        Args:
            backup_path: Path to backup file to restore

        Raises:
            ClaudeConfigError: If rollback fails
        """
        if not backup_path.exists():
            raise ClaudeConfigError(
                f"Backup file not found: {backup_path}"
            )

        try:
            shutil.copy2(backup_path, self.config_path)
        except Exception as e:
            raise ClaudeConfigError(
                f"Failed to rollback from backup: {e}"
            )

            logger.error(f"Error: {e}")
    def list_backups(self, limit: int = 10) -> List[Path]:
        """List available backup files.

        Args:
            limit: Maximum number of backups to return (default: 10)

        Returns:
            List of backup file paths, sorted by modification time (newest first)
        """
        if not self.backup_dir.exists():
            return []

        backups = sorted(
            self.backup_dir.glob("settings_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        return backups[:limit]

    def get_available_mcp_servers(self) -> List[str]:
        """Get list of all configured MCP server names.

        Returns:
            List of MCP server names from current config
        """
        return list(self.get_mcp_servers().keys())

    def validate_profile_against_config(self, profile: Profile) -> Dict[str, List[str]]:
        """Validate that a profile's MCP servers are available.

        Args:
            profile: Profile to validate

        Returns:
            Dictionary with 'available' and 'missing' lists of MCP names
        """
        all_servers = self.get_mcp_servers()
        result = {
            "available": [],
            "missing": []
        }

        for profile_mcp_name in profile.mcps:
            config_name = MCP_NAME_MAPPING.get(profile_mcp_name, profile_mcp_name)

            if config_name is None or config_name not in all_servers:
                result["missing"].append(profile_mcp_name)
            else:
                result["available"].append(profile_mcp_name)

        return result

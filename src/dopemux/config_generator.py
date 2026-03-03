"""
Dopemux Profile Manager - Config Generator

Transforms profile YAML to DopeBrainz config.json format.
Filters MCP servers based on profile selection.
"""

import json

import logging

logger = logging.getLogger(__name__)

from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import shutil
from datetime import datetime
from tempfile import NamedTemporaryFile

from .profile_models import Profile


class ConfigGenerator:
    """Generate DopeBrainz config.json from profile definitions"""

    def __init__(self, dope_brainz_config_path: Optional[Path] = None):
        """
        Initialize generator with Claude config path.

        Args:
            dope_brainz_config_path: Path to DopeBrainz settings.json
                Defaults to ~/.dope-brainz/settings.json
        """
        if dope_brainz_config_path is None:
            dope_brainz_config_path = Path.home() / ".dope-brainz" / "settings.json"

        self.config_path = Path(dope_brainz_config_path)
        self._full_config = None

    def load_full_config(self) -> Dict[str, Any]:
        """
        Load the full Claude configuration (all MCP servers).

        Returns:
            Full config dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config is invalid JSON
        """
        if self._full_config is not None:
            return self._full_config

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Claude config not found: {self.config_path}\n"
                f"Expected location: ~/.claude/settings.json"
            )

        with open(self.config_path, 'r') as f:
            self._full_config = json.load(f)

        return self._full_config

    def generate_config(self, profile: Profile) -> Dict[str, Any]:
        """
        Generate Claude config for a specific profile.

        Args:
            profile: Profile with MCP server selection

        Returns:
            Filtered config dictionary with only profile's MCPs

        Raises:
            ValueError: If profile requests MCPs not in full config
        """
        full_config = self.load_full_config()

        # Start with base config (non-MCP settings)
        filtered_config = {
            "env": full_config.get("env", {}),
            "statusLine": full_config.get("statusLine", {}),
            "alwaysThinkingEnabled": full_config.get("alwaysThinkingEnabled", False),
        }

        # Filter MCP servers
        all_mcps = full_config.get("mcpServers", {})
        filtered_mcps = {}

        missing_mcps = []
        for mcp_name in profile.mcps:
            # Handle name variations (serena-v2 -> serena, etc.)
            actual_name = self._resolve_mcp_name(mcp_name, all_mcps)

            if actual_name and actual_name in all_mcps:
                filtered_mcps[actual_name] = all_mcps[actual_name]
            else:
                missing_mcps.append(mcp_name)

        if missing_mcps:
            raise ValueError(
                f"Profile '{profile.name}' requests MCP servers not in Claude config: "
                f"{', '.join(missing_mcps)}\n"
                f"Available MCPs: {', '.join(all_mcps.keys())}\n"
                f"Fix: Update profile or add missing MCPs to Claude config"
            )

        filtered_config["mcpServers"] = filtered_mcps

        return filtered_config

    def _resolve_mcp_name(self, profile_name: str, available_mcps: Dict[str, Any]) -> Optional[str]:
        """
        Resolve profile MCP name to actual config name.

        Handles name variations like:
        - serena-v2 -> serena
        - zen -> zen (direct match)
        - dope-context -> dope-context

        Args:
            profile_name: MCP name from profile
            available_mcps: Dictionary of available MCPs

        Returns:
            Actual MCP name if found, None otherwise
        """
        # Direct match
        if profile_name in available_mcps:
            return profile_name

        # Common variations
        variations = [
            profile_name,
            profile_name.replace("-", "_"),
            profile_name.replace("_", "-"),
            profile_name.replace("-v2", ""),
            profile_name.replace("_v2", ""),
        ]

        for variation in variations:
            if variation in available_mcps:
                return variation

        return None

    def write_config(self, profile: Profile, output_path: Optional[Path] = None, backup: bool = True) -> Path:
        """
        Generate and write config file for profile.

        Args:
            profile: Profile to generate config for
            output_path: Where to write config (default: ~/.claude/settings.json)
            backup: Whether to backup existing config first

        Returns:
            Path to written config file

        Raises:
            ValueError: If profile has invalid MCPs
        """
        if output_path is None:
            output_path = self.config_path

        # Generate filtered config
        new_config = self.generate_config(profile)

        # Backup existing config
        backup_path: Optional[Path] = None
        if backup and output_path.exists():
            backup_path = self._create_backup(output_path)
            logger.info(f"📦 Backed up existing config to: {backup_path}")

        # Write new config with atomic swap and rollback-on-failure safety.
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Validate before writing
            self._validate_config_structure(new_config)
            self._atomic_write_json(output_path, new_config)
        except Exception:
            if backup_path and backup_path.exists():
                self.rollback_config(output_path, backup_path)
            raise

        return output_path

    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure before writing."""
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")
        if "mcpServers" in config:
            if not isinstance(config["mcpServers"], dict):
                raise ValueError("'mcpServers' must be a dictionary")
            for name, server in config["mcpServers"].items():
                if not isinstance(server, dict):
                    raise ValueError(f"MCP server '{name}' config must be a dictionary")

    def _atomic_write_json(self, output_path: Path, data: Dict[str, Any]) -> None:
        """
        Write JSON via temp file + atomic replace.
        """
        tmp_name: Optional[str] = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(output_path.parent),
                prefix=f"{output_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as tmp_file:
                tmp_name = tmp_file.name
                json.dump(data, tmp_file, indent=2)
                tmp_file.write("\n")
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            Path(tmp_name).replace(output_path)
        finally:
            if tmp_name:
                tmp_path = Path(tmp_name)
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)

    def _create_backup(self, config_path: Path) -> Path:
        """
        Create timestamped backup of config file.

        Args:
            config_path: Path to config to backup

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"settings.backup.{timestamp}.json"
        backup_path = config_path.parent / backup_name

        shutil.copy2(config_path, backup_path)

        return backup_path

    def rollback_config(self, output_path: Path, backup_path: Path) -> None:
        """
        Restore configuration from a backup snapshot.
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file does not exist: {backup_path}")
        shutil.copy2(backup_path, output_path)

    def validate_profile_mcps(self, profile: Profile) -> tuple[bool, List[str]]:
        """
        Check if all profile MCPs exist in Claude config.

        Args:
            profile: Profile to validate

        Returns:
            Tuple of (all_valid, missing_mcps)
            - all_valid: True if all MCPs found
            - missing_mcps: List of MCP names not found
        """
        full_config = self.load_full_config()
        all_mcps = full_config.get("mcpServers", {})

        missing = []
        for mcp_name in profile.mcps:
            actual_name = self._resolve_mcp_name(mcp_name, all_mcps)
            if not actual_name or actual_name not in all_mcps:
                missing.append(mcp_name)

        return len(missing) == 0, missing

    def get_mcp_tool_count(self, config: Dict[str, Any]) -> int:
        """
        Estimate tool count for a config (approximation).

        Args:
            config: Generated config dictionary

        Returns:
            Estimated number of tools exposed
        """
        # Rough estimates per MCP server (from observation)
        tool_estimates = {
            "conport": 20,
            "serena": 26,
            "serena-v2": 26,
            "zen": 8,
            "pal": 2,
            "gpt-researcher": 5,
            "dope-context": 8,
            "desktop-commander": 10,
            "magic-mcp": 3,
            "playwright": 15,
            "tavily": 1,
            "mas-sequential-thinking": 3,
            "sequential_thinking": 3,
        }

        total = 0
        for mcp_name in config.get("mcpServers", {}).keys():
            total += tool_estimates.get(mcp_name, 5)  # Default 5 if unknown

        return total

    def compare_configs(self, profile_a: Profile, profile_b: Profile) -> Dict[str, Any]:
        """
        Compare two profiles to show difference in tool count.

        Args:
            profile_a: First profile
            profile_b: Second profile

        Returns:
            Comparison dictionary with tool counts and differences
        """
        config_a = self.generate_config(profile_a)
        config_b = self.generate_config(profile_b)

        tools_a = self.get_mcp_tool_count(config_a)
        tools_b = self.get_mcp_tool_count(config_b)

        mcps_a = set(config_a.get("mcpServers", {}).keys())
        mcps_b = set(config_b.get("mcpServers", {}).keys())

        return {
            "profile_a": {
                "name": profile_a.name,
                "mcps": len(mcps_a),
                "tools": tools_a
            },
            "profile_b": {
                "name": profile_b.name,
                "mcps": len(mcps_b),
                "tools": tools_b
            },
            "difference": {
                "mcps": len(mcps_a) - len(mcps_b),
                "tools": tools_a - tools_b,
                "reduction_pct": ((tools_a - tools_b) / tools_a * 100) if tools_a > 0 else 0
            },
            "unique_to_a": list(mcps_a - mcps_b),
            "unique_to_b": list(mcps_b - mcps_a),
            "shared": list(mcps_a & mcps_b)
        }


def generate_config_for_profile(profile: Profile, output_path: Optional[Path] = None) -> Path:
    """
    Convenience function to generate config for a profile.

    Args:
        profile: Profile to generate config for
        output_path: Where to write (default: ~/.claude/settings.json)

    Returns:
        Path to written config
    """
    generator = ConfigGenerator()
    return generator.write_config(profile, output_path, backup=True)


if __name__ == "__main__":
    # Quick test
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from dopemux.profile_parser import load_all_profiles

    logger.info("Testing Config Generator...\n")

    try:
        # Load profiles
        profiles = load_all_profiles(Path("profiles"))
        generator = ConfigGenerator()

        # Test each profile
        for profile in profiles.profiles:
            logger.info(f"=== Profile: {profile.name} ===")

            # Validate MCPs
            valid, missing = generator.validate_profile_mcps(profile)
            if not valid:
                logger.info(f"❌ Missing MCPs: {', '.join(missing)}")
                continue

            # Generate config
            config = generator.generate_config(profile)
            mcp_count = len(config.get("mcpServers", {}))
            tool_count = generator.get_mcp_tool_count(config)

            logger.info(f"✅ Valid config generated")
            logger.info(f"   MCPs: {mcp_count}")
            logger.info(f"   Est. tools: {tool_count}")
            logger.info(f"   MCP list: {', '.join(config['mcpServers'].keys())}")
            logger.info()

        # Compare minimal vs developer
        minimal = profiles.get_profile("minimal")
        developer = profiles.get_profile("developer")

        if minimal and developer:
            logger.info("=== Comparison: minimal vs developer ===")
            comparison = generator.compare_configs(minimal, developer)
            logger.info(f"Minimal: {comparison['profile_a']['tools']} tools")
            logger.info(f"Developer: {comparison['profile_b']['tools']} tools")
            logger.info(f"Difference: {comparison['difference']['tools']} tools ({comparison['difference']['reduction_pct']:.0f}% reduction)")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

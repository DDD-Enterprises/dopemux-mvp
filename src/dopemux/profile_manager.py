#!/usr/bin/env python3
"""
Profile Manager for Dopemux Multi-Project Configuration

Manages profile-based configuration cascade:
  Global (~/.dopemux/config.yaml)
    ↓ merge
  Profile (~/.dopemux/profiles/{name}.yaml)
    ↓ merge
  Project ({workspace}/.dopemux/config.yaml)
    ↓ merge
  Environment variables

Supports profile selection, creation, and switching for multi-project workflows.
"""

import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class DopemuxProfile:
    """Represents a dopemux configuration profile."""

    name: str
    description: str
    mcp_servers: Dict[str, List[str]] = field(default_factory=dict)
    adhd_config: Dict[str, Any] = field(default_factory=dict)
    database_config: Dict[str, Dict[str, str]] = field(default_factory=dict)
    tools: Dict[str, Any] = field(default_factory=dict)
    markers: Dict[str, List[str]] = field(default_factory=dict)
    
    @property
    def mcps(self) -> List[str]:
        """Alias for mcp_servers for backward compatibility.
        
        Returns combined list of required and enabled MCP servers.
        """
        required = self.mcp_servers.get("required", [])
        enabled = self.mcp_servers.get("enabled", [])
        return list(set(required + enabled))

    @classmethod
    def from_yaml(cls, path: Path) -> "DopemuxProfile":
        """Load profile from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            name=data.get("name", path.stem),
            description=data.get("description", ""),
            mcp_servers=data.get("mcp_servers", {}),
            adhd_config=data.get("adhd_config", {}),
            database_config=data.get("database_config", {}),
            tools=data.get("tools", {}),
            markers=data.get("markers", {})
        )

    def to_yaml(self, path: Path) -> None:
        """Save profile to YAML file."""
        data = {
            "name": self.name,
            "description": self.description,
            "mcp_servers": self.mcp_servers,
            "adhd_config": self.adhd_config,
            "database_config": self.database_config,
            "tools": self.tools,
            "markers": self.markers
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class ProfileManager:
    """Manages dopemux configuration profiles."""

    def __init__(self, dopemux_home: Optional[Path] = None):
        """
        Initialize profile manager.

        Args:
            dopemux_home: Path to ~/.dopemux directory (auto-detects if None)
        """
        self.dopemux_home = dopemux_home or Path.home() / ".dopemux"
        self.profiles_dir = self.dopemux_home / "profiles"
        self.config_file = self.dopemux_home / "config.yaml"

        # Ensure directories exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> List[DopemuxProfile]:
        """List all available profiles."""
        profiles = []

        # Find all .yaml files in profiles directory
        for profile_file in self.profiles_dir.glob("*.yaml"):
            try:
                profile = DopemuxProfile.from_yaml(profile_file)
                profiles.append(profile)
            except Exception as e:
                print(f"Warning: Failed to load profile {profile_file}: {e}")

        return sorted(profiles, key=lambda p: p.name)

    def get_profile(self, name: str) -> Optional[DopemuxProfile]:
        """Get specific profile by name."""
        profile_path = self.profiles_dir / f"{name}.yaml"

        if not Path.exists(profile_path):
            return None

        return DopemuxProfile.from_yaml(profile_path)

    def create_profile(
        self,
        name: str,
        description: str,
        based_on: Optional[str] = None
    ) -> DopemuxProfile:
        """
        Create new profile.

        Args:
            name: Profile name (alphanumeric + hyphens)
            description: Human-readable description
            based_on: Optional base profile to copy from

        Returns:
            Created profile
        """
        # Validate name
        if not name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid profile name: {name}. Use alphanumeric + hyphens/underscores.")

        profile_path = self.profiles_dir / f"{name}.yaml"

        if Path.exists(profile_path):
            raise ValueError(f"Profile already exists: {name}")

        # Create profile (copy from base or use defaults)
        if based_on:
            base_profile = self.get_profile(based_on)
            if not base_profile:
                raise ValueError(f"Base profile not found: {based_on}")

            # Copy base profile
            profile = DopemuxProfile(
                name=name,
                description=description,
                mcp_servers=base_profile.mcp_servers.copy(),
                adhd_config=base_profile.adhd_config.copy(),
                database_config=base_profile.database_config.copy(),
                tools=base_profile.tools.copy(),
                markers=base_profile.markers.copy()
            )
        else:
            # Use minimal defaults
            profile = DopemuxProfile(
                name=name,
                description=description,
                mcp_servers={
                    "required": ["zen", "conport", "context7"],
                    "enabled": [],
                    "disabled": []
                },
                adhd_config={
                    "session_duration_minutes": 25,
                    "energy_tracking_enabled": True
                },
                database_config={
                    "conport": {"mode": "shared", "path": "~/.dopemux/databases/conport.db"},
                    "serena": {"mode": "local", "path": ".dopemux/databases/serena-{hash}.db"}
                }
            )

        # Save profile
        profile.to_yaml(profile_path)
        return profile

    def get_active_profile(self, workspace: Path) -> Optional[str]:
        """Get active profile name for workspace."""
        profile_marker = workspace / ".dopemux" / "active_profile"

        if Path.exists(profile_marker):
            return profile_marker.read_text().strip()

        return None

    def set_active_profile(self, workspace: Path, profile_name: str) -> None:
        """Set active profile for workspace."""
        profile_marker = workspace / ".dopemux" / "active_profile"
        profile_marker.parent.mkdir(parents=True, exist_ok=True)
        profile_marker.write_text(profile_name)

    def load_merged_config(
        self,
        workspace: Path,
        profile_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load merged configuration for workspace.

        Cascade order:
        1. Global ~/.dopemux/config.yaml
        2. Profile ~/.dopemux/profiles/{profile}.yaml
        3. Project {workspace}/.dopemux/config.yaml
        4. Environment variables override

        Returns:
            Merged configuration dictionary
        """
        merged = {}

        # 1. Global config
        if Path.exists(self.config_file):
            with open(self.config_file) as f:
                global_cfg = yaml.safe_load(f) or {}
                merged = self._deep_merge(merged, global_cfg)

        # 2. Profile config
        if not profile_name:
            profile_name = self.get_active_profile(workspace)

        if profile_name:
            profile = self.get_profile(profile_name)
            if profile:
                profile_dict = {
                    "mcp_servers": profile.mcp_servers,
                    "adhd_config": profile.adhd_config,
                    "database_config": profile.database_config,
                    "tools": profile.tools
                }
                merged = self._deep_merge(merged, profile_dict)

        # 3. Project config
        project_config_file = workspace / ".dopemux" / "config.yaml"
        if Path.exists(project_config_file):
            with open(project_config_file) as f:
                project_cfg = yaml.safe_load(f) or {}
                merged = self._deep_merge(merged, project_cfg)

        # 4. Environment variable overrides
        env_overrides = self._get_env_overrides()
        merged = self._deep_merge(merged, env_overrides)

        return merged

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries (override wins on conflicts)."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _get_env_overrides(self) -> Dict[str, Any]:
        """Extract dopemux config from environment variables."""
        overrides = {}

        # DOPEMUX_SESSION_DURATION → adhd_config.session_duration_minutes
        if os.getenv("DOPEMUX_SESSION_DURATION"):
            overrides.setdefault("adhd_config", {})
            overrides["adhd_config"]["session_duration_minutes"] = int(
                os.getenv("DOPEMUX_SESSION_DURATION")
            )

        # DOPEMUX_ENERGY_TRACKING → adhd_config.energy_tracking_enabled
        if os.getenv("DOPEMUX_ENERGY_TRACKING"):
            overrides.setdefault("adhd_config", {})
            overrides["adhd_config"]["energy_tracking_enabled"] = (
                os.getenv("DOPEMUX_ENERGY_TRACKING").lower() in ["true", "1", "yes"]
            )

        return overrides

    def install_default_profiles(self) -> None:
        """
        Install default profiles from config/profiles/ to ~/.dopemux/profiles/

        Called during setup.sh to initialize ~/.dopemux/
        """
        # Find source profiles in dopemux repo
        repo_profiles = Path(__file__).parent.parent.parent / "config" / "profiles"

        if not Path.exists(repo_profiles):
            print(f"Warning: Default profiles not found at {repo_profiles}")
            return

        # Copy to user's ~/.dopemux/profiles/
        for profile_file in repo_profiles.glob("*.yaml"):
            dest = self.profiles_dir / profile_file.name

            if not Path.exists(dest):
                shutil.copy(profile_file, dest)
                print(f"✅ Installed profile: {profile_file.stem}")
            else:
                print(f"⏭️  Profile already exists: {profile_file.stem}")

"""
Pydantic models for Dopemux profile management.

Provides type-safe validation for profile YAML configurations with ADHD-optimized
settings and auto-detection rules.

Schema Version: 1.0.0
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ProfileValidationError(Exception):
    """Custom exception for profile validation errors.

    Provides structured error information with actionable fix suggestions
    for better user experience.

    Attributes:
        reason: Human-readable explanation of what went wrong
        fix_suggestion: Optional actionable suggestion to fix the error
    """

    def __init__(self, reason: str, fix_suggestion: Optional[str] = None):
        """Initialize validation error with reason and optional fix suggestion.

        Args:
            reason: Explanation of the validation failure
            fix_suggestion: Optional suggestion for how to fix the issue
        """
        self.reason = reason
        self.fix_suggestion = fix_suggestion
        super().__init__(reason)


class EnergyPreference(str, Enum):
    """ADHD energy level preferences for profile matching."""

    ANY = "any"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HYPERFOCUS = "hyperfocus"


class AttentionMode(str, Enum):
    """ADHD attention mode preferences for profile matching."""

    ANY = "any"
    SCATTERED = "scattered"
    FOCUSED = "focused"
    HYPERFOCUSED = "hyperfocused"


class ADHDConfig(BaseModel):
    """ADHD optimization settings for a profile.

    Attributes:
        energy_preference: Preferred energy level for this profile
        attention_mode: Preferred attention mode for this profile
        session_duration: Recommended session length in minutes (default: 50)
    """

    energy_preference: EnergyPreference = Field(
        default=EnergyPreference.ANY,
        description="Preferred energy level (any, low, medium, high, hyperfocus)"
    )
    attention_mode: AttentionMode = Field(
        default=AttentionMode.ANY,
        description="Preferred attention mode (any, scattered, focused, hyperfocused)"
    )
    session_duration: int = Field(
        default=50,
        ge=1,
        le=180,
        description="Recommended session length in minutes"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AutoDetection(BaseModel):
    """Auto-detection rules for profile selection.

    Attributes:
        git_branches: Git branch patterns (supports wildcards)
        directories: Directory path patterns
        file_patterns: File extension patterns
        time_windows: Time ranges in HH:MM-HH:MM format
    """

    git_branches: List[str] = Field(
        default_factory=list,
        description="Git branch patterns (e.g., 'feature/*', 'fix/*')"
    )
    directories: List[str] = Field(
        default_factory=list,
        description="Directory path patterns (relative or absolute)"
    )
    file_patterns: List[str] = Field(
        default_factory=list,
        description="File extension patterns (e.g., '*.py', '*.ts')"
    )
    time_windows: List[str] = Field(
        default_factory=list,
        description="Time ranges in HH:MM-HH:MM format (24-hour)"
    )

    @field_validator("time_windows")
    @classmethod
    def validate_time_windows(cls, v: List[str]) -> List[str]:
        """Validate time window format: HH:MM-HH:MM."""
        time_pattern = re.compile(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$")

        for window in v:
            if not time_pattern.match(window):
                raise ValueError(
                    f"Invalid time window format: '{window}'. "
                    f"Expected HH:MM-HH:MM (24-hour format, e.g., '09:00-12:00')"
                )

        return v


class Profile(BaseModel):
    """Dopemux profile configuration.

    A profile defines which MCP servers to load and optional ADHD optimizations
    and auto-detection rules.

    Attributes:
        name: Unique profile identifier (lowercase, no spaces)
        display_name: Human-readable name for UI display
        description: Brief description of profile purpose
        mcps: List of MCP server names to load (conport required)
        adhd_config: Optional ADHD optimization settings
        auto_detection: Optional auto-detection rules
    """

    name: str = Field(
        ...,
        description="Unique profile identifier (lowercase, alphanumeric with hyphens)",
        min_length=1,
        max_length=50
    )
    display_name: str = Field(
        ...,
        description="Human-readable name for UI display",
        min_length=1,
        max_length=100
    )
    description: str = Field(
        ...,
        description="Brief description of profile purpose",
        min_length=1,
        max_length=500
    )
    mcps: List[str] = Field(
        ...,
        description="List of MCP server names to load (conport required)",
        min_length=1
    )
    adhd_config: Optional[ADHDConfig] = Field(
        default=None,
        description="ADHD optimization settings"
    )
    auto_detection: Optional[AutoDetection] = Field(
        default=None,
        description="Auto-detection rules for profile selection"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate profile name format: lowercase, alphanumeric with hyphens."""
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                f"Invalid profile name: '{v}'. "
                f"Name must be lowercase, alphanumeric with hyphens only (no spaces)"
            )
        return v

    @field_validator("mcps")
    @classmethod
    def validate_conport_required(cls, v: List[str]) -> List[str]:
        """Validate that 'conport' is present in MCP list."""
        if "conport" not in v:
            raise ValueError(
                "Profile is invalid: 'conport' is required in all profiles (memory authority). "
                "Fix: Add 'conport' to mcps array"
            )
        return v

    @model_validator(mode="after")
    def validate_unique_mcps(self) -> Profile:
        """Ensure no duplicate MCP servers in the list."""
        if len(self.mcps) != len(set(self.mcps)):
            duplicates = [mcp for mcp in set(self.mcps) if self.mcps.count(mcp) > 1]
            raise ValueError(
                f"Duplicate MCP servers found in profile '{self.name}': {', '.join(duplicates)}"
            )
        return self

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "examples": [
                {
                    "name": "developer",
                    "display_name": "Developer",
                    "description": "Code implementation and debugging",
                    "mcps": ["conport", "serena-v2", "dope-context"],
                    "adhd_config": {
                        "energy_preference": "medium",
                        "attention_mode": "focused",
                        "session_duration": 50
                    },
                    "auto_detection": {
                        "git_branches": ["feature/*", "fix/*"],
                        "directories": ["src/", "tests/"],
                        "file_patterns": ["*.py", "*.ts"],
                        "time_windows": ["09:00-12:00", "14:00-17:00"]
                    }
                }
            ]
        }


class ProfileCollection(BaseModel):
    """Collection of profiles with validation.

    Validates that profile names are unique and provides helper methods
    for profile lookup and management.

    Attributes:
        profiles: List of Profile objects
    """

    profiles: List[Profile] = Field(
        ...,
        description="List of profiles",
        min_length=1
    )

    @model_validator(mode="after")
    def validate_unique_names(self) -> ProfileCollection:
        """Ensure all profile names are unique."""
        names = [p.name for p in self.profiles]
        if len(names) != len(set(names)):
            duplicates = [name for name in set(names) if names.count(name) > 1]
            raise ValueError(
                f"Duplicate profile names found: {', '.join(duplicates)}. "
                f"Each profile must have a unique name."
            )
        return self

    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a profile by name.

        Args:
            name: Profile name to look up

        Returns:
            Profile object if found, None otherwise
        """
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None

    def get_profile_names(self) -> List[str]:
        """Get list of all profile names.

        Returns:
            List of profile names
        """
        return [p.name for p in self.profiles]

    def validate_mcp_servers(self, available_mcps: List[str]) -> dict[str, List[str]]:
        """Validate that all MCP servers in profiles are available.

        Args:
            available_mcps: List of available MCP server names from Claude config

        Returns:
            Dictionary mapping profile names to lists of invalid MCP servers.
            Empty lists indicate all MCPs are valid.
        """
        invalid_mcps: dict[str, List[str]] = {}

        for profile in self.profiles:
            invalid = [mcp for mcp in profile.mcps if mcp not in available_mcps]
            if invalid:
                invalid_mcps[profile.name] = invalid

        return invalid_mcps

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "examples": [
                {
                    "profiles": [
                        {
                            "name": "developer",
                            "display_name": "Developer",
                            "description": "Code implementation",
                            "mcps": ["conport", "serena-v2"]
                        },
                        {
                            "name": "researcher",
                            "display_name": "Researcher",
                            "description": "Deep research",
                            "mcps": ["conport", "zen", "gpt-researcher"]
                        }
                    ]
                }
            ]
        }


# Valid MCP server names (reference for validation)
VALID_MCP_SERVERS = [
    "conport",          # Memory authority (REQUIRED)
    "serena-v2",        # Code navigation and LSP
    "zen",              # Multi-model reasoning
    "pal",              # Code generation + API/SDK documentation (apilookup)
    "gpt-researcher",   # Deep web research
    "dope-context",     # Hybrid code search
    "desktop-commander", # Desktop automation and control
    "magic-mcp",        # UI component generation
    "playwright",       # Browser automation and testing
    "tavily",           # Web search API
    "mas-sequential-thinking",  # Multi-agent sequential thinking
    "sequential_thinking",  # Deprecated, use zen
]

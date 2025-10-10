"""
Dopemux Profile Manager - Pydantic Models

Defines validated data models for YAML profile loading and validation.
Based on YAML schema spec: docs/PROFILE-YAML-SCHEMA.md
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import re


# Enum types for ADHD configuration
EnergyPreference = Literal["any", "low", "medium", "high", "hyperfocus"]
AttentionMode = Literal["any", "scattered", "focused", "hyperfocused"]


class ADHDConfig(BaseModel):
    """ADHD optimization settings for profile"""

    energy_preference: EnergyPreference = Field(
        default="any",
        description="Preferred energy level for this profile"
    )
    attention_mode: AttentionMode = Field(
        default="any",
        description="Preferred attention mode for this profile"
    )
    session_duration: int = Field(
        default=50,
        ge=5,
        le=180,
        description="Recommended session length in minutes"
    )

    class Config:
        frozen = True  # Immutable after creation


class AutoDetection(BaseModel):
    """Auto-detection rules for profile selection"""

    git_branches: List[str] = Field(
        default_factory=list,
        description="Git branch patterns (supports wildcards)"
    )
    directories: List[str] = Field(
        default_factory=list,
        description="Directory path patterns"
    )
    file_patterns: List[str] = Field(
        default_factory=list,
        description="File extension patterns"
    )
    time_windows: List[str] = Field(
        default_factory=list,
        description="Time ranges in HH:MM-HH:MM format"
    )

    @field_validator("time_windows")
    @classmethod
    def validate_time_windows(cls, v: List[str]) -> List[str]:
        """Validate time window format: HH:MM-HH:MM"""
        time_pattern = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$')
        for window in v:
            if not time_pattern.match(window):
                raise ValueError(
                    f"time_window '{window}' must be in HH:MM-HH:MM format (24-hour). "
                    f"Example: '09:00-17:00'"
                )
        return v

    class Config:
        frozen = True


class Profile(BaseModel):
    """Complete profile definition with validation"""

    # Required fields
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique profile identifier"
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name for UI"
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Brief description of profile purpose"
    )
    mcps: List[str] = Field(
        ...,
        min_length=1,
        description="List of MCP server names to load"
    )

    # Optional fields
    adhd_config: Optional[ADHDConfig] = Field(
        default=None,
        description="ADHD optimization settings"
    )
    auto_detection: Optional[AutoDetection] = Field(
        default=None,
        description="Auto-detection rules"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate profile name format: lowercase, alphanumeric with hyphens"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError(
                f"Profile name '{v}' must be lowercase alphanumeric with hyphens only. "
                f"No spaces or special characters."
            )
        return v

    @model_validator(mode='after')
    def validate_conport_required(self) -> 'Profile':
        """Ensure conport is present in all profiles (memory authority)"""
        if 'conport' not in self.mcps:
            raise ValueError(
                f"Profile '{self.name}' is invalid: "
                f"'conport' is required in all profiles (memory authority). "
                f"Fix: Add 'conport' to mcps array"
            )
        return self

    @field_validator("mcps")
    @classmethod
    def validate_unique_mcps(cls, v: List[str]) -> List[str]:
        """Ensure no duplicate MCP servers"""
        if len(v) != len(set(v)):
            duplicates = [mcp for mcp in v if v.count(mcp) > 1]
            raise ValueError(
                f"Duplicate MCP servers found: {duplicates}. "
                f"Each MCP should only appear once in mcps array."
            )
        return v

    class Config:
        frozen = True  # Immutable after validation
        str_strip_whitespace = True  # Auto-strip whitespace from strings


class ProfileValidationError(Exception):
    """Custom exception for profile validation errors"""

    def __init__(self, profile_name: str, reason: str, fix_suggestion: str = ""):
        self.profile_name = profile_name
        self.reason = reason
        self.fix_suggestion = fix_suggestion

        message = f"Profile '{profile_name}' is invalid\nReason: {reason}"
        if fix_suggestion:
            message += f"\nFix: {fix_suggestion}"

        super().__init__(message)


class ProfileSet(BaseModel):
    """Collection of profiles with uniqueness validation"""

    profiles: List[Profile] = Field(
        ...,
        min_length=1,
        description="List of profile definitions"
    )

    @model_validator(mode='after')
    def validate_unique_names(self) -> 'ProfileSet':
        """Ensure all profile names are unique"""
        names = [p.name for p in self.profiles]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(
                f"Duplicate profile names found: {duplicates}. "
                f"Each profile must have a unique name."
            )
        return self

    def get_profile(self, name: str) -> Optional[Profile]:
        """Get profile by name"""
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None

    def list_names(self) -> List[str]:
        """Get list of all profile names"""
        return [p.name for p in self.profiles]

    class Config:
        frozen = True


# Valid MCP server names (from Claude settings.json)
# NOTE: This is a reference list - actual validation happens in config_generator
VALID_MCP_SERVERS = {
    "conport",           # REQUIRED - memory authority
    "serena",            # Code navigation and LSP (Serena v2)
    "zen",               # Multi-model reasoning
    "context7",          # Official library documentation
    "gpt-researcher",    # Deep web research
    "claude-context",    # Semantic code search (Milvus)
    "desktop-commander", # Desktop automation
    "morph-llm",         # Code transformation
    "magic-mcp",         # UI component generation
    "playwright",        # Browser automation
    "exa",               # Neural web search
    "tavily",            # Web search API
    "devdocs",           # Developer documentation
    "cli",               # CLI automation
    "openmemory",        # OpenMemory integration
    "task-master-ai",    # Task management
    "sequential_thinking",      # Multi-step reasoning
}


def validate_mcp_servers(mcps: List[str], available_mcps: set[str] = VALID_MCP_SERVERS) -> tuple[bool, str]:
    """
    Validate that all MCP servers exist in available set.

    Args:
        mcps: List of MCP server names from profile
        available_mcps: Set of valid MCP server names

    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, "")
        - If invalid: (False, "error message with details")
    """
    unknown_mcps = [mcp for mcp in mcps if mcp not in available_mcps]

    if unknown_mcps:
        available_list = ", ".join(sorted(available_mcps))
        error_msg = (
            f"MCP server(s) not found in Claude config: {', '.join(unknown_mcps)}\n"
            f"Available: {available_list}\n"
            f"Fix: Use only valid MCP server names"
        )
        return False, error_msg

    return True, ""


# Example usage and testing helpers
def create_minimal_profile(name: str = "minimal") -> Profile:
    """Create a minimal valid profile for testing"""
    return Profile(
        name=name,
        display_name="Minimal",
        description="Bare minimum profile for testing",
        mcps=["conport"]
    )


def create_developer_profile() -> Profile:
    """Create developer profile with typical configuration"""
    return Profile(
        name="developer",
        display_name="Developer",
        description="Code implementation and debugging",
        mcps=["conport", "serena-v2", "dope-context"],
        adhd_config=ADHDConfig(
            energy_preference="medium",
            attention_mode="focused",
            session_duration=50
        ),
        auto_detection=AutoDetection(
            git_branches=["feature/*", "fix/*", "refactor/*"],
            directories=["src/", "tests/", "lib/"],
            file_patterns=["*.py", "*.ts", "*.js", "*.go"],
            time_windows=["09:00-12:00", "14:00-17:00"]
        )
    )


if __name__ == "__main__":
    # Quick validation test
    print("Testing profile models...")

    # Test 1: Minimal profile
    try:
        minimal = create_minimal_profile()
        print(f"✅ Minimal profile valid: {minimal.name}")
    except Exception as e:
        print(f"❌ Minimal profile failed: {e}")

    # Test 2: Developer profile
    try:
        dev = create_developer_profile()
        print(f"✅ Developer profile valid: {dev.name}")
    except Exception as e:
        print(f"❌ Developer profile failed: {e}")

    # Test 3: Missing conport (should fail)
    try:
        invalid = Profile(
            name="invalid",
            display_name="Invalid",
            description="Missing conport",
            mcps=["serena-v2"]
        )
        print(f"❌ Should have failed: conport required")
    except ValueError as e:
        print(f"✅ Correctly rejected: {str(e)[:80]}...")

    # Test 4: Invalid name format (should fail)
    try:
        invalid_name = Profile(
            name="Invalid Name",  # Spaces not allowed
            display_name="Invalid",
            description="Bad name format",
            mcps=["conport"]
        )
        print(f"❌ Should have failed: invalid name format")
    except ValueError as e:
        print(f"✅ Correctly rejected: {str(e)[:80]}...")

    print("\nAll tests complete!")

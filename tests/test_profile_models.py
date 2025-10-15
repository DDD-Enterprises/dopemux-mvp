"""
Tests for Dopemux profile Pydantic models.

Tests validation rules, enum constraints, and error handling.
"""

import pytest
from pydantic import ValidationError

from dopemux.profile_models import (
    ADHDConfig,
    AttentionMode,
    AutoDetection,
    EnergyPreference,
    Profile,
    ProfileCollection,
    VALID_MCP_SERVERS,
)


class TestEnergyPreference:
    """Test EnergyPreference enum."""

    def test_valid_values(self):
        """Test all valid energy preference values."""
        assert EnergyPreference.ANY == "any"
        assert EnergyPreference.LOW == "low"
        assert EnergyPreference.MEDIUM == "medium"
        assert EnergyPreference.HIGH == "high"
        assert EnergyPreference.HYPERFOCUS == "hyperfocus"


class TestAttentionMode:
    """Test AttentionMode enum."""

    def test_valid_values(self):
        """Test all valid attention mode values."""
        assert AttentionMode.ANY == "any"
        assert AttentionMode.SCATTERED == "scattered"
        assert AttentionMode.FOCUSED == "focused"
        assert AttentionMode.HYPERFOCUSED == "hyperfocused"


class TestADHDConfig:
    """Test ADHDConfig model."""

    def test_default_values(self):
        """Test default ADHD configuration values."""
        config = ADHDConfig()
        assert config.energy_preference == EnergyPreference.ANY
        assert config.attention_mode == AttentionMode.ANY
        assert config.session_duration == 50

    def test_custom_values(self):
        """Test custom ADHD configuration."""
        config = ADHDConfig(
            energy_preference=EnergyPreference.HIGH,
            attention_mode=AttentionMode.FOCUSED,
            session_duration=90
        )
        assert config.energy_preference == EnergyPreference.HIGH
        assert config.attention_mode == AttentionMode.FOCUSED
        assert config.session_duration == 90

    def test_session_duration_validation(self):
        """Test session duration must be between 1 and 180."""
        with pytest.raises(ValidationError) as exc_info:
            ADHDConfig(session_duration=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ADHDConfig(session_duration=200)
        assert "less than or equal to 180" in str(exc_info.value)

    def test_invalid_energy_preference(self):
        """Test invalid energy preference value."""
        with pytest.raises(ValidationError):
            ADHDConfig(energy_preference="invalid")

    def test_invalid_attention_mode(self):
        """Test invalid attention mode value."""
        with pytest.raises(ValidationError):
            ADHDConfig(attention_mode="invalid")


class TestAutoDetection:
    """Test AutoDetection model."""

    def test_empty_defaults(self):
        """Test all lists default to empty."""
        auto = AutoDetection()
        assert auto.git_branches == []
        assert auto.directories == []
        assert auto.file_patterns == []
        assert auto.time_windows == []

    def test_valid_time_windows(self):
        """Test valid time window formats."""
        auto = AutoDetection(
            time_windows=["09:00-12:00", "14:00-17:00", "00:00-23:59"]
        )
        assert len(auto.time_windows) == 3

    def test_invalid_time_window_format(self):
        """Test invalid time window formats are rejected."""
        invalid_formats = [
            "9:00-12:00",     # Missing leading zero
            "09:00-12",       # Incomplete end time
            "09:00-25:00",    # Invalid hour
            "09:60-12:00",    # Invalid minute
            "09-12",          # Missing colons
            "09:00",          # Missing range
        ]
        for invalid in invalid_formats:
            with pytest.raises(ValidationError) as exc_info:
                AutoDetection(time_windows=[invalid])
            assert "Invalid time window format" in str(exc_info.value)

    def test_git_branches(self):
        """Test git branch patterns."""
        auto = AutoDetection(
            git_branches=["feature/*", "fix/*", "main"]
        )
        assert "feature/*" in auto.git_branches
        assert "main" in auto.git_branches


class TestProfile:
    """Test Profile model."""

    def test_minimal_valid_profile(self):
        """Test minimal valid profile with only required fields."""
        profile = Profile(
            name="minimal",
            display_name="Minimal",
            description="Test profile",
            mcps=["conport"]
        )
        assert profile.name == "minimal"
        assert profile.display_name == "Minimal"
        assert profile.mcps == ["conport"]
        assert profile.adhd_config is None
        assert profile.auto_detection is None

    def test_full_profile(self):
        """Test profile with all fields populated."""
        profile = Profile(
            name="developer",
            display_name="Developer",
            description="Code implementation",
            mcps=["conport", "serena-v2", "dope-context"],
            adhd_config=ADHDConfig(
                energy_preference=EnergyPreference.MEDIUM,
                attention_mode=AttentionMode.FOCUSED,
                session_duration=50
            ),
            auto_detection=AutoDetection(
                git_branches=["feature/*"],
                directories=["src/"],
                file_patterns=["*.py"],
                time_windows=["09:00-12:00"]
            )
        )
        assert profile.name == "developer"
        assert len(profile.mcps) == 3
        assert profile.adhd_config.energy_preference == EnergyPreference.MEDIUM
        assert profile.auto_detection.git_branches == ["feature/*"]

    def test_name_validation(self):
        """Test profile name format validation."""
        # Valid names
        valid_names = ["developer", "test-123", "my-profile"]
        for name in valid_names:
            profile = Profile(
                name=name,
                display_name="Test",
                description="Test",
                mcps=["conport"]
            )
            assert profile.name == name

        # Invalid names
        invalid_names = [
            "Developer",      # Uppercase
            "my profile",     # Space
            "test_profile",   # Underscore
            "test.profile",   # Dot
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                Profile(
                    name=name,
                    display_name="Test",
                    description="Test",
                    mcps=["conport"]
                )
            assert "lowercase, alphanumeric with hyphens" in str(exc_info.value)

    def test_conport_required(self):
        """Test that conport is required in MCP list."""
        with pytest.raises(ValidationError) as exc_info:
            Profile(
                name="test",
                display_name="Test",
                description="Test",
                mcps=["serena-v2", "zen"]  # Missing conport
            )
        assert "conport" in str(exc_info.value).lower()
        assert "required" in str(exc_info.value).lower()

    def test_duplicate_mcps_rejected(self):
        """Test that duplicate MCP servers are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Profile(
                name="test",
                display_name="Test",
                description="Test",
                mcps=["conport", "zen", "zen"]  # Duplicate zen
            )
        assert "Duplicate MCP servers" in str(exc_info.value)

    def test_empty_mcps_list_rejected(self):
        """Test that empty MCP list is rejected."""
        with pytest.raises(ValidationError):
            Profile(
                name="test",
                display_name="Test",
                description="Test",
                mcps=[]
            )


class TestProfileCollection:
    """Test ProfileCollection model."""

    def test_single_profile_collection(self):
        """Test collection with single profile."""
        collection = ProfileCollection(
            profiles=[
                Profile(
                    name="developer",
                    display_name="Developer",
                    description="Test",
                    mcps=["conport"]
                )
            ]
        )
        assert len(collection.profiles) == 1
        assert collection.profiles[0].name == "developer"

    def test_multiple_profiles(self):
        """Test collection with multiple profiles."""
        collection = ProfileCollection(
            profiles=[
                Profile(
                    name="developer",
                    display_name="Developer",
                    description="Dev profile",
                    mcps=["conport", "serena-v2"]
                ),
                Profile(
                    name="researcher",
                    display_name="Researcher",
                    description="Research profile",
                    mcps=["conport", "zen", "gpt-researcher"]
                )
            ]
        )
        assert len(collection.profiles) == 2

    def test_duplicate_profile_names_rejected(self):
        """Test that duplicate profile names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileCollection(
                profiles=[
                    Profile(
                        name="developer",
                        display_name="Developer 1",
                        description="Test",
                        mcps=["conport"]
                    ),
                    Profile(
                        name="developer",
                        display_name="Developer 2",
                        description="Test",
                        mcps=["conport"]
                    )
                ]
            )
        assert "Duplicate profile names" in str(exc_info.value)
        assert "developer" in str(exc_info.value)

    def test_get_profile(self):
        """Test getting a profile by name."""
        collection = ProfileCollection(
            profiles=[
                Profile(
                    name="developer",
                    display_name="Developer",
                    description="Test",
                    mcps=["conport"]
                ),
                Profile(
                    name="researcher",
                    display_name="Researcher",
                    description="Test",
                    mcps=["conport"]
                )
            ]
        )

        profile = collection.get_profile("developer")
        assert profile is not None
        assert profile.name == "developer"

        profile = collection.get_profile("nonexistent")
        assert profile is None

    def test_get_profile_names(self):
        """Test getting list of all profile names."""
        collection = ProfileCollection(
            profiles=[
                Profile(
                    name="developer",
                    display_name="Developer",
                    description="Test",
                    mcps=["conport"]
                ),
                Profile(
                    name="researcher",
                    display_name="Researcher",
                    description="Test",
                    mcps=["conport"]
                )
            ]
        )

        names = collection.get_profile_names()
        assert names == ["developer", "researcher"]

    def test_validate_mcp_servers(self):
        """Test MCP server validation against available servers."""
        collection = ProfileCollection(
            profiles=[
                Profile(
                    name="valid",
                    display_name="Valid",
                    description="Test",
                    mcps=["conport", "serena-v2"]
                ),
                Profile(
                    name="invalid",
                    display_name="Invalid",
                    description="Test",
                    mcps=["conport", "unknown-mcp", "another-unknown"]
                )
            ]
        )

        invalid_mcps = collection.validate_mcp_servers(VALID_MCP_SERVERS)

        assert "valid" not in invalid_mcps
        assert "invalid" in invalid_mcps
        assert "unknown-mcp" in invalid_mcps["invalid"]
        assert "another-unknown" in invalid_mcps["invalid"]

    def test_empty_collection_rejected(self):
        """Test that empty profile collection is rejected."""
        with pytest.raises(ValidationError):
            ProfileCollection(profiles=[])

"""
Tests for Dopemux profile YAML parser.

Tests YAML parsing, validation, error handling, and file operations.
"""

import tempfile
from pathlib import Path

import pytest

from dopemux.profile_models import VALID_MCP_SERVERS
from dopemux.profile_parser import (
    ProfileParseError,
    ProfileParser,
    parse_profile_file,
    parse_profile_string,
)


class TestProfileParser:
    """Test ProfileParser class."""

    def test_parse_minimal_profile_string(self):
        """Test parsing minimal valid profile from string."""
        yaml_content = """
name: minimal
display_name: "Minimal"
description: "Test profile"
mcps:
  - conport
"""
        parser = ProfileParser(validate_mcps=False)
        collection = parser.parse_string(yaml_content)

        assert len(collection.profiles) == 1
        profile = collection.profiles[0]
        assert profile.name == "minimal"
        assert profile.display_name == "Minimal"
        assert profile.mcps == ["conport"]

    def test_parse_full_profile_string(self):
        """Test parsing profile with all fields."""
        yaml_content = """
name: developer
display_name: "Developer"
description: "Code implementation"
mcps:
  - conport
  - serena-v2
  - dope-context
adhd_config:
  energy_preference: medium
  attention_mode: focused
  session_duration: 50
auto_detection:
  git_branches:
    - "feature/*"
    - "fix/*"
  directories:
    - "src/"
    - "tests/"
  file_patterns:
    - "*.py"
    - "*.ts"
  time_windows:
    - "09:00-12:00"
    - "14:00-17:00"
"""
        parser = ProfileParser(validate_mcps=False)
        collection = parser.parse_string(yaml_content)

        profile = collection.profiles[0]
        assert profile.name == "developer"
        assert len(profile.mcps) == 3
        assert profile.adhd_config.energy_preference == "medium"
        assert profile.adhd_config.session_duration == 50
        assert len(profile.auto_detection.git_branches) == 2
        assert len(profile.auto_detection.time_windows) == 2

    def test_parse_profile_collection_string(self):
        """Test parsing collection with multiple profiles."""
        yaml_content = """
profiles:
  - name: developer
    display_name: "Developer"
    description: "Dev profile"
    mcps:
      - conport
      - serena-v2

  - name: researcher
    display_name: "Researcher"
    description: "Research profile"
    mcps:
      - conport
      - zen
"""
        parser = ProfileParser(validate_mcps=False)
        collection = parser.parse_string(yaml_content)

        assert len(collection.profiles) == 2
        assert collection.profiles[0].name == "developer"
        assert collection.profiles[1].name == "researcher"

    def test_parse_profile_list_string(self):
        """Test parsing list of profiles."""
        yaml_content = """
- name: developer
  display_name: "Developer"
  description: "Dev profile"
  mcps:
    - conport

- name: researcher
  display_name: "Researcher"
  description: "Research profile"
  mcps:
    - conport
    - zen
"""
        parser = ProfileParser(validate_mcps=False)
        collection = parser.parse_string(yaml_content)

        assert len(collection.profiles) == 2

    def test_invalid_yaml_syntax(self):
        """Test parsing invalid YAML syntax."""
        yaml_content = """
name: test
display_name: "Test
description: "Missing quote
mcps:
  - conport
"""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string(yaml_content)
        assert "Invalid YAML syntax" in str(exc_info.value)

    def test_empty_yaml(self):
        """Test parsing empty YAML file."""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string("")
        assert "Empty YAML" in str(exc_info.value)

    def test_invalid_yaml_structure(self):
        """Test parsing invalid YAML structure."""
        yaml_content = "just a string"
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string(yaml_content)
        assert "Invalid YAML structure" in str(exc_info.value)

    def test_missing_required_field(self):
        """Test parsing profile missing required field."""
        yaml_content = """
name: test
display_name: "Test"
# Missing description
mcps:
  - conport
"""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string(yaml_content)
        assert "validation failed" in str(exc_info.value).lower()

    def test_missing_conport(self):
        """Test parsing profile without conport."""
        yaml_content = """
name: test
display_name: "Test"
description: "Test"
mcps:
  - serena-v2
  - zen
"""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string(yaml_content)
        assert "conport" in str(exc_info.value).lower()

    def test_duplicate_profile_names(self):
        """Test parsing collection with duplicate names."""
        yaml_content = """
profiles:
  - name: developer
    display_name: "Developer 1"
    description: "Test"
    mcps: [conport]

  - name: developer
    display_name: "Developer 2"
    description: "Test"
    mcps: [conport]
"""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string(yaml_content)
        assert "Duplicate profile names" in str(exc_info.value)

    def test_validate_mcps_enabled(self):
        """Test MCP validation when enabled."""
        yaml_content = """
name: test
display_name: "Test"
description: "Test"
mcps:
  - conport
  - unknown-mcp
  - another-unknown
"""
        parser = ProfileParser(validate_mcps=True, available_mcps=VALID_MCP_SERVERS)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string(yaml_content)
        assert "Invalid MCP server names" in str(exc_info.value)
        assert "unknown-mcp" in str(exc_info.value)

    def test_validate_mcps_disabled(self):
        """Test MCP validation when disabled."""
        yaml_content = """
name: test
display_name: "Test"
description: "Test"
mcps:
  - conport
  - unknown-mcp
"""
        parser = ProfileParser(validate_mcps=False)
        collection = parser.parse_string(yaml_content)
        assert len(collection.profiles) == 1

    def test_custom_available_mcps(self):
        """Test validation with custom MCP list."""
        yaml_content = """
name: test
display_name: "Test"
description: "Test"
mcps:
  - conport
  - custom-mcp
"""
        custom_mcps = ["conport", "custom-mcp"]
        parser = ProfileParser(validate_mcps=True, available_mcps=custom_mcps)
        collection = parser.parse_string(yaml_content)
        assert len(collection.profiles) == 1


class TestProfileParserFiles:
    """Test ProfileParser file operations."""

    def test_parse_single_profile_file(self):
        """Test parsing single profile from file."""
        yaml_content = """
name: developer
display_name: "Developer"
description: "Test"
mcps:
  - conport
  - serena-v2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = Path(f.name)

        try:
            parser = ProfileParser(validate_mcps=False)
            collection = parser.parse_file(temp_file)

            assert len(collection.profiles) == 1
            assert collection.profiles[0].name == "developer"
        finally:
            temp_file.unlink()

    def test_parse_file_not_found(self):
        """Test parsing nonexistent file."""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/path/profile.yaml")

    def test_parse_directory(self):
        """Test parsing all profiles from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple profile files
            (temp_path / "developer.yaml").write_text("""
name: developer
display_name: "Developer"
description: "Test"
mcps: [conport, serena-v2]
""")

            (temp_path / "researcher.yaml").write_text("""
name: researcher
display_name: "Researcher"
description: "Test"
mcps: [conport, zen]
""")

            # Create a non-YAML file (should be ignored)
            (temp_path / "readme.txt").write_text("This is not YAML")

            parser = ProfileParser(validate_mcps=False)
            collection = parser.parse_directory(temp_path)

            assert len(collection.profiles) == 2
            names = collection.get_profile_names()
            assert "developer" in names
            assert "researcher" in names

    def test_parse_directory_not_found(self):
        """Test parsing nonexistent directory."""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(FileNotFoundError):
            parser.parse_directory("/nonexistent/directory")

    def test_parse_directory_duplicate_names_across_files(self):
        """Test that duplicate names across files are caught."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            (temp_path / "profile1.yaml").write_text("""
name: developer
display_name: "Developer 1"
description: "Test"
mcps: [conport]
""")

            (temp_path / "profile2.yaml").write_text("""
name: developer
display_name: "Developer 2"
description: "Test"
mcps: [conport]
""")

            parser = ProfileParser(validate_mcps=False)
            with pytest.raises(ProfileParseError) as exc_info:
                parser.parse_directory(temp_path)
            assert "Duplicate profile names" in str(exc_info.value)

    def test_validate_profile_dict(self):
        """Test validating profile dictionary directly."""
        profile_data = {
            "name": "test",
            "display_name": "Test",
            "description": "Test profile",
            "mcps": ["conport", "zen"]
        }

        parser = ProfileParser(validate_mcps=False)
        profile = parser.validate_profile_dict(profile_data)

        assert profile.name == "test"
        assert len(profile.mcps) == 2


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_parse_profile_file_function(self):
        """Test parse_profile_file convenience function."""
        yaml_content = """
name: test
display_name: "Test"
description: "Test"
mcps: [conport]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = Path(f.name)

        try:
            collection = parse_profile_file(temp_file, validate_mcps=False)
            assert len(collection.profiles) == 1
        finally:
            temp_file.unlink()

    def test_parse_profile_string_function(self):
        """Test parse_profile_string convenience function."""
        yaml_content = """
name: test
display_name: "Test"
description: "Test"
mcps: [conport]
"""
        collection = parse_profile_string(yaml_content, validate_mcps=False)
        assert len(collection.profiles) == 1


class TestErrorMessages:
    """Test error message formatting."""

    def test_error_message_with_file_path(self):
        """Test that error messages include file path."""
        yaml_content = """
name: test
display_name: "Test"
# Missing description
mcps: [conport]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = Path(f.name)

        try:
            parser = ProfileParser(validate_mcps=False)
            with pytest.raises(ProfileParseError) as exc_info:
                parser.parse_file(temp_file)
            assert str(temp_file) in str(exc_info.value)
        finally:
            temp_file.unlink()

    def test_error_message_with_validation_details(self):
        """Test that error messages include validation details."""
        yaml_content = """
name: Invalid Name
display_name: "Test"
description: "Test"
mcps: [conport]
"""
        parser = ProfileParser(validate_mcps=False)
        with pytest.raises(ProfileParseError) as exc_info:
            parser.parse_string(yaml_content)

        error_msg = str(exc_info.value)
        assert "validation failed" in error_msg.lower()
        assert "name" in error_msg.lower()

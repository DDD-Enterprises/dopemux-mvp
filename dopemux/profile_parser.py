"""
YAML parser for Dopemux profile configurations.

Provides safe YAML loading with comprehensive validation and helpful error messages.
Supports both single profile files and multi-profile collections.

Schema Version: 1.0.0
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml
from pydantic import ValidationError

from .profile_models import (
    VALID_MCP_SERVERS,
    Profile,
    ProfileCollection,
)


class ProfileParseError(Exception):
    """Raised when profile YAML parsing or validation fails.

    Attributes:
        message: Human-readable error description
        file_path: Path to the profile file (if applicable)
        errors: List of validation errors from Pydantic
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        errors: Optional[List[Dict]] = None
    ):
        self.message = message
        self.file_path = file_path
        self.errors = errors or []
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Format error message with file path and validation details."""
        parts = []

        # Header with file path if available
        if self.file_path:
            parts.append(f"Error parsing profile: {self.file_path}")
        else:
            parts.append("Error parsing profile")

        # Main error message
        parts.append(f"\n{self.message}")

        # Validation errors if available
        if self.errors:
            parts.append("\n\nValidation errors:")
            for error in self.errors:
                loc = " → ".join(str(l) for l in error.get("loc", []))
                msg = error.get("msg", "Unknown error")
                parts.append(f"  • {loc}: {msg}")

        return "".join(parts)


class ProfileParser:
    """Parser for Dopemux profile YAML files.

    Handles both single profiles and profile collections with comprehensive
    validation and error reporting.
    """

    def __init__(self, validate_mcps: bool = True, available_mcps: Optional[List[str]] = None):
        """Initialize the profile parser.

        Args:
            validate_mcps: Whether to validate MCP server names against available servers
            available_mcps: List of available MCP server names (default: VALID_MCP_SERVERS)
        """
        self.validate_mcps = validate_mcps
        self.available_mcps = available_mcps or VALID_MCP_SERVERS

    def parse_file(self, file_path: Union[str, Path]) -> ProfileCollection:
        """Parse a profile YAML file.

        Supports both single profile files and files containing multiple profiles.

        Args:
            file_path: Path to the YAML file

        Returns:
            ProfileCollection containing validated profiles

        Raises:
            ProfileParseError: If file cannot be read or parsed
            FileNotFoundError: If file does not exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Profile file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ProfileParseError(
                f"Invalid YAML syntax: {e}",
                file_path=file_path
            )
        except Exception as e:
            raise ProfileParseError(
                f"Failed to read file: {e}",
                file_path=file_path
            )

        return self._parse_data(data, file_path)

    def parse_string(self, yaml_content: str) -> ProfileCollection:
        """Parse profile YAML from a string.

        Args:
            yaml_content: YAML content as string

        Returns:
            ProfileCollection containing validated profiles

        Raises:
            ProfileParseError: If YAML cannot be parsed or validated
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ProfileParseError(f"Invalid YAML syntax: {e}")

        return self._parse_data(data, file_path=None)

    def _parse_data(
        self,
        data: Union[Dict, List],
        file_path: Optional[Path] = None
    ) -> ProfileCollection:
        """Parse and validate YAML data.

        Args:
            data: Parsed YAML data (dict or list)
            file_path: Optional file path for error reporting

        Returns:
            ProfileCollection containing validated profiles

        Raises:
            ProfileParseError: If validation fails
        """
        if data is None:
            raise ProfileParseError("Empty YAML file", file_path=file_path)

        # Handle both single profile and collection formats
        if isinstance(data, dict):
            # Check if it's a collection format (has 'profiles' key)
            if "profiles" in data:
                profiles_data = data
            else:
                # Single profile - wrap in collection
                profiles_data = {"profiles": [data]}
        elif isinstance(data, list):
            # List of profiles
            profiles_data = {"profiles": data}
        else:
            raise ProfileParseError(
                f"Invalid YAML structure. Expected dict or list, got {type(data).__name__}",
                file_path=file_path
            )

        # Validate with Pydantic
        try:
            collection = ProfileCollection.model_validate(profiles_data)
        except ValidationError as e:
            errors = json.loads(e.json())
            raise ProfileParseError(
                "Profile validation failed",
                file_path=file_path,
                errors=errors
            )

        # Validate MCP servers if enabled
        if self.validate_mcps:
            invalid_mcps = collection.validate_mcp_servers(self.available_mcps)
            if invalid_mcps:
                error_details = []
                for profile_name, invalid in invalid_mcps.items():
                    error_details.append(
                        f"  • Profile '{profile_name}': Unknown MCP servers: {', '.join(invalid)}"
                    )

                raise ProfileParseError(
                    f"Invalid MCP server names found:\n" +
                    "\n".join(error_details) +
                    f"\n\nAvailable MCP servers: {', '.join(self.available_mcps)}",
                    file_path=file_path
                )

        return collection

    def parse_directory(
        self,
        directory_path: Union[str, Path],
        pattern: str = "*.yaml"
    ) -> ProfileCollection:
        """Parse all profile YAML files in a directory.

        Args:
            directory_path: Path to directory containing profile files
            pattern: Glob pattern for profile files (default: *.yaml)

        Returns:
            ProfileCollection containing all profiles from all files

        Raises:
            ProfileParseError: If any file fails to parse
            FileNotFoundError: If directory does not exist
        """
        directory_path = Path(directory_path)

        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not directory_path.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")

        # Collect all profiles from all files
        all_profiles: List[Profile] = []
        errors: List[str] = []

        for file_path in sorted(directory_path.glob(pattern)):
            try:
                collection = self.parse_file(file_path)
                all_profiles.extend(collection.profiles)
            except ProfileParseError as e:
                errors.append(f"{file_path.name}: {e.message}")

        if errors:
            raise ProfileParseError(
                f"Failed to parse {len(errors)} profile file(s):\n" +
                "\n".join(f"  • {err}" for err in errors)
            )

        if not all_profiles:
            raise ProfileParseError(
                f"No valid profiles found in {directory_path} (pattern: {pattern})"
            )

        # Create collection and validate uniqueness across all files
        try:
            return ProfileCollection(profiles=all_profiles)
        except ValidationError as e:
            errors = json.loads(e.json())
            raise ProfileParseError(
                "Profile collection validation failed",
                errors=errors
            )

    def validate_profile_dict(self, profile_data: Dict) -> Profile:
        """Validate a profile dictionary without YAML parsing.

        Useful for testing or programmatic profile creation.

        Args:
            profile_data: Profile data as dictionary

        Returns:
            Validated Profile object

        Raises:
            ProfileParseError: If validation fails
        """
        try:
            profile = Profile.model_validate(profile_data)
        except ValidationError as e:
            errors = json.loads(e.json())
            raise ProfileParseError(
                "Profile validation failed",
                errors=errors
            )

        # Validate MCP servers if enabled
        if self.validate_mcps:
            invalid_mcps = [
                mcp for mcp in profile.mcps
                if mcp not in self.available_mcps
            ]
            if invalid_mcps:
                raise ProfileParseError(
                    f"Profile '{profile.name}' contains invalid MCP servers: " +
                    f"{', '.join(invalid_mcps)}\n" +
                    f"Available: {', '.join(self.available_mcps)}"
                )

        return profile


def parse_profile_file(
    file_path: Union[str, Path],
    validate_mcps: bool = True,
    available_mcps: Optional[List[str]] = None
) -> ProfileCollection:
    """Convenience function to parse a profile file.

    Args:
        file_path: Path to the YAML file
        validate_mcps: Whether to validate MCP server names
        available_mcps: List of available MCP server names

    Returns:
        ProfileCollection containing validated profiles

    Raises:
        ProfileParseError: If parsing or validation fails
        FileNotFoundError: If file does not exist
    """
    parser = ProfileParser(validate_mcps=validate_mcps, available_mcps=available_mcps)
    return parser.parse_file(file_path)


def parse_profile_string(
    yaml_content: str,
    validate_mcps: bool = True,
    available_mcps: Optional[List[str]] = None
) -> ProfileCollection:
    """Convenience function to parse profile YAML from a string.

    Args:
        yaml_content: YAML content as string
        validate_mcps: Whether to validate MCP server names
        available_mcps: List of available MCP server names

    Returns:
        ProfileCollection containing validated profiles

    Raises:
        ProfileParseError: If parsing or validation fails
    """
    parser = ProfileParser(validate_mcps=validate_mcps, available_mcps=available_mcps)
    return parser.parse_string(yaml_content)

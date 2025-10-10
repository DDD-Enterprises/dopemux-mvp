"""
Dopemux Profile Manager - YAML Parser

Loads and validates profile YAML files using Pydantic models.
Handles profile discovery, parsing, and validation.
"""

import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import ValidationError

from .profile_models import (
    Profile,
    ProfileSet,
    ProfileValidationError,
    validate_mcp_servers,
    VALID_MCP_SERVERS,
)


class ProfileParser:
    """YAML profile parser with validation and discovery"""

    def __init__(self, profile_dir: Optional[Path] = None):
        """
        Initialize parser with profile directory.

        Args:
            profile_dir: Directory containing .yaml profile files
                        Defaults to ~/.config/dopemux/profiles
        """
        if profile_dir is None:
            profile_dir = Path.home() / ".config" / "dopemux" / "profiles"

        self.profile_dir = Path(profile_dir)
        self._available_mcps = VALID_MCP_SERVERS

    def discover_profiles(self) -> List[Path]:
        """
        Discover all .yaml files in profile directory.

        Returns:
            List of Path objects for .yaml files

        Raises:
            FileNotFoundError: If profile directory doesn't exist
        """
        if not self.profile_dir.exists():
            raise FileNotFoundError(
                f"Profile directory not found: {self.profile_dir}\n"
                f"Create it with: mkdir -p {self.profile_dir}"
            )

        yaml_files = list(self.profile_dir.glob("*.yaml"))
        yml_files = list(self.profile_dir.glob("*.yml"))

        return sorted(yaml_files + yml_files)

    def load_profile(self, path: Path) -> Profile:
        """
        Load and validate a single profile from YAML file.

        Args:
            path: Path to .yaml profile file

        Returns:
            Validated Profile object

        Raises:
            ProfileValidationError: If profile is invalid
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML syntax is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {path}")

        # Load YAML
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ProfileValidationError(
                profile_name=path.stem,
                reason=f"Invalid YAML syntax: {e}",
                fix_suggestion="Check YAML formatting (indentation, colons, quotes)"
            )

        if not isinstance(data, dict):
            raise ProfileValidationError(
                profile_name=path.stem,
                reason="Profile must be a YAML dictionary/object",
                fix_suggestion="Ensure file starts with field definitions, not a list"
            )

        # Validate with Pydantic
        try:
            profile = Profile(**data)
        except ValidationError as e:
            # Extract first error for cleaner message
            error = e.errors()[0]
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]

            raise ProfileValidationError(
                profile_name=data.get("name", path.stem),
                reason=f"Field '{field}': {msg}",
                fix_suggestion="Check field values against schema"
            )

        # Validate MCP servers exist in Claude config
        is_valid, error_msg = validate_mcp_servers(profile.mcps, self._available_mcps)
        if not is_valid:
            raise ProfileValidationError(
                profile_name=profile.name,
                reason=error_msg,
                fix_suggestion="Use only MCP servers configured in Claude settings"
            )

        return profile

    def load_all_profiles(self, fail_fast: bool = False) -> ProfileSet:
        """
        Load all profiles from profile directory.

        Args:
            fail_fast: If True, raise on first error. If False, skip invalid profiles.

        Returns:
            ProfileSet with all valid profiles

        Raises:
            ProfileValidationError: If fail_fast=True and any profile is invalid
            FileNotFoundError: If profile directory doesn't exist
        """
        profile_paths = self.discover_profiles()

        if not profile_paths:
            raise FileNotFoundError(
                f"No profile files found in {self.profile_dir}\n"
                f"Create at least one profile: {self.profile_dir}/developer.yaml"
            )

        profiles: List[Profile] = []
        errors: List[tuple[Path, Exception]] = []

        for path in profile_paths:
            try:
                profile = self.load_profile(path)
                profiles.append(profile)
            except (ProfileValidationError, yaml.YAMLError) as e:
                if fail_fast:
                    raise
                errors.append((path, e))

        if not profiles:
            raise ProfileValidationError(
                profile_name="all",
                reason=f"No valid profiles found. {len(errors)} profiles had errors.",
                fix_suggestion="Fix validation errors or create valid profiles"
            )

        # Validate unique names across all profiles
        try:
            profile_set = ProfileSet(profiles=profiles)
        except ValidationError as e:
            raise ProfileValidationError(
                profile_name="profile_set",
                reason=str(e),
                fix_suggestion="Ensure all profile names are unique"
            )

        # Log skipped profiles if any
        if errors:
            print(f"⚠️  Warning: Skipped {len(errors)} invalid profile(s):")
            for path, error in errors:
                print(f"   - {path.name}: {str(error)[:100]}...")

        return profile_set

    def validate_profile_file(self, path: Path) -> tuple[bool, str]:
        """
        Validate a profile file without loading it into memory.

        Args:
            path: Path to profile file

        Returns:
            Tuple of (is_valid, message)
            - If valid: (True, "Profile 'name' is valid")
            - If invalid: (False, "Error: validation message")
        """
        try:
            profile = self.load_profile(path)
            return True, f"Profile '{profile.name}' is valid ✅"
        except ProfileValidationError as e:
            return False, f"Error: {e}"
        except Exception as e:
            return False, f"Error: Unexpected error: {e}"

    def set_available_mcps(self, mcps: set[str]):
        """
        Override available MCP servers (for testing or custom Claude configs).

        Args:
            mcps: Set of available MCP server names
        """
        self._available_mcps = mcps


def load_profile_from_file(path: Path) -> Profile:
    """
    Convenience function to load a single profile.

    Args:
        path: Path to .yaml profile file

    Returns:
        Validated Profile object

    Raises:
        ProfileValidationError: If profile is invalid
    """
    parser = ProfileParser()
    return parser.load_profile(path)


def load_all_profiles(profile_dir: Optional[Path] = None, fail_fast: bool = False) -> ProfileSet:
    """
    Convenience function to load all profiles from directory.

    Args:
        profile_dir: Directory containing profiles (default: ~/.config/dopemux/profiles)
        fail_fast: If True, raise on first error

    Returns:
        ProfileSet with all valid profiles

    Raises:
        ProfileValidationError: If fail_fast=True and any profile is invalid
    """
    parser = ProfileParser(profile_dir)
    return parser.load_all_profiles(fail_fast=fail_fast)


# CLI validation helper
def validate_profile_cli(profile_path: str) -> int:
    """
    CLI helper to validate a profile file.

    Args:
        profile_path: Path to profile file (string)

    Returns:
        Exit code: 0 if valid, 1 if invalid
    """
    path = Path(profile_path).expanduser()

    parser = ProfileParser()
    is_valid, message = parser.validate_profile_file(path)

    print(message)
    return 0 if is_valid else 1


if __name__ == "__main__":
    # Quick test if run directly
    import sys
    from .profile_models import create_developer_profile, create_minimal_profile
    import tempfile

    print("Testing profile parser...")

    # Create temporary test profiles
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Test 1: Write and load minimal profile
        print("\nTest 1: Minimal profile")
        minimal = create_minimal_profile()
        minimal_path = tmp_path / "minimal.yaml"

        minimal_yaml = f"""
name: {minimal.name}
display_name: {minimal.display_name}
description: {minimal.description}
mcps:
  - conport
"""
        minimal_path.write_text(minimal_yaml)

        parser = ProfileParser(tmp_path)
        try:
            loaded = parser.load_profile(minimal_path)
            print(f"✅ Loaded: {loaded.name}")
        except Exception as e:
            print(f"❌ Failed: {e}")

        # Test 2: Write and load developer profile
        print("\nTest 2: Developer profile")
        dev = create_developer_profile()
        dev_path = tmp_path / "developer.yaml"

        dev_yaml = f"""
name: {dev.name}
display_name: {dev.display_name}
description: {dev.description}
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
        dev_path.write_text(dev_yaml)

        try:
            loaded_dev = parser.load_profile(dev_path)
            print(f"✅ Loaded: {loaded_dev.name}")
            print(f"   MCPs: {', '.join(loaded_dev.mcps)}")
            print(f"   ADHD: energy={loaded_dev.adhd_config.energy_preference}")
        except Exception as e:
            print(f"❌ Failed: {e}")

        # Test 3: Load all profiles
        print("\nTest 3: Load all profiles")
        try:
            profile_set = parser.load_all_profiles()
            print(f"✅ Loaded {len(profile_set.profiles)} profiles: {', '.join(profile_set.list_names())}")
        except Exception as e:
            print(f"❌ Failed: {e}")

        # Test 4: Invalid profile (missing conport)
        print("\nTest 4: Invalid profile (should fail)")
        invalid_path = tmp_path / "invalid.yaml"
        invalid_yaml = """
name: invalid
display_name: Invalid
description: Missing conport
mcps:
  - serena-v2
"""
        invalid_path.write_text(invalid_yaml)

        is_valid, msg = parser.validate_profile_file(invalid_path)
        if not is_valid:
            print(f"✅ Correctly rejected")
            print(f"   Message: {msg[:100]}...")
        else:
            print(f"❌ Should have been rejected")

    print("\nAll parser tests complete!")

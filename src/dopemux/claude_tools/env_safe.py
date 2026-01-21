"""
Environment Safe Tools for Claude-Code-Tools

Provides secure environment variable inspection without exposing
sensitive values. Based on Claude-Code-Tools env-safe functionality.

Allows AI agents to reason about environment configuration without
leaking secrets.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class EnvSafeError(Exception):
    """Raised when env-safe operations fail."""
    pass


class EnvSafe:
    """
    Secure environment variable inspection.

    Provides read-only access to environment variable keys and status
    without exposing actual values.
    """

    def __init__(self, env_file: str = ".env"):
        """
        Initialize env-safe tools.

        Args:
            env_file: Path to environment file (default: .env)
        """
        self.env_file = Path(env_file)

    def list(self, show_status: bool = False) -> Dict[str, Dict[str, str]]:
        """
        List all environment variable keys.

        Args:
            show_status: Whether to show set/empty status

        Returns:
            Dict mapping keys to status info
        """
        try:
            variables = self._load_env_file()

            result = {}
            for key in sorted(variables.keys()):
                if show_status:
                    status = "SET" if variables[key] else "EMPTY"
                    result[key] = {"status": status}
                else:
                    result[key] = {}

            return result

        except Exception as e:
            raise EnvSafeError(f"Failed to list environment variables: {e}")

            logger.error(f"Error: {e}")
    def check(self, key: str) -> bool:
        """
        Check if an environment variable is present.

        Args:
            key: Variable name to check

        Returns:
            True if variable exists, False otherwise
        """
        try:
            variables = self._load_env_file()
            return key in variables
        except Exception as e:
            logger.warning(f"Error checking env var {key}: {e}")
            return False

    def count(self) -> Dict[str, int]:
        """
        Count total variables and set vs empty.

        Returns:
            Dict with counts
        """
        try:
            variables = self._load_env_file()

            total = len(variables)
            set_count = sum(1 for v in variables.values() if v)
            empty_count = total - set_count

            return {
                "total": total,
                "set": set_count,
                "empty": empty_count
            }

        except Exception as e:
            raise EnvSafeError(f"Failed to count variables: {e}")

            logger.error(f"Error: {e}")
    def validate(self) -> Dict[str, Any]:
        """
        Validate .env file syntax.

        Returns:
            Dict with validation results
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }

            if not self.env_file.exists():
                validation_result["valid"] = False
                validation_result["errors"].append("Environment file does not exist")
                return validation_result

            content = self.env_file.read_text(encoding='utf-8')

            # Check for basic syntax issues
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Check for key=value format
                if '=' not in line:
                    validation_result["errors"].append(
                        f"Line {i}: Missing '=' separator"
                    )
                    validation_result["valid"] = False
                    continue

                key, value = line.split('=', 1)
                key = key.strip()

                # Validate key format
                if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
                    validation_result["warnings"].append(
                        f"Line {i}: Key '{key}' doesn't follow naming convention (should be UPPER_CASE)"
                    )

                # Check for unquoted values with spaces (basic check)
                if ' ' in value and not (value.startswith('"') and value.endswith('"')):
                    validation_result["warnings"].append(
                        f"Line {i}: Value contains spaces but isn't quoted"
                    )

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Failed to validate file: {e}"],
                "warnings": []
            }

            logger.error(f"Error: {e}")
    def _load_env_file(self) -> Dict[str, str]:
        """
        Load and parse .env file.

        Returns:
            Dict of variable key -> value (empty string for unset)
        """
        variables = {}

        # Load from actual environment first
        for key, value in os.environ.items():
            variables[key] = value

        # Override with .env file values
        if self.env_file.exists():
            try:
                content = self.env_file.read_text(encoding='utf-8')

                for line in content.splitlines():
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse key=value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]

                        variables[key] = value

            except Exception as e:
                logger.warning(f"Error loading .env file: {e}")

        return variables
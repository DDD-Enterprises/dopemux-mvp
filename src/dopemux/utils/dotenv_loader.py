"""
Utility module for loading .env files safely.
Handles cases where python-dotenv might not be installed.
"""
import warnings
from typing import Any, Dict, Optional, Union

try:
    from dotenv import load_dotenv as _load_dotenv
    _DOTENV_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DOTENV_AVAILABLE = False

    def _load_dotenv(*args: Any, **kwargs: Any) -> bool:
        """Fallback load_dotenv when python-dotenv is unavailable."""
        return False


def load_dotenv(*args: Any, **kwargs: Any) -> bool:
    """
    Load environment variables from a .env file.
    Safely wraps dotenv.load_dotenv to handle missing dependency.

    Args:
        *args: Passed to dotenv.load_dotenv
        **kwargs: Passed to dotenv.load_dotenv

    Returns:
        bool: True if environment variables were loaded (or dotenv call succeeded), False otherwise.
    """
    return _load_dotenv(*args, **kwargs)


def is_dotenv_available() -> bool:
    """Check if python-dotenv is installed."""
    return _DOTENV_AVAILABLE


def check_dotenv_support() -> None:
    """
    Check if python-dotenv is installed and warn if not.
    Use this when environment variables are expected to be loaded from .env.
    """
    if not _DOTENV_AVAILABLE:
        warnings.warn(
            "python-dotenv not installed; environment variables from .env files "
            "will not be auto-loaded. Install python-dotenv to enable this feature.",
            RuntimeWarning,
        )

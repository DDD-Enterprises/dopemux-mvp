"""CLI bootstrap utilities for initialization and side effects."""

import sys
from pathlib import Path

from .utils.dotenv_loader import check_dotenv_support, load_dotenv


def load_env() -> None:
    """Load environment variables from .env file."""
    check_dotenv_support()
    load_dotenv()


def configure_sys_path() -> None:
    """Configure sys.path for genetic-agent and service imports."""
    services_path = Path(__file__).resolve().parent.parent / "services"
    if str(services_path) not in sys.path:
        sys.path.insert(0, str(services_path))

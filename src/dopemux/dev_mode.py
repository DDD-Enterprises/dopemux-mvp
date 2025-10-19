#!/usr/bin/env python3
"""
Development Mode Detection and Management

Auto-detects local development checkouts of MCP servers and dopemux itself.
Enables contributors to work on Zen MCP, dopemux core, or any MCP server.
"""

import os
from pathlib import Path
from typing import Optional, Dict


class DevMode:
    """Detects and manages development mode settings."""

    # Standard development locations (checked in order)
    STANDARD_DEV_PATHS = {
        "zen": [
            "~/code/zen-mcp-server",
            "~/zen-mcp-server",
            "~/dev/zen-mcp-server"
        ],
        "conport": [
            "~/code/conport-mcp",
            "~/conport-mcp"
        ],
        "serena": [
            "~/code/serena-lsp",
            "~/serena-lsp"
        ]
    }

    @staticmethod
    def is_active() -> bool:
        """
        Check if development mode is active.

        Returns True if:
        - DOPEMUX_DEV_MODE=true env var set
        - Running from within dopemux repo (has pyproject.toml + src/dopemux/)
        - Any component dev path detected
        """
        # Explicit env var
        if os.getenv("DOPEMUX_DEV_MODE") == "true":
            return True

        # Auto-detect: inside dopemux repo?
        if (Path("pyproject.toml").exists() and
            (Path("src/dopemux").exists() or
             Path("docker/mcp-servers").exists())):
            return True

        # Check for any dev component paths
        for component in DevMode.STANDARD_DEV_PATHS.keys():
            if DevMode.get_component_path(component):
                return True

        return False

    @staticmethod
    def get_component_path(component: str) -> Optional[Path]:
        """
        Get development path for component if available.

        Checks (in order):
        1. {COMPONENT}_DEV_PATH env var
        2. Standard locations (~/code/{component}, etc.)
        3. Returns None if not found

        Args:
            component: Component name (zen, conport, serena, etc.)

        Returns:
            Path to component dev checkout, or None
        """
        # Check env var first (explicit override)
        env_var = f"{component.upper()}_DEV_PATH"
        if os.getenv(env_var):
            path = Path(os.getenv(env_var)).expanduser()
            if path.exists():
                return path

        # Check standard locations
        for path_str in DevMode.STANDARD_DEV_PATHS.get(component, []):
            path = Path(path_str).expanduser()

            # Validate path has expected structure
            if component == "zen" and path.exists() and (path / "server.py").exists():
                return path
            elif path.exists():
                return path

        return None

    @staticmethod
    def get_all_dev_components() -> Dict[str, Optional[Path]]:
        """
        Get all detected development components.

        Returns:
            Dict mapping component names to dev paths (None if not in dev mode)
        """
        components = {}

        for component in DevMode.STANDARD_DEV_PATHS.keys():
            dev_path = DevMode.get_component_path(component)
            if dev_path:
                components[component] = dev_path

        return components

    @staticmethod
    def use_test_databases() -> bool:
        """Check if test databases should be used instead of production."""
        # Explicit env var
        if os.getenv("DOPEMUX_USE_TEST_DB") == "true":
            return True

        # Auto: if dev mode active
        return DevMode.is_active()

    @staticmethod
    def get_log_level() -> str:
        """Get appropriate log level for dev mode."""
        if DevMode.is_active():
            return os.getenv("LOG_LEVEL", "DEBUG")
        return "INFO"

    @staticmethod
    def get_database_dir() -> Path:
        """Get database directory (test vs production)."""
        if DevMode.use_test_databases():
            return Path.home() / ".dopemux" / "dev" / "databases"
        return Path.home() / ".dopemux" / "databases"

    @staticmethod
    def should_skip_service(service: str) -> bool:
        """Check if service should be skipped in dev mode."""
        skip_services = os.getenv("DOPEMUX_SKIP_SERVICES", "").split(",")

        # Clean and check
        skip_services = [s.strip() for s in skip_services if s.strip()]

        return service in skip_services

    @staticmethod
    def get_status() -> Dict[str, any]:
        """
        Get comprehensive dev mode status.

        Returns:
            Dictionary with dev mode state, component paths, settings
        """
        return {
            "active": DevMode.is_active(),
            "test_databases": DevMode.use_test_databases(),
            "log_level": DevMode.get_log_level(),
            "database_dir": str(DevMode.get_database_dir()),
            "dev_components": {
                name: str(path) if path else None
                for name, path in DevMode.get_all_dev_components().items()
            },
            "skip_services": os.getenv("DOPEMUX_SKIP_SERVICES", "").split(",")
        }

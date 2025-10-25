"""
Workspace Mapper - Map Applications to Workspace Paths

Maps application names to workspace paths for ADHD activity tracking.
Uses config.json for user-defined mappings.

ADHD Benefit: Know which workspace you're in based on active application.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class WorkspaceMapper:
    """
    Maps application names to workspace paths.

    Uses config.json for user-defined mappings.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize workspace mapper.

        Args:
            config_path: Path to config file with app → workspace mappings
        """
        self.config_path = config_path
        self.mappings: Dict[str, Optional[str]] = {}
        self.default_workspace: Optional[str] = None

        self._load_config()

    def _load_config(self):
        """Load workspace mappings from config file"""
        try:
            config_file = Path(__file__).parent / self.config_path

            if not config_file.exists():
                logger.warning(f"Config file not found: {config_file}, using defaults")
                self._load_defaults()
                return

            with open(config_file, "r") as f:
                config = json.load(f)

            self.mappings = config.get("app_mappings", {})
            self.default_workspace = config.get("default_workspace", None)

            logger.info(f"Loaded {len(self.mappings)} app mappings from {config_file}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            self._load_defaults()

    def _load_defaults(self):
        """Load default workspace mappings"""
        # Default mappings for common development apps
        self.mappings = {
            "Claude Code": "/Users/hue/code/dopemux-mvp",
            "Code": "/Users/hue/code/dopemux-mvp",  # VS Code
            "Visual Studio Code": "/Users/hue/code/dopemux-mvp",
            "Terminal": "/Users/hue/code/dopemux-mvp",
            "iTerm2": "/Users/hue/code/dopemux-mvp",
            "Cursor": "/Users/hue/code/dopemux-mvp",
            # Non-development apps (None = not tracked)
            "Google Chrome": None,
            "Chrome": None,
            "Safari": None,
            "Firefox": None,
            "Slack": None,
            "Mail": None,
            "Messages": None,
            "Spotify": None
        }
        self.default_workspace = None

    def get_workspace(self, app_name: str) -> Optional[str]:
        """
        Get workspace path for given application.

        Args:
            app_name: Application name (e.g., "Claude Code")

        Returns:
            Workspace path or None if app not mapped/not tracked
        """
        # Try exact match first
        if app_name in self.mappings:
            return self.mappings[app_name]

        # Try case-insensitive match
        app_lower = app_name.lower()
        for mapped_app, workspace in self.mappings.items():
            if mapped_app.lower() == app_lower:
                return workspace

        # Try partial match (e.g., "Code" matches "Visual Studio Code")
        for mapped_app, workspace in self.mappings.items():
            if app_lower in mapped_app.lower() or mapped_app.lower() in app_lower:
                logger.debug(f"Partial match: {app_name} → {mapped_app} → {workspace}")
                return workspace

        # No match found
        logger.debug(f"No workspace mapping for app: {app_name}")
        return self.default_workspace

    def is_development_app(self, app_name: str) -> bool:
        """
        Check if app is a development/coding application.

        Args:
            app_name: Application name

        Returns:
            True if app maps to a workspace (is tracked)
        """
        workspace = self.get_workspace(app_name)
        return workspace is not None

    def reload_config(self):
        """Reload config file (useful for live updates)"""
        logger.info("Reloading workspace mappings...")
        self._load_config()

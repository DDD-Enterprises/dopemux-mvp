"""
Workspace Mapper - Maps Applications to Workspaces

Maps application names to workspace paths for context tracking.
"""

import json
import os
from typing import Dict, Optional

import logging
logger = logging.getLogger(__name__)


class WorkspaceMapper:
    """
    Maps application names to workspace paths.

    Provides user-configurable mappings from applications to development workspaces.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize workspace mapper.

        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = config_path
        self.mappings: Dict[str, str] = {}

        self._load_config()

    def _load_config(self):
        """Load workspace mappings from config file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.mappings = config.get("workspace_mappings", {})
                    logger.info(f"Loaded {len(self.mappings)} workspace mappings")
            else:
                # Default mappings
                self.mappings = {
                    "Visual Studio Code": "/Users/hue/code",
                    "Cursor": "/Users/hue/code",
                    "PyCharm": "/Users/hue/code",
                    "WebStorm": "/Users/hue/code",
                    "Terminal": "/Users/hue/code",
                    "iTerm2": "/Users/hue/code"
                }
                self._save_config()
                logger.info("Created default workspace mappings")

        except Exception as e:
            logger.error(f"Error loading workspace config: {e}")
            self.mappings = {}

    def _save_config(self):
        """Save workspace mappings to config file."""
        try:
            config = {"workspace_mappings": self.mappings}
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving workspace config: {e}")

    def get_workspace(self, app_name: str) -> Optional[str]:
        """
        Get workspace path for application.

        Args:
            app_name: Application name

        Returns:
            Workspace path or None if not mapped
        """
        return self.mappings.get(app_name)

    def add_mapping(self, app_name: str, workspace_path: str):
        """
        Add workspace mapping.

        Args:
            app_name: Application name
            workspace_path: Workspace path
        """
        self.mappings[app_name] = workspace_path
        self._save_config()
        logger.info(f"Added mapping: {app_name} → {workspace_path}")

    def remove_mapping(self, app_name: str):
        """
        Remove workspace mapping.

        Args:
            app_name: Application name
        """
        if app_name in self.mappings:
            del self.mappings[app_name]
            self._save_config()
            logger.info(f"Removed mapping for: {app_name}")
        else:
            logger.warning(f"No mapping found for: {app_name}")

    def list_mappings(self) -> Dict[str, str]:
        """List all workspace mappings."""
        return self.mappings.copy()
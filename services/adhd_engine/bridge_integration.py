"""
Integration Bridge Client for ADHD Engine.
Replaces direct SQLite access with HTTP API calls through the bridge.
"""

import sys
import os

# Add parent to path for shared client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.integrations.bridge_client import IntegrationBridgeClient


class ConPortBridgeAdapter:
    """
    Adapter that provides same interface as ConPortSQLiteClient
    but uses Integration Bridge HTTP API instead of direct SQLite.
    
    Drop-in replacement for conport_client.py
    """

    def __init__(self, workspace_id: str):
        """Initialize with Integration Bridge client."""
        self.workspace_id = workspace_id
        self.bridge = IntegrationBridgeClient(source_plane="cognitive_plane")

    async def write_custom_data(
        self,
        category: str,
        key: str,
        value: any
    ) -> bool:
        """Save custom data via bridge (replaces SQLite write)."""
        return await self.bridge.save_custom_data(
            workspace_id=self.workspace_id,
            category=category,
            key=key,
            value=value
        )

    async def get_custom_data(
        self,
        category: str,
        key: Optional[str] = None
    ) -> any:
        """Get custom data via bridge (replaces SQLite read)."""
        return await self.bridge.get_custom_data(
            workspace_id=self.workspace_id,
            category=category,
            key=key
        )

    async def health_check(self) -> dict:
        """Check bridge connectivity."""
        return await self.bridge.health_check()

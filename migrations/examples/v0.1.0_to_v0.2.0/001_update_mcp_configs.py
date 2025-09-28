"""
Migration: v0.1.0 to v0.2.0 - Update MCP server configurations

Example migration showing how to update MCP server configurations
when new versions introduce configuration changes.
"""

import json
from pathlib import Path
from typing import Dict, Any


def migrate_forward(project_root: Path) -> bool:
    """
    Apply migration: v0.1.0 → v0.2.0

    Updates MCP server configurations to new format.
    """
    try:
        # Update MCP broker configurations
        broker_config = project_root / "config" / "mcp" / "broker.yaml"
        if broker_config.exists():
            # Example: Add new timeout settings
            print("  → Adding timeout configurations to MCP broker")

        # Update individual MCP server configs
        mcp_servers_dir = project_root / "docker" / "mcp-servers"
        if mcp_servers_dir.exists():
            print("  → Updating MCP server Docker configurations")

        print("  ✅ MCP configurations updated")
        return True

    except Exception as e:
        print(f"  ❌ Migration failed: {e}")
        return False


def migrate_backward(project_root: Path) -> bool:
    """
    Rollback migration: v0.2.0 → v0.1.0

    Reverts MCP server configurations to previous format.
    """
    try:
        print("  → Reverting MCP configuration changes")

        # Remove v0.2.0 specific configurations
        # Restore v0.1.0 format

        print("  ✅ MCP configuration rollback complete")
        return True

    except Exception as e:
        print(f"  ❌ Rollback failed: {e}")
        return False


# Migration metadata
MIGRATION_INFO = {
    "version_from": "0.1.0",
    "version_to": "0.2.0",
    "description": "Update MCP server configurations for new timeout settings",
    "breaking_changes": False,
    "estimated_duration_seconds": 30,
    "requires_restart": ["mcp-servers"]
}
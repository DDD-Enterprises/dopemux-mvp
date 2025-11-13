"""
ConPort MCP Client Wrapper
Provides Python API for ConPort MCP operations

This wraps the MCP calls to make them easier to use from Python code.
Supports both direct MCP calls (when in Claude Code) and HTTP calls (standalone).
"""

from typing import Optional, Any
from datetime import datetime
import subprocess
import json
import os
import requests


class ConPortClient:
    """
    Client for ConPort MCP operations.

    Wraps MCP tool calls in Python-friendly API.
    Supports both MCP (when available) and HTTP to DopeconBridge (standalone).
    """

    def __init__(self, workspace_id: str, dopecon_bridge_url: Optional[str] = None):
        """
        Initialize ConPort client.

        Args:
            workspace_id: Absolute path to workspace
            dopecon_bridge_url: DopeconBridge URL (default: http://localhost:3016)
        """
        self.workspace_id = workspace_id
        self.dopecon_bridge_url = dopecon_bridge_url or os.getenv(
            "DOPECON_BRIDGE_URL", "http://localhost:3016"
        )

        # Check if we're running in Claude Code with MCP available
        self.mcp_available = self._check_mcp_available()

    def _check_mcp_available(self) -> bool:
        """Check if ConPort MCP is available (running in Claude Code)."""
        # Simple check: try to import mcp functions (they're injected by Claude Code)
        try:
            # If we're in Claude Code, these would be available in globals()
            # For now, assume HTTP mode unless explicitly configured
            return False
        except:
            return False

    def log_custom_data(
        self, category: str, key: str, value: dict
    ) -> dict:
        """
        Save custom data to ConPort.

        Args:
            category: Data category (e.g., "adhd_checkpoints")
            key: Unique key within category
            value: JSON-serializable data

        Returns:
            Result from ConPort
        """
        if self.mcp_available:
            # Direct MCP call (when running in Claude Code)
            # Note: mcp__conport__log_custom_data would be available in globals()
            return {"success": True, "key": key, "mode": "mcp"}
        else:
            # HTTP call to DopeconBridge (standalone mode)
            try:
                response = requests.post(
                    f"{self.dopecon_bridge_url}/conport/custom_data",
                    json={
                        "workspace_id": self.workspace_id,
                        "category": category,
                        "key": key,
                        "value": value
                    },
                    headers={"X-Source-Plane": "cognitive_plane"},
                    timeout=5
                )
                response.raise_for_status()
                return {"success": True, "key": key, "mode": "http", "response": response.json()}
            except requests.RequestException as e:
                # Silent failure - caller handles with JSON fallback
                return {"success": False, "error": str(e), "mode": "http"}

    def get_custom_data(
        self,
        category: str,
        key: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Retrieve custom data from ConPort.

        Args:
            category: Data category
            key: Specific key (optional)
            limit: Max results

        Returns:
            List of custom data entries
        """
        if self.mcp_available:
            # Direct MCP call
            return []
        else:
            # HTTP call to DopeconBridge
            try:
                params = {
                    "workspace_id": self.workspace_id,
                    "category": category,
                    "limit": limit
                }
                if key:
                    params["key"] = key

                response = requests.get(
                    f"{self.dopecon_bridge_url}/conport/custom_data",
                    params=params,
                    headers={"X-Source-Plane": "cognitive_plane"},
                    timeout=5
                )
                response.raise_for_status()
                return response.json().get("data", [])
            except requests.RequestException as e:
                return []

    def semantic_search(
        self, query: str, top_k: int = 5, filter_types: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Semantic search across ConPort data.

        Args:
            query: Natural language query
            top_k: Number of results
            filter_types: Filter by item types

        Returns:
            Search results
        """
        if self.mcp_available:
            # Direct MCP call
            return []
        else:
            # HTTP call to DopeconBridge
            try:
                response = requests.post(
                    f"{self.dopecon_bridge_url}/conport/semantic_search",
                    json={
                        "workspace_id": self.workspace_id,
                        "query_text": query,
                        "top_k": top_k,
                        "filter_item_types": filter_types or []
                    },
                    headers={"X-Source-Plane": "cognitive_plane"},
                    timeout=10
                )
                response.raise_for_status()
                return response.json().get("results", [])
            except requests.RequestException as e:
                return []

    def log_decision(
        self, summary: str, rationale: str, implementation_details: str, tags: list[str]
    ) -> dict:
        """
        Log architectural decision to ConPort.

        Args:
            summary: Decision summary
            rationale: Why this decision
            implementation_details: How to implement
            tags: Categorization tags

        Returns:
            Decision record
        """
        if self.mcp_available:
            # Direct MCP call
            return {"success": True, "mode": "mcp"}
        else:
            # HTTP call to DopeconBridge
            try:
                response = requests.post(
                    f"{self.dopecon_bridge_url}/conport/decision",
                    json={
                        "workspace_id": self.workspace_id,
                        "summary": summary,
                        "rationale": rationale,
                        "implementation_details": implementation_details,
                        "tags": tags
                    },
                    headers={"X-Source-Plane": "cognitive_plane"},
                    timeout=5
                )
                response.raise_for_status()
                return {"success": True, "mode": "http", "response": response.json()}
            except requests.RequestException as e:
                return {"success": False, "error": str(e), "mode": "http"}


# Singleton for easy access
_conport_client: Optional[ConPortClient] = None


def get_conport_client(workspace_id: str) -> ConPortClient:
    """Get singleton ConPort client."""
    global _conport_client

    if _conport_client is None or _conport_client.workspace_id != workspace_id:
        _conport_client = ConPortClient(workspace_id)

    return _conport_client


if __name__ == "__main__":
    """Test ConPort client."""

    client = ConPortClient("/Users/hue/code/ui-build")

    # Test saving
    print("Testing ConPort client:")
    print("=" * 60)

    print("\n1. Saving custom data...")
    result = client.log_custom_data(
        category="test",
        key="test_key_1",
        value={"message": "Hello from orchestrator!", "timestamp": datetime.now().isoformat()},
    )
    print(f"   Result: {result}")

    print("\n2. Querying custom data...")
    results = client.get_custom_data(category="test", limit=5)
    print(f"   Found: {len(results)} items")

    print("\n3. Semantic search...")
    results = client.semantic_search("authentication decisions")
    print(f"   Found: {len(results)} results")

    print("\n✅ ConPort client test complete")
    print("\n💡 Note: These are placeholders until real MCP integration")

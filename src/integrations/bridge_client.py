#!/usr/bin/env python3
"""
DopeconBridge HTTP Client.

Used by services to call DopeconBridge instead of direct database access.
Respects two-plane architecture and authority boundaries.
"""

import os
import aiohttp
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DopeconBridgeClient:
    """
    HTTP client for DopeconBridge API.

    Services use this to access ConPort data through the bridge,
    respecting authority boundaries and avoiding direct database access.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        source_plane: str = "cognitive_plane"
    ):
        """
        Initialize bridge client.

        Args:
            base_url: Bridge URL (default from env or localhost:3016)
            source_plane: Calling service's plane (default: cognitive_plane)
        """
        self.base_url = base_url or os.getenv(
            "DOPECON_BRIDGE_URL",
            f"http://localhost:{int(os.getenv('PORT_BASE', '3000')) + 16}"
        )
        self.source_plane = source_plane
        self.timeout = aiohttp.ClientTimeout(total=10)

        logger.info(f"DopeconBridge client initialized: {self.base_url}")

    async def save_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Dict[str, Any]
    ) -> bool:
        """
        Save custom data via DopeconBridge.

        Args:
            workspace_id: Workspace identifier
            category: Data category
            key: Unique key
            value: JSON-serializable data

        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/custom_data",
                    json={
                        "workspace_id": workspace_id,
                        "category": category,
                        "key": key,
                        "value": value
                    },
                    headers={"X-Source-Plane": self.source_plane}
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.debug(f"✅ Saved custom_data via bridge: {category}/{key}")
                        return result.get("success", True)
                    else:
                        error = await resp.text()
                        logger.error(f"❌ Bridge save failed ({resp.status}): {error}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"❌ Bridge connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error saving via bridge: {e}")
            return False

    async def get_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: Optional[str] = None,
        limit: int = 10
    ) -> Any:
        """
        Get custom data via DopeconBridge.

        Args:
            workspace_id: Workspace identifier
            category: Data category
            key: Optional specific key (None = all in category)
            limit: Maximum results

        Returns:
            Single value (if key provided) or dict of values (if key=None)
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "category": category,
                "limit": limit
            }
            if key:
                params["key"] = key

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/custom_data",
                    params=params,
                    headers={"X-Source-Plane": self.source_plane}
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        data = result.get("data", [])

                        # Return format matching old SQLite client
                        if key:
                            # Single value
                            return data[0] if data else None
                        else:
                            # Dict of all values in category
                            return {item["key"]: item["value"] for item in data}

                    else:
                        logger.error(f"❌ Bridge get failed ({resp.status})")
                        return None if key else {}

        except aiohttp.ClientError as e:
            logger.error(f"❌ Bridge connection failed: {e}")
            return None if key else {}
        except Exception as e:
            logger.error(f"❌ Unexpected error getting via bridge: {e}")
            return None if key else {}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check DopeconBridge health.

        Returns:
            Health status dict
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/kg/health",
                    headers={"X-Source-Plane": self.source_plane}
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {
                            "status": "unhealthy",
                            "bridge_status_code": resp.status
                        }

        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }


# Example usage
async def main():
    """Test bridge client"""
    client = DopeconBridgeClient()

    # Test save
    success = await client.save_custom_data(
        workspace_id="/test",
        category="test_category",
        key="test_key",
        value={"message": "test"}
    )
    print(f"Save: {'✅' if success else '❌'}")

    # Test get
    data = await client.get_custom_data(
        workspace_id="/test",
        category="test_category",
        key="test_key"
    )
    print(f"Get: {data}")

    # Health
    health = await client.health_check()
    print(f"Health: {health}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

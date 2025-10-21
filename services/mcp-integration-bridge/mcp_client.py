#!/usr/bin/env python3
"""
MCP Client for Integration Bridge.

Connects Integration Bridge to Dope Decision Graph database for custom_data persistence.
Uses direct PostgreSQL AGE access since bridge already has database connection.
"""

import os
import sys
import json
import asyncpg
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConPortMCPClient:
    """
    Client for Dope Decision Graph database operations from Integration Bridge.

    Since Integration Bridge already connects to PostgreSQL AGE for KG queries,
    we can directly access the Decision Graph tables without an additional MCP hop.

    This is architecturally sound because:
    - Bridge is the coordination layer (allowed to access shared database)
    - Eliminates HTTP→MCP→DB triple hop
    - Uses existing database connection pool
    - Respects authority boundaries via HTTP middleware
    """

    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        """
        Initialize Dope Decision Graph MCP client.

        Args:
            db_pool: Existing PostgreSQL connection pool (from main.py)
                    If None, creates own connection
        """
        self.db_pool = db_pool
        self.workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

        # Database configuration (shared with Dope Decision Graph)
        self.db_config = {
            "host": os.getenv("AGE_HOST", "localhost"),
            "port": int(os.getenv("AGE_PORT", "5455")),
            "database": os.getenv("AGE_DATABASE", "dopemux_knowledge_graph"),
            "user": os.getenv("AGE_USER", "dopemux_age"),
            "password": os.getenv("AGE_PASSWORD", "dopemux_age_dev_password")
        }

    async def initialize(self):
        """Initialize database connection if not provided."""
        if not self.db_pool:
            try:
                self.db_pool = await asyncpg.create_pool(
                    **self.db_config,
                    min_size=2,
                    max_size=10
                )
                logger.info("✅ Decision Graph MCP client initialized with own connection pool")
            except Exception as e:
                logger.error(f"❌ Failed to connect to ConPort database: {e}")
                raise
        else:
            logger.info("✅ Decision Graph MCP client using shared connection pool")

    async def close(self):
        """Close database connection if we created it."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("ConPort MCP client connection closed")

    async def save_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save custom data to Decision Graph database.

        Args:
            workspace_id: Workspace identifier
            category: Data category
            key: Unique key within category
            value: JSON-serializable data

        Returns:
            Success status with metadata
        """
        if not self.db_pool:
            raise RuntimeError("MCP client not initialized")

        try:
            # Serialize value to JSON
            value_json = json.dumps(value)
            timestamp = datetime.utcnow().isoformat()

            # Insert or update custom_data
            # Note: ConPort uses SQLite in some configs, PostgreSQL in others
            # This assumes PostgreSQL schema matching ConPort's custom_data table

            async with self.db_pool.acquire() as conn:
                # Upsert pattern for PostgreSQL
                await conn.execute(
                    """
                    INSERT INTO custom_data (workspace_id, category, key, value, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (workspace_id, category, key)
                    DO UPDATE SET value = $4, timestamp = $5
                    """,
                    workspace_id, category, key, value_json, timestamp
                )

            logger.info(f"✅ Saved custom_data: {category}/{key} to Decision Graph")

            return {
                "success": True,
                "workspace_id": workspace_id,
                "category": category,
                "key": key,
                "timestamp": timestamp
            }

        except Exception as e:
            logger.error(f"❌ Failed to save custom_data {category}/{key}: {e}")
            return {
                "success": False,
                "error": str(e),
                "category": category,
                "key": key
            }

    async def get_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve custom data from ConPort database.

        Args:
            workspace_id: Workspace identifier
            category: Data category
            key: Optional specific key (if None, get all in category)
            limit: Maximum results to return

        Returns:
            List of custom data entries
        """
        if not self.db_pool:
            raise RuntimeError("MCP client not initialized")

        try:
            async with self.db_pool.acquire() as conn:
                if key:
                    # Get specific key
                    row = await conn.fetchrow(
                        """
                        SELECT category, key, value, timestamp
                        FROM custom_data
                        WHERE workspace_id = $1 AND category = $2 AND key = $3
                        """,
                        workspace_id, category, key
                    )

                    if row:
                        return [{
                            "category": row["category"],
                            "key": row["key"],
                            "value": json.loads(row["value"]),
                            "timestamp": row["timestamp"]
                        }]
                    else:
                        return []

                else:
                    # Get all in category
                    rows = await conn.fetch(
                        """
                        SELECT category, key, value, timestamp
                        FROM custom_data
                        WHERE workspace_id = $1 AND category = $2
                        ORDER BY timestamp DESC
                        LIMIT $3
                        """,
                        workspace_id, category, limit
                    )

                    return [
                        {
                            "category": row["category"],
                            "key": row["key"],
                            "value": json.loads(row["value"]),
                            "timestamp": row["timestamp"]
                        }
                        for row in rows
                    ]

        except Exception as e:
            logger.error(f"❌ Failed to get custom_data {category}: {e}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Check ConPort database connection health."""
        if not self.db_pool:
            return {"status": "not_initialized", "error": "Connection pool not created"}

        try:
            async with self.db_pool.acquire() as conn:
                # Simple query to verify connection
                result = await conn.fetchval("SELECT COUNT(*) FROM custom_data")

                return {
                    "status": "healthy",
                    "custom_data_count": result,
                    "database": self.db_config["database"]
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Example usage
async def main():
    """Test MCP client"""
    client = ConPortMCPClient()
    await client.initialize()

    # Test save
    result = await client.save_custom_data(
        workspace_id="/test",
        category="test_category",
        key="test_key",
        value={"message": "test"}
    )
    print(f"Save result: {result}")

    # Test get
    data = await client.get_custom_data(
        workspace_id="/test",
        category="test_category",
        key="test_key"
    )
    print(f"Get result: {data}")

    # Health check
    health = await client.health_check()
    print(f"Health: {health}")

    await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

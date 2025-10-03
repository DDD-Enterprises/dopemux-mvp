"""
ConPort SQLite Client - Read-Only Data Access

Week 1: Direct SQLite access for MVP
Week 7+: Migrate to ConPort HTTP API service

Provides read-only access to:
- Progress entries (task completion data)
- Custom data (activity logs, ADHD state)

TECHNICAL DEBT: This violates service boundaries (2 services -> 1 database).
Documented for future refactor to proper HTTP API.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class ConPortSQLiteClient:
    """
    Read-only SQLite client for ConPort data access.

    Connects to ConPort's SQLite database in read-only mode to prevent
    write conflicts. Provides typed access to progress entries and custom data.
    """

    def __init__(self, db_path: str, workspace_id: str):
        """
        Initialize ConPort SQLite client.

        Args:
            db_path: Absolute path to context.db (e.g., /conport_data/context.db in Docker)
            workspace_id: Workspace identifier (e.g., /Users/hue/code/dopemux-mvp)
        """
        self.db_path = db_path
        self.workspace_id = workspace_id

        # Verify database exists
        if not Path(db_path).exists():
            logger.warning(f"⚠️ ConPort database not found at {db_path}")
            logger.warning("   ActivityTracker will use default data until database is available")
        else:
            logger.info(f"✅ ConPort database found: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get read-only SQLite connection."""
        try:
            # Read-only connection prevents accidental writes
            conn = sqlite3.connect(
                f"file:{self.db_path}?mode=ro",
                uri=True,
                timeout=5.0
            )
            conn.row_factory = sqlite3.Row  # Dict-like row access
            return conn

        except sqlite3.Error as e:
            logger.error(f"Failed to connect to ConPort database: {e}")
            raise

    def get_progress_entries(
        self,
        limit: int = 20,
        status_filter: Optional[str] = None,
        hours_ago: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent progress entries.

        Args:
            limit: Maximum number of entries to return
            status_filter: Optional status filter (TODO, IN_PROGRESS, DONE, BLOCKED)
            hours_ago: How many hours back to query

        Returns:
            List of progress entry dicts
        """
        conn = self._get_connection()

        try:
            # Calculate cutoff timestamp
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()

            # Build query
            query = "SELECT * FROM progress_entries WHERE timestamp > ?"
            params = [cutoff]

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            # Execute
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # Convert to dicts
            entries = [dict(row) for row in rows]
            logger.debug(f"📊 Retrieved {len(entries)} progress entries from ConPort")

            return entries

        except sqlite3.Error as e:
            logger.error(f"Failed to query progress entries: {e}")
            return []

        finally:
            conn.close()

    def get_custom_data(
        self,
        category: str,
        key: Optional[str] = None
    ) -> Any:
        """
        Get custom data by category and optional key.

        Args:
            category: Data category (e.g., 'activity_log', 'adhd_state')
            key: Optional specific key within category

        Returns:
            Single value (if key provided) or dict of all values in category
        """
        conn = self._get_connection()

        try:
            if key:
                # Get specific key
                cursor = conn.execute(
                    "SELECT value FROM custom_data WHERE category = ? AND key = ?",
                    (category, key)
                )
                row = cursor.fetchone()

                if row:
                    try:
                        return json.loads(row['value'])
                    except json.JSONDecodeError:
                        return row['value']  # Return as string if not JSON
                return None

            else:
                # Get all in category
                cursor = conn.execute(
                    "SELECT key, value FROM custom_data WHERE category = ?",
                    (category,)
                )
                rows = cursor.fetchall()

                result = {}
                for row in rows:
                    try:
                        result[row['key']] = json.loads(row['value'])
                    except json.JSONDecodeError:
                        result[row['key']] = row['value']

                logger.debug(f"📊 Retrieved {len(result)} items from category '{category}'")
                return result

        except sqlite3.Error as e:
            logger.error(f"Failed to query custom data: {e}")
            return None if key else {}

        finally:
            conn.close()

    def get_recent_decisions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent decisions (for ADHD context awareness).

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of decision dicts with id, summary, timestamp
        """
        conn = self._get_connection()

        try:
            cursor = conn.execute(
                "SELECT id, summary, timestamp FROM decisions ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()

            decisions = [dict(row) for row in rows]
            logger.debug(f"📊 Retrieved {len(decisions)} recent decisions from ConPort")

            return decisions

        except sqlite3.Error as e:
            logger.error(f"Failed to query decisions: {e}")
            return []

        finally:
            conn.close()

    def health_check(self) -> Dict[str, Any]:
        """
        Check if ConPort database is accessible.

        Returns:
            Health status dict
        """
        try:
            conn = self._get_connection()

            try:
                # Simple query to verify database works
                cursor = conn.execute("SELECT COUNT(*) as count FROM progress_entries")
                row = cursor.fetchone()
                total_entries = row['count']

                cursor = conn.execute("SELECT COUNT(*) as count FROM decisions")
                row = cursor.fetchone()
                total_decisions = row['count']

                return {
                    "status": "healthy",
                    "database": self.db_path,
                    "accessible": True,
                    "total_progress_entries": total_entries,
                    "total_decisions": total_decisions
                }

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"ConPort health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": self.db_path,
                "accessible": False,
                "error": str(e)
            }

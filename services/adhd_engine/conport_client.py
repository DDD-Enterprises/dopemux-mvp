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
    SQLite client for ConPort data access (read + write for Week 3).

    Week 3: Extended to support writes for ADHD state persistence
    Week 7+: Migrate to ConPort HTTP API service (proper boundaries)

    Connects to ConPort's SQLite database. Read operations use read-only mode,
    write operations use read-write mode. Provides typed access to progress
    entries and custom data.
    """

    def __init__(self, db_path: str, workspace_id: str, read_only: bool = True):
        """
        Initialize ConPort SQLite client.

        Args:
            db_path: Absolute path to context.db (e.g., /conport_data/context.db in Docker)
            workspace_id: Workspace identifier (e.g., /Users/hue/code/dopemux-mvp)
            read_only: Use read-only mode (default True for safety)
        """
        self.db_path = db_path
        self.workspace_id = workspace_id
        self.read_only = read_only

        # Verify database exists
        if not Path(db_path).exists():
            logger.warning(f"⚠️ ConPort database not found at {db_path}")
            logger.warning("   ActivityTracker will use default data until database is available")
        else:
            mode_str = "read-only" if read_only else "read-write"
            logger.info(f"✅ ConPort database found: {db_path} (mode: {mode_str})")

    def _get_connection(self, write_mode: bool = False) -> sqlite3.Connection:
        """
        Get SQLite connection (read-only or read-write).

        Args:
            write_mode: Force read-write mode for this connection

        Returns:
            SQLite connection
        """
        try:
            # Use read-only mode unless explicitly requesting writes
            if self.read_only and not write_mode:
                conn = sqlite3.connect(
                    f"file:{self.db_path}?mode=ro",
                    uri=True,
                    timeout=5.0
                )
            else:
                # Read-write mode for writes
                conn = sqlite3.connect(
                    self.db_path,
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

    # Week 3 Write Operations

    def write_custom_data(
        self,
        category: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Write custom data to ConPort (Week 3 integration).

        Args:
            category: Data category (e.g., 'adhd_state', 'cognitive_load')
            key: Unique key within category
            value: JSON-serializable value to store

        Returns:
            True if write succeeded, False otherwise
        """
        conn = self._get_connection(write_mode=True)

        try:
            # Serialize value to JSON
            value_json = json.dumps(value) if not isinstance(value, str) else value

            # Upsert (INSERT OR REPLACE)
            conn.execute(
                """
                INSERT OR REPLACE INTO custom_data (category, key, value, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (category, key, value_json, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()

            logger.debug(f"✅ Wrote custom_data: {category}/{key}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to write custom_data {category}/{key}: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def log_progress_entry(
        self,
        status: str,
        description: str,
        parent_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Create progress entry in ConPort (Week 3 integration).

        Args:
            status: Status (TODO, IN_PROGRESS, DONE, BLOCKED)
            description: Task description
            parent_id: Optional parent task ID

        Returns:
            New progress entry ID if successful, None otherwise
        """
        conn = self._get_connection(write_mode=True)

        try:
            cursor = conn.execute(
                """
                INSERT INTO progress_entries (status, description, parent_id, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (status, description, parent_id, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()

            entry_id = cursor.lastrowid
            logger.debug(f"✅ Created progress entry #{entry_id}: {description[:50]}")
            return entry_id

        except sqlite3.Error as e:
            logger.error(f"Failed to create progress entry: {e}")
            conn.rollback()
            return None

        finally:
            conn.close()
